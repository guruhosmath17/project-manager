from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Attachment, Comment, Task
from projects.models import Project, ProjectMember

from ai_helper import (
    generate_task_description,
    suggest_task_priority,
    suggest_team_member,
)


UserModel = get_user_model()


def _user_is_project_member(request, project: Project) -> bool:
    return project.members.filter(id=request.user.id).exists()



@login_required
def task_list(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)
    if not _user_is_project_member(request, project):
        messages.error(request, 'You are not a member of this project.')
        return redirect(reverse('projects:project_list'))

    tasks = project.tasks.select_related('assigned_to', 'created_by')

    # Kanban grouping
    kanban = {
        Task.Status.TODO: [],
        Task.Status.IN_PROGRESS: [],
        Task.Status.REVIEW: [],
        Task.Status.DONE: [],
    }
    for t in tasks:
        kanban[t.status].append(t)

    return render(request, 'tasks/task_kanban.html', {
        'project': project,
        'kanban': kanban,
        'members': project.memberships.select_related('user').all(),
    })


@login_required
def task_create(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)
    if not _user_is_project_member(request, project):
        messages.error(request, 'You are not a member of this project.')
        return redirect(reverse('projects:project_list'))

    members_qs = project.memberships.select_related('user').all()
    members_payload = [
        {
            'id': m.user.id,
            'username': m.user.username,
            'skills': getattr(m.user, 'designation', None),
            'workload': m.user.tasks_assigned.count() if hasattr(m.user, 'tasks_assigned') else 0,
        }
        for m in members_qs
    ]

    ai_priority_suggestion = None
    ai_description_suggestion = None
    ai_member_suggestion_id = None

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        assigned_to_id = request.POST.get('assigned_to') or None
        priority = request.POST.get('priority', Task.Priority.LOW)
        status = request.POST.get('status', Task.Status.TODO)
        deadline = request.POST.get('deadline') or None

        if not title:
            messages.error(request, 'Title is required.')
            return redirect(reverse('tasks:task_create', args=[project.id]))

        # Accept AI suggestions (optional)
        if request.POST.get('accept_ai_priority') == '1':
            try:
                ai_priority_suggestion = suggest_task_priority(
                    title=title,
                    deadline=str(deadline) if deadline else None,
                    workload_hint=str(members_qs.count()),
                )
                priority = ai_priority_suggestion
            except Exception:
                pass

        if request.POST.get('accept_ai_description') == '1':
            try:
                ai_description_suggestion = generate_task_description(title=title)
                description = ai_description_suggestion
            except Exception:
                pass

        if request.POST.get('accept_ai_member') == '1':
            try:
                ai_member_suggestion_id = suggest_team_member(
                    title=title,
                    members_payload=members_payload,
                )
                if ai_member_suggestion_id:
                    assigned_to_id = str(ai_member_suggestion_id)
            except Exception:
                pass

        assigned_to = None
        if assigned_to_id:
            assigned_to = get_object_or_404(UserModel, id=assigned_to_id)

        task = Task.objects.create(
            title=title,
            description=description,
            project=project,
            assigned_to=assigned_to,
            priority=priority,
            status=status,
            deadline=deadline,
            created_by=request.user,
        )

        messages.success(request, 'Task created.')
        return redirect(reverse('tasks:task_detail', args=[task.id]))

    # GET: show suggestions if title/deadline present in query string
    ai_title = request.GET.get('title', '')
    ai_deadline = request.GET.get('deadline', '')
    if ai_title:
        try:
            ai_priority_suggestion = suggest_task_priority(
                title=ai_title,
                deadline=ai_deadline or None,
                workload_hint=str(members_qs.count()),
            )
        except Exception:
            ai_priority_suggestion = None
        try:
            ai_description_suggestion = generate_task_description(title=ai_title)
        except Exception:
            ai_description_suggestion = None
        try:
            ai_member_suggestion_id = suggest_team_member(title=ai_title, members_payload=members_payload)
        except Exception:
            ai_member_suggestion_id = None

    # For edit view suggestions (if you call task_create with title query params)
    return render(request, 'tasks/task_form.html', {
        'project': project,
        'task': None,
        'action': 'Create',
        'statuses': Task.Status.choices,
        'priorities': Task.Priority.choices,
        'members': members_qs,
        'ai_priority_suggestion': ai_priority_suggestion,
        'ai_description_suggestion': ai_description_suggestion,
        'ai_member_suggestion_id': ai_member_suggestion_id,
    })





@login_required
def task_detail(request, task_id: int):
    task = get_object_or_404(Task, id=task_id)
    project = task.project
    if not _user_is_project_member(request, project):
        messages.error(request, 'You are not a member of this project.')
        return redirect(reverse('projects:project_list'))

    comments = task.comments.select_related('user').order_by('-created_at')
    attachments = task.attachments.select_related('uploaded_by').order_by('-created_at')

    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'project': project,
        'comments': comments,
        'attachments': attachments,
    })


