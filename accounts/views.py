from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.conf import settings
from django.db import IntegrityError
from .forms import RegisterForm, LoginForm

def register_view(request):
    # Fetch default redirect path from settings (defaults to 'home')
    redirect_url = getattr(settings, 'LOGIN_REDIRECT_URL', 'home')

    if request.user.is_authenticated:
        return redirect(redirect_url)

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)  # Authenticates user session
                messages.success(request, "Account created successfully!")
                return redirect(redirect_url)  # Redirects straight to protected home page
            except IntegrityError:
                messages.error(request, "A user with these details already exists.")
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    redirect_url = getattr(settings, 'LOGIN_REDIRECT_URL', 'home')

    if request.user.is_authenticated:
        return redirect(redirect_url)

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Logged in successfully")
            # Redirects to 'next' URL parameter if accessing a login_required page, else default home
            next_page = request.GET.get('next', redirect_url)
            return redirect(next_page)

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('login')