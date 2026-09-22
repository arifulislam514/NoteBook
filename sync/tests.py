import uuid
from datetime import datetime, timezone, timedelta
from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from academic.models import Semester, Subject
from skills.models import Skill, SubSkill, SkillTopic, EvaluationQuestion, EvaluationAnswer
from sessions.models import TopicSession


class SyncTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='sync1@example.com', password='password123')
        self.user2 = User.objects.create_user(email='sync2@example.com', password='password123')

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

    def test_sync_push_create_and_server_changes(self):
        sem_id = str(uuid.uuid4())
        skill_id = str(uuid.uuid4())
        client_time = "2024-05-01T12:00:00+00:00"

        payload = {
            "last_sync": None,
            "changes": {
                "semesters": [
                    {
                        "id": sem_id,
                        "name": "Offline Semester",
                        "year": 2024,
                        "is_deleted": False,
                        "updated_at": client_time,
                    }
                ],
                "skills": [
                    {
                        "id": skill_id,
                        "name": "Offline Skill",
                        "is_deleted": False,
                        "updated_at": client_time,
                    }
                ]
            }
        }

        res = self.client1.post('/api/sync/push/', payload, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['success'])
        server_changes = res.data['data']['server_changes']
        self.assertEqual(len(server_changes['semesters']), 1)
        self.assertEqual(server_changes['semesters'][0]['id'], sem_id)
        self.assertEqual(server_changes['semesters'][0]['name'], 'Offline Semester')

        # Isolation test: user2 does not see user1's records in server_changes
        res2 = self.client2.post('/api/sync/push/', {"last_sync": None, "changes": {}}, format='json')
        self.assertEqual(len(res2.data['data']['server_changes']['semesters']), 0)

    def test_sync_conflict_resolution(self):
        sem_id = str(uuid.uuid4())
        older_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        newer_time = datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)

        # Server record with newer_time
        sem = Semester.objects.create(user=self.user1, id=sem_id, name="Server Version", year=2024)
        Semester.objects.filter(id=sem_id).update(updated_at=newer_time)

        # Client sends older change -> Should be ignored
        payload = {
            "last_sync": older_time.isoformat(),
            "changes": {
                "semesters": [
                    {
                        "id": sem_id,
                        "name": "Stale Client Version",
                        "year": 2024,
                        "is_deleted": False,
                        "updated_at": older_time.isoformat(),
                    }
                ]
            }
        }
        res = self.client1.post('/api/sync/push/', payload, format='json')
        self.assertEqual(res.status_code, 200)
        sem.refresh_from_db()
        self.assertEqual(sem.name, "Server Version")

        # Client sends even newer change -> Should overwrite
        even_newer_time = datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc)
        payload['changes']['semesters'][0]['name'] = "Newest Client Version"
        payload['changes']['semesters'][0]['updated_at'] = even_newer_time.isoformat()

        res2 = self.client1.post('/api/sync/push/', payload, format='json')
        self.assertEqual(res2.status_code, 200)
        sem.refresh_from_db()
        self.assertEqual(sem.name, "Newest Client Version")

    def test_sync_evaluation_questions_and_answers(self):
        skill = Skill.objects.create(user=self.user1, name="Python")
        sub = SubSkill.objects.create(skill=skill, name="Asyncio")
        topic = SkillTopic.objects.create(sub_skill=sub, title="Coroutines")

        q_id = str(uuid.uuid4())
        ans_id = str(uuid.uuid4())
        client_time = "2024-05-01T12:00:00+00:00"

        payload = {
            "last_sync": None,
            "changes": {
                "evaluation_questions": [
                    {
                        "id": q_id,
                        "level": "basic",
                        "text": "What is a coroutine?",
                        "order": 0,
                        "is_default": False,
                        "is_deleted": False,
                        "updated_at": client_time,
                    }
                ],
                "evaluation_answers": [
                    {
                        "id": ans_id,
                        "skill_topic_id": str(topic.id),
                        "level": "basic",
                        "question_id": q_id,
                        "is_deleted": False,
                        "updated_at": client_time,
                    }
                ]
            }
        }

        res = self.client1.post('/api/sync/push/', payload, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(EvaluationQuestion.objects.filter(id=q_id).exists())
        self.assertTrue(EvaluationAnswer.objects.filter(id=ans_id, question_id=q_id).exists())

        # Check server_changes returned
        server_changes = res.data['data']['server_changes']
        self.assertIn('evaluation_questions', server_changes)
        self.assertIn('evaluation_answers', server_changes)
        self.assertEqual(len(server_changes['evaluation_questions']), 1)
        self.assertEqual(len(server_changes['evaluation_answers']), 1)
        self.assertEqual(server_changes['evaluation_answers'][0]['question_id'], q_id)

    def test_sync_topic_sessions(self):
        skill = Skill.objects.create(user=self.user1, name="Rust")
        sub = SubSkill.objects.create(skill=skill, name="Ownership")
        topic = SkillTopic.objects.create(sub_skill=sub, title="Borrow Checker")

        sess_id = str(uuid.uuid4())
        start_time = "2024-05-01T10:00:00+00:00"
        client_time = "2024-05-01T10:30:00+00:00"

        # 1. Sync new session from client
        payload = {
            "last_sync": None,
            "changes": {
                "topic_sessions": [
                    {
                        "id": sess_id,
                        "mode": "stopwatch",
                        "timer_goal_seconds": None,
                        "academic_topic_id": None,
                        "skill_topic_id": str(topic.id),
                        "started_at": start_time,
                        "ended_at": None,
                        "duration_seconds": 600,
                        "is_completed": False,
                        "is_deleted": False,
                        "updated_at": client_time,
                    }
                ]
            }
        }

        res = self.client1.post('/api/sync/push/', payload, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(TopicSession.objects.filter(id=sess_id).exists())
        sess = TopicSession.objects.get(id=sess_id)
        self.assertEqual(sess.duration_seconds, 600)
        self.assertFalse(sess.is_completed)

        # 2. Sync update (session ended)
        end_time = "2024-05-01T11:00:00+00:00"
        later_client_time = "2024-05-01T11:00:00+00:00"
        payload_update = {
            "last_sync": client_time,
            "changes": {
                "topic_sessions": [
                    {
                        "id": sess_id,
                        "duration_seconds": 1800,
                        "is_completed": True,
                        "ended_at": end_time,
                        "is_deleted": False,
                        "updated_at": later_client_time,
                    }
                ]
            }
        }
        res2 = self.client1.post('/api/sync/push/', payload_update, format='json')
        self.assertEqual(res2.status_code, 200)
        sess.refresh_from_db()
        self.assertEqual(sess.duration_seconds, 1800)
        self.assertTrue(sess.is_completed)


