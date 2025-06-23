import logging

from django.urls import reverse
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.views.decorators.http import require_http_methods

from .models import UserProfile
from .forms import UserProfileForm, SignUpForm, LoginForm


logger = logging.getLogger(__name__)

# Constants
PROFILE_URL = 'account:profile'

FORM_MESSAGES = {
    'success': 'Account created successfully, Please log in.',
    'login_success': 'Login successful.',
    'profile_update': 'Your profile has been updated successfully.'

}


@require_http_methods(["GET", "POST"])
def signup(request):
    """
    Handles user signup by creating a new User instance.
    Expects POST data with name, email, password1, and password2.
    Redirects to login on success or renders signup form on failure.
    Uses a custom User model with name and email fields.
    """
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            logger.info(f"New user signed up: {user.email}")
            messages.success(request, FORM_MESSAGES['success'])
            return redirect(reverse('account:login'))
        else:
            logger.warning(f"Failed signup attempt: {form.errors}")
            messages.error(request, form.errors.as_text())
    else:
        form = SignUpForm()

    return render(request, 'account/signup.html', {'form': form})


@require_http_methods(["GET", "POST"])
def login(request):
    """
    Handles user login by authenticating email and password.
    Expects POST data with email and password.
    Redirects to projects on success or renders login form on failure.
    Uses a custom User model with email as USERNAME_FIELD.
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']  # Retrieve the authenticated user
            auth_login(request, user)
            logger.info(f"User logged in: {form.cleaned_data['email']}")
            messages.success(request, FORM_MESSAGES['login_success'])
            return redirect(reverse('project:projects'))
        else:
            logger.warning(f"Invalid login form: {form.errors}")
            messages.error(request, form.errors.as_text())
    else:
        form = LoginForm()

    return render(request, 'account/login.html', {'form': form})


@login_required(login_url='/login')
@require_http_methods(["GET", "POST"])
def profile(request):
    return render(request, 'account/profile_page.html', {'user': request.user})


def handle_profile_form(request, profile):
    """Process the profile form and return form or redirect."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, FORM_MESSAGES['profile_update'])
            return redirect(reverse(PROFILE_URL))
        messages.error(request, form.errors.as_text())
    else:
        form = UserProfileForm(instance=profile)
    return form


@login_required(login_url='/login')
@require_http_methods(["GET", "POST"])
def edit_profile(request):
    """Handle user profile editing, including form validation and saving."""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        try:
            profile = UserProfile.objects.create(user=request.user)
        except IntegrityError:
            messages.error(request, 'Unable to retrieve or create profile.')
            return redirect(reverse(PROFILE_URL))

    # Ensure user owns the profile
    if profile.user != request.user:
        messages.error(request, 'Unauthorized access.')
        return redirect(reverse(PROFILE_URL))

    form = handle_profile_form(request, profile)
    if isinstance(form, HttpResponse):  # Redirect case
        return form

    return render(request, 'account/edit_profile.html', {'form': form})


def logout(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out!')
    return redirect('account:login')
