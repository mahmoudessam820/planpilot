from django.urls import path 


from . import views 


# if you have the same name page in multiple apps you can use app_name to differentiate. 
app_name = 'project'



urlpatterns = [
    path('', views.projects, name='projects'),
]