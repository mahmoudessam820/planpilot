from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect 
from django.contrib import messages

from project.models import Project 
from .models import Todolist 



@login_required 
def add(request, project_id):

    try:
        project = get_object_or_404(Project, created_by=request.user, pk=project_id)
    except Project.DoesNotExist:
        messages.error(request, "Project does not exist.")
        return redirect('/porject/')

    if request.method == 'POST':
        name = request.POST.get('name', '')
        description = request.POST.get('description', '')
        if name:
            Todolist.objects.create(project=project, name=name, description=description, created_by=request.user)
            return redirect(f'/projects/{project_id}/')
        else:
            messages.info(request, 'Please provide a name for the todo list') 

    context = {'project': project}

    return render(request, 'todolist/add.html', context) 


@login_required 
def todolist(request, project_id, pk):
    try:
        filtered_project = get_object_or_404(Project, created_by=request.user, pk=project_id)
        filtered_todolist = get_object_or_404(Todolist, project=filtered_project, pk=pk)
        return render(request, 'todolist/todolist.html', {
            'project': filtered_project,
            'todolist': filtered_todolist
        })
    except (Project.DoesNotExist, Todolist.DoesNotExist):
        messages.error(request, 'The requested project or todo list does not exist.')
        return redirect('/porject/')
    

@login_required 
def edit(request, project_id, pk):
    try:
        filtered_project = get_object_or_404(Project, created_by=request.user, pk=project_id)
        filtered_todolist = get_object_or_404(Todolist, project=filtered_project, pk=pk)

        if request.method == 'POST':
            name = request.POST.get('name', '')
            description = request.POST.get('description', '')

            if name:
                filtered_todolist.name = name
                filtered_todolist.description = description
                filtered_todolist.save()

                return redirect(f'/projects/{project_id}/')
            else:
                messages.error(request, 'Name is required.')
    except Todolist.DoesNotExist:
        messages.error(request, 'Todolist does not exist.')
        return redirect('/porject/')

    return render(request, 'todolist/edit.html', {
            'project': filtered_project,
            'todolist': filtered_todolist
        })


@login_required 
def delete(request, project_id, pk):

    project = get_object_or_404(Project, created_by=request.user, pk=project_id)
    todolist = get_object_or_404(Todolist, project=project, pk=pk)
    todolist.delete()
    return redirect(f'/projects/{project_id}/')