from django import forms

from .models import Task


class TaskAIContextFormMixin:
    """Small helper for future extension."""


class TaskForm(forms.Form):
    # Not used directly (we post manually from templates), kept for consistency.
    pass


