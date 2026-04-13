#import random
import re
from django.http import HttpResponse
from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db.models import Q, Prefetch
from django.template.loader import render_to_string
from workorders.models import (
    GiftCertificateRedemption,
    Workorder,
    WorkorderCreditMemo,
    WorkorderItem,
    WorkorderPayment,
)
from customers.models import Customer, Contact
from inventory.models import Inventory, InventoryMaster
from accounts.decorators import allowed_users
from controls.models import JobStatus
from archive_overlay.services.archive_api import ArchiveApiClient
from finance.helpers_ar import (
    live_open_balance,
    normalize_open_balance,
    workorders_base_ar_qs,
)


#from articles.models import Article

@login_required
def home_view(request, id=None):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    else:
        return redirect('accounts/login')

def parse_search_amount(value):
    if value is None:
        return None

    cleaned = str(value).strip()
    if not cleaned:
        return None

    cleaned = cleaned.replace("$", "").replace(",", "").strip()

    if not re.fullmatch(r"-?\d+(\.\d{1,2})?", cleaned):
        return None

    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def text_amount_to_decimal(value):
    if value in (None, ""):
        return None

    cleaned = str(value).strip().replace("$", "").replace(",", "")
    try:
        return Decimal(cleaned).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


@login_required
def search(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return render(request, "search.html", {"message": "Please enter a search term"})

    search_amount = parse_search_amount(q)

    workorders = (
        Workorder.objects.filter(
            Q(hr_customer__icontains=q)
            | Q(workorder__icontains=q)
            | Q(description__icontains=q)
            | Q(lk_workorder__icontains=q)
            | Q(printleader_workorder__icontains=q)
            | Q(kos_workorder__icontains=q)
        )
        .select_related("customer")
        .distinct()
    )

    live_open_candidates = (
        workorders_base_ar_qs()
        .filter(pk__in=workorders.values("pk"))
        .select_related("customer")
        .prefetch_related(
            Prefetch(
                "workorderpayment_set",
                queryset=WorkorderPayment.objects.filter(void=False),
            ),
            Prefetch(
                "workordercreditmemo_set",
                queryset=WorkorderCreditMemo.objects.filter(void=False),
            ),
            Prefetch(
                "giftcertificateredemption_set",
                queryset=GiftCertificateRedemption.objects.filter(void=False),
            ),
        )
        .distinct()
    )

    open_workorders = []
    for wo in live_open_candidates:
        live = live_open_balance(wo)
        open_balance = normalize_open_balance(live)
        if open_balance > 0:
            wo._live_open_balance = open_balance
            wo._live_total_due = live["total_due"]
            open_workorders.append(wo)

        balance = []
        if search_amount is not None:
            amount_candidates = (
                Workorder.objects.filter(
                    void=False
                ).filter(
                    Q(normalized_workorder_total=search_amount)
                    | Q(normalized_subtotal=search_amount)
                    | Q(normalized_tax=search_amount)
                    | Q(billed=True, quote="0")
                )
                .select_related("customer")
                .prefetch_related(
                    Prefetch(
                        "workorderpayment_set",
                        queryset=WorkorderPayment.objects.filter(void=False),
                    ),
                    Prefetch(
                        "workordercreditmemo_set",
                        queryset=WorkorderCreditMemo.objects.filter(void=False),
                    ),
                    Prefetch(
                        "giftcertificateredemption_set",
                        queryset=GiftCertificateRedemption.objects.filter(void=False),
                    ),
                )
                .distinct()
            )

            seen = set()
            for wo in amount_candidates:
                matched = False

                if search_amount in {
                    wo.normalized_workorder_total,
                    wo.normalized_subtotal,
                    wo.normalized_tax,
                }:
                    matched = True

                if not matched and wo.billed and not wo.void and wo.quote == "0":
                    live = live_open_balance(wo)
                    live_total_due = live["total_due"]
                    live_open = normalize_open_balance(live)

                    if search_amount in {live_total_due, live_open}:
                        wo._live_total_due = live_total_due
                        wo._live_open_balance = live_open
                        matched = True

                if matched and wo.pk not in seen:
                    seen.add(wo.pk)
                    balance.append(wo)

    workorder_item = WorkorderItem.objects.filter(
        description__icontains=q
    ).distinct()

    customer = Customer.objects.filter(
        Q(company_name__icontains=q)
        | Q(first_name__icontains=q)
        | Q(last_name__icontains=q)
    ).distinct()

    contact = Contact.objects.filter(
        Q(fname__icontains=q) | Q(lname__icontains=q)
    ).distinct()

    inventory_items = (
        Inventory.objects.filter(
            Q(vendor_part_number__icontains=q)
            | Q(internal_part_number__name__icontains=q)
            | Q(internal_part_number__primary_vendor_part_number__icontains=q)
        )
        .select_related("internal_part_number", "internal_part_number__primary_vendor")
        .distinct()
    )

    archive_results = None
    archive_error = None
    try:
        archive_results = ArchiveApiClient().search(q)
    except Exception as exc:
        archive_error = str(exc)

    context = {
        "balance": balance,
        "workorders": workorders,
        "open": open_workorders,
        "workorder_item": workorder_item,
        "customer": customer,
        "contact": contact,
        "inventory_items": inventory_items,
        "archive_results": archive_results,
        "archive_error": archive_error,
        "query": q,
    }
    return render(request, "search.html", context)

def username(request):
    # user = request.user.logged_in
    # logged = Profile.objects.get(user=user)
    test = 'test123'
    context = {
        'test':test
    }
    return render(request, 'navbar.html', context)

# @login_required
# def assigned_item_list(request, id=None):
#     user = request.user.id
#     items = WorkorderItem.objects.filter(assigned_user_id = user).exclude(completed=1).order_by("-workorder")

#     context = {
#         'items':items,

#     }

#     return render(request, "dashboard/partials/assigned_item_list.html", context)

# @login_required
# def design_item_list(request, id=None):
#     user = request.user.id
#     items = WorkorderItem.objects.filter(job_status_id = 2).exclude(completed=1).order_by("-workorder")

#     context = {
#         'items':items,
#     }
#     return render(request, "dashboard/partials/design_item_list.html", context)

# @login_required
# def selected_item_list(request, id=None):
#     item_status = ''
#     status = JobStatus.objects.all()
#     if request.method == "GET":
#         item = request.GET.get('items')
#         print(item)
#         item_status = JobStatus.objects.get(id=item)
#         items = WorkorderItem.objects.filter(job_status_id = item).exclude(completed=1).order_by("-workorder")
#     context = {
#         'item_status':item_status,
#         'items':items,
#         'status':status,
#     }
#     return render(request, "dashboard/partials/selected_item_list.html", context)