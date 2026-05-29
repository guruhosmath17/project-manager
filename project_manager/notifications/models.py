from django.conf import settings
from django.db import models


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        TASK_ASSIGNED = 'TASK_ASSIGNED', 'Task assigned'
        COMMENT_ADDED = 'COMMENT_ADDED', 'Comment added'
        DEADLINE_NEAR = 'DEADLINE_NEAR', 'Project deadline near'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications_received',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_sent',
    )

    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    notification_type = models.CharField(
        max_length=64,
        choices=NotificationType.choices,
        default=NotificationType.TASK_ASSIGNED,
    )

    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
    )
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
    )

    def __str__(self):
        return f"{self.notification_type} -> {self.recipient_id}: {self.message[:30]}"

