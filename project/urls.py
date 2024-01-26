from django.urls import path 


from . import views 


# if you have the same name page in multiple apps you can use app_name to differentiate. 
app_name = 'project'



urlpatterns = [
    path('', views.projects, name='projects'),
    path('add/', views.add_project, name='add'),
    path('<uuid:pk>/', views.project, name='project'),
    path('<uuid:pk>/edit/', views.edit, name='edit'),
    path('<uuid:pk>/delete/', views.delete, name='delete'),
]