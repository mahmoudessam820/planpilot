from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import IntegrityError
from django.urls import reverse


from .models import User


def signup(request):

    if request.method == 'POST':

        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        password1 = request.POST.get('password1', '' )
        password2 = request.POST.get('password2', '' )

        if not (name and email and password1 and password2):
            messages.warning(request, 'All fields are required.')
            return redirect('/signup/')

        if password1 != password2:
            messages.warning(request, 'Passwords do not match.')
            return redirect('/signup/')

        try:
            User.objects.create_user(name=name, email=email, password=password1)
            messages.success(request, 'Account created successfully.')
            return redirect('/login/')
        except IntegrityError:
            messages.error(request, 'Email already exists, Please try again with a different email.')
            return redirect('/signup/')

    return render(request, 'account/signup.html')


def login(request):

    if request.method == 'POST':

        email = request.POST.get('email', '')
        password = request.POST.get('password', '')

        if email and password:

            user = authenticate(email=email, password=password)
            if user is not None:
                auth_login(request, user) 
                messages.success(request, 'Login successful')
                return redirect('/')
            else:
                messages.error(request, 'Invalid email or password') 

        else:
            messages.error(request, 'Please provide email and password')  

    return render(request, 'account/login.html')

