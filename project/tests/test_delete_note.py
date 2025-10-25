import uuid
import logging
from unittest.mock import patch

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import IntegrityError

from project.models import Project, ProjectNote
from project.views import FORM_MESSAGES

User = get_user_model()


class NoteDeleteViewTests(TestCase):
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
            name='Test Note',
            body='Some content'
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_note_delete_success(self):
        """GET request by the owner deletes the note and redirects."""
        self.client.login(email='testuser@example.com', password='testpass123')
        response = self.client.get(
            reverse('project:note_delete',
                    kwargs={'project_id': self.project.pk, 'pk': self.note.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'/projects/{self.project.pk}/')

        self.assertFalse(ProjectNote.objects.filter(pk=self.note.pk).exists())

        messages = [m.message for m in response.wsgi_request._messages]
        self.assertIn(FORM_MESSAGES['note_deleted'], messages)

    def test_note_delete_unauthenticated(self):
        """Unauthenticated request redirects to login."""
        response = self.client.get(
            reverse('project:note_delete',
                    kwargs={'project_id': self.project.pk, 'pk': self.note.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        self.assertTrue(ProjectNote.objects.filter(pk=self.note.pk).exists())

    def test_note_delete_non_owner(self):
        """User who does not own the project gets 404."""
        self.client.login(email='otheruser@example.com', password='testpass123')
        response = self.client.get(
            reverse('project:note_delete',
                    kwargs={'project_id': self.project.pk, 'pk': self.note.pk})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(ProjectNote.objects.filter(pk=self.note.pk).exists())

    def test_note_delete_invalid_project_id(self):
        """Non-existent project returns 404."""
        self.client.login(email='testuser@example.com', password='testpass123')
        bad_id = uuid.uuid4()
        response = self.client.get(
            reverse('project:note_delete',
                    kwargs={'project_id': bad_id, 'pk': self.note.pk})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(ProjectNote.objects.filter(pk=self.note.pk).exists())

    def test_note_delete_invalid_note_id(self):
        """Non-existent note returns 404."""
        self.client.login(email='testuser@example.com', password='testpass123')
        bad_id = uuid.uuid4()
        response = self.client.get(
            reverse('project:note_delete',
                    kwargs={'project_id': self.project.pk, 'pk': bad_id})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(ProjectNote.objects.filter(pk=self.note.pk).exists())

    def test_note_delete_integrity_error(self):
        """Database IntegrityError is caught, logged and user sees error."""
        self.client.login(email='testuser@example.com', password='testpass123')

        with patch.object(ProjectNote, 'delete') as mock_delete:
            mock_delete.side_effect = IntegrityError('FK violation')
            with patch('project.views.logger.error') as mock_logger:
                response = self.client.get(
                    reverse('project:note_delete',
                            kwargs={'project_id': self.project.pk, 'pk': self.note.pk})
                )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'/projects/{self.project.pk}/')

        self.assertTrue(ProjectNote.objects.filter(pk=self.note.pk).exists())

        mock_logger.assert_called_once_with(
            f"IntegrityError deleting note pk={self.note.pk} for project_id={self.project.pk}"
        )

        messages = [m.message for m in response.wsgi_request._messages]
        self.assertIn('Failed to delete note due to a database error.', messages)

