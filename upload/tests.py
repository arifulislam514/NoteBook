from unittest.mock import patch
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from users.models import User


class UploadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='uploader@example.com', password='password123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_missing_image(self):
        res = self.client.post('/api/upload/image/', {})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['error'], 'No image provided')

    def test_invalid_file_type(self):
        txt_file = SimpleUploadedFile("test.txt", b"hello world", content_type="text/plain")
        res = self.client.post('/api/upload/image/', {'image': txt_file}, format='multipart')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['error'], 'Invalid file type')

    @patch('cloudinary.uploader.upload')
    def test_successful_upload(self, mock_upload):
        mock_upload.return_value = {
            'secure_url': 'https://res.cloudinary.com/demo/image/upload/sample.jpg'
        }
        img_file = SimpleUploadedFile("test.png", b"\x89PNG\r\n\x1a\nfakecontent", content_type="image/png")
        res = self.client.post('/api/upload/image/', {'image': img_file}, format='multipart')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['success'])
        self.assertEqual(res.data['data']['url'], 'https://res.cloudinary.com/demo/image/upload/sample.jpg')
