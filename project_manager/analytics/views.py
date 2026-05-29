from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from projects.models import Project
from tasks.models import Task

from .exports import build_project_status_pdf
from .models import ActivityLog



@login_required
def dashboard(request):
    total_projects = Project.objects.count()
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status=Task.Status.DONE).count()
    pending_tasks = total_tasks - completed_tasks

    # Task completion rate per project (Chart.js bar)
    projects = Project.objects.order_by('-created_at')
    completion_labels = []
    completion_rates = []

    for p in projects:
        p_total = Task.objects.filter(project=p).count()
        if p_total == 0:
            rate = 0
        else:
            rate = round(
                (Task.objects.filter(project=p, status=Task.Status.DONE).count() / p_total) * 100,
                2,
            )

        completion_labels.append(p.title)
        completion_rates.append(rate)

    # Team productivity: completed tasks per assignee
    productivity_qs = (
        Task.objects.filter(assigned_to__isnull=False)
        .values('assigned_to__username')
        .annotate(
            completed=Count(
                'id',
                filter=models.Q(status=Task.Status.DONE),
            )
        )
        .order_by('-completed')
    )

    team_labels = [row['assigned_to__username'] for row in productivity_qs[:10]]
    team_completed = [row['completed'] for row in productivity_qs[:10]]

    # Task priority distribution (Chart.js pie)
    priority_rows = (
        Task.objects.values('priority')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')
    )

    priority_labels = [r['priority'] for r in priority_rows]
    priority_counts = [r['cnt'] for r in priority_rows]

    activity = ActivityLog.objects.select_related('actor', 'project', 'task').order_by('-created_at')[:30]

    return render(
        request,
        'analytics/dashboard.html',
        {
            'total_projects': total_projects,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'completion_labels': completion_labels,
            'completion_rates': completion_rates,
            'team_labels': team_labels,
            'team_completed': team_completed,
            'priority_labels': priority_labels,
            'priority_counts': priority_counts,
            'activity': activity,
        },
    )


@login_required
def project_status_report(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)


    tasks = Task.objects.filter(project=project).select_related('assigned_to', 'created_by')

    member_rows = (
        tasks.values('assigned_to__id', 'assigned_to__username')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    contributions = []
    for r in member_rows:
        assigned_to_id = r['assigned_to__id']
        done = tasks.filter(assigned_to_id=assigned_to_id, status=Task.Status.DONE).count()
        contributions.append(
            {
                'user_id': assigned_to_id,
                'username': r['assigned_to__username'] or 'Unassigned',
                'total': r['total'],
                'done': done,
            }
        )

    activity = ActivityLog.objects.filter(project=project).order_by('-created_at')[:50]

    return render(
        request,
        'analytics/project_status_report.html',
        {
            'project': project,
            'tasks': tasks,
            'contributions': contributions,
            'activity': activity,
        },
    )


@login_required
def project_status_report_pdf(request, project_id: int):
    project = get_object_or_404(Project, id=project_id)
    tasks = Task.objects.filter(project=project).select_related('assigned_to', 'created_by')

    member_rows = (
        tasks.values('assigned_to__id', 'assigned_to__username')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    lines = [
        f"Project: {project.title}",
        f"Status: {project.status}",
        "",
        "Task Summary:",
    ]

    for task in tasks.order_by('status', 'deadline'):
        assignee = task.assigned_to.username if task.assigned_to else 'Unassigned'
        lines.append(f"- {task.title} [{task.get_status_display()}] ({assignee})")

    lines.append("")
    lines.append("Team Contributions:")
    for r in member_rows:
        lines.append(
            f"- {r['assigned_to__username'] or 'Unassigned'}: {r['total']} task(s)"
        )

    report_bytes = build_project_status_pdf(project_title=project.title, lines=lines)
    response = HttpResponse(report_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="project_{project.id}_status_report.pdf"'
    return response

