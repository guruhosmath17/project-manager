from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Project, ProjectMember


@login_required
def project_list(request):
    # Projects where user is a member
    projects = Project.objects.filter(members=request.user).order_by('-created_at')
    return render(request, 'projects/project_list.html', {'projects': projects})


@login_required
def project_create(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        status = request.POST.get('status', Project.Status.PLANNED)
        deadline = request.POST.get('deadline') or None

        if not title:
            messages.error(request, 'Title is required.')
            return redirect(reverse('projects:project_create'))

        project = Project.objects.create(
            title=title,
            description=description,
            status=status,
            deadline=deadline,
            created_by=request.user,
        )
        ProjectMember.objects.create(project=project, user=request.user, role=ProjectMember.Role.ADMIN)

        messages.success(request, 'Project created successfully.')
        return redirect(reverse('projects:project_detail', args=[project.id]))

    return render(request, 'projects/project_form.html', {'action': 'Create', 'project': None})


@login_required
def project_detail(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)

    # Authorization: only members can view
    if not project.members.filter(id=request.user.id).exists():
        messages.error(request, 'You are not a member of this project.')
        return redirect(reverse('projects:project_list'))

    # Progress bar (updated in Step 4): compute from tasks statuses.
    progress_percent = 0
    try:
        from tasks.models import Task  # imported here to avoid circular issues

        total = Task.objects.filter(project=project).count()
        if total:
            done = Task.objects.filter(project=project, status=Task.Status.DONE).count()
            progress_percent = int((done / total) * 100)
    except Exception:
        # If tasks app isn't migrated/available yet, keep default 0%
        progress_percent = 0


    members = project.memberships.select_related('user').all()
    return render(
        request,
        'projects/project_detail.html',
        {
            'project': project,
            'members': members,
            'progress_percent': progress_percent,
        },
    )


@login_required
def project_edit(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)

    if not project.members.filter(id=request.user.id).exists():
        messages.error(request, 'You are not a member of this project.')
        return redirect(reverse('projects:project_list'))

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        status = request.POST.get('status', project.status)
        deadline = request.POST.get('deadline') or None

        if not title:
            messages.error(request, 'Title is required.')
            return redirect(reverse('projects:project_edit', args=[project.id]))

        project.title = title
        project.description = description
        project.status = status
        project.deadline = deadline
        project.save()

        messages.success(request, 'Project updated successfully.')
        return redirect(reverse('projects:project_detail', args=[project.id]))

    return render(request, 'projects/project_form.html', {'action': 'Edit', 'project': project})


@login_required
def project_delete(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)

    if not project.members.filter(id=request.user.id).exists():
        messages.error(request, 'You are not a member of this project.')
        return redirect(reverse('projects:project_list'))

    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted.')
        return redirect(reverse('projects:project_list'))

    return render(request, 'projects/project_confirm_delete.html', {'project': project})


@login_required
def project_member_add(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)

    if not project.members.filter(id=request.user.id).exists():
        messages.error(request, 'You are not a member of this project.')
        return redirect(reverse('projects:project_list'))

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        member_role = request.POST.get('role', ProjectMember.Role.VIEWER)

        user_model = settings.AUTH_USER_MODEL
        User = __import__(user_model, fromlist=['']).__class__  # not used; keep simple

        # Import the User model properly
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()
        user = get_object_or_404(UserModel, id=user_id)

        ProjectMember.objects.get_or_create(project=project, user=user, defaults={'role': member_role})

        messages.success(request, 'Member added.')
        return redirect(reverse('projects:project_detail', args=[project.id]))

    from django.contrib.auth import get_user_model

    UserModel = get_user_model()
    candidates = UserModel.objects.exclude(id__in=project.members.values_list('id', flat=True))
    return render(
        request,
        'projects/project_member_add.html',
        {'project': project, 'candidates': candidates, 'ProjectMember': ProjectMember},
    )


@login_required
def project_member_remove(request, project_id: int, user_id: int):
    project = get_object_or_404(Project, id=project_id)

    if not project.members.filter(id=request.user.id).exists():
        messages.error(request, 'You are not a member of this project.')
        return redirect(reverse('projects:project_list'))

    if request.method == 'POST':
        membership = get_object_or_404(ProjectMember, project=project, user_id=user_id)
        if membership.user_id == request.user.id:
            messages.error(request, 'You cannot remove yourself from the project.')
            return redirect(reverse('projects:project_detail', args=[project.id]))
        membership.delete()
        messages.success(request, 'Member removed.')
        return redirect(reverse('projects:project_detail', args=[project.id]))

    return redirect(reverse('projects:project_detail', args=[project.id]))

