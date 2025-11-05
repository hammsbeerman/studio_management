from django.conf import settings

def env_flags(request):
    return {
        "ENV_DEV": bool(getattr(settings, "TESTING", False) or getattr(settings, "DEBUG", False)),
    }