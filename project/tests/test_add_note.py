import uuid
import logging
from unittest.mock import patch

from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from project.models import Project, ProjectNote
from project.forms import ProjectNoteForm
from project.views import FORM_MESSAGES


User = get_user_model()


class AddNoteViewTests(TestCase):
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

    def test_add_note_get_authenticated_owner(self):
        """Test normal case: GET request by authenticated user who owns the project"""
        self.client.login(email='testuser@example.com', password='testpass123')
        response = self.client.get(reverse('project:add_note', kwargs={'project_id': self.project.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/add_note.html')
        self.assertIsInstance(response.context['form'], ProjectNoteForm)
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(ProjectNote.objects.count(), 0)

    def test_add_note_post_success(self):
        """Test normal case: POST request with valid form data"""
        self.client.login(email='testuser@example.com', password='testpass123')
        post_data = {
            'content': 'This is a test note',  # Adjust based on actual ProjectNoteForm fields
        }

        with patch('project.forms.ProjectNoteForm.is_valid', return_value=True) as mock_form_valid:
            with patch('project.forms.ProjectNoteForm.save') as mock_form_save:
                mock_instance = mock_form_save.return_value
                mock_instance.project = None  # Simulate unsaved project
                response = self.client.post(
                    reverse('project:add_note', kwargs={'project_id': self.project.pk}),
                    data=post_data
                )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'/projects/{self.project.pk}/')

        mock_form_save.assert_called_once()
        mock_instance.project = self.project  # Simulate project assignment
        mock_instance.save.assert_called_once()
        messages = [msg.message for msg in response.wsgi_request._messages]

        self.assertIn(FORM_MESSAGES['note_created'], messages)

    def test_add_note_post_invalid_form(self):
        """Test edge case: POST request with invalid form data"""
        self.client.login(email='testuser@example.com', password='testpass123')
        post_data = {
            'content': '',  # Invalid: empty content
        }

        with patch('project.forms.ProjectNoteForm.is_valid', return_value=False) as mock_form_valid:
            with patch('project.forms.ProjectNoteForm.errors') as mock_form_errors:
                mock_form_errors.as_text.return_value = 'Content is required.'
                response = self.client.post(
                    reverse('project:add_note', kwargs={'project_id': self.project.pk}),
                    data=post_data
                )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/add_note.html')
        self.assertIsInstance(response.context['form'], ProjectNoteForm)
        self.assertEqual(response.context['project'], self.project)

        messages = [msg.message for msg in response.wsgi_request._messages]

        self.assertIn('Content is required.', messages)
        self.assertEqual(ProjectNote.objects.count(), 0)

    def test_add_note_post_integrity_error(self):
        """Test edge case: POST request with IntegrityError during save"""
        self.client.login(email='testuser@example.com', password='testpass123')
        post_data = {
            'content': 'This is a test note',
        }

        with patch('project.forms.ProjectNoteForm.is_valid', return_value=True) as mock_form_valid:
            with patch('project.forms.ProjectNoteForm.save') as mock_form_save:
                mock_form_save.side_effect = IntegrityError("Database constraint violation")
                response = self.client.post(
                    reverse('project:add_note', kwargs={'project_id': self.project.pk}),
                    data=post_data
                )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/add_note.html')
        self.assertIsInstance(response.context['form'], ProjectNoteForm)
        self.assertEqual(response.context['project'], self.project)

        messages = [msg.message for msg in response.wsgi_request._messages]

        self.assertIn('Database constraint violation', messages)
        self.assertEqual(ProjectNote.objects.count(), 0)

    def test_add_note_unauthenticated(self):
        """Test edge case: Unauthenticated user is redirected to login"""
        response = self.client.get(reverse('project:add_note', kwargs={'project_id': self.project.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        self.assertEqual(ProjectNote.objects.count(), 0)

    def test_add_note_non_owner(self):
        """Test edge case: Authenticated user who doesn't own the project gets 404"""
        self.client.login(email='otheruser@example.com', password='testpass123')

        response = self.client.get(
            reverse('project:add_note', kwargs={'project_id': self.project.pk})
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ProjectNote.objects.count(), 0)

    def test_add_note_invalid_project_id(self):
        """Test invalid input: Non-existent project ID returns 404"""
        self.client.login(email='testuser@example.com', password='testpass123')

        invalid_project_id = uuid.uuid4()

        response = self.client.get(
            reverse('project:add_note', kwargs={'project_id': invalid_project_id})
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ProjectNote.objects.count(), 0)

    def test_add_note_invalid_method(self):
        """Test invalid input: Invalid HTTP method (PUT) returns 405"""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.put(
            reverse('project:add_note', kwargs={'project_id': self.project.pk})
        )

        self.assertEqual(response.status_code, 405)
        self.assertEqual(ProjectNote.objects.count(), 0)
