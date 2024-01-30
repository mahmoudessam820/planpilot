from django.contrib import admin
from django.urls import path, include



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('', include('account.urls')),
    path('projects/', include('project.urls')),
    path('projects/<uuid:project_id>/', include('todolist.urls')),
    path('projects/<uuid:project_id>/<uuid:todolist_id>/', include('task.urls')),
]
