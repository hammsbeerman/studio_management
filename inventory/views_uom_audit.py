from decimal import Decimal
from collections import Counter

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme

from controls.models import Measurement
from inventory.forms import UomAuditFilterForm
from inventory.models import InventoryLedger, InventoryMaster, InventoryQtyVariations
from inventory.services.uom_audit import (
    bulk_uom_used_ids,
    deactivate_uom_rows,
    audit_uoms, 
    ensure_base_uom, 
    set_default_receive_uom, 
    set_default_sell_uom, 
    normalize_item_uoms, 
    LEDGER_MODE_BLOCK, 
    LEDGER_MODE_SAFE,
    bulk_apply_to_queryset,
    get_or_create_uom_row
)

from inventory.services.item_usage import classify_item_usage


@login_required
def uom_audit_admin(request):
    form = UomAuditFilterForm(request.GET or None)
    result = None

    # UI toggles
    only_issues = request.GET.get("only_issues") in ("1", "true", "on", "yes")
    compact = request.GET.get("compact") in ("1", "true", "on", "yes")

    ledger_item_ids: set[int] = set()
    used_uom_ids: set[int] = set()

    # Provide full measurement list for "Add UOM row" + bulk measurement picker
    measurements = Measurement.objects.all().order_by("name")

    if form.is_valid() and form.cleaned_data:
        only_active = form.cleaned_data.get("only_active", True)
        vendor = form.cleaned_data.get("vendor")
        name_contains = (form.cleaned_data.get("name_contains") or "").strip()
        limit = int(form.cleaned_data.get("limit") or 200)

        result = audit_uoms(
            only_active=only_active,
            vendor_id=vendor.id if vendor else None,
            name_contains=name_contains,
            retail_only=False,
            supplies_only=False,
            include_non_inventory=False,
            limit=limit,
        )

        # Filter rows server-side
        if result and only_issues:
            result.rows = [r for r in result.rows if r.issues]

        if result and result.rows:
            item_ids = [r.item.id for r in result.rows]

            # bulk ledger check
            ledger_item_ids = set(
                InventoryLedger.objects.filter(inventory_item_id__in=item_ids)
                .values_list("inventory_item_id", flat=True)
                .distinct()
            )

            # bulk "used in history" check for all variation rows displayed
            all_uom_ids: list[int] = []
            for r in result.rows:
                # variations are prefetched by audit queryset
                all_uom_ids.extend([v.id for v in r.item.variations.all()])

            used_uom_ids = bulk_uom_used_ids(all_uom_ids)

    return render(
        request,
        "inventory/uom_audit_admin.html",
        {
            "form": form,
            "result": result,
            "rows": result.rows if result else [],
            "summary": result.summary if result else None,
            "ledger_item_ids": ledger_item_ids,
            "used_uom_ids": used_uom_ids,
            "measurements": measurements,  # ✅ needed by template
            "only_issues": only_issues,
            "compact": compact,
        },
    )

def has_ledger(item_id: int) -> bool:
    return InventoryLedger.objects.filter(inventory_item_id=item_id).exists()

