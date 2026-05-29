from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'Admin', 'Admin'
        PROJECT_MANAGER = 'Project Manager', 'Project Manager'
        DEVELOPER = 'Developer', 'Developer'
        VIEWER = 'Viewer', 'Viewer'

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.VIEWER,
    )


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    designation = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f'Profile({self.user.username})'

