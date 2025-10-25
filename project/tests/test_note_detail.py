import uuid
import logging

from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from project.models import Project, ProjectNote
from project.views import FORM_MESSAGES


User = get_user_model()


class NoteDetailViewTests(TestCase):
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
            body='Test Note'  # Adjust based on actual ProjectNote model
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_note_detail_get_authenticated_owner(self):
        """Test normal case: GET request by authenticated user who owns the project"""
        self.client.login(email='testuser@example.com', password='testpass123')
        response = self.client.get(
            reverse('project:note_detail', kwargs={'project_id': self.project.pk, 'pk': self.note.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/note_detail.html')
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(response.context['note'], self.note)

    def test_note_detail_unauthenticated(self):
        """Test edge case: Unauthenticated user is redirected to login"""
        response = self.client.get(
            reverse('project:note_detail', kwargs={'project_id': self.project.pk, 'pk': self.note.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_note_detail_non_owner(self):
        """Test edge case: Authenticated user who doesn't own the project gets 404"""
        self.client.login(email='otheruser@example.com', password='testpass123')
        response = self.client.get(
            reverse('project:note_detail', kwargs={'project_id': self.project.pk, 'pk': self.note.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_note_detail_invalid_project_id(self):
        """Test invalid input: Non-existent project ID returns 404"""
        self.client.login(email='testuser@example.com', password='testpass123')
        invalid_project_id = uuid.uuid4()
        response = self.client.get(
            reverse('project:note_detail', kwargs={'project_id': invalid_project_id, 'pk': self.note.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_note_detail_invalid_note_id(self):
        """Test invalid input: Non-existent note ID returns 404"""
        self.client.login(email='testuser@example.com', password='testpass123')
        invalid_note_id = uuid.uuid4()
        response = self.client.get(
            reverse('project:note_detail', kwargs={'project_id': self.project.pk, 'pk': invalid_note_id})
        )
        self.assertEqual(response.status_code, 404)

    def test_note_detail_invalid_method(self):
        """Test invalid input: Invalid HTTP method (POST) returns 405"""
        self.client.login(email='testuser@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('project:note_detail', kwargs={'project_id': self.project.pk, 'pk': self.note.pk})
        )
        self.assertEqual(response.status_code, 405)