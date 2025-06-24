import logging

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

from account.forms import SignUpForm


User = get_user_model()


class SignupViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('account:signup')
        self.logger = logging.getLogger('django')
        self.log_handler = logging.StreamHandler()
        self.logger.addHandler(self.log_handler)

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)

    def test_get_request_renders_signup_form(self):
        """Test GET request renders signup template with empty form"""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/signup.html')
        self.assertIsInstance(response.context['form'], SignUpForm)
        self.assertFalse(response.context['form'].is_bound)

    def test_post_valid_data_creates_user(self):
        """Test POST with valid data creates user and redirects to login"""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        response = self.client.post(self.signup_url, data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login'))

        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.name, 'Test User')

        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Account created successfully, Please log in.')

    def test_post_invalid_email(self):
        """Test POST with invalid email format"""
        data = {
            'name': 'Test User',
            'email': 'invalid-email',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        response = self.client.post(self.signup_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/signup.html')
        self.assertTrue(response.context['form'].is_bound)
        self.assertFalse(response.context['form'].is_valid())

        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertIn('Enter a valid email address', str(messages[0]))

    def test_post_mismatched_passwords(self):
        """Test POST with mismatched passwords"""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass123!'
        }
        response = self.client.post(self.signup_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/signup.html')
        self.assertFalse(response.context['form'].is_valid())
        
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertIn('The two password fields did not match', str(messages[0]))

    def test_post_empty_fields(self):
        """Test POST with empty fields"""
        data = {
            'name': '',
            'email': '',
            'password1': '',
            'password2': ''
        }

        response = self.client.post(self.signup_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/signup.html')
        self.assertFalse(response.context['form'].is_valid())

        form_errors = response.context['form'].errors

        self.assertIn('name', form_errors)
        self.assertIn('email', form_errors)
        self.assertIn('password1', form_errors)

    def test_post_duplicate_email(self):
        """Test POST with email that already exists"""
        User.objects.create_user(
            name='Existing User',
            email='test@example.com',
            password='TestPass123!'
        )
        
        data = {
            'name': 'New User',
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }
        response = self.client.post(self.signup_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/signup.html')
        self.assertFalse(response.context['form'].is_valid())
        
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertIn('A user with that email already exists.', str(messages[0]))

    def test_post_short_password(self):
        """Test POST with password that's too short"""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password1': 'Short1!',
            'password2': 'Short1!'
        }
        response = self.client.post(self.signup_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/signup.html')
        self.assertFalse(response.context['form'].is_valid())
        
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertIn('Password must be at least 8 characters long.', str(messages[0]))

    def test_post_long_name(self):
        """Test POST with excessively long name"""
        data = {
            'name': 'A' * 151,  # Assuming max_length=150 for name
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!'
        }

        response = self.client.post(self.signup_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/signup.html')
        self.assertFalse(response.context['form'].is_valid())
        
        form_errors = response.context['form'].errors

        self.assertIn('name', form_errors)
        self.assertIn('Name cannot exceed 150 characters.', form_errors['name'][0])