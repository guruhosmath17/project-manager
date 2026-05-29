from django.contrib.auth import get_user_model
from rest_framework import serializers

from notifications.models import Notification
from projects.models import Project, ProjectMember
from tasks.models import Attachment, Comment, Task


User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = getattr(__import__("users.models", fromlist=["Profile"]), "Profile")
        fields = ["avatar", "bio", "designation"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True, source="profile")

    class Meta:
        model = User
        fields = ["id", "username", "email", "role", "profile"]


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectMember
        fields = ["user", "role"]


class ProjectSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    members = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "status",
            "deadline",
            "created_by",
            "members",
        ]

    def get_members(self, obj):
        memberships = obj.memberships.select_related("user").all()
        return ProjectMemberSerializer(memberships, many=True).data


class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = Attachment
        fields = ["id", "file", "uploaded_by", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "task", "user", "content", "created_at"]
        read_only_fields = ["id", "user", "created_at", "task"]


class TaskSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "title",
            "description",
            "assigned_to",
            "priority",
            "status",
            "deadline",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class NotificationSerializer(serializers.ModelSerializer):
    recipient = UserSerializer(read_only=True)
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "sender",
            "message",
            "is_read",
            "created_at",
            "notification_type",
            "project",
            "task",
        ]
        read_only_fields = ["id", "recipient", "created_at"]

