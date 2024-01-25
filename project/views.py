from django.shortcuts import render



def projects(request):
    return render(request, 'project/projects.html')