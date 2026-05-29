from django.contrib import admin

from .models import Project, ProjectMember


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'deadline', 'created_by', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'description')


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'role')
    list_filter = ('role',)
    search_fields = ('project__title', 'user__username')

