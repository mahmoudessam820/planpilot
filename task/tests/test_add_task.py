import uuid
import logging
from unittest.mock import patch

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from project.models import Project
from todolist.models import Todolist
from task.models import Task
from task.views import FORM_MESSAGES
from task.forms import TaskForm


User = get_user_model()


class AddTaskViewTests(TestCase):
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

        self.todolist = Todolist.objects.create(
            project=self.project,
            name='Test List',
            created_by=self.user
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_add_task_get_authenticated_owner(self):
        """GET request renders the add-task form."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(
            reverse('task:add',
                    kwargs={'project_id': self.project.pk,
                            'todolist_id': self.todolist.pk}
                    )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task/add.html')
        self.assertIsInstance(response.context['form'], TaskForm)
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(response.context['todolist'], self.todolist)
        self.assertEqual(Task.objects.count(), 0)

    def test_add_task_post_success(self):
        """POST with valid data creates a task and redirects."""
        self.client.login(email='testuser@example.com', password='testpass123')
        post_data = {
            'title': 'New Task',
            'description': 'Task description',
        }

        with patch('task.forms.TaskForm.is_valid', return_value=True) as mock_valid:
            with patch('task.forms.TaskForm.save') as mock_save:
                mock_instance = mock_save.return_value
                response = self.client.post(
                    reverse('task:add',
                            kwargs={'project_id': self.project.pk,
                                    'todolist_id': self.todolist.pk}
                            ),

                    data=post_data
                )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f'/projects/{self.project.pk}/{self.todolist.pk}/'
        )

        # instance fields were set correctly
        self.assertEqual(mock_instance.project, self.project)
        self.assertEqual(mock_instance.todolist, self.todolist)
        self.assertEqual(mock_instance.created_by, self.user)

        mock_instance.save.assert_called_once()
        messages = [m.message for m in response.wsgi_request._messages]

        self.assertIn(FORM_MESSAGES['task_created'], messages)

    def test_add_task_post_invalid_form(self):
        """POST with missing required fields re-renders the form with errors."""
        self.client.login(email='testuser@example.com', password='testpass123')
        post_data = {
            'title': '',               # required field left empty
            'description': ''
        }

        with patch('task.forms.TaskForm.is_valid', return_value=False) as mock_valid:
            with patch('task.forms.TaskForm.errors') as mock_errors:
                mock_errors.as_text.return_value = '* title\n  * This field is required.'
                response = self.client.post(
                    reverse('task:add',
                            kwargs={'project_id': self.project.pk, 'todolist_id': self.todolist.pk}),
                    data=post_data
                )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task/add.html')
        self.assertIsInstance(response.context['form'], TaskForm)
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(response.context['todolist'], self.todolist)

        messages = [m.message for m in response.wsgi_request._messages]

        self.assertIn(mock_errors.as_text.return_value, messages)
        self.assertEqual(Task.objects.count(), 0)

    def test_add_task_unauthenticated(self):
        """Unauthenticated request redirects to login."""
        response = self.client.get(
            reverse('task:add',
                    kwargs={'project_id': self.project.pk, 'todolist_id': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        self.assertEqual(Task.objects.count(), 0)

    def test_add_task_non_owner(self):
        """User who does not own the project gets 404."""
        self.client.login(email='otheruser@example.com', password='testpass123')

        response = self.client.get(
            reverse('task:add',
                    kwargs={'project_id': self.project.pk, 'todolist_id': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Task.objects.count(), 0)

    def test_add_task_invalid_project_id(self):
        """Non-existent project returns 404."""
        self.client.login(email='testuser@example.com', password='testpass123')
        bad_id = uuid.uuid4()

        response = self.client.get(
            reverse('task:add',
                    kwargs={'project_id': bad_id, 'todolist_id': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Task.objects.count(), 0)

    def test_add_task_invalid_todolist_id(self):
        """Todolist not found or not in the project returns 404."""
        self.client.login(email='testuser@example.com', password='testpass123')
        bad_id = uuid.uuid4()

        response = self.client.get(
            reverse('task:add',
                    kwargs={'project_id': self.project.pk, 'todolist_id': bad_id})
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Task.objects.count(), 0)

    def test_add_task_invalid_method(self):
        """PUT (or any method other than GET/POST) returns 405."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.put(
            reverse('task:add',
                    kwargs={'project_id': self.project.pk, 'todolist_id': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 405)
        self.assertEqual(Task.objects.count(), 0)
