import logging
import uuid

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages

from account.models import User
from project.models import Project
from project.forms import ProjectForm


class EditViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.logger = logging.getLogger('project.views')
        self.log_handler = logging.StreamHandler()
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.ERROR)  # Ensure ERROR level logs are captured

        self.user = User.objects.create_user(
            name='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            name='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        self.project = Project.objects.create(
            name='Test Project',
            created_by=self.user,
            description='Test description'
        )

        self.url = reverse('project:edit', kwargs={'pk': self.project.pk})

        self.valid_data = {
            'name': 'Updated Project',
            'description': 'Updated description'
        }

        self.invalid_data = {
            'name': '',  # Empty name should be invalid
            'description': 'Invalid description'
        }

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)

    def test_get_edit_form_authenticated(self):
        """Test GET request with authenticated user who owns the project"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/edit.html')
        self.assertIsInstance(response.context['form'], ProjectForm)
        self.assertEqual(response.context['project'], self.project)

    def test_get_edit_form_unauthenticated(self):
        """Test GET request redirects to login for unauthenticated user"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_get_edit_form_wrong_user(self):
        """Test GET request when user is not project creator"""
        self.client.login(email='other@example.com', password='testpass123')
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, 404)
        
    def test_get_nonexistent_project(self):
        """Test GET request for non-existent project"""
        self.client.login(email='other@example.com', password='testpass123')
        pk = uuid.uuid4()

        nonexistent_url = reverse('project:edit', kwargs={'pk': pk})
        response = self.client.get(nonexistent_url)

        self.assertEqual(response.status_code, 404)

    def test_post_valid_data(self):
        """Test POST request with valid data"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.post(self.url, data=self.valid_data)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('project:projects'))
        
        # Verify project was updated
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Project')
        self.assertEqual(self.project.description, 'Updated description')
        
        # Verify success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Project updated successfully.')
        
    def test_post_invalid_data(self):
        """Test POST request with invalid data"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.post(self.url, data=self.invalid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/edit.html')
        self.assertFalse(response.context['form'].is_valid())
        
        # Verify project was not updated
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Test Project')
        
        # Verify error message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('name', str(messages[0]).lower())

    def test_post_empty_form(self):
        """Test POST request with empty form data"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.post(self.url, data={})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project/edit.html')
        self.assertFalse(response.context['form'].is_valid())
        
        # Verify project was not updated
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Test Project')

    def test_post_unauthenticated(self):
        """Test POST request redirects for unauthenticated user"""
        response = self.client.post(self.url, data=self.valid_data)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_post_wrong_user(self):
        """Test POST request when user is not project creator"""
        self.client.login(email='other@example.com', password='testpass123')
        response = self.client.post(self.url, data=self.valid_data)
        
        self.assertEqual(response.status_code, 404)
        
        # Verify project was not updated
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Test Project')

    def test_post_invalid_method(self):
        """Test invalid HTTP method (PUT)"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.put(self.url)
        
        self.assertEqual(response.status_code, 405)
