from sqlite3 import IntegrityError
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages 


from project.models import Project 
from todolist.models import Todolist
from .models import Task



@login_required
def add(request, project_id, todolist_id):

    try:
        project = get_object_or_404(Project, created_by=request.user, pk=project_id)
        todolist = get_object_or_404(Todolist, project=project, pk=todolist_id)
    except (Project.DoesNotExist, Todolist.DoesNotExist):
        messages.error(request, 'Project or Todolist does not exist.')
        return redirect(f'/projects/{project_id}/{todolist_id}/')

    if request.method == 'POST':

        name = request.POST.get('name', '')
        description = request.POST.get('description', '')

        if name:
            try:
                Task.objects.create(name=name, description=description, project=project, todolist=todolist, created_by=request.user)
                messages.success(request, 'Task created successfully.')
                return redirect(f'/projects/{project_id}/{todolist_id}/')
            except IntegrityError:
                messages.error(request, 'An error occurred while creating the task. Please try again.')
        else:
            messages.warning(request, 'Task name cannot be empty.')

    return render(request, 'task/add.html')


@login_required
def detail(request, project_id, todolist_id, pk):
    
    try:

        project = get_object_or_404(Project, created_by=request.user, pk=project_id)
        todolist = get_object_or_404(Todolist, project=project, pk=todolist_id)
        task = get_object_or_404(Task, project=project, todolist=todolist, pk=pk)

    except (Project.DoesNotExist, Todolist.DoesNotExist, Task.DoesNotExist): 
        messages.error(request, 'Project or Todolist or Task does not exist.')
        return redirect(f'/projects/{project_id}/{todolist_id}/')
    
    if request.GET.get('is_done', '') == 'yes':
        task.is_done = True 
        task.save() 

    context = {'task': task}

    return render(request, 'task/detail.html', context)



@login_required
def edit(request, project_id, todolist_id, pk):

    try:

        project = get_object_or_404(Project, created_by=request.user, pk=project_id)
        todolist = get_object_or_404(Todolist, project=project, pk=todolist_id)
        task = get_object_or_404(Task, project=project, todolist=todolist, pk=pk)

    except (Project.DoesNotExist, Todolist.DoesNotExist, Task.DoesNotExist): 
        messages.error(request, 'Project or Todolist or Task does not exist.')
        return redirect(f'/projects/{project_id}/{todolist_id}/')
    
    if request.method == 'POST':

        name = request.POST.get('name', '')
        description = request.POST.get('description', '')

        if name:
            try:
                task.name = name 
                task.decsriptio = description
                task.save() 
                messages.success(request, 'Task updated successfully.')
                return redirect(f'/projects/{project_id}/{todolist_id}/')
            except IntegrityError:
                messages.error(request, 'An error occurred while creating the task. Please try again.')
        else:
            messages.warning(request, 'Task name cannot be empty.')

    context = {'task': task}
    return render(request, 'task/edit.html', context)


@login_required
def delete(request, project_id, todolist_id, pk):

    project = Project.objects.filter(created_by=request.user).get(pk=project_id)
    todolist = Todolist.objects.filter(project=project).get(pk=todolist_id)
    task = Task.objects.filter(project=project).filter(todolist=todolist).get(pk=pk)
    task.delete()

    messages.success(request, 'Task deleted successfully')

    return redirect(f'/projects/{project_id}/{todolist_id}/')