import uuid
import logging
from unittest.mock import patch

from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from project.models import Project, ProjectNote
from project.views import ProjectNoteForm, FORM_MESSAGES

User = get_user_model()


class NoteEditViewTests(TestCase):
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
        self.note = ProjectNote.objects.create(
            project=self.project,
            name='Original Note',  # Adjust based on actual ProjectNote model
            body='Original content'  # Adjust based on actual ProjectNote model
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_note_edit_get_authenticated_owner(self):
        """Test normal case: GET request by authenticated user who owns the project"""
        self.client.login(email='testuser@example.com', password='testpass123')
        response = self.client.get(
            reverse('project:note_edit', kwargs={'project_id': self.project.pk, 'pk': self.note.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/note_edit.html')
        self.assertIsInstance(response.context['form'], ProjectNoteForm)
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(response.context['note'], self.note)
        self.assertEqual(ProjectNote.objects.count(), 1)

    def test_note_edit_post_success(self):
        """Test normal case: POST request with valid form data"""
        self.client.login(email='testuser@example.com', password='testpass123')

        post_data = {
            'name': 'Updated Note',
            'body': 'Updated content',  # Adjust based on actual ProjectNoteForm fields
        }

        with patch('project.forms.ProjectNoteForm.is_valid', return_value=True) as mock_form_valid:
            with patch('project.forms.ProjectNoteForm.save') as mock_form_save:
                with patch('project.views.logger.info') as mock_logger:
                    response = self.client.post(
                        reverse('project:note_edit', kwargs={'project_id': self.project.pk, 'pk': self.note.pk}),
                        data=post_data
                    )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'/projects/{self.project.pk}/')

        mock_form_save.assert_called_once()
        mock_logger.assert_called_once_with(
            f"User {self.user} updated note pk={self.note.pk} for project {self.project.pk}"
        )

        messages = [msg.message for msg in response.wsgi_request._messages]

        self.assertIn(FORM_MESSAGES['note_updated'], messages)
        self.assertEqual(ProjectNote.objects.count(), 1)

    def test_note_edit_post_invalid_form(self):
        """Test edge case: POST request with invalid form data"""
        self.client.login(email='testuser@example.com', password='testpass123')

        post_data = {
            'name': '',
            'body': '',  # Invalid: empty fields
        }

        with patch('project.forms.ProjectNoteForm.is_valid', return_value=False) as mock_form_valid:
            with patch('project.forms.ProjectNoteForm.errors') as mock_form_errors:
                mock_form_errors.as_text.return_value = '* name\n  * This field is required.\n* body\n  * Body cannot be empty.'
                with patch('project.views.logger.warning') as mock_logger:
                    response = self.client.post(
                        reverse('project:note_edit', kwargs={'project_id': self.project.pk, 'pk': self.note.pk}),
                        data=post_data
                    )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/note_edit.html')
        self.assertIsInstance(response.context['form'], ProjectNoteForm)
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(response.context['note'], self.note)

        mock_logger.assert_called_once_with(
            f"Failed note update attempt for project {self.project.pk}: {mock_form_errors.as_text.return_value}"
        )

        messages = [msg.message for msg in response.wsgi_request._messages]

        self.assertIn(mock_form_errors.as_text.return_value, messages)
        self.assertEqual(ProjectNote.objects.count(), 1)

    def test_note_edit_post_integrity_error(self):
        """Test edge case: POST request with IntegrityError during save"""
        self.client.login(email='testuser@example.com', password='testpass123')
        post_data = {
            'name': 'Updated Note',
            'body': 'Updated content',
        }

        with patch('project.forms.ProjectNoteForm.is_valid', return_value=True) as mock_form_valid:
            with patch('project.forms.ProjectNoteForm.save') as mock_form_save:
                mock_form_save.side_effect = IntegrityError("Database constraint violation")
                with patch('project.views.logger.error') as mock_logger:
                    response = self.client.post(
                        reverse('project:note_edit', kwargs={'project_id': self.project.pk, 'pk': self.note.pk}),
                        data=post_data
                    )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/note_edit.html')
        self.assertIsInstance(response.context['form'], ProjectNoteForm)
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(response.context['note'], self.note)

        mock_logger.assert_called_once_with(
            f"Integrity error updating note pk={self.note.pk} for project_id={self.project.pk}"
        )

        self.assertEqual(ProjectNote.objects.count(), 1)

    def test_note_edit_unauthenticated(self):
        """Test edge case: Unauthenticated user is redirected to login"""
        
        response = self.client.get(
            reverse('project:note_edit', kwargs={'project_id': self.project.pk, 'pk': self.note.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        self.assertEqual(ProjectNote.objects.count(), 1)

    def test_note_edit_non_owner(self):
        """Test edge case: Authenticated user who doesn't own the project gets 404"""
        self.client.login(email='otheruser@example.com', password='testpass123')

        response = self.client.get(
            reverse('project:note_edit', kwargs={'project_id': self.project.pk, 'pk': self.note.pk})
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ProjectNote.objects.count(), 1)

    def test_note_edit_invalid_project_id(self):
        """Test invalid input: Non-existent project ID returns 404"""
        self.client.login(email='testuser@example.com', password='testpass123')

        invalid_project_id = uuid.uuid4()

        response = self.client.get(
            reverse('project:note_edit', kwargs={'project_id': invalid_project_id, 'pk': self.note.pk})
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ProjectNote.objects.count(), 1)

    def test_note_edit_invalid_note_id(self):
        """Test invalid input: Non-existent note ID returns 404"""
        self.client.login(email='testuser@example.com', password='testpass123')

        invalid_note_id = uuid.uuid4()

        response = self.client.get(
            reverse('project:note_edit', kwargs={'project_id': self.project.pk, 'pk': invalid_note_id})
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ProjectNote.objects.count(), 1)

    def test_note_edit_invalid_method(self):
        """Test invalid input: Invalid HTTP method (PUT) returns 405"""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.put(
            reverse('project:note_edit', kwargs={'project_id': self.project.pk, 'pk': self.note.pk})
        )

        self.assertEqual(response.status_code, 405)
        self.assertEqual(ProjectNote.objects.count(), 1)
