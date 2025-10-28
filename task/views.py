import logging

from sqlite3 import IntegrityError

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

from project.models import Project
from todolist.models import Todolist

from .models import Task
from .forms import TaskForm, EditTaskForm


# Configure logging
logger = logging.getLogger(__name__)

# constants
FORM_MESSAGES = {
    'task_created': 'Task created successfully.',
    'task_updated': 'Task updated successfully.',
    'tast_done': 'Task marked as done',
    'task_deleted': 'Task deleted successfully.',
}


@login_required(login_url='/login/')
@require_http_methods(["GET", "POST"])
def add(request, project_id, todolist_id):
    """
    Add a task to a to-do list within a project owned by the authenticated user.
    """
    project = get_object_or_404(
        Project,
        pk=project_id,
        created_by=request.user
    )
    todolist = get_object_or_404(Todolist, pk=todolist_id, project=project)

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            try:
                task = form.save(commit=False)
                task.project = project
                task.todolist = todolist
                task.created_by = request.user
                task.save()
                messages.success(request, FORM_MESSAGES['task_created'])
                return redirect(f'/projects/{project_id}/{todolist_id}/')
            except IntegrityError as e:
                logger.error(f"Error creating task for project_id={project_id}, todolist_id={todolist_id}: {str(e)}")
                messages.error(request, form.errors.as_text())
                return redirect(f'/projects/{project_id}/{todolist_id}/')
        else:
            messages.error(request, form.errors.as_text())
    else:
        form = TaskForm()

    return render(request, 'task/add.html', {
        'project': project,
        'todolist': todolist,
        'form': form,
    })


@login_required(login_url='/login')
@require_http_methods(["GET"])
def detail(request, project_id, todolist_id, pk):
    """
    Display details of a task within a to-do list and project owned by the authenticated user.
    """
    project = get_object_or_404(
        Project,
        created_by=request.user,
        pk=project_id
    )
    todolist = get_object_or_404(Todolist, project=project, pk=todolist_id)
    task = get_object_or_404(Task, project=project, todolist=todolist, pk=pk)

    context = {
        'project': project,
        'todolist': todolist,
        'task': task
    }

    return render(request, 'task/detail.html', context)


@login_required(login_url='/login')
@require_http_methods(["POST"])
def toggle_done(request, project_id, todolist_id, pk):
    """
    Toggle the 'is_done' status of a task within a to-do list and project owned by the authenticated user.
    """
    project = get_object_or_404(Project, pk=project_id, created_by=request.user)
    todolist = get_object_or_404(Todolist, pk=todolist_id, project=project)
    task = get_object_or_404(Task, pk=pk, project=project, todolist=todolist)

    try:
        task.is_done = not task.is_done  # Toggle the current state
        task.save()
        messages.success(request, FORM_MESSAGES['tast_done'])
    except IntegrityError:
        logger.error(f"Error toggling is_done for task pk={pk}, project_id={project_id}, todolist_id={todolist_id}: {str(e)}")
        messages.error(request, 'Failed to update task status due to a database error.')

    return redirect(f'/projects/{project_id}/{todolist_id}/')


@login_required(login_url='/login')
@require_http_methods(["GET", "POST"])
def edit(request, project_id, todolist_id, pk):
    """
    Edit a task within a to-do list and project owned by the authenticated user.
    """
    project = get_object_or_404(Project, pk=project_id, created_by=request.user)
    todolist = get_object_or_404(Todolist, pk=todolist_id, project=project)
    task = get_object_or_404(Task, pk=pk, project=project, todolist=todolist)

    if request.method == 'POST':
        form = EditTaskForm(request.POST, instance=task)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, FORM_MESSAGES['task_updated'])
                return redirect(f'/projects/{project_id}/{todolist_id}/')
            except IntegrityError as e:
                logger.error(f"Error updating task pk={pk} for project_id={project_id}, todolist_id={todolist_id}: {str(e)}")
                messages.error(request, form.errors.as_text())
        else:
            messages.error(request, form.errors.as_text())
    else:
        form = EditTaskForm(instance=task)

    return render(request, 'task/edit.html', {
                    'task': task,
                    'form': form
                })


@require_http_methods(["DELETE", "GET"])
@login_required(login_url='/login/')
def delete(request, project_id, todolist_id, pk):
    """
    Delete a task from a to-do list within a project owned by the authenticated user.
    """
    project = get_object_or_404(Project, pk=project_id, created_by=request.user)
    todolist = get_object_or_404(Todolist, pk=todolist_id, project=project)
    task = get_object_or_404(todolist.tasks, pk=pk)

    try:
        task.delete()
        messages.success(request, FORM_MESSAGES['task_deleted'])
    except IntegrityError:
        logger.error(f"IntegrityError deleting task pk={pk} for project_id={project_id}, todolist_id={todolist_id}")
        messages.error(request, 'Failed to delete task due to a database error.')

    return redirect(f'/projects/{project_id}/{todolist_id}/')
