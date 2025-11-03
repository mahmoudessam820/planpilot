import uuid
import logging

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from project.models import Project
from todolist.models import Todolist
from todolist.forms import EditTodolistForm
from todolist.views import FORM_MESSAGES


User = get_user_model()


class TodolistEditViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.logger = logging.getLogger('todolist.views')
        self.log_handler = logging.StreamHandler()
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.INFO)

        # Users
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

        # Project owned by self.user
        self.project = Project.objects.create(
            name='Test Project',
            created_by=self.user
        )

        # Existing todolist
        self.todolist = Todolist.objects.create(
            project=self.project,
            name='Original List',
            description='Original description',
            created_by=self.user
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_edit_get_authenticated_owner(self):
        """GET renders edit form with pre-filled data."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(
            reverse('todolist:edit',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'todolist/edit.html')
        self.assertIsInstance(response.context['form'], EditTodolistForm)
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(response.context['todolist'], self.todolist)

    def test_edit_post_success(self):
        """Valid POST updates todolist and redirects."""
        self.client.login(email='testuser@example.com', password='testpass123')

        post_data = {
            'name': 'Updated List',
            'description': 'Updated description'
        }

        response = self.client.post(
            reverse('todolist:edit',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk}),
            data=post_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/projects/{self.project.pk}/')

        # DB updated
        self.todolist.refresh_from_db()
        self.assertEqual(self.todolist.name, 'Updated List')
        self.assertEqual(self.todolist.description, 'Updated description')

        # Success message
        messages = [m.message for m in response.wsgi_request._messages]
        self.assertIn(FORM_MESSAGES['update'], messages)

    def test_edit_post_invalid_form(self):
        """Invalid data re-renders form with errors."""
        self.client.login(email='testuser@example.com', password='testpass123')

        post_data = {
            'name': '',  # required
            'description': 'valid'
        }

        response = self.client.post(
            reverse('todolist:edit',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk}),
            data=post_data
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'todolist/edit.html')
        self.assertIsInstance(response.context['form'], EditTodolistForm)
        self.assertEqual(response.context['todolist'], self.todolist)

        messages = [m.message for m in response.wsgi_request._messages]
        self.assertIn('This field is required.', ' '.join(messages))

    def test_edit_unauthenticated(self):
        """Unauthenticated → login redirect."""

        response = self.client.get(
            reverse('todolist:edit',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login'))

    def test_edit_non_owner(self):
        """Non-owner → 404."""
        self.client.login(email='otheruser@example.com', password='testpass123')

        response = self.client.get(
            reverse('todolist:edit',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_edit_invalid_project(self):
        self.client.login(email='testuser@example.com', password='testpass123')

        project_id = uuid.uuid4()

        response = self.client.get(
            reverse('todolist:edit',
                    kwargs={'project_id': project_id, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_edit_invalid_todolist(self):
        self.client.login(email='testuser@example.com', password='testpass123')

        todolist_id = uuid.uuid4() 

        response = self.client.get(
            reverse('todolist:edit',
                    kwargs={'project_id': self.project.pk, 'pk': todolist_id})
        )

        self.assertEqual(response.status_code, 404)

    def test_edit_invalid_method(self):
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.put(
            reverse('todolist:edit',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 405)
