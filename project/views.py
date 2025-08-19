import logging

from django.urls import reverse
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ProjectFileForm, ProjectForm, ProjectNoteForm
from .models import Project


logger = logging.getLogger(__name__)


# Constants
FORM_MESSAGES = {
    'project_created': 'Project created successfully.',
    'update_project': 'Project updated successfully.',
    'project_deleted': 'Project deleted successfully.',
    'upload_file': 'File uploaded successfully.',
    'delete_file': 'File deleted successfully.',
    'note_created': 'Note created successfully',
    'note_updated': 'Note updated successfully',
    'note_deleted': 'Note deleted successfully',
}


# Project

@login_required(login_url='/login')
@require_http_methods(["GET"])
def projects(request):
    """
    View to display a list of projects created by the authenticated user.
    Projects are always sorted by creation date (newest first).
    """
    try:
        # Get projects sorted by created_at (newest first)
        projects_list = Project.objects.select_related('created_by') \
                                    .filter(created_by=request.user) \
                                    .order_by('-created_at')
    except Exception as e:
        logger.error(f"Error fetching projects: {str(e)}")
        messages.error(request, 'An error occurred while fetching projects.')
        projects_list = Project.objects.none()  # Return empty queryset

    context = {
        'projects': projects_list
    }

    return render(request, 'project/projects.html', context)


@login_required(login_url='/login/')
@require_http_methods(["GET", "POST"])
@permission_required('project.add_project', raise_exception=True)
def add_project(request):
    """
    View to handle project creation.
    Renders a form for GET requests and processes.
    form submission for POST requests.
    """
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            try:
                project = form.save(commit=False)
                project.created_by = request.user
                project.save()
                logger.info(
                    f"New project created: {project.name} by "
                    f"{request.user.email}"
                )
                messages.success(request, FORM_MESSAGES['project_created'])
                return redirect(reverse('project:projects'))
            except ValidationError as e:
                logger.error(f"Failed to create project: {str(e)}")
                messages.error(request, f'Failed to create project: {str(e)}')
        else:
            logger.warning(f"Failed project creation attempt: {form.errors}")
            messages.error(request, form.errors.as_text())
    else:
        form = ProjectForm()

    return render(request, 'project/add.html', {'form': form})


@login_required(login_url='/login/')
@require_http_methods(["GET"])
def project_detail(request, pk):
    """
    View to display details of a single project owned by the authenticated user.
    """
    try:
        project_detail = get_object_or_404(
            Project.objects.select_related('created_by'),
            created_by=request.user,
            pk=pk
        )
        context = {'project': project_detail}
    except Exception as e:
        logger.error(f'Error fetching project {pk}: {str(e)}', exc_info=True)
        messages.error(request, 'An error occurred while fetching the project.')

    return render(request, 'project/project_detail.html', context)


@login_required(login_url='/login/')
@require_http_methods(["GET", "POST"])
def edit(request, pk):
    """
    View to edit an existing project. Only the project creator can edit it.
    On GET, renders the edit form. On POST, validates and saves the project.
    Redirects to the project list on success or re-renders the form with errors.
    """
    project_edit = get_object_or_404(
        Project.objects.select_related('created_by'),
        pk=pk,
        created_by=request.user
    )
    form = ProjectForm(
            request.POST if request.method == 'POST' else None,
            instance=project_edit
    )

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            logger.info(
                f"Project updated: {project_edit.name} by {request.user.email}"
            )
            messages.success(request, FORM_MESSAGES['update_project'])
            return redirect(reverse('project:projects'))
        else:
            logger.warning(f"Failed project update attempt: {form.errors}")
            messages.error(request, form.errors.as_text())

    context = {'form': form, 'project': project_edit}
    return render(request, 'project/edit.html', context)


@login_required(login_url='/login/')
@require_http_methods(["GET", "POST"])
def delete(request, pk):
    """
    View to delete a project owned by the authenticated user.
    On GET, renders a confirmation template. On POST, deletes the project and redirects to the project list.
    """
    project = get_object_or_404(
        Project.objects.select_related('created_by'),
        pk=pk, created_by=request.user
    )
    try:
        with transaction.atomic():
            project.delete()
        logger.info(f"Project {project.name} deleted by {request.user.email}")
        messages.success(request, FORM_MESSAGES['project_deleted'])
        return redirect(reverse('project:projects'))
    except Exception:
        logger.error(f"Failed to delete project {project.name} by {request.user.email}")
        messages.error(request, 'An error occurred while deleting the project.')
        return redirect(reverse('project:projects'))


