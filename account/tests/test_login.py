import logging

from django.urls import reverse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

from account.forms import LoginForm

User = get_user_model()


class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('account:login')
        self.logger = logging.getLogger('django')
        self.log_handler = logging.StreamHandler()
        self.logger.addHandler(self.log_handler)

        # Create a test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            name='Test User'
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)

    def test_get_request_renders_login_form(self):
        """Test GET request renders login template with empty form"""
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/login.html')
        self.assertIsInstance(response.context['form'], LoginForm)
        self.assertFalse(response.context['form'].is_bound)

    def test_post_valid_credentials_logs_in_user(self):
        """Test POST with valid credentials logs in user and redirects to projects"""
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('project:projects'))
        
        # Check user is logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.email, 'test@example.com')
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Login successful!')

    def test_post_invalid_credentials(self):
        """Test POST with invalid password"""
        data = {
            'email': 'test@example.com',
            'password': 'WrongPass123!'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/login.html')
        self.assertTrue(response.context['form'].is_bound)
        self.assertFalse(response.context['form'].is_valid())
        
        # Check user is not logged in
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('Invalid email or password', str(messages[0]))

    def test_post_nonexistent_email(self):
        """Test POST with email that doesn't exist"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/login.html')
        self.assertFalse(response.context['form'].is_valid())
        
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertIn('Invalid email or password', str(messages[0]))

    def test_post_empty_fields(self):
        """Test POST with empty email and password"""
        data = {
            'email': '',
            'password': ''
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/login.html')
        self.assertFalse(response.context['form'].is_valid())
        
        form_errors = response.context['form'].errors

        self.assertIn('email', form_errors)
        self.assertIn('password', form_errors)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_post_invalid_email_format(self):
        """Test POST with invalid email format"""
        data = {
            'email': 'invalid-email',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/login.html')
        self.assertFalse(response.context['form'].is_valid())
        
        form_errors = response.context['form'].errors

        self.assertIn('email', form_errors)
        self.assertIn('Enter a valid email address', form_errors['email'][0])        
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_post_case_insensitive_email(self):
        """Test POST with email in different case (edge case)"""
        data = {
            'email': 'TEST@example.com',  # Different case
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('project:projects'))
        
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.email, 'test@example.com')
        
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Login successful!')

    def test_post_already_authenticated(self):
        """Test POST when user is already logged in (edge case)"""
        self.client.login(email='test@example.com', password='TestPass123!')
        
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('project:projects'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        
