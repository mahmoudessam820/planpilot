from django.urls import path 


from . import views 


# if you have the same name page in multiple apps you can use app_name to differentiate. 
app_name = 'task'


urlpatterns = [
    path('add/', views.add, name='add'),
    path('<uuid:pk>', views.detail, name='detail'),
    path('<uuid:pk>/edit/', views.edit, name='edit'),
    path('<uuid:pk>/delete/', views.delete, name='delete'),
]