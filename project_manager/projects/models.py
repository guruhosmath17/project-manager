from django.conf import settings
from django.db import models


class Project(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'Planned', 'Planned'
        ACTIVE = 'Active', 'Active'
        COMPLETED = 'Completed', 'Completed'
        ON_HOLD = 'On Hold', 'On Hold'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PLANNED)
    deadline = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projects_created',
    )

    # Members are managed via ProjectMember
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ProjectMember',
        related_name='projects',
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ProjectMember(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'Admin', 'Admin'
        MANAGER = 'Manager', 'Manager'
        DEVELOPER = 'Developer', 'Developer'
        VIEWER = 'Viewer', 'Viewer'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.VIEWER)

    class Meta:
        unique_together = (('project', 'user'),)

    def __str__(self):
        return f'{self.user} in {self.project} ({self.role})'

