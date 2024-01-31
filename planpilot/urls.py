from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('', include('account.urls')),
    path('projects/', include('project.urls')),
    path('projects/<uuid:project_id>/', include('todolist.urls')),
    path('projects/<uuid:project_id>/<uuid:todolist_id>/', include('task.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # This is for handling url it will create url for attchment files, 
                                                                  # Can than open the file in a new tab.
