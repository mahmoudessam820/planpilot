from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect 


from .models import Todolist 
from project.models import Project 


@login_required 
def todolist(request, project_id, pk):
    pass