@login_required
def task_edit(request, task_id: int):

    task = get_object_or_404(Task, id=task_id)

    project = task.project
    if not _user_is_project_member(request, project):
        messages.error(request, 'You are not a member of this project.')
        return redirect(reverse('projects:project_list'))

    members_qs = project.memberships.select_related('user').all()
    members_payload = [
        {
            'id': m.user.id,
            'username': m.user.username,
            'skills': getattr(m.user, 'designation', None),
            'workload': m.user.tasks_assigned.count() if hasattr(m.user, 'tasks_assigned') else 0,
        }
        for m in members_qs
    ]

    ai_priority_suggestion = None
    ai_description_suggestion = None
    ai_member_suggestion_id = None

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        assigned_to_id = request.POST.get('assigned_to') or None
        priority = request.POST.get('priority', task.priority)
        status = request.POST.get('status', task.status)
        deadline = request.POST.get('deadline') or None

        # Accept AI suggestions
        if request.POST.get('accept_ai_priority') == '1':
            try:
                ai_priority_suggestion = suggest_task_priority(
                    title=title,
                    deadline=str(deadline) if deadline else None,
                    workload_hint=str(members_qs.count()),
                )
                priority = ai_priority_suggestion
            except Exception:
                pass

        if request.POST.get('accept_ai_description') == '1':
            try:
                ai_description_suggestion = generate_task_description(title=title)
                description = ai_description_suggestion
            except Exception:
                pass

        if request.POST.get('accept_ai_member') == '1':
            try:
                ai_member_suggestion_id = suggest_team_member(title=title, members_payload=members_payload)
                if ai_member_suggestion_id:
                    assigned_to_id = str(ai_member_suggestion_id)
            except Exception:
                pass


        if not title:
            messages.error(request, 'Title is required.')
            return redirect(reverse('tasks:task_edit', args=[task.id]))

        task.title = title
        task.description = description
        if assigned_to_id:
            task.assigned_to = get_object_or_404(UserModel, id=assigned_to_id)
        else:
            task.assigned_to = None
        task.priority = priority
        task.status = status
        task.deadline = deadline
        task.save()

        messages.success(request, 'Task updated.')
        return redirect(reverse('tasks:task_detail', args=[task.id]))

    # Optional: show suggestions on edit page when user provides title/deadline via query params
    ai_title = request.GET.get('title', task.title)
    ai_deadline = request.GET.get('deadline', task.deadline)
    try:
        ai_priority_suggestion = suggest_task_priority(
            title=ai_title,
            deadline=str(ai_deadline) if ai_deadline else None,
            workload_hint=str(members_qs.count()),
        )
    except Exception:
        ai_priority_suggestion = None

    try:
        ai_description_suggestion = generate_task_description(title=ai_title)
    except Exception:
        ai_description_suggestion = None

    try:
        ai_member_suggestion_id = suggest_team_member(title=ai_title, members_payload=members_payload)
    except Exception:
        ai_member_suggestion_id = None

    return render(request, 'tasks/task_form.html', {
        'project': project,
        'task': task,
        'action': 'Edit',
        'statuses': Task.Status.choices,
        'priorities': Task.Priority.choices,
        'members': members_qs,
        'ai_priority_suggestion': ai_priority_suggestion,
        'ai_description_suggestion': ai_description_suggestion,
        'ai_member_suggestion_id': ai_member_suggestion_id,
    })



@login_required
def task_delete(request, task_id: int):
    task = get_object_or_404(Task, id=task_id)
    project = task.project
    if not _user_is_project_member(request, project):
        messages.error(request, 'You are not a member of this project.')
        return redirect(reverse('projects:project_list'))

    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted.')
        return redirect(reverse('tasks:task_list', args=[project.id]))

    return render(request, 'tasks/task_confirm_delete.html', {'task': task, 'project': project})


@login_required
def task_add_comment(request, task_id: int):
    task = get_object_or_404(Task, id=task_id)
    project = task.project
    if not _user_is_project_member(request, project):
        messages.error(request, 'You are not a member of this project.')
        return redirect(reverse('projects:project_list'))

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if not content:
            messages.error(request, 'Comment cannot be empty.')
            return redirect(reverse('tasks:task_detail', args=[task.id]))

        Comment.objects.create(task=task, user=request.user, content=content)
        messages.success(request, 'Comment added.')

    return redirect(reverse('tasks:task_detail', args=[task.id]))


@login_required
def task_upload_attachment(request, task_id: int):
    task = get_object_or_404(Task, id=task_id)
    project = task.project
    if not _user_is_project_member(request, project):
        messages.error(request, 'You are not a member of this project.')
        return redirect(reverse('projects:project_list'))

    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'Please choose a file to upload.')
            return redirect(reverse('tasks:task_detail', args=[task.id]))

        Attachment.objects.create(task=task, file=file, uploaded_by=request.user)
        messages.success(request, 'Attachment uploaded.')

    return redirect(reverse('tasks:task_detail', args=[task.id]))

