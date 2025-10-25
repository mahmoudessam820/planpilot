import logging
import uuid

from unittest.mock import patch
from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from project.models import Project
from project.views import FORM_MESSAGES
from project.forms import ProjectFileForm

User = get_user_model()


class UploadFileViewTests(TestCase):
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

    def test_upload_file_get_authenticated(self):
        """Test normal case: GET request by authenticated user displays upload form"""
        self.client.login(email='testuser@example.com', password='testpass123')
        response = self.client.get(reverse('project:upload_file', kwargs={'project_id': self.project.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/upload_file.html')
        self.assertIsInstance(response.context['form'], ProjectFileForm)
        self.assertEqual(response.context['project'], self.project)

    def test_upload_file_post_success(self):
        """Test normal case: POST request with valid file upload"""
        self.client.login(email='testuser@example.com', password='testpass123')
        file_content = b'Test file content'
        uploaded_file = SimpleUploadedFile('test.txt', file_content, content_type='text/plain')
        post_data = {
            'name': 'Test File',
        }
        with patch('project.forms.ProjectFileForm.is_valid', return_value=True) as mock_form_valid:
            with patch('project.forms.ProjectFileForm.save') as mock_form_save:
                mock_instance = mock_form_save.return_value
                mock_instance.project = None  # Simulate unsaved project
                response = self.client.post(
                    reverse('project:upload_file', kwargs={'project_id': self.project.pk}),
                    data={**post_data, 'file': uploaded_file}
                )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'/projects/{self.project.pk}/')

        mock_form_save.assert_called_once()
        mock_instance.project = self.project  # Simulate project assignment
        mock_instance.save.assert_called_once()
        messages = [msg.message for msg in response.wsgi_request._messages]

        self.assertIn(FORM_MESSAGES['upload_file'], messages)

    def test_upload_file_post_invalid_form(self):
        """Test edge case: POST request with invalid form data"""
        self.client.login(email='testuser@example.com', password='testpass123')
        post_data = {
            'name': '',  # Invalid: empty name
        }
        with patch('project.forms.ProjectFileForm.is_valid', return_value=False) as mock_form_valid:
            with patch('project.forms.ProjectFileForm.errors') as mock_form_errors:
                mock_form_errors.as_text.return_value = 'Name is required.'
                with patch('project.views.logger.warning') as mock_logger:
                    response = self.client.post(
                        reverse('project:upload_file', kwargs={'project_id': self.project.pk}),
                        data=post_data
                    )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'/projects/{self.project.pk}/files/upload/')
        mock_logger.assert_called_once_with('Failed file upload attempt: Name is required.')

        messages = [msg.message for msg in response.wsgi_request._messages]

        self.assertIn('Name is required.', messages)

    def test_upload_file_unauthenticated(self):
        """Test edge case: Unauthenticated user is redirected to login"""
        response = self.client.get(reverse('project:upload_file', kwargs={'project_id': self.project.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_upload_file_invalid_project_id(self):
        """Test invalid input: Non-existent project ID returns 404"""
        self.client.login(email='testuser@example.com', password='testpass123')
        invalid_project_id = uuid.uuid4()
        response = self.client.get(reverse('project:upload_file', kwargs={'project_id': invalid_project_id}))

        self.assertEqual(response.status_code, 404)

    def test_upload_file_invalid_method(self):
        """Test invalid input: Invalid HTTP method (PUT) returns 405"""
        self.client.login(email='testuser@example.com', password='testpass123')
        response = self.client.put(reverse('project:upload_file', kwargs={'project_id': self.project.pk}))

        self.assertEqual(response.status_code, 405)
