from django.urls import path

from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('projects/<int:project_id>/report/', views.project_status_report, name='project_status_report'),
    path('projects/<int:project_id>/report/pdf/', views.project_status_report_pdf, name='project_status_report_pdf'),
]

