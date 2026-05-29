from django.contrib.auth import get_user_model
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from notifications.models import Notification
from projects.models import Project, ProjectMember
from tasks.models import Comment, Task

from .permissions import AllowReadOnlyForNonPrivileged
from .serializers import (
    CommentSerializer,
    NotificationSerializer,
    ProjectSerializer,
    TaskSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        role = request.data.get("role", User.Role.VIEWER) if hasattr(User, "Role") else "Viewer"

        if not username or not email or not password:
            return Response({"detail": "username, email, password are required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"detail": "username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password, role=role)
        # profile is optional if your migrations create it; best-effort create
        try:
            from users.models import Profile

            Profile.objects.create(user=user)
        except Exception:
            pass

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_roles = ["Admin", "Manager"]

    def get_queryset(self):
        return Project.objects.filter(members=self.request.user)

    def perform_create(self, serializer):
        project = serializer.save(created_by=self.request.user)
        ProjectMember.objects.get_or_create(project=project, user=self.request.user, defaults={"role": ProjectMember.Role.ADMIN})

    def perform_update(self, serializer):
        serializer.save()

    def check_object_permissions(self, request, obj):
        # Always require membership
        super().check_object_permissions(request, obj)


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, AllowReadOnlyForNonPrivileged]

    required_roles = ["Admin", "Manager"]

    def get_queryset(self):
        return Task.objects.filter(project__members=self.request.user)

    def perform_create(self, serializer):
        project = serializer.validated_data["project"]
        if not project.members.filter(id=self.request.user.id).exists():
            raise permissions.PermissionDenied("Not a project member")
        serializer.save(created_by=self.request.user)

    def get_permissions(self):
        return super().get_permissions()

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        if request.method in ["PUT", "PATCH"]:
            # writers require membership role
            self.check_object_permissions(request, task)
        return super().update(request, *args, **kwargs)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(task__project__members=self.request.user)

    def perform_create(self, serializer):
        task_id = self.kwargs.get("task_id")
        task = Task.objects.get(id=task_id)
        if not task.project.members.filter(id=self.request.user.id).exists():
            raise permissions.PermissionDenied("Not a project member")
        serializer.save(user=self.request.user, task=task)

    def get_serializer_context(self):
        return {"request": self.request}


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by("-created_at")

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({"detail": "ok"})

