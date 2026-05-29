from django.conf import settings
from django.db import models


class ActivityLog(models.Model):
    class ActionType(models.TextChoices):
        PROJECT_CREATED = 'PROJECT_CREATED', 'Project created'
        PROJECT_UPDATED = 'PROJECT_UPDATED', 'Project updated'
        PROJECT_DELETED = 'PROJECT_DELETED', 'Project deleted'

        TASK_CREATED = 'TASK_CREATED', 'Task created'
        TASK_UPDATED = 'TASK_UPDATED', 'Task updated'
        TASK_DELETED = 'TASK_DELETED', 'Task deleted'
        TASK_COMMENTED = 'TASK_COMMENTED', 'Task comment added'
        TASK_ASSIGNED = 'TASK_ASSIGNED', 'Task assigned'
        TASK_STATUS_CHANGED = 'TASK_STATUS_CHANGED', 'Task status changed'

        MEMBER_ADDED = 'MEMBER_ADDED', 'Member added'
        MEMBER_REMOVED = 'MEMBER_REMOVED', 'Member removed'

        SYSTEM_EVENT = 'SYSTEM_EVENT', 'System event'

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
    )

    action_type = models.CharField(max_length=64, choices=ActionType.choices)
    message = models.TextField(blank=True)

    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
    )
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        actor = getattr(self.actor, 'username', 'System')
        return f'[{self.action_type}] {actor} @ {self.created_at:%Y-%m-%d %H:%M}'

