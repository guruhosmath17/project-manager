from django.contrib import admin

from .models import Attachment, Comment, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'assigned_to', 'priority', 'status', 'deadline', 'created_by', 'created_at')
    list_filter = ('status', 'priority')
    search_fields = ('title', 'description', 'project__title', 'assigned_to__username')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'created_at')
    search_fields = ('task__title', 'user__username', 'content')


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('task', 'uploaded_by', 'created_at')
    search_fields = ('task__title', 'uploaded_by__username')

