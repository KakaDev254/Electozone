from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm

User = get_user_model()

@login_required
def profile_view(request):
    """View for displaying and editing the user profile."""
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)  # Prefill the form with current user data
        if form.is_valid():
            form.save()  # Save the updated user profile
            return redirect('profile')  # Redirect to the same page or to a success page
    else:
        form = ProfileForm(instance=request.user)  # Prefill the form with current user data

    return render(request, 'accounts/profile.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password.")
            return redirect('login')

    return render(request, 'accounts/login.html')


def register_view(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        second_name = request.POST['second_name']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
            return redirect('register')

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            second_name=second_name  # Assuming your custom user model includes this field
        )
        messages.success(request, "Account created successfully. You can now log in.")
        return redirect('login')

    return render(request, 'accounts/register.html')


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('login')
