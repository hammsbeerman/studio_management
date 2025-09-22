from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings

from .decorators import unauthenticated_user
from .forms import LoginForm, ChangePasswordForm

@unauthenticated_user
def login_view(request):
    next_url = request.GET.get("next") or request.POST.get("next")
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            # Respect ?next= if safe; otherwise go to dashboard
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            messages.success(request, "You have been logged in.")
            return redirect("dashboard:dashboard")
        messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm(request)
    return render(request, "accounts/login.html", {"form": form, "next": next_url})

@login_required
def logout_view(request):
    # Accept POST for safety; optionally allow GET to show a confirmation page
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("accounts:login")
    return render(request, "accounts/logout.html", {})

@login_required
def update_password(request):
    if request.method == "POST":
        form = ChangePasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep user logged in
            messages.success(request, "Your password has been changed.")
            return redirect("dashboard:dashboard")
    else:
        form = ChangePasswordForm(user=request.user)
    return render(request, "accounts/update_password.html", {"form": form})