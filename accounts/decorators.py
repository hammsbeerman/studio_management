from django.shortcuts import redirect
from functools import wraps

def unauthenticated_user(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard:dashboard")  # your existing target
        return view_func(request, *args, **kwargs)
    return wrapper

def allowed_users(allowed_roles=None):
    """
    Pass a list of role names. We check both Django Groups and your Profile.group (UserGroup).
    Example: @allowed_users(["Managers", "CSR"])
    """
    allowed_roles = set(allowed_roles or [])

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("accounts:login")

            # Check Django groups
            user_groups = set(request.user.groups.values_list("name", flat=True))

            # Check custom UserGroup via Profile
            try:
                profile_groups = set(request.user.profile.group.values_list("name", flat=True))
            except Exception:
                profile_groups = set()

            if allowed_roles and not (user_groups | profile_groups) & allowed_roles:
                # No permission — you can customize this (403, message, redirect)
                return redirect("dashboard:dashboard")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator