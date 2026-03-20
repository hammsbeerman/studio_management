from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from customers.models import Customer
from workorders.models import Workorder

from .forms import ArchiveAssetNoteForm, ArchiveAssetOverlayForm
from .models import ArchiveAssetNote, ArchiveAssetOverlay
from .services.archive_api import ArchiveApiClient


def _save_overlay_from_payload(overlay: ArchiveAssetOverlay, payload: dict):
    overlay.archive_filename = payload.get("filename", overlay.archive_filename)
    overlay.archive_path = payload.get("path", overlay.archive_path)
    overlay.archive_hash = payload.get("sha256", overlay.archive_hash)
    overlay.save()
    return overlay


@login_required
def archive_search(request):
    q = (request.GET.get("q") or "").strip()
    results = None
    if q:
        try:
            results = ArchiveApiClient().search(q)
        except Exception as exc:
            results = {"query": q, "results": [], "error": str(exc)}
    return render(request, "archive_overlay/search.html", {"results": results, "query": q})


@login_required
def picker(request):
    q = (request.GET.get("q") or "").strip()
    customer_id = request.GET.get("customer_id") or ""
    workorder_id = request.GET.get("workorder_id") or ""
    results = None
    if q:
        try:
            results = ArchiveApiClient().search(q)
        except Exception as exc:
            results = {"query": q, "results": [], "error": str(exc)}
    return render(request, "archive_overlay/partials/picker.html", {
        "results": results,
        "query": q,
        "customer_id": customer_id,
        "workorder_id": workorder_id,
    })


@login_required
def link_asset(request):
    item_id = request.POST.get("archive_item_id")
    if not item_id:
        return HttpResponseBadRequest("archive_item_id is required")

    overlay, _ = ArchiveAssetOverlay.objects.get_or_create(archive_item_id=item_id, defaults={"created_by": request.user})
    customer_id = request.POST.get("customer_id")
    workorder_id = request.POST.get("workorder_id")
    if customer_id:
        overlay.customer_id = customer_id
    if workorder_id:
        overlay.workorder_id = workorder_id
    try:
        payload = ArchiveApiClient().item(item_id)
    except Exception:
        payload = {"id": item_id}
    _save_overlay_from_payload(overlay, payload)
    return redirect(request.META.get("HTTP_REFERER") or reverse("archive_overlay:search"))


@login_required
def edit_overlay(request, pk: int):
    overlay = get_object_or_404(ArchiveAssetOverlay, pk=pk)
    if request.method == "POST":
        form = ArchiveAssetOverlayForm(request.POST, instance=overlay)
        if form.is_valid():
            form.save()
            return redirect(request.META.get("HTTP_REFERER") or reverse("archive_overlay:search"))
    else:
        form = ArchiveAssetOverlayForm(instance=overlay)
    return render(request, "archive_overlay/edit_overlay.html", {"overlay": overlay, "form": form})


@login_required
def add_note(request, pk: int):
    overlay = get_object_or_404(ArchiveAssetOverlay, pk=pk)
    if request.method == "POST":
        form = ArchiveAssetNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.overlay = overlay
            note.created_by = request.user
            note.save()
            return redirect(request.META.get("HTTP_REFERER") or reverse("archive_overlay:search"))
    else:
        form = ArchiveAssetNoteForm()
    return render(request, "archive_overlay/add_note.html", {"overlay": overlay, "form": form})


@login_required
def customer_panel(request, customer_id: int):
    customer = get_object_or_404(Customer, pk=customer_id)
    overlays = ArchiveAssetOverlay.objects.filter(customer=customer).select_related("workorder").order_by("-updated")[:50]
    return render(request, "archive_overlay/partials/customer_panel.html", {"customer": customer, "overlays": overlays})


@login_required
def workorder_panel(request, workorder_id: int):
    workorder = get_object_or_404(Workorder, pk=workorder_id)
    overlays = ArchiveAssetOverlay.objects.filter(workorder=workorder).select_related("customer").order_by("-updated")[:50]
    return render(request, "archive_overlay/partials/workorder_panel.html", {"workorder": workorder, "overlays": overlays})