def _redirect_back(request, fallback="inventory:uom_audit_admin"):
    """
    Redirect back to the current filtered audit page (vendor, only_issues, compact, etc.)
    using a safe `next` parameter.
    """
    nxt = (request.POST.get("next") or "").strip()
    if nxt and url_has_allowed_host_and_scheme(
        url=nxt,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(nxt)
    return redirect(fallback)


@require_POST
@login_required
def uom_audit_apply(request):
    item_id = request.POST.get("item_id")
    if not item_id:
        messages.error(request, "Missing item_id.")
        return _redirect_back(request)

    item = get_object_or_404(InventoryMaster, pk=item_id)
    has_ledger_flag = InventoryLedger.objects.filter(inventory_item=item).exists()

    # ------------------------------------------------------------
    # 1) Add UOM row (measurement + qty)  ✅ NEW
    # ------------------------------------------------------------
    do_add_uom = request.POST.get("do_add_uom") in ("1", "true", "on", "yes")
    add_measurement_id = (request.POST.get("add_measurement") or "").strip()
    add_qty_raw = (request.POST.get("add_qty") or "").strip()

    if do_add_uom:
        if not add_measurement_id:
            messages.error(request, "Pick a measurement to add.")
            return _redirect_back(request)
        try:
            m = get_object_or_404(Measurement, pk=add_measurement_id)
            qty = Decimal(add_qty_raw or "1.0000")
            uom = get_or_create_uom_row(item=item, measurement=m, qty=qty)
            messages.success(request, f"{item.name}: added {uom.variation.name} × {uom.variation_qty}.")
        except ValidationError as e:
            messages.error(request, f"{item.name}: add failed: {e}")
        except Exception as e:
            messages.error(request, f"{item.name}: add failed: {e}")
        return _redirect_back(request)

    # ------------------------------------------------------------
    # 2) Normalize toggles
    # ------------------------------------------------------------
    normalize_preview = request.POST.get("normalize_preview") in ("1", "true", "on", "yes")
    normalize = request.POST.get("normalize") in ("1", "true", "on", "yes")
    normalize_ledger_safe = request.POST.get("normalize_ledger_safe") in ("1", "true", "on", "yes")

    if normalize_preview or normalize or normalize_ledger_safe:
        try:
            res = normalize_item_uoms(
                item=item,
                dry_run=normalize_preview,
                ledger_mode=LEDGER_MODE_SAFE if normalize_ledger_safe else LEDGER_MODE_BLOCK,
            )
            stats = res.get("stats", {})
            actions = res.get("actions", [])

            if normalize_preview:
                preview = "; ".join(actions[:6]) + ("; …" if len(actions) > 6 else "")
                messages.info(request, f"{item.name}: normalize preview → {preview or 'no changes'}")
            else:
                messages.success(
                    request,
                    f"{item.name}: normalized. "
                    f"dupe_groups={stats.get('dupe_groups', 0)}, "
                    f"inactivated={stats.get('dupe_rows_inactivated', 0)}, "
                    f"flags_cleared={stats.get('flags_cleared', 0)}, "
                    f"qty_fixed={stats.get('qty_fixed', 0)}"
                )
        except ValidationError as e:
            messages.error(request, f"{item.name}: {e}")
        except Exception as e:
            messages.error(request, f"{item.name}: Normalize failed: {e}")

        return _redirect_back(request)

    # ------------------------------------------------------------
    # 3) Deactivate selected UOM rows (no delete)
    # ------------------------------------------------------------
    if request.POST.get("deactivate_uoms") in ("1", "true", "on", "yes"):
        try:
            uom_ids_int = [int(x) for x in request.POST.getlist("deactivate_uom_ids") if str(x).isdigit()]
            res = deactivate_uom_rows(item=item, uom_ids=uom_ids_int)

            # optional label lists (if your deactivate helper returns them)
            deact_labels = res.get("deactivated_labels", [])
            used_labels = res.get("skipped_used_labels", [])
            flagged_labels = res.get("skipped_flagged_labels", [])

            def short(labels: list[str]) -> str:
                if not labels:
                    return ""
                s = ", ".join(labels[:4])
                return s + (" …" if len(labels) > 4 else "")

            msg = (
                f"{item.name}: deactivated={res.get('deactivated', 0)}"
                + (f" ({short(deact_labels)})" if deact_labels else "")
                + f", skipped_used={res.get('skipped_used', 0)}"
                + (f" [{short(used_labels)}]" if used_labels else "")
                + f", skipped_flagged={res.get('skipped_flagged', 0)}"
                + (f" [{short(flagged_labels)}]" if flagged_labels else "")
                + f", skipped_missing={res.get('skipped_missing', 0)}"
            )
            messages.success(request, msg)
        except Exception as e:
            messages.error(request, f"{item.name}: deactivate failed: {e}")
        return _redirect_back(request)

    # ------------------------------------------------------------
    # 4) Normal apply fields (Base / Sell / Receive / Non-inv)
    # ------------------------------------------------------------
    base_measurement_id = (request.POST.get("base_measurement") or "").strip()
    sell_measurement_id = (request.POST.get("sell_measurement") or "").strip()
    receive_measurement_id = (request.POST.get("receive_measurement") or "").strip()

    sell_qty_raw = (request.POST.get("sell_qty") or "").strip()
    receive_qty_raw = (request.POST.get("receive_qty") or "").strip()

    mark_non_inventory = request.POST.get("mark_non_inventory") in ("1", "true", "on", "yes")

    # Guardrail: block removing from inventory if ledger exists
    if mark_non_inventory and has_ledger_flag:
        messages.error(request, "This item has ledger history; removing from inventory is blocked.")
        return _redirect_back(request)

    # qty defaults
    sell_qty = Decimal("1.0000")
    receive_qty = Decimal("1.0000")

    if sell_qty_raw:
        try:
            sell_qty = Decimal(sell_qty_raw)
        except Exception:
            messages.error(request, "Invalid sell_qty.")
            return _redirect_back(request)

    if receive_qty_raw:
        try:
            receive_qty = Decimal(receive_qty_raw)
        except Exception:
            messages.error(request, "Invalid receive_qty.")
            return _redirect_back(request)

    # Guardrail: base changes blocked if ledger exists
    if base_measurement_id and has_ledger_flag:
        messages.error(request, "This item has ledger history; base UOM change is blocked here.")
        return _redirect_back(request)

    try:
        with transaction.atomic():
            changed_any = False

            # Non-inventory toggle
            if mark_non_inventory and not item.non_inventory:
                item.non_inventory = True
                item.save(update_fields=["non_inventory"])
                changed_any = True

            # Base
            if base_measurement_id:
                base_m = get_object_or_404(Measurement, pk=base_measurement_id)
                ensure_base_uom(item=item, measurement=base_m, activate=True)
                changed_any = True

            # Default sell: use safe creator to avoid MultipleObjectsReturned
            if sell_measurement_id:
                sell_m = get_object_or_404(Measurement, pk=sell_measurement_id)
                sell_uom = get_or_create_uom_row(item=item, measurement=sell_m, qty=sell_qty)
                set_default_sell_uom(item=item, uom=sell_uom)
                changed_any = True

            # Default receive: use safe creator to avoid MultipleObjectsReturned
            if receive_measurement_id:
                recv_m = get_object_or_404(Measurement, pk=receive_measurement_id)
                recv_uom = get_or_create_uom_row(item=item, measurement=recv_m, qty=receive_qty)
                set_default_receive_uom(item=item, uom=recv_uom)
                changed_any = True

        if changed_any:
            messages.success(request, f"{item.name}: updated.")
        else:
            messages.info(request, f"{item.name}: no changes selected.")
    except Exception as e:
        messages.error(request, f"Update failed: {e}")

    return _redirect_back(request)


BULK_HARD_CAP = 50  # safety: never do more than this per run


def _int_list(values):
    out = []
    for x in values:
        try:
            out.append(int(x))
        except Exception:
            pass
    return out


def _short_list(items, n=6):
    items = [i for i in (items or []) if i]
    if not items:
        return ""
    s = ", ".join(str(x) for x in items[:n])
    return s + (" …" if len(items) > n else "")


@require_POST
@login_required
def uom_audit_bulk_apply(request):
    form = UomAuditFilterForm(request.POST or None)

    action = (request.POST.get("bulk_action") or "").strip()
    normalize_mode = (request.POST.get("normalize_mode") or "safe").strip()  # safe | ledger_safe
    dry_run = request.POST.get("bulk_preview") in ("1", "true", "on", "yes")

    # selection (optional)
    selected_ids = _int_list(request.POST.getlist("selected_item_ids"))
    selected_ids = selected_ids or None  # None => apply to whole filtered set

    # measurements for deactivate_by_measurement
    selected_measurement_ids = _int_list(request.POST.getlist("bulk_measurements")) or None

    if not action:
        messages.error(request, "Pick a bulk action.")
        return _redirect_back(request)

    if action == "deactivate_by_measurement" and not selected_measurement_ids:
        messages.error(request, "Pick at least one Measurement for bulk deactivation.")
        return _redirect_back(request)

    if not (form.is_valid() and form.cleaned_data):
        messages.error(request, "Invalid filters for bulk action.")
        return _redirect_back(request)

    only_active = form.cleaned_data.get("only_active", True)
    vendor = form.cleaned_data.get("vendor")
    name_contains = (form.cleaned_data.get("name_contains") or "").strip()
    limit = int(form.cleaned_data.get("limit") or 200)

    # Safety: cap the run size even if user set a bigger limit
    effective_limit = min(limit, BULK_HARD_CAP)

    # ---------------------------------------------------------------------
    # Bulk: Archive unused items (based on classify_item_usage)
    # ---------------------------------------------------------------------
    if action == "archive_unused":
        # NOTE: requires these imports somewhere in this module:
        # from collections import Counter
        # from inventory.models import InventoryMaster
        # from inventory.services.item_usage import classify_item_usage

        qs = InventoryMaster.objects.all()

        if only_active and hasattr(InventoryMaster, "active"):
            qs = qs.filter(active=True)

        # match your bulk behavior: do not include already-non-inventory items
        qs = qs.filter(non_inventory=False)

        if vendor:
            qs = qs.filter(primary_vendor_id=vendor.id)

        if name_contains:
            qs = qs.filter(name__icontains=name_contains)

        if selected_ids:
            qs = qs.filter(id__in=selected_ids)

        qs = qs.order_by("id")[:effective_limit]

        scanned = 0
        eligible = 0
        archived = 0
        blocked = 0
        errors = 0

        blocked_reasons = Counter()
        ex_archived = []
        ex_blocked = []
        ex_errors = []

        for item in qs:
            scanned += 1
            try:
                usage = classify_item_usage(item)
                if usage.safe_to_archive:
                    eligible += 1
                    if not dry_run:
                        # Archive policy: remove from inventory
                        item.non_inventory = True
                        item.save(update_fields=["non_inventory"])
                        archived += 1
                        if len(ex_archived) < 10:
                            ex_archived.append(f"{item.id}:{item.name}")
                else:
                    blocked += 1
                    for r in usage.reasons_blocked:
                        blocked_reasons[r] += 1
                    if len(ex_blocked) < 10:
                        ex_blocked.append(f"{item.id}:{item.name} ({', '.join(usage.reasons_blocked)})")
            except Exception as e:
                errors += 1
                if len(ex_errors) < 10:
                    ex_errors.append(f"{item.id}:{item.name} ({e})")

        scope = f"{len(selected_ids)} selected item(s)" if selected_ids else f"filtered set (limit {effective_limit})"
        label = "PREVIEW" if dry_run else "DONE"

        parts = [
            f"{label} bulk '{action}' on {scope}.",
            f"scanned={scanned}",
            f"eligible={eligible}",
            f"archived={archived}",
            f"blocked={blocked}",
            f"errors={errors}",
        ]
        messages.success(request, " · ".join(parts))

        if blocked_reasons:
            br = [f"{k}={v}" for k, v in sorted(blocked_reasons.items(), key=lambda kv: (-kv[1], kv[0]))]
            messages.info(request, "Blocked reasons: " + ", ".join(br[:12]))

        if ex_archived:
            messages.info(request, f"Archived examples: {_short_list(ex_archived)}")
        if ex_blocked:
            messages.info(request, f"Blocked examples: {_short_list(ex_blocked)}")
        if ex_errors:
            messages.info(request, f"Error examples: {_short_list(ex_errors)}")

        if limit > BULK_HARD_CAP:
            messages.info(request, f"Safety cap applied: requested limit={limit}, capped to {BULK_HARD_CAP}.")

        return _redirect_back(request)

    # ---------------------------------------------------------------------
    # All other actions go through bulk_apply_to_queryset
    # ---------------------------------------------------------------------
    stats = bulk_apply_to_queryset(
        only_active=only_active,
        vendor_id=vendor.id if vendor else None,
        name_contains=name_contains,
        include_non_inventory=False,
        limit=effective_limit,
        selected_item_ids=selected_ids,
        action=action,
        normalize_mode=("ledger_safe" if normalize_mode == "ledger_safe" else "safe"),
        dry_run=dry_run,
        selected_measurement_ids=selected_measurement_ids,
    )

    action_name = {
        "normalize": "Normalize",
        "deactivate_unused": "Deactivate unused variations",
        "deactivate_by_measurement": "Deactivate by measurement",
        "deactivate_duplicates": "Deactivate duplicate measurement rows",
        "mark_non_inventory": "Mark non-inventory",
        "archive_unused": "Archive unused items",
    }.get(action, action)

    scope = f"{len(selected_ids)} selected item(s)" if selected_ids else f"filtered set (limit {effective_limit})"
    label = "PREVIEW" if dry_run else "DONE"

    # Optional fields (safe if missing)
    examples = getattr(stats, "examples", {}) or {}
    ex_deactivated = _short_list(examples.get("deactivated_rows"))
    ex_skipped_used = _short_list(examples.get("skipped_used_rows"))
    ex_errors = _short_list(examples.get("errors"))

    parts = [
        f"{label} bulk '{action_name}' on {scope}.",
        f"scanned={getattr(stats, 'scanned', 0)}",
    ]

    if getattr(stats, "normalized", 0) or getattr(stats, "normalized_skipped_ledger", 0):
        parts.append(
            f"normalized={getattr(stats, 'normalized', 0)} "
            f"(skipped_ledger={getattr(stats, 'normalized_skipped_ledger', 0)})"
        )

    if getattr(stats, "deactivated_rows", 0) or getattr(stats, "deactivated_skipped_used", 0) or getattr(stats, "deactivated_skipped_flagged", 0):
        parts.append(
            f"deactivated_rows={getattr(stats, 'deactivated_rows', 0)} "
            f"(skipped_used={getattr(stats, 'deactivated_skipped_used', 0)}, "
            f"skipped_flagged={getattr(stats, 'deactivated_skipped_flagged', 0)})"
        )

    if getattr(stats, "marked_non_inventory", 0) or getattr(stats, "marked_non_inventory_skipped_ledger", 0):
        parts.append(
            f"marked_non_inventory={getattr(stats, 'marked_non_inventory', 0)} "
            f"(skipped_ledger={getattr(stats, 'marked_non_inventory_skipped_ledger', 0)})"
        )

    parts.append(f"errors={getattr(stats, 'errors', 0)}")

    messages.success(request, " · ".join(parts))

    if ex_deactivated:
        messages.info(request, f"Deactivated examples: {ex_deactivated}")
    if ex_skipped_used:
        messages.info(request, f"Skipped (used) examples: {ex_skipped_used}")
    if ex_errors:
        messages.info(request, f"Error examples: {ex_errors}")

    if limit > BULK_HARD_CAP:
        messages.info(request, f"Safety cap applied: requested limit={limit}, capped to {BULK_HARD_CAP}.")

    return _redirect_back(request)