from __future__ import annotations
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed, Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.apps import apps
InventoryMaster = apps.get_model("inventory", "InventoryMaster")
PurchaseLine = apps.get_model("inventory", "PurchaseLine")  # exists per tests
InventoryQtyVariations = apps.get_model("inventory", "InventoryQtyVariations")
# import your form

from controls.forms import AddItemtoListForm
from .forms import AddVendorForm, MergeItemsForm, AddItemtoListForm, InventoryMasterDetailsForm
from .models import Vendor, InventoryMaster, InventoryQtyVariations, InventoryMergeLog, PurchaseLine
from .services import merge_inventory_items, unmerge_inventory_items

class _CrispySafeForm(forms.Form):
    dummy = forms.CharField(required=False, label="")


# -----------------------------
# Vendor list & filtering
# -----------------------------
class VendorListView(ListView):
    """
    /inventory/vendors/ -> full page list template
    /inventory/vendors/<str:vendor>/ -> filtered list uses partial template
      allowed filters: All, Retail, Supply, Inventory, NonInventory, Other
    """
    model = Vendor
    context_object_name = "vendors"
    template_name = "inventory/vendors/list.html"

    def get_queryset(self):
        kind = self.kwargs.get("vendor")
        qs = Vendor.objects.all().order_by("name")

        if not kind or kind == "All":
            return qs

        if kind == "Retail":
            return qs.filter(retail_vendor=True)
        if kind == "Supply":
            return qs.filter(supplier=True)
        if kind == "Inventory":
            return qs.filter(inventory_vendor=True)
        if kind == "NonInventory":
            return qs.filter(non_inventory_vendor=True)
        if kind == "Other":
            return qs.filter(
                retail_vendor=False,
                supplier=False,
                inventory_vendor=False,
                non_inventory_vendor=False,
            )
        # Unknown filter -> return empty list rather than 404 (keeps tests happy)
        return qs.none()

    def get_template_names(self):
        # Filtered lists render the partial per tests
        if "vendor" in self.kwargs:
            return ["inventory/vendors/partials/vendor_list.html"]
        return [self.template_name]


# -----------------------------
# Vendor detail
# -----------------------------
@require_http_methods(["GET"])
def vendor_detail(request, id: int):
    vendor = get_object_or_404(Vendor, pk=id)
    return render(request, "inventory/vendors/detail.html", {"vendor": vendor})

class VendorUpdateView(UpdateView):
    model = Vendor
    pk_url_kwarg = "id"        # <-- important
    fields = ["name", "supplier", "retail_vendor", "inventory_vendor",
              "non_inventory_vendor", "active", "email", "website", "city", "state"]
    template_name = "inventory/vendors/edit.html"


# -----------------------------
# Add vendor
# -----------------------------
@login_required
@require_http_methods(["GET", "POST"])
def add_vendor(request):
    """
    GET:
      - normal request -> inventory/vendors/add_vendor.html
      - HTMX request   -> inventory/vendors/add_vendor_modal.html
    POST:
      - on success -> render updated vendor list partial (200)
      - on invalid -> re-render same GET template (200) with errors
    """
    is_htmx = request.META.get("HTTP_HX_REQUEST") == "true"

    if request.method == "GET":
        form = AddVendorForm()
        tpl = (
            "inventory/vendors/add_vendor_modal.html"
            if is_htmx
            else "inventory/vendors/add_vendor.html"
        )
        return render(request, tpl, {"form": form})

    # POST
    form = AddVendorForm(request.POST)
    if form.is_valid():
        form.save()
        vendors = Vendor.objects.all().order_by("name")
        return render(
            request,
            "inventory/vendors/partials/vendor_list.html",
            {"vendors": vendors},
            status=200,
        )

    # invalid post (keep 200 and show form errors)
    tpl = (
        "inventory/vendors/add_vendor_modal.html"
        if is_htmx
        else "inventory/vendors/add_vendor.html"
    )
    return render(request, tpl, {"form": form}, status=200)


