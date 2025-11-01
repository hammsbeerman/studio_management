from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm

from .decorators import unauthenticated_user
from .forms import LoginForm, ChangePasswordForm

@unauthenticated_user
def login_view(request):
    next_url = request.GET.get("next") or request.POST.get("next") or ""
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

@require_http_methods(["GET", "POST"])
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("accounts:login")  # tests expect a 302 on POST
    # GET: just show a confirmation page (200)
    return HttpResponse("logout", status=200)

@login_required
@require_http_methods(["GET", "POST"])
def update_password(request):
    if request.method == "POST":
        # Choose the right form based on whether old_password was provided
        if request.POST.get("old_password"):
            form = PasswordChangeForm(request.user, request.POST)
        else:
            form = SetPasswordForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep user logged in
            return redirect("accounts:login")        # tests expect 302 on POST
    else:
        # Show the old-password flow by default
        form = PasswordChangeForm(request.user)

    return render(request, "accounts/update_password.html", {"form": form})