from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404 

from .forms import ProjectFileForm
from .models import Project, ProjectNote


# Project

@login_required
def projects(request):

    projects_list = Project.objects.filter(created_by=request.user)
    context = {'projects': projects_list}
    return render(request, 'project/projects.html', context)


@login_required
def add_project(request):

    if request.method == 'POST':

        name = request.POST.get('name', '')
        description = request.POST.get('description', '')

        if not name:
            messages.info(request, 'Project name is required')
        else:
            try:
                Project.objects.create(name=name, description=description, created_by=request.user)
                return redirect('/projects/')
            except ValidationError as e:
                messages.error(request, f'Failed to create project: {str(e)}')

    return render(request, 'project/add.html')


@login_required 
def project(request, pk):

    project_detail = get_object_or_404(Project, created_by=request.user, pk=pk)
    context = {'project': project_detail}
    return render(request, 'project/project.html', context)


@login_required
def edit(request, pk):

    project_edit = get_object_or_404(Project, pk=pk, created_by=request.user)

    if request.method == 'POST':
        name = request.POST.get('name', '')
        description = request.POST.get('description', '')

        if name:
            project_edit.name = name
            project_edit.description = description
            project_edit.save()
            return redirect('/projects/')
        else:
            messages.info(request, 'Project name is required')

    context = {'project': project_edit}
    return render(request, 'project/edit.html', context)


@login_required 
def delete(request, pk):

    project = get_object_or_404(Project, pk=pk, created_by=request.user)
    project.delete()

    return redirect('/projects/')


# Files

@login_required
def upload_file(request, project_id):

    project = get_object_or_404(Project, pk=project_id, created_by=request.user)

    if request.method == 'POST':
        form = ProjectFileForm(request.POST, request.FILES)
        try:
            if form.is_valid():
                projectfile = form.save(commit=False)
                projectfile.project = project
                projectfile.save()
                messages.success(request, 'File uploaded successfully.')
                return redirect(f'/projects/{project_id}/')
            else: 
                messages.error(request, 'Form is not valid. Please correct the errors.')
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
    else:
        form = ProjectFileForm()
    return render(request, 'project/upload_file.html', {
        'project': project,
        'form': form
    })


@login_required 
def delete_file(request, project_id, pk):

    project = get_object_or_404(Project, pk=project_id, created_by=request.user)
    projectfile = project.files.get(pk=pk)
    projectfile.delete()
    
    messages.success(request, 'File deleted successfully')
    
    return redirect(f'/projects/{project_id}/')



# Notes

@login_required
def add_note(request, project_id):

    project = get_object_or_404(Project, pk=project_id, created_by=request.user)

    if request.method == 'POST':

        name = request.POST.get('name', '')
        body = request.POST.get('body', '')

        if name and body:

            ProjectNote.objects.create(name=name, body=body, project=project)
            return redirect(f'/projects/{project_id}/')
    
    return render(request, 'project/add_note.html', {
        'project': project
    })



@login_required
def note_detail(request, project_id, pk):
    
    project = get_object_or_404(Project, pk=project_id, created_by=request.user)
    note = project.notes.get(pk=pk)

    return render(request, 'project/note_detail.html', {
        'project': project,
        'note': note
    })


@login_required
def note_edit(request, project_id, pk):
    project = get_object_or_404(Project, pk=project_id, created_by=request.user)
    note = project.notes.get(pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '')
        body = request.POST.get('body', '')

        if name and body:
            note.name = name
            note.body = body
            note.save()

            return redirect(f'/projects/{project_id}/')

    return render(request, 'project/note_edit.html', {
        'project': project,
        'note': note
    })


@login_required
def note_delete(request, project_id, pk):

    project = Project.objects.filter(created_by=request.user).get(pk=project_id)
    note = project.notes.get(pk=pk)
    note.delete()

    return redirect(f'/projects/{project_id}/')