from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'actor', 'project', 'task', 'created_at')
    list_filter = ('action_type', 'created_at')
    search_fields = ('message',)

