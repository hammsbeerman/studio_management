from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional, List

from django.conf import settings
from django.http import HttpRequest, HttpResponse, Http404
from django.shortcuts import render
from django.utils.html import escape

BASE_DIR = Path(getattr(settings, "BASE_DIR", "."))


def _run_git(args: List[str]) -> subprocess.CompletedProcess[str]:
    """
    Run a git command, returning CompletedProcess with stdout/stderr/returncode.
    """
    return subprocess.run(
        ["git", *args],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        timeout=10,
    )


def _validate_base(base: str, debug: List[str]) -> bool:
    """
    Return True if `base` resolves to a commit. Append debug logs.
    """
    args = ["rev-parse", "--verify", f"{base}^{{commit}}"]
    res = _run_git(args)
    debug.append(f"$ git {' '.join(args)}")
    if res.stdout:
        debug.append(res.stdout.strip())
    if res.stderr:
        debug.append(res.stderr.strip())
    return res.returncode == 0


def _detect_origin_default(repo_root: Path) -> Optional[str]:
    """
    Try to choose a sensible default compare base:
    - If origin/main exists, use 'origin/main'
    - Else if origin/master exists, use 'origin/master'
    - Else fallback to 'HEAD~1'
    """
    debug: List[str] = []
    for ref in ("origin/main", "origin/master"):
        if _validate_base(ref, debug):
            return ref
        # one fetch attempt to populate remotes
        fetch_res = _run_git(["fetch", "--all"])
        # ignore output here; just try validate again
        if _validate_base(ref, debug):
            return ref
    return "HEAD~1"


def changed_templates(request: HttpRequest) -> HttpResponse:
    """
    Show changed *.html files between `base` and HEAD, with full debug output.
    - ?base=… (default: settings.GIT_DEFAULT_BASE or auto-detected or HEAD~1)
    """
    default_base = getattr(settings, "GIT_DEFAULT_BASE", None) or _detect_origin_default(BASE_DIR)
    base = request.GET.get("base") or default_base

    debug: List[str] = []
    invalid_base: Optional[str] = None

    # 1) Validate base; if it's a remote ref, try a fetch once if needed.
    valid = _validate_base(base, debug)
    if not valid and base.startswith("origin/"):
        fetch_args = ["fetch", "--all"]
        fetch_res = _run_git(fetch_args)
        debug.append(f"$ git {' '.join(fetch_args)}")
        if fetch_res.stdout:
            debug.append(fetch_res.stdout.strip())
        if fetch_res.stderr:
            debug.append(fetch_res.stderr.strip())
        valid = _validate_base(base, debug)

    if not valid:
        invalid_base = base

    changed: List[str] = []
    diff_rc: Optional[int] = None

    # 2) Only run diff if base is valid
    if invalid_base is None:
        diff_args = ["diff", "--name-only", base, "HEAD"]
        diff_res = _run_git(diff_args)
        diff_rc = diff_res.returncode
        debug.append(f"$ git {' '.join(diff_args)}")
        if diff_res.stdout:
            debug.append(diff_res.stdout.rstrip())
        if diff_res.stderr:
            debug.append(diff_res.stderr.strip())

        if diff_rc == 0 and diff_res.stdout.strip():
            files = [ln.strip() for ln in diff_res.stdout.splitlines() if ln.strip()]
            # Prefer anything under templates/ and ending in .html
            for f in files:
                if f.endswith(".html") or f.startswith("templates/"):
                    changed.append(f)

            # De-dup & sort
            changed = sorted(set(changed))

    context = {
        "base": base,
        "invalid_base": invalid_base,
        "changed_templates": changed,
        "git_returncode": diff_rc,
        "git_command": f"git diff --name-only {base} HEAD" if invalid_base is None else "",
        "debug_output": "\n".join(debug) or "(no debug output)",
    }
    return render(request, "devtools/changed_templates.html", context)


# Your urls.py imports this name; keep it as an alias to the main view.
def changed_templates_dashboard(request: HttpRequest) -> HttpResponse:
    return changed_templates(request)


def preview_template(request: HttpRequest) -> HttpResponse:
    """
    Very simple, safe-ish viewer for files under the templates/ directory.
    Usage: /dev/preview?path=templates/app/page.html
    """
    rel = request.GET.get("path") or ""
    if not rel:
        raise Http404("Missing 'path' query parameter")

    # Only allow paths inside templates/
    rel_path = Path(rel)
    if rel_path.is_absolute() or ".." in rel_path.parts or not str(rel_path).startswith("templates/"):
        raise Http404("Invalid template path")

    full_path = BASE_DIR / rel_path
    if not full_path.exists() or not full_path.is_file():
        raise Http404("Template not found")

    try:
        content = full_path.read_text(encoding="utf-8")
    except Exception:
        content = "(unable to read file as utf-8)"

    return render(
        request,
        "devtools/preview_template.html",
        {"path": str(rel_path), "content": content},
    )