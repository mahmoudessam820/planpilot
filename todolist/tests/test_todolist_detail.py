import uuid
import logging

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from project.models import Project
from todolist.models import Todolist
from task.models import Task

User = get_user_model()


class TodolistDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.logger = logging.getLogger(__name__)  # or 'project.views' if you use that
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

        # Todolist with tasks (prefetched)
        self.todolist = Todolist.objects.create(
            project=self.project,
            name='Test List',
            created_by=self.user
        )
        Task.objects.create(
            project=self.project,
            todolist=self.todolist,
            name='Task 1',
            description='First task',
            created_by=self.user
        )
        Task.objects.create(
            project=self.project,
            todolist=self.todolist,
            name='Task 2',
            description='Second task',
            created_by=self.user
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_todolist_detail_success(self):
        """GET renders todolist with prefetched tasks."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(
            reverse('todolist:todolist',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'todolist/todolist.html')
        self.assertEqual(response.context['project'], self.project)
        self.assertEqual(response.context['todolist'], self.todolist)

        # Tasks are prefetched and accessible
        tasks = response.context['todolist'].tasks.all()
        self.assertEqual(tasks.count(), 2)
        self.assertEqual(set(tasks.values_list('name', flat=True)), {'Task 1', 'Task 2'})

    def test_todolist_detail_unauthenticated(self):
        """Unauthenticated → login redirect."""

        response = self.client.get(
            reverse('todolist:todolist',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login'))

    def test_todolist_detail_non_owner(self):
        """Non-owner → 404."""
        self.client.login(email='otheruser@example.com', password='testpass123')

        response = self.client.get(
            reverse('todolist:todolist',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_todolist_detail_invalid_project(self):
        """
        This function tests for an invalid project ID in a to-do list detail view.
        """
        self.client.login(email='testuser@example.com', password='testpass123')

        project_id = uuid.uuid4()

        response = self.client.get(
            reverse('todolist:todolist',
                    kwargs={'project_id': project_id, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_todolist_detail_invalid_todolist(self):
        """
        The function `test_todolist_detail_invalid_todolist` tests for an invalid to-do list detail by
        attempting to retrieve a non-existent to-do list.
        """

        self.client.login(email='testuser@example.com', password='testpass123')

        todolist_id = uuid.uuid4()

        response = self.client.get(
            reverse('todolist:todolist',
                    kwargs={'project_id': self.project.pk, 'pk': todolist_id})
        )

        self.assertEqual(response.status_code, 404)

    def test_todolist_detail_invalid_method(self):
        """POST returns 405."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.post(
            reverse('todolist:todolist',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 405)
