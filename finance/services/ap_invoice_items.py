import logging
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import get_object_or_404

from finance.forms import AddInvoiceItemForm
from finance.models import AccountsPayable, InvoiceItem
from inventory.models import InventoryMaster, InventoryQtyVariations, Measurement
from inventory.services.uom import qty_to_base
from inventory.services.ledger import record_inventory_movement

logger = logging.getLogger(__name__)


def _safe_decimal(val, default="1"):
    try:
        return Decimal(str(val or default))
    except Exception:
        return Decimal(default)


def resolve_invoice_unit(base_item, unit=None, variation_id=None, item_qty_raw=None):
    """
    Returns (invoice_unit_obj, variation_qty, error_message)
    """
    variation_qty = Decimal("1")
    variation_obj = None

    if unit and base_item:
        measurement = Measurement.objects.filter(pk=unit).first()
        if not measurement:
            return None, variation_qty, "Invalid unit selected."

        variation_qty = _safe_decimal(item_qty_raw, default="1")

        from inventory.views_uom_audit import get_or_create_uom_row
        variation_obj = get_or_create_uom_row(
            item=base_item,
            measurement=measurement,
            qty=variation_qty,
        )
        return variation_obj, variation_qty, None

    if variation_id:
        variation_obj = InventoryQtyVariations.objects.filter(pk=variation_id).first()
        if not variation_obj or variation_obj.inventory_id != getattr(base_item, "id", None):
            return None, variation_qty, "Invalid unit selection."
        if not variation_obj.active:
            return None, variation_qty, "That unit is inactive for this item."

        variation_qty = Decimal(variation_obj.variation_qty or 1)
        return variation_obj, variation_qty, None

    return None, variation_qty, None


def save_ap_invoice_item_from_post(*, request_post, invoice, instance=None):
    """
    Shared AP invoice item save path for create/edit.

    Returns dict:
    {
        "ok": bool,
        "form": form,
        "invoice_item": obj_or_none,
        "error": str_or_none,
    }
    """
    ppm_flag = request_post.get("ppm")
    ipn = request_post.get("internal_part_number")
    variation_id = request_post.get("variation")
    unit = request_post.get("unit")
    item_qty_raw = request_post.get("variation_qty")

    old_qty = None
    old_item = None

    if instance is not None:
        if getattr(instance, "ledger_locked", False):
            form = AddInvoiceItemForm(request_post, instance=instance)
            return {
                "ok": False,
                "form": form,
                "invoice_item": None,
                "error": "This line has already affected inventory. To change qty/unit/item/cost, use an adjustment flow.",
            }

        old_qty = instance.qty or Decimal("0")
        old_item = instance.internal_part_number
        form = AddInvoiceItemForm(request_post, instance=instance)
    else:
        form = AddInvoiceItemForm(request_post)

    try:
        base_item = InventoryMaster.objects.get(pk=ipn)
    except (InventoryMaster.DoesNotExist, ValueError, TypeError):
        base_item = None

    invoice_unit_obj, _variation_qty, error = resolve_invoice_unit(
        base_item=base_item,
        unit=unit,
        variation_id=variation_id,
        item_qty_raw=item_qty_raw,
    )
    if error:
        return {
            "ok": False,
            "form": form,
            "invoice_item": None,
            "error": error,
        }

    if form.is_valid():
        invoice_qty = form.instance.invoice_qty or Decimal("0")

        if invoice_unit_obj and not getattr(invoice_unit_obj, "active", True):
            return {
                "ok": False,
                "form": form,
                "invoice_item": None,
                "error": "That unit is inactive for this item.",
            }

        mult = Decimal(getattr(invoice_unit_obj, "variation_qty", None) or "1")
        qty = qty_to_base(invoice_qty, invoice_unit_obj)

        raw_cost = form.instance.invoice_unit_cost or Decimal("0.00")
        if raw_cost and ppm_flag == "1":
            unit_cost = raw_cost / Decimal("1000")
        else:
            unit_cost = raw_cost / (mult or Decimal("1"))
            ppm_flag = "0"

        form.instance.qty = qty
        form.instance.unit_cost = unit_cost
        form.instance.invoice = invoice
        if not form.instance.vendor_id and invoice.vendor_id:
            form.instance.vendor_id = invoice.vendor_id
        form.instance.invoice_unit = invoice_unit_obj
        form.instance.ppm = bool(ppm_flag == "1")
        form.instance.line_total = qty * unit_cost

        invoice_item = form.save()
        invoice_item_id = invoice_item.pk

        total = (
            InvoiceItem.objects.filter(invoice=invoice)
            .aggregate(sum_total=Sum("line_total"))["sum_total"]
            or Decimal("0.00")
        )
        invoice.calculated_total = total
        invoice.save(update_fields=["calculated_total"])

        wrote_ledger = False
        try:
            new_item = invoice_item.internal_part_number
            new_qty = Decimal(qty or 0)

            if instance is None:
                if new_item and new_qty:
                    record_inventory_movement(
                        inventory_item=new_item,
                        qty_delta=new_qty,
                        source_type="AP_RECEIPT",
                        source_id=str(invoice_item_id),
                        note=f"AP invoice {invoice.pk} item {invoice_item_id}",
                    )
                    wrote_ledger = True
            else:
                old_qty_decimal = Decimal(old_qty or 0)

                if old_item == new_item:
                    delta = new_qty - old_qty_decimal
                    if delta:
                        record_inventory_movement(
                            inventory_item=new_item,
                            qty_delta=delta,
                            source_type="AP_RECEIPT_ADJUST",
                            source_id=str(invoice_item_id),
                            note=f"Adjust AP invoice {invoice.pk} item {invoice_item_id}",
                        )
                        wrote_ledger = True
                else:
                    if old_item and old_qty_decimal:
                        record_inventory_movement(
                            inventory_item=old_item,
                            qty_delta=-old_qty_decimal,
                            source_type="AP_RECEIPT_ADJUST",
                            source_id=str(invoice_item_id),
                            note=f"Reassign AP invoice {invoice.pk} item {invoice_item_id} (old item)",
                        )
                        wrote_ledger = True
                    if new_item and new_qty:
                        record_inventory_movement(
                            inventory_item=new_item,
                            qty_delta=new_qty,
                            source_type="AP_RECEIPT_ADJUST",
                            source_id=str(invoice_item_id),
                            note=f"Reassign AP invoice {invoice.pk} item {invoice_item_id} (new item)",
                        )
                        wrote_ledger = True

            if wrote_ledger:
                InvoiceItem.objects.filter(pk=invoice_item_id).update(ledger_locked=True)

        except Exception:
            logger.exception(
                "Failed to record inventory movement for AP invoice item %s",
                invoice_item_id,
            )

        return {
            "ok": True,
            "form": form,
            "invoice_item": invoice_item,
            "error": None,
        }

    return {
        "ok": False,
        "form": form,
        "invoice_item": None,
        "error": "Please correct the errors below.",
    }