"""
URL configuration for project_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),

    # Web UI
    path('', include(('users.urls', 'users'), namespace='users')),
    path('', include(('analytics.urls', 'analytics'), namespace='analytics')),
    path('projects/', include(('projects.urls', 'projects'), namespace='projects')),
    path('tasks/', include(('tasks.urls', 'tasks'), namespace='tasks')),

    # API
    path('api/', include(('api.urls', 'api'), namespace='api')),
]






