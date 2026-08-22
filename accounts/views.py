from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from .forms import RegisterForm, LoginForm, ProfileForm

def register_view(request):
    redirect_url = getattr(settings, 'LOGIN_REDIRECT_URL', 'home')

    if request.user.is_authenticated:
        return redirect(redirect_url)

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, f"Welcome to GlobeTrotter, {user.first_name or user.username}! Your account was created successfully.")
                return redirect(redirect_url)
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
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_page = request.GET.get('next', redirect_url)
            return redirect(next_page)
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('login')


@login_required
def profile_view(request):
    user = request.user
    today = timezone.now().date()

    from app.models import Trip
    user_trips = Trip.objects.filter(user=user)
    total_trips = user_trips.count()
    upcoming_trips = user_trips.filter(start_date__gt=today)
    ongoing_trips = user_trips.filter(start_date__lte=today, end_date__gte=today)
    completed_trips = user_trips.filter(end_date__lt=today)

    if request.method == 'POST':
        if request.POST.get('action') == 'delete_account':
            user.delete()
            messages.warning(request, "Your account has been deleted.")
            return redirect('register')

        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Please check the errors in the form.")
    else:
        form = ProfileForm(instance=user)

    context = {
        'form': form,
        'user': user,
        'total_trips': total_trips,
        'upcoming_trips': upcoming_trips,
        'ongoing_trips': ongoing_trips,
        'completed_trips': completed_trips,
    }
    return render(request, 'auth/profile.html', context)