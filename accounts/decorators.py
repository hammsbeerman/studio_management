from django.http import HttpResponse
from functools import wraps
from django.shortcuts import redirect

def unauthenticated_user(view_func):
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
        next_url = request.GET.get("next") or request.POST.get("next")

        if request.user.is_authenticated:
            if next_url:
                return redirect(next_url)
            return redirect("dashboard:dashboard")

        return view_func(request, *args, **kwargs)

    return wrapper_func

def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            print('Working', allowed_roles)
            return view_func(request, *args, **kwargs)
        return wrapper_func
    return decorator