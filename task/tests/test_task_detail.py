import uuid
import logging

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from project.models import Project
from todolist.models import Todolist
from task.models import Task

User = get_user_model()


class TaskDetailViewTests(TestCase):
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

        # A task in the todolist
        self.task = Task.objects.create(
            project=self.project,
            todolist=self.todolist,
            name='Test Task',
            description='Task description',
            created_by=self.user
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_task_detail_success(self):
        """GET request by owner renders task detail."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(
            reverse('task:detail',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'task/detail.html')
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(response.context['todolist'], self.todolist)
        self.assertEqual(response.context['task'], self.task)

    def test_task_detail_unauthenticated(self):
        """Unauthenticated request redirects to login."""
        response = self.client.get(
            reverse('task:detail',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login'))

    def test_task_detail_non_owner(self):
        """Non-owner gets 404 (project query filters by created_by)."""
        self.client.login(email='otheruser@example.com', password='testpass123')

        response = self.client.get(
            reverse('task:detail',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 404)

    def test_task_detail_invalid_project_id(self):
        """Non-existent project returns 404."""
        self.client.login(email='testuser@example.com', password='testpass123')
        bad_id = uuid.uuid4()

        response = self.client.get(
            reverse('task:detail',
                    kwargs={
                        'project_id': bad_id,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 404)

    def test_task_detail_invalid_todolist_id(self):
        """Non-existent todolist returns 404."""
        self.client.login(email='testuser@example.com', password='testpass123')
        bad_id = uuid.uuid4()

        response = self.client.get(
            reverse('task:detail',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': bad_id,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 404)

    def test_task_detail_invalid_task_id(self):
        """Non-existent task returns 404."""
        self.client.login(email='testuser@example.com', password='testpass123')
        bad_id = uuid.uuid4()

        response = self.client.get(
            reverse('task:detail',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': bad_id
                    })
        )

        self.assertEqual(response.status_code, 404)

    def test_task_detail_invalid_method(self):
        """POST request returns 405 (only GET allowed)."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.post(
            reverse('task:detail',
                    kwargs={
                        'project_id': self.project.pk,
                        'todolist_id': self.todolist.pk,
                        'pk': self.task.pk
                    })
        )

        self.assertEqual(response.status_code, 405)
