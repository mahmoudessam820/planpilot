import logging
import uuid

from django.urls import reverse
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from project.models import Project
from project.views import FORM_MESSAGES

User = get_user_model()


class DeleteProjectViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.logger = logging.getLogger('project.views')
        self.log_handler = logging.StreamHandler()
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.INFO)

        self.user = User.objects.create_user(
            name='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            name='otheruser',
            email='otheruser@example.com',
            password='testpass123'
        )

        self.project = Project.objects.create(
            name='Test Project',
            created_by=self.user
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_delete_project_get_authenticated(self):
        """Test normal case: GET request by authenticated user deletes project and redirects"""
        self.client.login(email='testuser@example.com', password='testpass123')

        with patch('project.views.logger.info') as mock_logger:
            response = self.client.get(reverse('project:delete', kwargs={'pk': self.project.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('project:projects'))
        self.assertEqual(Project.objects.count(), 0)

        mock_logger.assert_called_once_with(f"Project {self.project.name} deleted by {self.user.email}")
        messages = [msg.message for msg in response.wsgi_request._messages]

        self.assertIn(FORM_MESSAGES['project_deleted'], messages)

    def test_delete_project_post_success(self):
        """Test normal case: POST request successfully deletes project"""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        with patch('project.views.logger.info') as mock_logger:
            response = self.client.post(reverse('project:delete', kwargs={'pk': self.project.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('project:projects'))
        self.assertEqual(Project.objects.count(), 0)
        
        mock_logger.assert_called_once_with(f"Project {self.project.name} deleted by {self.user.email}")
        messages = [msg.message for msg in response.wsgi_request._messages]
        
        self.assertIn(FORM_MESSAGES['project_deleted'], messages)

    def test_delete_project_unauthenticated(self):
        """Test edge case: Unauthenticated user is redirected to login"""
        response = self.client.get(reverse('project:delete', kwargs={'pk': self.project.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        self.assertEqual(Project.objects.count(), 1)

    def test_delete_project_non_owner(self):
        """Test edge case: Authenticated user without ownership gets 404"""
        self.client.login(email='otheruser@example.com', password='testpass123')
        response = self.client.get(reverse('project:delete', kwargs={'pk': self.project.pk}))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Project.objects.count(), 1)

    def test_delete_project_invalid_pk(self):
        """Test invalid input: Non-existent project ID returns 404"""
        self.client.login(email='testuser@example.com', password='testpass123')
        invalid_pk = uuid.uuid4()
        response = self.client.get(reverse('project:delete', kwargs={'pk': invalid_pk}))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Project.objects.count(), 1)

    def test_delete_project_post_db_error(self):
        """Test edge case: POST with database error handles gracefully"""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        with patch('project.views.transaction.atomic') as mock_transaction:
            mock_transaction.side_effect = Exception("Database error")
            with patch('project.views.logger.error') as mock_logger:
                response = self.client.post(reverse('project:delete', kwargs={'pk': self.project.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('project:projects'))
        self.assertEqual(Project.objects.count(), 1)
        
        mock_logger.assert_called_once_with(f"Failed to delete project {self.project.name} by {self.user.email}")
        messages = [msg.message for msg in response.wsgi_request._messages]
        
        self.assertIn('An error occurred while deleting the project.', messages)

    def test_delete_project_invalid_method(self):
        """Test invalid input: Invalid HTTP method (PUT) returns 405"""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        response = self.client.put(reverse('project:delete', kwargs={'pk': self.project.pk}))

        self.assertEqual(response.status_code, 405)
        self.assertEqual(Project.objects.count(), 1)
