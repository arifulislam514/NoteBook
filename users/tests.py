from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_login_me(self):
        # 1. Register
        reg_resp = self.client.post('/api/auth/register/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')
        self.assertEqual(reg_resp.status_code, 201)
        self.assertTrue(reg_resp.data['success'])
        self.assertEqual(reg_resp.data['data']['user']['email'], 'test@example.com')
        access_token = reg_resp.data['data']['tokens']['access']

        # 2. Register duplicate email
        dup_resp = self.client.post('/api/auth/register/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')
        self.assertEqual(dup_resp.status_code, 400)
        self.assertFalse(dup_resp.data['success'])

        # 3. Login
        login_resp = self.client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'password123'
        }, format='json')
        self.assertEqual(login_resp.status_code, 200)
        self.assertTrue(login_resp.data['success'])

        # 4. Access /me/
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        me_resp = self.client.get('/api/auth/me/')
        self.assertEqual(me_resp.status_code, 200)
        self.assertTrue(me_resp.data['success'])
        self.assertEqual(me_resp.data['data']['email'], 'test@example.com')
