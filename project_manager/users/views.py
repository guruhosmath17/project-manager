from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import User, Profile


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', User.Role.VIEWER)

        if not username or not email or not password:
            messages.error(request, 'All fields are required.')
            return redirect(reverse('users:register'))

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect(reverse('users:register'))

        user = User.objects.create_user(username=username, email=email, password=password, role=role)
        Profile.objects.create(user=user)

        messages.success(request, 'Account created successfully. Please log in.')
        return redirect(reverse('users:login'))

    return render(request, 'users/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, 'Invalid username or password.')
            return redirect(reverse('users:login'))

        login(request, user)
        return redirect('/')

    return render(request, 'users/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect(reverse('users:login'))

