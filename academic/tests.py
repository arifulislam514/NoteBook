import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from academic.models import Semester, Subject, Chapter, AcademicTopic, AcademicTopicBlock


class AcademicTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(email='user1@example.com', password='password123')
        self.user2 = User.objects.create_user(email='user2@example.com', password='password123')

        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)

        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

    def test_semester_crud_and_isolation(self):
        sem_id = str(uuid.uuid4())
        # 1. Create semester with client uuid
        res = self.client1.post('/api/academic/semesters/', {
            'id': sem_id,
            'name': 'Semester 1',
            'year': 2024
        }, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['data']['id'], sem_id)

        # 2. List user1 semesters
        res = self.client1.get('/api/academic/semesters/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['count'], 1)

        # 3. Isolation: user2 cannot see user1 semester
        res2 = self.client2.get('/api/academic/semesters/')
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.data['count'], 0)

        # 4. Isolation: user2 cannot access user1 semester -> 404
        res_iso = self.client2.patch(f'/api/academic/semesters/{sem_id}/', {'name': 'Hacked'}, format='json')
        self.assertEqual(res_iso.status_code, 404)

        # 5. Patch semester
        res = self.client1.patch(f'/api/academic/semesters/{sem_id}/', {'name': 'Semester 1 Updated'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['data']['name'], 'Semester 1 Updated')

        # 6. Soft delete
        res = self.client1.delete(f'/api/academic/semesters/{sem_id}/')
        self.assertEqual(res.status_code, 200)
        sem = Semester.objects.get(id=sem_id)
        self.assertTrue(sem.is_deleted)

        # List should now be empty
        res = self.client1.get('/api/academic/semesters/')
        self.assertEqual(res.data['count'], 0)

    def test_academic_hierarchy_and_reorder(self):
        # Create semester
        sem = Semester.objects.create(user=self.user1, name='Sem 1', year=2024)
        sub_id = str(uuid.uuid4())

        # Create subject
        res = self.client1.post('/api/academic/subjects/', {
            'id': sub_id,
            'semester_id': str(sem.id),
            'name': 'Computer Science'
        }, format='json')
        self.assertEqual(res.status_code, 201)

        # Create Chapter
        ch_id = str(uuid.uuid4())
        res = self.client1.post('/api/academic/chapters/', {
            'id': ch_id,
            'subject_id': sub_id,
            'name': 'Chapter 1'
        }, format='json')
        self.assertEqual(res.status_code, 201)

        # Create Topic
        top_id = str(uuid.uuid4())
        res = self.client1.post('/api/academic/topics/', {
            'id': top_id,
            'chapter_id': ch_id,
            'title': 'Topic 1'
        }, format='json')
        self.assertEqual(res.status_code, 201)

        # Create Blocks
        b1_id = str(uuid.uuid4())
        b2_id = str(uuid.uuid4())
        self.client1.post('/api/academic/topic-blocks/', {
            'id': b1_id,
            'topic_id': top_id,
            'type': 'text',
            'content': {'value': 'First block'},
            'order': 0
        }, format='json')
        self.client1.post('/api/academic/topic-blocks/', {
            'id': b2_id,
            'topic_id': top_id,
            'type': 'code',
            'content': {'language': 'python', 'value': 'print(1)'},
            'order': 1
        }, format='json')

        # Reorder blocks
        res = self.client1.post('/api/academic/topic-blocks/reorder/', {
            'blocks': [
                {'id': b1_id, 'order': 1},
                {'id': b2_id, 'order': 0},
            ]
        }, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(AcademicTopicBlock.objects.get(id=b1_id).order, 1)
        self.assertEqual(AcademicTopicBlock.objects.get(id=b2_id).order, 0)
