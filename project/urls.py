from django.urls import path 

from . import views 


# if you have the same name page in multiple apps you can use app_name to differentiate. 
app_name = 'project'

urlpatterns = [
    path('', views.projects, name='projects'),
    path('add/', views.add_project, name='add'),
    path('<uuid:pk>/', views.project_detail, name='project_detail'),
    path('<uuid:pk>/edit/', views.edit, name='edit'),
    path('<uuid:pk>/delete/', views.delete, name='delete'),
    path('<uuid:project_id>/files/upload/', views.upload_file, name='upload_file'),
    path('<uuid:project_id>/files/<uuid:pk>/delete/', views.delete_file, name='delete_file'),
    path('<uuid:project_id>/notes/add/', views.add_note, name='add_note'),
    path('<uuid:project_id>/notes/<uuid:pk>/detail', views.note_detail, name='note_detail'),
    path('<uuid:project_id>/notes/<uuid:pk>/edit/', views.note_edit, name='note_edit'),
    path('<uuid:project_id>/notes/<uuid:pk>/delete/', views.note_delete, name='note_delete'),
]