import uuid
import logging

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from project.models import Project
from task.models import Task
from todolist.models import Todolist
from task.views import FORM_MESSAGES

User = get_user_model()


class TaskDeleteViewTests(TestCase):
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
            name='Task to delete',
            description='Will be removed',
            created_by=self.user
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_delete_success(self):
        """GET request deletes the task and redirects with success message."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(
            reverse('task:delete',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f'/projects/{self.project.pk}/{self.todolist.pk}/'
        )

        # Task is gone
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

        # Success message
        messages = [m.message for m in response.wsgi_request._messages]
        self.assertIn(FORM_MESSAGES['task_deleted'], messages)

    def test_delete_unauthenticated(self):
        """Unauthenticated request redirects to login."""

        response = self.client.get(
            reverse('task:delete',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_delete_non_owner(self):
        """User who does not own the project gets 404."""
        self.client.login(email='otheruser@example.com', password='testpass123')

        response = self.client.get(
            reverse('task:delete',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_delete_invalid_project_id(self):
        self.client.login(email='testuser@example.com', password='testpass123')

        invalid_id = uuid.uuid4()

        response = self.client.get(
            reverse('task:delete',
                    kwargs={
                        'project_id': invalid_id,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())

    def test_delete_invalid_method(self):
        """POST (or any other method) returns 405."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.post(
            reverse('task:delete',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())
