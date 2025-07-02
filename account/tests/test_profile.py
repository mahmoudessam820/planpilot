import logging

from django.urls import reverse
from unittest.mock import patch
from django.db import IntegrityError
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.files.uploadedfile import SimpleUploadedFile

from account.forms import UserProfileForm
from account.models import UserProfile


User = get_user_model()


class EditProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile_url = reverse('account:profile')
        self.edit_profile_url = reverse('account:edit')
        self.logger = logging.getLogger('django')
        self.log_handler = logging.StreamHandler()
        self.logger.addHandler(self.log_handler)

        # Create a test user and profile
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            name='Test User'
        )
        self.profile = UserProfile.objects.create(user=self.user)

        # Create another user for unauthorized access test
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='OtherPass123!',
            name='Other User'
        )

    def tearDown(self):
        self.logger.removeHandler(self.log_handler)

    def test_get_request_renders_edit_profile_form(self):
        """Test GET request renders edit profile template with form"""
        self.client.login(email='test@example.com', password='TestPass123!')
        response = self.client.get(self.edit_profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/edit_profile.html')
        self.assertIsInstance(response.context['form'], UserProfileForm)
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(response.context['form'].instance, self.profile)

    def test_post_valid_form_updates_profile(self):
        """Test POST with valid form data updates profile and redirects"""
        self.client.login(email='test@example.com', password='TestPass123!')

        data = {
            'bio': 'Updated bio',  # Example field, adjust based on UserProfileForm
            'phone_number': '1234567890'
        }
        response = self.client.post(self.edit_profile_url, data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)

        self.profile.refresh_from_db()

        self.assertEqual(self.profile.bio, 'Updated bio')
        self.assertEqual(self.profile.phone_number, '1234567890')

        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Profile updated successfully!')

    def test_post_invalid_form(self):
        """Test POST with invalid form data"""
        self.client.login(email='test@example.com', password='TestPass123!')

        data = {
            'bio': 'x' * 1001,  # Assuming max_length=1000 for bio
            'phone_number': 'invalid'  # Invalid phone number format
        }

        response = self.client.post(self.edit_profile_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/edit_profile.html')
        self.assertTrue(response.context['form'].is_bound)
        self.assertFalse(response.context['form'].is_valid())

        form_errors = response.context['form'].errors

        self.assertIn('bio', form_errors)
        self.assertIn('phone_number', form_errors)

        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(len(messages), 1)
        self.assertIn('Bio cannot exceed 1000 characters.', str(messages[0]))

    def test_nonexistent_profile_creation(self):
        """Test profile creation when UserProfile does not exist"""
        self.client.login(email='test@example.com', password='TestPass123!')
        self.profile.delete()  # Remove existing profile

        response = self.client.get(self.edit_profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/edit_profile.html')
        self.assertIsInstance(response.context['form'], UserProfileForm)
        self.assertEqual(response.context['form'].instance.user, self.user)

        profile = UserProfile.objects.get(user=self.user)

        self.assertIsNotNone(profile)

    def test_profile_creation_integrity_error(self):
        """Test handling of IntegrityError during profile creation"""
        self.client.login(email='test@example.com', password='TestPass123!')
        self.profile.delete()
        
        with patch('account.models.UserProfile.objects.create', side_effect=IntegrityError):
            response = self.client.get(self.edit_profile_url)
            
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, self.profile_url)
            
            messages = list(get_messages(response.wsgi_request))
            
            self.assertEqual(len(messages), 1)
            self.assertEqual(str(messages[0]), 'Unable to retrieve or create profile.')

    def test_unauthorized_profile_access(self):
        """Test accessing another user's profile"""
        other_profile = UserProfile.objects.create(user=self.other_user)
        self.client.login(email='test@example.com', password='TestPass123!')
        
        # Mock UserProfile.objects.get to return another user's profile
        with patch('account.models.UserProfile.objects.get', return_value=other_profile):
            response = self.client.get(self.edit_profile_url)
            
            self.assertEqual(response.status_code, 302)
            self.assertRedirects(response, self.profile_url)
            
            messages = list(get_messages(response.wsgi_request))
            
            self.assertEqual(len(messages), 1)
            self.assertEqual(str(messages[0]), 'Unauthorized access.')

