import uuid
import logging

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from project.models import Project
from task.models import Task
from task.forms import EditTaskForm
from todolist.models import Todolist
from task.views import FORM_MESSAGES


User = get_user_model()


class TaskEditViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.logger = logging.getLogger('project.views')
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

        # Todolist belonging to the project
        self.todolist = Todolist.objects.create(
            project=self.project,
            name='Test List',
            created_by=self.user
        )

        # Existing task
        self.task = Task.objects.create(
            project=self.project,
            todolist=self.todolist,
            name='Original Task',
            description='Original description',
            created_by=self.user
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_edit_get_authenticated_owner(self):
        """GET request renders the edit form with the task pre-filled."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(
            reverse('task:edit',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task/edit.html')
        self.assertIsInstance(response.context['form'], EditTaskForm)
        self.assertEqual(response.context['task'], self.task)

    def test_edit_post_success(self):
        """Valid POST updates the task and redirects."""
        self.client.login(email='testuser@example.com', password='testpass123')

        post_data = {
            'name': 'Updated Task',
            'description': 'Updated description',
        }

        response = self.client.post(
            reverse('task:edit',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    }),
            data=post_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'/projects/{self.project.pk}/{self.todolist.pk}/'
        )

        messages = [m.message for m in response.wsgi_request._messages]
        self.assertIn(FORM_MESSAGES['task_updated'], messages)

        # DB was really updated
        self.task.refresh_from_db()
        self.assertEqual(self.task.name, 'Updated Task')
        self.assertEqual(self.task.description, 'Updated description')

    def test_edit_post_invalid_form(self):
        """Invalid data re-renders the form with errors."""
        self.client.login(email='testuser@example.com', password='testpass123')
        post_data = {
            'title': '',                     
            'description': 'still here'
        }

        with patch('task.forms.EditTaskForm.is_valid', return_value=False):
            with patch('task.forms.EditTaskForm.errors') as mock_errors:
                mock_errors.as_text.return_value = '* title\n  * This field is required.'
                with patch('task.views.logger'):
                    response = self.client.post(
                        reverse('task:edit',
                                kwargs={
                                    'project_id': self.project.pk,
                                    'todolist_id': self.todolist.pk,
                                    'pk': self.task.pk
                                }),
                        data=post_data
                    )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task/edit.html')
        self.assertIsInstance(response.context['form'], EditTaskForm)
        self.assertEqual(response.context['task'], self.task)

        messages = [m.message for m in response.wsgi_request._messages]
        self.assertIn('* title\n  * This field is required.', messages)

    def test_edit_unauthenticated(self):
        """Unauthenticated request redirects to login."""

        response = self.client.get(
            reverse('task:edit',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login'))

    def test_edit_non_owner(self):
        """User who does not own the project gets 404."""
        self.client.login(email='otheruser@example.com', password='testpass123')

        response = self.client.get(
            reverse('task:edit',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 404)

    def test_edit_invalid_project_id(self):
        self.client.login(email='testuser@example.com', password='testpass123')

        invalid_id = uuid.uuid4()

        response = self.client.get(
            reverse('task:edit',
                    kwargs={
                        'project_id': invalid_id,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 404)

    def test_edit_invalid_method(self):
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.put(
            reverse('task:edit',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 405)
