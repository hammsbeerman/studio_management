from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from controls.models import Measurement
from inventory.forms import UomAuditFilterForm, UomFixActionForm
from inventory.models import InventoryMaster, InventoryQtyVariations, InventoryLedger

from .forms import UomSetTripleForm

from inventory.services.uom_audit import (
    build_items_for_uom_audit,
    audit_uom_for_items,
    set_base_uom_by_measurement,
    set_default_sell_by_measurement,
    set_default_receive_by_measurement,
    ensure_base_uom,
    set_default_sell_uom,
    set_default_receive_uom,
)


@login_required
def uom_audit_admin(request):
    form = UomAuditFilterForm(request.GET or None)

    rows = []
    summary = None

    if form.is_valid():
        only_active = form.cleaned_data.get("only_active", True)
        vendor = form.cleaned_data.get("vendor")
        name_contains = (form.cleaned_data.get("name_contains") or "").strip()

        items_qs = build_items_for_uom_audit(
            only_active=only_active,
            vendor_id=vendor.id if vendor else None,
            name_contains=name_contains,
            retail_only=False,
            supplies_only=False,
            include_non_inventory=False,
        )

        result = audit_uom_for_items(items_qs)
        rows = result.rows
        summary = result.summary

    fix_form = UomFixActionForm()

    return render(
        request,
        "inventory/uom_audit_admin.html",
        {
            "form": form,
            "rows": rows,
            "summary": summary,
            "fix_form": fix_form,
        },
    )


@require_POST
@login_required
def uom_audit_apply(request):
    form = UomSetTripleForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Invalid request.")
        return redirect("inventory:uom_audit_admin")

    item = get_object_or_404(InventoryMaster, pk=form.cleaned_data["item_id"])

    base_m = form.cleaned_data.get("base_measurement")
    sell_m = form.cleaned_data.get("sell_measurement")
    recv_m = form.cleaned_data.get("receive_measurement")

    sell_qty = form.cleaned_data.get("sell_qty") or Decimal("1.0000")
    recv_qty = form.cleaned_data.get("receive_qty") or Decimal("1.0000")

    # guardrail: base changes + ledger history
    if base_m and InventoryLedger.objects.filter(inventory_item=item).exists():
        messages.error(request, "This item has ledger history; base UOM change is blocked here.")
        return redirect("inventory:uom_audit_admin")

    try:
        changed_any = False

        if base_m:
            set_base_uom_by_measurement(item=item, measurement=base_m)
            changed_any = True

        if sell_m:
            set_default_sell_by_measurement(item=item, measurement=sell_m, variation_qty=sell_qty)
            changed_any = True

        if recv_m:
            set_default_receive_by_measurement(item=item, measurement=recv_m, variation_qty=recv_qty)
            changed_any = True

        if changed_any:
            messages.success(request, f"{item.name}: updated.")
        else:
            messages.info(request, f"{item.name}: no changes selected.")
    except Exception as e:
        messages.error(request, f"Update failed: {e}")

    return redirect("inventory:uom_audit_admin")