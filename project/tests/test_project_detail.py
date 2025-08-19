import logging

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from project.models import Project


User = get_user_model()


class ProjectDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.logger = logging.getLogger('project.views')
        self.log_handler = logging.StreamHandler()
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.ERROR)  # Capture ERROR and above for logger.error

        self.user = User.objects.create_user(
            name='testuser',
            email='testuser@gmail.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            name='otheruser',
            email='otheruser@gmail.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project',
            created_by=self.user
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_project_detail_get_authenticated_user(self):
        """Test normal case: GET request by authenticated user for their own project"""
        self.client.login(email='testuser@gmail.com', password='testpass123')
        response = self.client.get(reverse('project:project_detail', kwargs={'pk': self.project.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/project_detail.html')
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(response.context['project'].name, 'Test Project')
        self.assertEqual(response.context['project'].created_by, self.user)

    def test_project_detail_unauthenticated_user(self):
        """Test invalid input: GET request by unauthenticated user"""
        response = self.client.get(reverse('project:project_detail', kwargs={'pk': self.project.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_project_detail_invalid_method(self):
        """Test edge case: Request with disallowed HTTP method (e.g., POST)"""
        self.client.login(email='testuser@gmail.com', password='testpass123')
        response = self.client.post(reverse('project:project_detail', kwargs={'pk': self.project.pk}))

        self.assertEqual(response.status_code, 405)  # Method Not Allowed
