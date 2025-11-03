import logging

from django.urls import reverse
from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods

from project.models import Project
from .models import Todolist
from .forms import TodolistForm, EditTodolistForm


# configure logging
logger = logging.getLogger(__name__)

# form messages
FORM_MESSAGES = {
    'success': 'To-do list created successfully.',
    'update': 'To-do list updated successfully.',
    'delete': 'To-do list deleted successfully.',
}


@login_required(login_url='/login')
@require_http_methods(["GET", "POST"])
def add(request, project_id):
    """
    Add a to-do list to a project owned by the authenticated user.
    """
    project = get_object_or_404(
        Project,
        pk=project_id,
        created_by=request.user
    )

    if request.method == 'POST':
        form = TodolistForm(request.POST)
        if form.is_valid():
            try:
                todolist = form.save(commit=False)
                todolist.project = project
                todolist.created_by = request.user
                todolist.save()
                messages.success(request, FORM_MESSAGES['success'])
                return redirect(f'/projects/{project_id}/')
            except IntegrityError as e:
                logger.error(f"Error creating to-do list for project_id={project_id}: {str(e)}")
                messages.error(request, form.errors.as_text())
        else:
            messages.error(request, form.errors.as_text())
    else:
        form = TodolistForm()

    context = {
        'project': project,
        'form': form,
    }

    return render(request, 'todolist/add.html', context)


@login_required(login_url='/login')
@require_http_methods(["GET"])
def todolist(request, project_id, pk):
    """
    Display details of a to-do list within a project owned by the authenticated user.
    """
    project = get_object_or_404(Project, pk=project_id, created_by=request.user)
    todolist = get_object_or_404(Todolist.objects.prefetch_related('tasks'), pk=pk, project=project)

    try:
        return render(request, 'todolist/todolist.html', {
            'project': project,
            'todolist': todolist,
        })
    except MultipleObjectsReturned:
        logger.error(f"Multiple to-do lists found with pk={pk} for project_id={project_id}")
        messages.error(request, 'An error occurred while retrieving the to-do list.')
        return redirect(reverse('project:projects'))


@login_required(login_url='/login')
@require_http_methods(["GET", "POST"])
def edit(request, project_id, pk):
    """
    Edit a to-do list within a project owned by the authenticated user.
    """
    project = get_object_or_404(Project, pk=project_id, created_by=request.user)
    todolist = get_object_or_404(Todolist, pk=pk, project=project)

    if request.method == 'POST':
        form = EditTodolistForm(request.POST, instance=todolist)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, FORM_MESSAGES['update'])
                return redirect(f'/projects/{project_id}/')
            except IntegrityError as e:
                logger.error(f"Error updating to-do list pk={pk} for project_id={project_id}: {str(e)}")
                messages.error(request, 'Failed to update to-do list due to a database error.')
        else:
            messages.error(request, form.errors.as_text())
    else:
        form = EditTodolistForm(instance=todolist)

    return render(request, 'todolist/edit.html', {
        'project': project,
        'todolist': todolist,
        'form': form
    })


@login_required(login_url='/login')
@require_http_methods(["DELETE", "GET"])
def delete(request, project_id, pk):
    """
    Delete a to-do list from a project owned by the authenticated user.
    """
    project = get_object_or_404(Project, pk=project_id, created_by=request.user)
    todolist = get_object_or_404(Todolist, pk=pk, project=project)

    try:
        todolist.delete()
        messages.success(request, FORM_MESSAGES['delete'])
    except IntegrityError:
        logger.error(f"IntegrityError deleting to-do list pk={pk} for project_id={project_id}")
        messages.error(request, 'Failed to delete to-do list due to a database error.')

    return redirect(f'/projects/{project_id}/')
