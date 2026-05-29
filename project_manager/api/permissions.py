from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsProjectMember(BasePermission):
    """Checks that the requesting user is a member of the referenced project."""

    def has_object_permission(self, request, view, obj):
        # obj can be Task/Comment/Notification/etc. that has `project` or `task.project`
        user = request.user
        project = getattr(obj, "project", None)
        if project is None and hasattr(obj, "task"):
            project = getattr(obj.task, "project", None)
        if project is None:
            # fallback: if obj has project_id
            project_id = getattr(obj, "project_id", None)
            if project_id is not None:
                from projects.models import Project

                project = Project.objects.filter(id=project_id).first()
        if project is None:
            return False
        return project.members.filter(id=user.id).exists()


class RoleBasedProjectPermission(BasePermission):
    """Role gate based on ProjectMember.role.

    Required roles can be provided by setting:
      view.required_roles = ["Admin", "Manager"] etc.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        required_roles = getattr(view, "required_roles", None)
        if not required_roles:
            return True

        user = request.user
        project = getattr(obj, "project", None)
        if project is None and hasattr(obj, "task"):
            project = getattr(obj.task, "project", None)
        if project is None:
            return False

        # If user has membership via ProjectMember
        from projects.models import ProjectMember

        membership = ProjectMember.objects.filter(project=project, user=user).first()
        if membership is None:
            return False
        return membership.role in required_roles


class AllowReadOnlyForNonPrivileged(RoleBasedProjectPermission):
    """Allow safe methods for any member, but writes require required_roles."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return IsProjectMember().has_object_permission(request, view, obj)
        return super().has_object_permission(request, view, obj)

