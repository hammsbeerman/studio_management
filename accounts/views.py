from django import forms
from .forms import ChangePasswordForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .decorators import unauthenticated_user, allowed_users

@unauthenticated_user
def login_view(request):
    if request.method == "POST":
        # form = AuthenticationForm(request, data=request.POST)
        # if form.is_valid():
        #     user = form.get_user()
        #     login(request, user)
        #     return redirect('/')
        # #print(user)
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, ("You have been logged in"))
            return redirect('/')
        else:
            messages.success(request, ("There was an error"))
            return redirect('accounts:login')
    else:
        form = AuthenticationForm(request)
    context = {
        "form": form
    }
    return render(request, "accounts/login.html", context)

def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("accounts:login")
    return render(request, "accounts/logout.html", {})

@login_required
def register_view(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        user_obj = form.save()
        return redirect("accounts:login")
    context = {"form": form}
    return render(request, "accounts/register.html", context)

def update_password(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id=request.user.id)
        if request.method == 'POST':
            form = ChangePasswordForm(current_user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password has been changed")
                #relogin user after password change
                login(request, current_user)
                return redirect('/')
            else:
                for error in list(form.errors.values()):
                    messages.error(request, error)
                    return redirect('accounts:update_password')
        else:
            form = ChangePasswordForm(current_user)
            return render(request, 'accounts/update_password.html', {'form':form})
    else:
        messages.success(request, "You must be logged in")
        return redirect('home')
