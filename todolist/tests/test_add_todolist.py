import uuid
import logging

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from project.models import Project
from todolist.models import Todolist
from todolist.forms import TodolistForm
from todolist.views import FORM_MESSAGES


User = get_user_model()


class TodolistAddViewTests(TestCase):
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

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_add_get_authenticated(self):
        """GET renders form with project in context."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.get(
            reverse('todolist:add', kwargs={'project_id': self.project.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'todolist/add.html')
        self.assertIsInstance(response.context['form'], TodolistForm)
        self.assertEqual(response.context['project'], self.project)

    def test_add_post_success(self):
        """Valid POST creates todolist and redirects."""
        self.client.login(email='testuser@example.com', password='testpass123')

        post_data = {
            'name': 'My Todo List',
            'description': 'A test description'
        }

        response = self.client.post(
            reverse('todolist:add', kwargs={'project_id': self.project.pk}),
            data=post_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/projects/{self.project.pk}/')

        # Todolist created
        todolist = Todolist.objects.get(name='My Todo List')
        self.assertEqual(todolist.project, self.project)
        self.assertEqual(todolist.created_by, self.user)

        # Success message
        messages = [m.message for m in response.wsgi_request._messages]
        self.assertIn(FORM_MESSAGES['success'], messages)

    def test_add_post_empty_name(self):
        """Empty name fails form validation."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.post(
            reverse('todolist:add', kwargs={'project_id': self.project.pk}),
            data={'name': '', 'description': 'valid desc'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'todolist/add.html')
        self.assertEqual(Todolist.objects.count(), 0)

    def test_add_post_name_too_long(self):
        """Name > 100 chars fails validation."""
        self.client.login(email='testuser@example.com', password='testpass123')

        long_name = 'a' * 101

        response = self.client.post(
            reverse('todolist:add', kwargs={'project_id': self.project.pk}),
            data={'name': long_name, 'description': ''}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Todolist.objects.count(), 0)

    def test_add_post_alphanumeric_name(self):
        """Alphanumeric name fails validation."""
        self.client.login(email='testuser@example.com', password='testpass123')

        response = self.client.post(
            reverse('todolist:add', kwargs={'project_id': self.project.pk}),
            data={'name': 'test123', 'description': ''}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Todolist.objects.count(), 0)

    def test_add_post_duplicate_name(self):
        """Duplicate name fails validation."""
        self.client.login(email='testuser@example.com', password='testpass123')

        # Create duplicate
        Todolist.objects.create(
            project=self.project,
            name='Duplicate Name',
            created_by=self.user
        )

        response = self.client.post(
            reverse('todolist:add', kwargs={'project_id': self.project.pk}),
            data={'name': 'Duplicate Name', 'description': ''}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Todolist.objects.filter(name='Duplicate Name').count(), 1)

    def test_add_unauthenticated(self):
        """Unauthenticated → login redirect."""
        response = self.client.get(reverse('todolist:add', kwargs={'project_id': self.project.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login'))

    def test_add_non_owner(self):
        """Non-owner → 404."""
        self.client.login(email='otheruser@example.com', password='testpass123')

        response = self.client.get(reverse('todolist:add', kwargs={'project_id': self.project.pk}))

        self.assertEqual(response.status_code, 404)

    def test_add_invalid_project(self):
        """Invalid project → 404."""
        self.client.login(email='testuser@example.com', password='testpass123')

        invalid_project_id = uuid.uuid4()

        response = self.client.get(reverse('todolist:add', kwargs={'project_id': invalid_project_id}))

        self.assertEqual(response.status_code, 404)
