from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404 


from .models import Project



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
    
    context = {'project': project_edit}
    return render(request, 'project/edit.html', context)


@login_required 
def delete(request, pk):

    project = get_object_or_404(Project, pk=pk, created_by=request.user)
    project.delete()

    return redirect('/projects/')