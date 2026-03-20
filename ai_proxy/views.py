from __future__ import annotations

import re

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt


PROXY_PREFIX = "/ai"


def _base_url() -> str:
    return getattr(settings, "AI_IMAGE_BASE_URL", "").rstrip("/")


def _public_base_url() -> str:
    return getattr(settings, "AI_IMAGE_PUBLIC_BASE_URL", _base_url()).rstrip("/")


def _timeout() -> int:
    return int(getattr(settings, "AI_IMAGE_PROXY_TIMEOUT", 60))


def _shared_secret() -> str:
    return getattr(settings, "AI_IMAGE_PROXY_SHARED_SECRET", "")


def _allowed_path(path: str) -> bool:
    path = path.lstrip("/")
    return (
        path == ""
        or path.startswith("ui/")
        or path.startswith("api/")
        or path.startswith("media/")
        or path.startswith("login/")
        or path == "login"
        or path.startswith("logout/")
        or path == "logout"
    )


def _target_url(path: str) -> str:
    base = _base_url()
    clean = path.lstrip("/")
    return f"{base}/{clean}" if clean else f"{base}/ui/"


def _rewrite_html(html: str) -> str:
    public_ai = _public_base_url()

    replacements = [
        ('href="/logout/"', 'href="/accounts/logout/"'),
        ("href='/logout/'", "href='/accounts/logout/'"),
        ('href="/login/"', 'href="/accounts/login/"'),
        ("href='/login/'", "href='/accounts/login/'"),
        ('href="/admin/"', f'href="{public_ai}/admin/"'),
        ("href='/admin/'", f"href='{public_ai}/admin/'"),
        ('action="/admin/"', f'action="{public_ai}/admin/"'),
        ("action='/admin/'", f"action='{public_ai}/admin/'"),
        ('href="/', f'href="{PROXY_PREFIX}/'),
        ("href='/", f"href='{PROXY_PREFIX}/"),
        ('src="/', f'src="{PROXY_PREFIX}/'),
        ("src='/", f"src='{PROXY_PREFIX}/"),
        ('action="/', f'action="{PROXY_PREFIX}/'),
        ("action='/", f"action='{PROXY_PREFIX}/"),
        ('hx-get="/', f'hx-get="{PROXY_PREFIX}/'),
        ("hx-get='/", f"hx-get='{PROXY_PREFIX}/"),
        ('hx-post="/', f'hx-post="{PROXY_PREFIX}/'),
        ("hx-post='/", f"hx-post='{PROXY_PREFIX}/"),
        ('hx-delete="/', f'hx-delete="{PROXY_PREFIX}/'),
        ("hx-delete='/", f"hx-delete='{PROXY_PREFIX}/"),
        ('hx-put="/', f'hx-put="{PROXY_PREFIX}/'),
        ("hx-put='/", f"hx-put='{PROXY_PREFIX}/"),
        ('fetch("/', f'fetch("{PROXY_PREFIX}/'),
        ("fetch('/", f"fetch('{PROXY_PREFIX}/"),
    ]

    for old, new in replacements:
        html = html.replace(old, new)

    # Catch JS snippets like location.href="/ui/..."
    html = re.sub(r'(["\'])/(ui|api|media)/', rf'\1{PROXY_PREFIX}/\2/', html)

    return html


def _copy_upstream_headers(upstream, response: HttpResponse) -> None:
    passthrough = [
        "Content-Disposition",
        "HX-Redirect",
        "HX-Refresh",
        "HX-Push-Url",
        "HX-Replace-Url",
        "HX-Trigger",
        "HX-Trigger-After-Settle",
        "HX-Trigger-After-Swap",
    ]
    for name in passthrough:
        value = upstream.headers.get(name)
        if value:
            response[name] = value


@csrf_exempt
@login_required
def proxy(request, subpath: str = ""):
    subpath = (subpath or "").lstrip("/")

    if not _allowed_path(subpath):
        raise Http404("Unsupported AI proxy path")

    url = _target_url(subpath)

    headers = {
        "Accept": request.headers.get("Accept", "*/*"),
        "User-Agent": request.headers.get("User-Agent", "StudioManagement-AIProxy"),
        "X-STUDIO-PROXY-SECRET": _shared_secret(),
    }

    forwarded_header_names = [
        "Content-Type",
        "HX-Request",
        "HX-Boosted",
        "HX-Current-URL",
        "HX-Target",
        "HX-Trigger",
        "HX-Trigger-Name",
        "X-Requested-With",
    ]
    for name in forwarded_header_names:
        value = request.headers.get(name)
        if value:
            headers[name] = value

    request_kwargs = {
        "method": request.method,
        "url": url,
        "headers": headers,
        "params": request.GET,
        "timeout": _timeout(),
        "allow_redirects": False,
    }

    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        request_kwargs["data"] = request.body

    upstream = requests.request(**request_kwargs)

    if upstream.status_code in {301, 302, 303, 307, 308}:
        location = upstream.headers.get("Location", "")

        if location.startswith("/admin/"):
            location = f"{_public_base_url()}{location}"
        elif location.startswith("/ui/"):
            location = f"{PROXY_PREFIX}{location}"
        elif location.startswith("/api/"):
            location = f"{PROXY_PREFIX}{location}"
        elif location.startswith("/media/"):
            location = f"{PROXY_PREFIX}{location}"
        elif location.startswith("/login"):
            # send AI login redirects to Studio login instead
            location = "/accounts/login/"
        elif location.startswith("/logout"):
            location = "/accounts/logout/"
        elif location.startswith("/"):
            location = f"{PROXY_PREFIX}{location}"

        return HttpResponseRedirect(location or f"{PROXY_PREFIX}/ui/")

    content_type = upstream.headers.get("Content-Type", "")

    if "text/html" in content_type:
        body = _rewrite_html(upstream.text)
        response = HttpResponse(body, status=upstream.status_code, content_type=content_type)
        _copy_upstream_headers(upstream, response)
        return response

    response = HttpResponse(
        upstream.content,
        status=upstream.status_code,
        content_type=content_type or "application/octet-stream",
    )
    _copy_upstream_headers(upstream, response)
    return response