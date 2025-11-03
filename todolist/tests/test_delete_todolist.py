import uuid
import logging

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from project.models import Project
from todolist.models import Todolist
from todolist.views import FORM_MESSAGES


User = get_user_model()


class TodolistDeleteViewTests(TestCase):
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

        # Todolist to delete
        self.todolist = Todolist.objects.create(
            project=self.project,
            name='List to Delete',
            description='Will be removed',
            created_by=self.user
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_delete_success(self):
        """GET request deletes todolist and redirects with success message."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(
            reverse('todolist:delete',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/projects/{self.project.pk}/')

        # Todolist is gone
        self.assertFalse(Todolist.objects.filter(pk=self.todolist.pk).exists())

        # Success message
        messages = [m.message for m in response.wsgi_request._messages]
        self.assertIn(FORM_MESSAGES['delete'], messages)

    def test_delete_unauthenticated(self):
        """Unauthenticated → login redirect."""
        
        response = self.client.get(
            reverse('todolist:delete',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login'))
        self.assertTrue(Todolist.objects.filter(pk=self.todolist.pk).exists())

    def test_delete_non_owner(self):
        """Non-owner → 404."""
        self.client.login(email='otheruser@example.com', password='testpass123')

        response = self.client.get(
            reverse('todolist:delete',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Todolist.objects.filter(pk=self.todolist.pk).exists())

    def test_delete_invalid_project(self):
        """
        The function `test_delete_invalid_project` tests the deletion of an invalid project in a to-do list
        application.
        """
        self.client.login(email='testuser@example.com', password='testpass123')

        project_id = uuid.uuid4()

        response = self.client.get(
            reverse('todolist:delete',
                    kwargs={'project_id': project_id, 'pk': self.todolist.pk})
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Todolist.objects.filter(pk=self.todolist.pk).exists())

    def test_delete_invalid_todolist(self):
        """
        The function `test_delete_invalid_todolist` tests the deletion of an invalid to-do list in a Django
        project.
        """
        self.client.login(email='testuser@example.com', password='testpass123')

        todolist_id = uuid.uuid4()

        response = self.client.get(
            reverse('todolist:delete',
                    kwargs={'project_id': self.project.pk,
                            'pk': todolist_id})
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Todolist.objects.filter(pk=self.todolist.pk).exists())

    def test_delete_invalid_method(self):
        """POST returns 405."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.post(
            reverse('todolist:delete',
                    kwargs={'project_id': self.project.pk, 'pk': self.todolist.pk})
        )

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Todolist.objects.filter(pk=self.todolist.pk).exists())
