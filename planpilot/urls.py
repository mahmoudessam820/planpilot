from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls', namespace='main')),
    path('', include('account.urls', namespace='account')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('projects/', include('project.urls')),
    path('projects/<uuid:project_id>/', include('todolist.urls')),
    path('projects/<uuid:project_id>/<uuid:todolist_id>/', include('task.urls')),
    path('__debug__/', include('debug_toolbar.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) # This is for handling url it will create url for attchment files, Can than open the file in a new tab.
