from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, resolve_url
from django.urls import reverse, NoReverseMatch
from .decorators import unauthenticated_user, allowed_users
from .forms import ChangePasswordForm
from .models import Profile


def _clean_next_url(value):
    if value is None:
        return None
    value = str(value).strip()
    if value.lower() in {"", "none", "null"}:
        return None
    return value


@unauthenticated_user
def login_view(request):
    next_url = _clean_next_url(request.GET.get("next") or request.POST.get("next"))

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            Profile.objects.get_or_create(
                user=user,
                defaults={"primary_company": "LK Design"},
            )

            messages.success(request, "You have been logged in")

            if next_url:
                return redirect(next_url)
            return redirect("/")

        messages.error(request, "There was an error")
    else:
        form = AuthenticationForm(request)

    context = {
        "form": form,
        "next": next_url,
    }
    return render(request, "accounts/login.html", context)


def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You’ve been logged out.")
        try:
            return redirect("accounts:login")
        except NoReverseMatch:
            return redirect("/")
    return render(request, "accounts/logout.html", {})


@login_required
def register_view(request):
    form = UserCreationForm(request.POST or None)
    if form.is_valid():
        user_obj = form.save()
        Profile.objects.get_or_create(
            user=user_obj,
            defaults={"primary_company": "LK Design"},
        )
        return redirect("accounts:login")
    context = {"form": form}
    return render(request, "accounts/register.html", context)


@login_required
def update_password(request):
    if request.method == "POST":
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been changed.")
            try:
                return redirect("dashboard")
            except NoReverseMatch:
                return redirect("/")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ChangePasswordForm(request.user)

    return render(request, "accounts/update_password.html", {"form": form})