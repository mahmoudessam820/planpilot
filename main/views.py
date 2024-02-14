from django.shortcuts import render



def index(request):
    return render(request, 'main/index.html')


def pricing(request):
    return render(request, 'main/pricing.html')


def features(request):
    return render(request, 'main/features.html')


def team(request):
    return render(request, 'main/team.html')


def contact(request):
    return render(request, 'main/contact.html')


def about(request):
    return render(request, 'main/about.html')
