import logging

from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from project.forms import ProjectForm
from project.models import Project

User = get_user_model()


class AddProjectViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.logger = logging.getLogger('project.views')
        self.log_handler = logging.StreamHandler()
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.INFO)  # Capture INFO and above for logger.info

        self.user = User.objects.create_user(
            name='testuser',
            email='testuser@gmail.com',
            password='testpass123'
        )
        # Grant the user the required permission
        content_type = ContentType.objects.get(app_label='project', model='project')
        permission = Permission.objects.get(codename='add_project', content_type=content_type)
        self.user.user_permissions.add(permission)

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_add_project_get_authenticated_user(self):
        """Test normal case: GET request by authenticated user with permission"""
        self.client.login(email='testuser@gmail.com', password='testpass123')
        response = self.client.get(reverse('project:add'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/add.html')
        self.assertIsInstance(response.context['form'], ProjectForm)
        self.assertEqual(Project.objects.count(), 0)

    def test_add_project_post_valid_form(self):
        """Test normal case: POST request with valid form data"""
        self.client.login(email='testuser@gmail.com', password='testpass123')
        form_data = {'name': 'New Project', 'description': 'Test project description'}

        with self.assertLogs('project.views', level='INFO') as cm:
            response = self.client.post(reverse('project:add'), form_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('project:projects'))
        self.assertEqual(Project.objects.count(), 1)

        project = Project.objects.first()

        self.assertEqual(project.name, 'New Project')
        self.assertEqual(project.created_by, self.user)
        self.assertIn(f"New project created: New Project by {self.user.email}", cm.output[0])

        messages = list(response.wsgi_request._messages)

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Project created successfully.')

    def test_add_project_post_invalid_form(self):
        """Test invalid input: POST request with invalid form data"""
        self.client.login(email='testuser@gmail.com', password='testpass123')
        form_data = {'name': ''}  # Invalid: name is required

        with self.assertLogs('project.views', level='WARNING') as cm:
            response = self.client.post(reverse('project:add'), form_data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/add.html')
        self.assertIsInstance(response.context['form'], ProjectForm)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('Failed project creation attempt', cm.output[0])

        messages = list(response.wsgi_request._messages)

        self.assertEqual(len(messages), 1)
        self.assertIn('This field is required', str(messages[0]))

    @patch('project.models.Project.save')
    def test_add_project_post_validation_error(self, mock_save):
        """Test edge case: POST request with valid form but database validation error"""
        mock_save.side_effect = ValidationError("Database validation error")
        self.client.login(email='testuser@gmail.com', password='testpass123')
        form_data = {'name': 'New Project', 'description': 'Test project description'}

        with self.assertLogs('project.views', level='ERROR') as cm:
            response = self.client.post(reverse('project:add'), form_data)
            
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/add.html')
        self.assertIsInstance(response.context['form'], ProjectForm)
        self.assertEqual(Project.objects.count(), 0)
        self.assertIn("Failed to create project: ['Database validation error']", cm.output[0])

        messages = list(response.wsgi_request._messages)

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Failed to create project: ['Database validation error']")

    def test_add_project_no_permission(self):
        """Test invalid input: Authenticated user without add_project permission"""
        # Create a user without the add_project permission
        no_perm_user = User.objects.create_user(
            name='nopermuser',
            email='nopermuser@gmail.com',
            password='testpass123'
        )

        self.client.login(email='nopermuser@gmail.com', password='testpass123')

        response = self.client.get(reverse('project:add'))
        
        self.assertEqual(response.status_code, 403)

    def test_add_project_invalid_method(self):
        """Test edge case: Request with disallowed HTTP method (e.g., PUT)"""
        self.client.login(email='testuser@gmail.com', password='testpass123')
        response = self.client.put(reverse('project:add'))

        self.assertEqual(response.status_code, 405)  
        




