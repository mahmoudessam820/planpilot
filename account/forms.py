from django import forms
from django.forms import ValidationError
from django.core.validators import RegexValidator
from django.core.validators import validate_image_file_extension
from django.contrib.auth import authenticate

from .models import UserProfile, User


# Custom form for signup validation
class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['name', 'email']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Name cannot be empty.')
        if len(name) < 2:
            raise forms.ValidationError('Name must be at least 2 characters long.')
        if len(name) > 150:
            raise forms.ValidationError('Name cannot exceed 150 characters.')
        return name

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with that email already exists.')
        return email

    def clean_password1(self):
        password = self.cleaned_data['password1']
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError({'password2': 'The two password fields did not match.'})
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


# Custom login form validation
class LoginForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=255)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        return email

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        if email and password:
            user = authenticate(email=email, password=password)
            if user is None:
                raise forms.ValidationError('Invalid email or password.')
            cleaned_data['user'] = user  # Store the authenticated user
        return cleaned_data


# User profile validation form 
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'job_title', 'bio', 'avatar', 'cover_photo','country','city',
            'department', 'phone_number','linkedin', 'github', 'website', 
            'youtube', 'facebook', 'instagram', 'x'
        ]

    # Custom validation for the avatar and cover photo fields
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 10 * 1024 * 1024:  # 10MB limit
                raise forms.ValidationError('Avatar file size must be under 10MB.')
            try:
                validate_image_file_extension(avatar)
            except forms.ValidationError:
                raise forms.ValidationError('Avatar must be an image file (e.g., PNG, JPG).')
        return avatar

    def clean_cover_photo(self):
        cover_photo = self.cleaned_data.get('cover_photo')
        if cover_photo:
            if cover_photo.size > 10 * 1024 * 1024:  # 10MB limit
                raise forms.ValidationError('Cover photo file size must be under 10MB.')
            try:
                validate_image_file_extension(cover_photo)
            except ValidationError:
                raise forms.ValidationError('Cover photo must be an image file (e.g., PNG, JPG).')
        return cover_photo

    # Custom validation for the phone number field
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Regex to validate phone number format
            phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$')
            try:
                phone_regex(phone_number)
            except ValidationError:
                raise forms.ValidationError("Phone number must be entered in the format: '+1234567890'. Up to 15 digits allowed.")
        return phone_number

