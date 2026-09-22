import uuid
from datetime import datetime, timezone, timedelta, date
from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from academic.models import Semester, Subject, Chapter, AcademicTopic
from skills.models import Skill, SubSkill, SkillTopic
from sessions.models import TopicSession


class SessionsAndAnalyticsTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='timer1@example.com', password='password123')
        self.user2 = User.objects.create_user(email='timer2@example.com', password='password123')

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

        # Setup Academic topic for user1
        self.sem = Semester.objects.create(user=self.user1, name="Fall 2024", year=2024)
        self.subj = Subject.objects.create(semester=self.sem, name="Physics")
        self.chap = Chapter.objects.create(subject=self.subj, name="Mechanics", order=0)
        self.acad_topic = AcademicTopic.objects.create(chapter=self.chap, title="Newton's Laws")

        # Setup Skill topic for user1
        self.skill = Skill.objects.create(user=self.user1, name="Mobile Dev")
        self.sub_skill = SubSkill.objects.create(skill=self.skill, name="Flutter")
        self.skill_topic = SkillTopic.objects.create(sub_skill=self.sub_skill, title="State Management")

    def test_session_lifecycle(self):
        # 1. Start a stopwatch session for an academic topic
        start_time = datetime.now(timezone.utc).isoformat()
        res = self.client1.post('/api/sessions/start/', {
            'topic_type': 'academic',
            'topic_id': str(self.acad_topic.id),
            'mode': 'stopwatch',
            'started_at': start_time,
        }, format='json')
        self.assertEqual(res.status_code, 201)
        session_id = res.data['data']['id']
        self.assertEqual(res.data['data']['mode'], 'stopwatch')
        self.assertEqual(res.data['data']['academic_topic_id'], str(self.acad_topic.id))
        self.assertEqual(res.data['data']['academic_topic_title'], "Newton's Laws")
        self.assertFalse(res.data['data']['is_completed'])

        # 2. Prevent starting another session while one is active
        res_conflict = self.client1.post('/api/sessions/start/', {
            'topic_type': 'skill',
            'topic_id': str(self.skill_topic.id),
            'mode': 'stopwatch',
            'started_at': start_time,
        }, format='json')
        self.assertEqual(res_conflict.status_code, 400)
        self.assertEqual(res_conflict.data['error'], "A session is already active. End it before starting a new one.")

        # 3. GET active session
        res_active = self.client1.get('/api/sessions/active/')
        self.assertEqual(res_active.status_code, 200)
        self.assertIsNotNone(res_active.data['data'])
        self.assertEqual(res_active.data['data']['id'], session_id)

        # 4. Update (pause) session: update duration_seconds
        res_pause = self.client1.patch(f'/api/sessions/{session_id}/', {
            'duration_seconds': 600,
        }, format='json')
        self.assertEqual(res_pause.status_code, 200)
        self.assertEqual(res_pause.data['data']['duration_seconds'], 600)
        self.assertFalse(res_pause.data['data']['is_completed'])

        # 5. End session: update duration_seconds, is_completed, ended_at
        end_time = datetime.now(timezone.utc).isoformat()
        res_end = self.client1.patch(f'/api/sessions/{session_id}/', {
            'duration_seconds': 1200,
            'is_completed': True,
            'ended_at': end_time,
        }, format='json')
        self.assertEqual(res_end.status_code, 200)
        self.assertEqual(res_end.data['data']['duration_seconds'], 1200)
        self.assertTrue(res_end.data['data']['is_completed'])

        # 6. Cannot update an already completed session
        res_after = self.client1.patch(f'/api/sessions/{session_id}/', {
            'duration_seconds': 1500,
        }, format='json')
        self.assertEqual(res_after.status_code, 400)
        self.assertEqual(res_after.data['error'], "Session already completed")

        # 7. GET active session now returns None
        res_none = self.client1.get('/api/sessions/active/')
        self.assertEqual(res_none.status_code, 200)
        self.assertIsNone(res_none.data['data'])

    def test_timer_mode_validation(self):
        # Timer mode requires timer_goal_seconds
        start_time = datetime.now(timezone.utc).isoformat()
        res = self.client1.post('/api/sessions/start/', {
            'topic_type': 'skill',
            'topic_id': str(self.skill_topic.id),
            'mode': 'timer',
            'started_at': start_time,
        }, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['error'], "timer_goal_seconds is required for timer mode")

        # With timer_goal_seconds
        res2 = self.client1.post('/api/sessions/start/', {
            'topic_type': 'skill',
            'topic_id': str(self.skill_topic.id),
            'mode': 'timer',
            'timer_goal_seconds': 1800,
            'started_at': start_time,
        }, format='json')
        self.assertEqual(res2.status_code, 201)
        self.assertEqual(res2.data['data']['timer_goal_seconds'], 1800)

    def test_analytics_endpoints(self):
        now = datetime.now(timezone.utc)
        # Create completed sessions for user1
        TopicSession.objects.create(
            user=self.user1,
            academic_topic=self.acad_topic,
            mode='stopwatch',
            started_at=now - timedelta(hours=2),
            ended_at=now - timedelta(hours=1),
            duration_seconds=3600,
            is_completed=True,
        )
        TopicSession.objects.create(
            user=self.user1,
            skill_topic=self.skill_topic,
            mode='timer',
            timer_goal_seconds=1800,
            started_at=now - timedelta(minutes=45),
            ended_at=now,
            duration_seconds=1800,
            is_completed=True,
        )
        # Incompleted session should NOT be counted in analytics
        TopicSession.objects.create(
            user=self.user1,
            academic_topic=self.acad_topic,
            mode='stopwatch',
            started_at=now,
            duration_seconds=500,
            is_completed=False,
        )

        # 1. Topic time
        res_topic_acad = self.client1.get(f'/api/analytics/topic/?topic_type=academic&topic_id={self.acad_topic.id}')
        self.assertEqual(res_topic_acad.status_code, 200)
        self.assertEqual(res_topic_acad.data['data']['total_seconds'], 3600)

        res_topic_skill = self.client1.get(f'/api/analytics/topic/?topic_type=skill&topic_id={self.skill_topic.id}')
        self.assertEqual(res_topic_skill.status_code, 200)
        self.assertEqual(res_topic_skill.data['data']['total_seconds'], 1800)

        # 2. SubSkill time
        res_sub = self.client1.get(f'/api/analytics/sub-skill/?sub_skill_id={self.sub_skill.id}')
        self.assertEqual(res_sub.status_code, 200)
        self.assertEqual(res_sub.data['data']['total_seconds'], 1800)

        # 3. Skill time
        res_skill = self.client1.get(f'/api/analytics/skill/?skill_id={self.skill.id}')
        self.assertEqual(res_skill.status_code, 200)
        self.assertEqual(res_skill.data['data']['total_seconds'], 1800)

        # 4. Overview weekly
        today_str = date.today().isoformat()
        res_overview = self.client1.get(f'/api/analytics/overview/?period=weekly&date={today_str}')
        self.assertEqual(res_overview.status_code, 200)
        data = res_overview.data['data']
        self.assertEqual(data['period'], 'weekly')
        self.assertEqual(data['academic_seconds'], 3600)
        self.assertEqual(data['skill_seconds'], 1800)
        self.assertEqual(data['total_seconds'], 5400)
        self.assertEqual(len(data['top_academic_topics']), 1)
        self.assertEqual(data['top_academic_topics'][0]['title'], "Newton's Laws")
        self.assertEqual(len(data['top_skill_topics']), 1)
        self.assertEqual(data['top_skill_topics'][0]['title'], "State Management")

        # 5. Isolation: user2 gets 0 seconds
        res_u2 = self.client2.get(f'/api/analytics/overview/?period=weekly&date={today_str}')
        self.assertEqual(res_u2.status_code, 200)
        self.assertEqual(res_u2.data['data']['total_seconds'], 0)