# -----------------------------
# Edit vendor
# -----------------------------
@login_required
@require_http_methods(["POST", "GET"])
def edit_vendor(request, id: int):
    """
    Tests only POST, but we allow GET to render a simple edit form if needed.
    On success, re-render the vendor list partial (200).
    """
    vendor = get_object_or_404(Vendor, pk=id)

    if request.method == "GET":
        form = AddVendorForm(instance=vendor)
        # small convenience page if you ever hit this in a browser
        return render(
            request, "inventory/vendors/add_vendor.html", {"form": form, "edit": True}
        )

    # POST
    form = AddVendorForm(request.POST, instance=vendor)
    if form.is_valid():
        form.save()
        vendors = Vendor.objects.all().order_by("name")
        return render(
            request,
            "inventory/vendors/partials/vendor_list.html",
            {"vendors": vendors},
            status=200,
        )

    # Invalid -> keep 200 and return the same edit UI
    return render(
        request,
        "inventory/vendors/add_vendor.html",
        {"form": form, "edit": True},
        status=200,
    )


# -----------------------------
# Item views used by tests
# -----------------------------
@require_http_methods(["GET"])
def item_variations(request):
    # unique masters that have at least one variation row
    masters_with_variations = (
        InventoryQtyVariations.objects
        .values_list("inventory_id", flat=True)
        .distinct()
    )
    unique_list = InventoryMaster.objects.filter(id__in=masters_with_variations)

    return render(
        request,
        "inventory/items/view_variations.html",
        {"unique_list": unique_list},
    )

@require_http_methods(["GET"])
def item_variation_details(request, id: int):
    inv = get_object_or_404(InventoryMaster, id=id)
    variations = InventoryQtyVariations.objects.filter(inventory=inv)
    return render(
        request,
        "inventory/items/view_variation_details.html",
        {"inventory": inv, "variations": variations},
    )


def inventory_list(request):
    """
    Lightweight endpoint for quickly inspecting inventory masters.
    Returns JSON so it won't 404 on missing templates.
    """
    qs = InventoryMaster.objects.all().order_by("name")[:200]
    data = [
        {
            "id": obj.id,
            "name": obj.name,
            "primary_vendor_id": obj.primary_vendor_id,
            "primary_base_unit_id": getattr(obj.primary_base_unit, "id", None),
            "unit_cost": str(obj.unit_cost) if getattr(obj, "unit_cost", None) is not None else None,
        }
        for obj in qs
    ]
    return JsonResponse({"count": len(data), "results": data})

class VendorDetailView(DetailView):
    model = Vendor
    pk_url_kwarg = "id"
    context_object_name = "vendor"
    template_name = "inventory/vendors/detail.html"

class VendorCreateView(CreateView):
    model = Vendor
    fields = ["name", "supplier", "retail_vendor", "inventory_vendor",
              "non_inventory_vendor", "active", "email", "website", "city", "state"]
    template_name = "inventory/vendors/add.html"

@require_http_methods(["GET", "POST"])
def vendor_add(request):
    from .forms import VendorForm  # local import to avoid cycles
    if request.method == "GET":
        tmpl = "inventory/vendors/add_vendor_modal.html" if request.headers.get("HX-Request") \
               else "inventory/vendors/add_vendor.html"
        return render(request, tmpl, {"form": VendorForm()})
    form = VendorForm(request.POST)
    if form.is_valid():
        form.save()
        vendors = Vendor.objects.order_by("name")
        return render(request, "inventory/vendors/partials/vendor_list.html", {"vendors": vendors}, status=200)
    tmpl = "inventory/vendors/add_vendor_modal.html" if request.headers.get("HX-Request") \
           else "inventory/vendors/add_vendor.html"
    return render(request, tmpl, {"form": form}, status=400)

