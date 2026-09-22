import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from skills.models import Skill, SubSkill, SkillTopic, EvaluationQuestion, EvaluationAnswer, EvaluationAnswerBlock


class SkillsTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(email='user2@example.com', password='password123')

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

    def test_skills_crud_and_isolation(self):
        skill_id = str(uuid.uuid4())
        res = self.client1.post('/api/skills/', {
            'id': skill_id,
            'name': 'Backend Development'
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['data']['id'], skill_id)

        # Isolation
        res2 = self.client2.get('/api/skills/')
        self.assertEqual(res2.data['count'], 0)

        # Patch
        res = self.client1.patch(f'/api/skills/{skill_id}/', {'name': 'Backend Eng'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['data']['name'], 'Backend Eng')

        # SubSkill
        sub_id = str(uuid.uuid4())
        res = self.client1.post('/api/skills/sub-skills/', {
            'id': sub_id,
            'skill_id': skill_id,
            'name': 'Django'
        }, format='json')
        self.assertEqual(res.status_code, 201)

        # Topic
        topic_id = str(uuid.uuid4())
        res = self.client1.post('/api/skills/topics/', {
            'id': topic_id,
            'sub_skill_id': sub_id,
            'title': 'Django Signals'
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['data']['current_level'], 'none')

        # Update topic current_level
        res = self.client1.patch(f'/api/skills/topics/{topic_id}/', {
            'current_level': 'intermediate'
        }, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['data']['current_level'], 'intermediate')

        # 1. Evaluation Questions: Seed defaults via GET
        q_res = self.client1.get('/api/skills/questions/?level=basic')
        self.assertEqual(q_res.status_code, 200)
        questions = q_res.data['data']
        self.assertEqual(len(questions), 5)
        self.assertTrue(all(q['is_default'] for q in questions))
        q1_id = questions[0]['id']

        # 2. Evaluation Questions: Create custom question
        custom_q_res = self.client1.post('/api/skills/questions/', {
            'level': 'basic',
            'text': 'Custom question about signals?',
            'order': 5,
        }, format='json')
        self.assertEqual(custom_q_res.status_code, 201)
        self.assertFalse(custom_q_res.data['data']['is_default'])
        custom_q_id = custom_q_res.data['data']['id']

        # 3. Evaluation Questions: Patch question
        patch_q_res = self.client1.patch(f'/api/skills/questions/{custom_q_id}/', {
            'text': 'Updated custom question text'
        }, format='json')
        self.assertEqual(patch_q_res.status_code, 200)
        self.assertEqual(patch_q_res.data['data']['text'], 'Updated custom question text')

        # 4. Evaluation Questions: Reorder
        reorder_res = self.client1.post('/api/skills/questions/reorder/', {
            'questions': [
                {'id': q1_id, 'order': 1},
                {'id': custom_q_id, 'order': 0},
            ]
        }, format='json')
        self.assertEqual(reorder_res.status_code, 200)
        self.assertEqual(EvaluationQuestion.objects.get(id=custom_q_id).order, 0)

        # 5. Evaluation Answer
        ans_id = str(uuid.uuid4())
        res = self.client1.post('/api/skills/evaluation-answers/', {
            'id': ans_id,
            'skill_topic_id': topic_id,
            'question_id': q1_id,
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['data']['question_id'], q1_id)
        self.assertEqual(res.data['data']['level'], 'basic')

        # Duplicate answer error
        dup_res = self.client1.post('/api/skills/evaluation-answers/', {
            'skill_topic_id': topic_id,
            'question_id': q1_id,
        }, format='json')
        self.assertEqual(dup_res.status_code, 400)
        self.assertEqual(dup_res.data['error'], 'Answer already exists for this question')

        # Add Answer Block
        blk_id = str(uuid.uuid4())
        res = self.client1.post('/api/skills/answer-blocks/', {
            'id': blk_id,
            'answer_id': ans_id,
            'type': 'text',
            'content': {'value': 'My explanation of signals'},
            'order': 0
        }, format='json')
        self.assertEqual(res.status_code, 201)

        # Fetch Answer Detail with nested blocks and question_text
        res = self.client1.get(f'/api/skills/evaluation-answers/{ans_id}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['data']['blocks']), 1)
        self.assertEqual(res.data['data']['blocks'][0]['content']['value'], 'My explanation of signals')
        self.assertIn('question_text', res.data['data'])
        self.assertTrue(len(res.data['data']['question_text']) > 0)

        # Delete Question -> soft deletes question and linked evaluation answers
        del_q_res = self.client1.delete(f'/api/skills/questions/{q1_id}/')
        self.assertEqual(del_q_res.status_code, 200)
        self.assertTrue(EvaluationQuestion.objects.get(id=q1_id).is_deleted)
        self.assertTrue(EvaluationAnswer.objects.get(id=ans_id).is_deleted)

        # Soft Delete Skill
        del_res = self.client1.delete(f'/api/skills/{skill_id}/')
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(Skill.objects.get(id=skill_id).is_deleted)
