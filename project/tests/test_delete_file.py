import logging
import uuid 

from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.messages.storage.fallback import FallbackStorage


from project.models import Project, ProjectFile
from project.views import FORM_MESSAGES

User = get_user_model()


class DeleteFileViewTests(TestCase):
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
        self.project_file = ProjectFile.objects.create(
            project=self.project,
            name='Test File',
            attachment='test.txt'  # Adjust based on actual ProjectFile model
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_delete_file_get_authenticated_owner(self):
        """Test normal case: GET request by authenticated user who owns the project"""
        self.client.login(email='testuser@example.com', password='testpass123')

        with patch('project.views.logger.info') as mock_logger:
            response = self.client.get(
                reverse('project:delete_file', kwargs={'project_id': self.project.pk, 'pk': self.project_file.pk})
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'/projects/{self.project.pk}/')
        self.assertFalse(ProjectFile.objects.filter(pk=self.project_file.pk).exists())

        mock_logger.assert_called_once_with(
            f"User {self.user} deleted file from project {self.project.pk}"
        )

        messages = [msg.message for msg in response.wsgi_request._messages]
    
        self.assertIn(FORM_MESSAGES['delete_file'], messages)

    def test_delete_file_unauthenticated(self):
        """Test edge case: Unauthenticated user is redirected to login"""
        response = self.client.get(
            reverse('project:delete_file', kwargs={'project_id': self.project.pk, 'pk': self.project_file.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        self.assertTrue(ProjectFile.objects.filter(pk=self.project_file.pk).exists())

    def test_delete_file_non_owner(self):
        """Test edge case: Authenticated user who doesn't own the project gets 404"""
        self.client.login(email='otheruser@example.com', password='testpass123')

        response = self.client.get(
            reverse('project:delete_file', kwargs={'project_id': self.project.pk, 'pk': self.project_file.pk})
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(ProjectFile.objects.filter(pk=self.project_file.pk).exists())

    def test_delete_file_invalid_project_id(self):
        """Test invalid input: Non-existent project ID returns 404"""
        self.client.login(email='testuser@example.com', password='testpass123')
        invalid_project_id = uuid.uuid4()

        response = self.client.get(
            reverse('project:delete_file', kwargs={'project_id': invalid_project_id, 'pk': self.project_file.pk})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(ProjectFile.objects.filter(pk=self.project_file.pk).exists())

    def test_delete_file_invalid_file_id(self):
        """Test invalid input: Non-existent file ID returns 404"""
        self.client.login(email='testuser@example.com', password='testpass123')
        invalid_file_id = uuid.uuid4()

        response = self.client.get(
            reverse('project:delete_file', kwargs={'project_id': self.project.pk, 'pk': invalid_file_id})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(ProjectFile.objects.filter(pk=self.project_file.pk).exists())

    def test_delete_file_invalid_method(self):
        """Test invalid input: Invalid HTTP method (POST) returns 405"""
        self.client.login(email='testuser@example.com', password='testpass123')
        response = self.client.post(
            reverse('project:delete_file', kwargs={'project_id': self.project.pk, 'pk': self.project_file.pk})
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(ProjectFile.objects.filter(pk=self.project_file.pk).exists())

    def test_delete_file_db_error(self):
        """Test edge case: Database error during file deletion handles gracefully"""
        self.client.login(email='testuser@example.com', password='testpass123')

        with patch('project.models.ProjectFile.delete') as mock_delete:
            mock_delete.side_effect = Exception("Database error")
            with patch('project.views.logger.error') as mock_logger:
                response = self.client.get(
                    reverse('project:delete_file', kwargs={'project_id': self.project.pk, 'pk': self.project_file.pk})
                )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'/projects/{self.project.pk}/')
        self.assertTrue(ProjectFile.objects.filter(pk=self.project_file.pk).exists())

        mock_logger.assert_called_once_with(
            f"Failed to delete file {self.project_file.pk} from project {self.project.pk} by {self.user}: Database error"
        )

        messages = [msg.message for msg in response.wsgi_request._messages]
        self.assertIn('An error occurred while deleting the file.', messages)
