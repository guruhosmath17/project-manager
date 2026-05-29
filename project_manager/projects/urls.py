from django.urls import path

from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('create/', views.project_create, name='project_create'),
    path('<int:project_id>/', views.project_detail, name='project_detail'),
    path('<int:project_id>/edit/', views.project_edit, name='project_edit'),
    path('<int:project_id>/delete/', views.project_delete, name='project_delete'),
    path('<int:project_id>/members/add/', views.project_member_add, name='project_member_add'),
    path('<int:project_id>/members/remove/<int:user_id>/', views.project_member_remove, name='project_member_remove'),
]