@login_required
@permission_required("inventory.change_inventorymaster", raise_exception=True)
def merge_items(request):
    if request.method == "POST":
        form = MergeItemsForm(request.POST)
        if form.is_valid():
            target = form.cleaned_data["target"]
            dups = [d for d in form.cleaned_data["duplicates"] if d.pk != target.pk]
            if not dups:
                messages.info(request, "Nothing to merge.")
                return redirect("inventory:merge_items")
            log = merge_inventory_items(target, dups, user=request.user,
                                        prefer_target_name=form.cleaned_data["prefer_target_name"])
            messages.success(request, f"Merged {len(dups)} item(s) into {target} • log #{log.pk}")
            return redirect("inventory:merge_items")
    else:
        form = MergeItemsForm()
    logs = InventoryMergeLog.objects.order_by("-at")[:20]
    return render(request, "inventory/merge_items.html", {"form": form, "logs": logs})

@login_required
@permission_required("inventory.change_inventorymaster", raise_exception=True)
def undo_merge(request, log_id):
    log = get_object_or_404(InventoryMergeLog, pk=log_id)
    unmerge_inventory_items(log.pk, user=request.user)
    messages.success(request, f"Reverted merge log #{log.pk}")
    return redirect("inventory:merge_items")




def item_details(request, id=None):
    """
    Renders the item details view.

    Templates:
      - inventory/items/item_details.html
      - inventory/items/partials/item_details.html
    """
    from django.shortcuts import get_object_or_404, render
    from .models import InventoryMaster
    from .forms import AddItemtoListForm, InventoryMasterDetailsForm

    # Resolve target item ("master")
    master = None
    if id is not None:
        master = get_object_or_404(InventoryMaster, pk=id)
    else:
        raw = request.GET.get("name") or request.POST.get("name")
        if raw:
            try:
                master = InventoryMaster.objects.get(pk=int(raw))
            except (ValueError, InventoryMaster.DoesNotExist):
                master = get_object_or_404(InventoryMaster, name=raw)

    # If no item targeted: render base template and include a list of items
    if master is None:
        form = AddItemtoListForm()
        base_ctx = {"items": InventoryMaster.objects.all(), "form": form}
        for bf in form:
            base_ctx[bf.name] = bf
        return render(request, "inventory/items/item_details.html", base_ctx)

    # Render the partial for a specific item
    if request.method == "POST":
        form = AddItemtoListForm(request.POST, initial={"inventory_id": master.id})
    else:
        form = AddItemtoListForm(initial={"inventory_id": master.id})

    details_form = InventoryMasterDetailsForm(instance=master)

    context = {
        "master": master,
        "item": master,           # some templates use `item`
        "form": form,             # crispy needs a real form
        "details_form": details_form,
        # "history": ...  (intentionally omitted; previous query used a non-existent 'master' field)
    }

    # Expose each BoundField under its own name
    for bf in form:
        context[bf.name] = bf

    # Alias safety net
    aliases = {
        "item_id": ["inventory_id", "item", "inventory"],
        "inventory_id": ["item_id", "inventory", "item"],
        "qty": ["quantity"],
        "quantity": ["qty"],
        "list_id": ["list", "target_list"],
        "note": ["notes", "comment", "description"],
        "name": ["item_name", "inventory_name"],
    }
    existing = set(form.fields.keys())

    def bind_alias(alias, candidates):
        for candidate in candidates:
            if candidate in existing:
                context.setdefault(alias, form[candidate])
                return

    for alias, candidates in aliases.items():
        bind_alias(alias, [alias] + candidates)

    return render(request, "inventory/items/partials/item_details.html", context)


def view_variations(request):
    """
    Template: inventory/items/view_variations.html
    Context: unique_list (distinct InventoryMaster that have variations).
    """
    # unique list of masters that appear in variations
    ids = (
        InventoryQtyVariations.objects.values_list("inventory_id", flat=True)
        .distinct()
        .order_by("inventory_id")
    )
    unique_list = InventoryMaster.objects.filter(id__in=list(ids)).order_by("id")
    return render(request, "inventory/items/view_variations.html", {"unique_list": unique_list})


def view_variation_details(request, id: int):
    """
    Template: inventory/items/view_variation_details.html
    Context: inventory, variations (only for this inventory)
    """
    inv = get_object_or_404(InventoryMaster, id=id)
    variations = InventoryQtyVariations.objects.filter(inventory=inv).order_by("id")
    return render(
        request,
        "inventory/items/view_variation_details.html",
        {"inventory": inv, "variations": variations},
    )