# Files

@login_required(login_url='/login/')
@require_http_methods(["GET", "POST"])
def upload_file(request, project_id):
    """
    Handles file uploads for a specific project.
    GET: Displays the file upload form.
    POST: Processes the file upload and associates it with the project.
    """
    project = get_object_or_404(
        Project.objects.select_related('created_by'),
        pk=project_id
    )

    if request.method == 'POST':
        form = ProjectFileForm(request.POST, request.FILES)
        if form.is_valid():
            projectfile = form.save(commit=False)
            projectfile.project = project
            projectfile.save()
            messages.success(request, FORM_MESSAGES['upload_file'])
            return redirect(f'/projects/{project_id}/')
        else:
            logger.warning(f"Failed file upload attempt: {form.errors}")
            messages.error(request, form.errors.as_text())
            return redirect(f'/projects/{project_id}/files/upload/')
    else:
        form = ProjectFileForm()
    return render(request, 'project/upload_file.html', {
        'project': project,
        'form': form
    })


@login_required(login_url='/login/')
@require_http_methods(["GET"])
def delete_file(request, project_id, pk):
    """
    Deletes a file from a project if the user is authenticated and owns the project.
    """
    project = get_object_or_404(
        Project, pk=project_id,
        created_by=request.user
    )
    projectfile = get_object_or_404(project.files, pk=pk)

    projectfile.delete()
    logger.info(f"User {request.user} deleted file {projectfile.pk} from project {project_id}")

    messages.success(request, FORM_MESSAGES['delete_file'])

    return redirect(f'/projects/{project_id}/')



# Notes

@login_required(login_url='/login/')
@require_http_methods(["GET", "POST"])
def add_note(request, project_id):
    """
    Add a note to a project for the authenticated user.
    """
    project = get_object_or_404(
        Project, pk=project_id,
        created_by=request.user
    )

    if request.method == 'POST':
        form = ProjectNoteForm(request.POST)
        if form.is_valid():
            try:
                note = form.save(commit=False)
                note.project = project
                note.save()
                messages.success(request, FORM_MESSAGES['note_created'])
                return redirect(f'/projects/{project_id}/')
            except IntegrityError:
                messages.error(request, form.errors.as_text())
        else:
            messages.error(request, form.errors.as_text())
    else:
        form = ProjectNoteForm()

    return render(request, 'project/add_note.html', {'project': project, 'form': form})


@login_required(login_url='/login/')
@require_http_methods(["GET"])
def note_detail(request, project_id, pk):
    """
    Display details of a specific note for a project owned by the authenticated user.
    """
    project = get_object_or_404(
        Project, pk=project_id,
        created_by=request.user
    )
    try:
        note = get_object_or_404(project.notes, pk=pk)
    except project.notes.model.MultipleObjectsReturned:
        logger.error(f"Multiple notes found with pk={pk} for project_id={project_id}")
        messages.error(request, 'An error occurred while retrieving the note.')
        return redirect('/projects/')

    return render(request, 'project/note_detail.html', {'project': project, 'note': note})


@login_required(login_url='/login/')
@require_http_methods(["GET", "POST"])
def note_edit(request, project_id, pk):
    """
    Edit a note for a project owned by the authenticated user.
    """

    project = get_object_or_404(
        Project, pk=project_id,
        created_by=request.user
    )
    note = get_object_or_404(project.notes, pk=pk)

    if request.method == 'POST':
        form = ProjectNoteForm(request.POST, instance=note)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, FORM_MESSAGES['note_updated'])
                return redirect(f'/projects/{project_id}/')
            except IntegrityError:
                logger.error(f"Integrity error updating note pk={pk} for project_id={project_id}")
                messages.error(request, form.errors.as_text())
        else:
            messages.error(request, form.errors.as_text())
    else:
        form = ProjectNoteForm(instance=note)

    return render(request, 'project/note_edit.html', {'project': project, 'note': note, 'form': form})


@login_required(login_url='/login/')
def note_delete(request, project_id, pk):
    """
    Delete a note from a project owned by the authenticated user..
    """
    project = get_object_or_404(
        Project, pk=project_id,
        created_by=request.user
    )
    note = get_object_or_404(project.notes, pk=pk)

    try:
        note.delete()
        messages.success(request, FORM_MESSAGES['note_deleted'])
    except IntegrityError:
        logger.error(f"IntegrityError deleting note pk={pk} for project_id={project_id}")
        messages.error(request, 'Failed to delete note due to a database error.')

    return redirect(f'/projects/{project_id}/')
