from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

from customers.models import Customer, ShipTo
from inventory.models import (
    Vendor,
    InventoryMaster,
    InventoryRetailPrice,
    InventoryLedger,
)
from workorders.models import Workorder, JobStatus
from retail.models import RetailSale, RetailSaleLine, RetailCashSale


def create_vendor(name="Test Vendor"):
    return Vendor.objects.create(
        name=name,
        supplier=True,
        retail_vendor=True,
        inventory_vendor=True,
        non_inventory_vendor=True,
    )


def create_customer(
    company_name="Test Customer",
    customer_number="CUST1",
    tax_exempt=False,
):
    return Customer.objects.create(
        company_name=company_name,
        first_name="Test",
        last_name="Customer",
        address1="123 Main",
        city="Reedsburg",
        state="WI",
        zipcode="53959",
        phone1="555-555-5555",
        email="test@example.com",
        website="https://example.com",
        notes="",
        po_number="",
        customer_number=customer_number,
        tax_exempt=tax_exempt,
        avg_days_to_pay="",
    )


def create_walkin_customer():
    return Customer.objects.create(
        company_name="Walk-in / Cash Sale",
        first_name="Walk-in",
        last_name="Customer",
        address1="",
        city="",
        state="",
        zipcode="",
        phone1="",
        email="",
        website="",
        notes="",
        po_number="",
        customer_number="WALKIN",
        tax_exempt=False,
        avg_days_to_pay="",
    )


def create_inventory_item(
    name="Test Item",
    unit_cost=Decimal("5.00"),
    retail=True,
    non_inventory=False,
):
    vendor = create_vendor()
    item = InventoryMaster.objects.create(
        name=name,
        description="Test item",
        primary_vendor=vendor,
        primary_vendor_part_number="PN-123",
        unit_cost=unit_cost,
        supplies=True,
        retail=retail,
        non_inventory=non_inventory,  # 🔴 REQUIRED: no default on model
        online_store=True,
        not_grouped=False,
        grouped=False,
        active=True,
    )
    # basic retail pricing snapshot
    InventoryRetailPrice.objects.create(
        inventory=item,
        purchase_price=unit_cost,
        calculated_price=unit_cost * Decimal("2.0"),
        override_price=None,
    )
    return item


def create_user(username="cashier"):
    User = get_user_model()
    return User.objects.create_user(
        username=username,
        password="testpass",
        email="cashier@example.com",
    )


def create_pos_sale(
    customer=None,
    cashier=None,
    is_refund=False,
    qty=Decimal("1.00"),
    unit_price=Decimal("10.00"),
):
    if cashier is None:
        cashier = create_user()

    sale = RetailSale.objects.create(
        cashier=cashier,
        customer=customer,
        internal_company="Office Supplies",
        status=RetailSale.STATUS_OPEN,
        locked=False,
        is_refund=is_refund,
        tax_exempt=False,
        tax_rate=Decimal("0.055"),
    )

    item = create_inventory_item()
    line = RetailSaleLine.objects.create(
        sale=sale,
        inventory=item,
        description=item.name,
        qty=qty,
        unit_price=unit_price,
        tax_rate=Decimal("0.00"),
    )

    return sale, line, item


def create_job_status(name="Open"):
    return JobStatus.objects.create(name=name)


def create_workorder_for_sale(sale, status_name="Open"):
    cust = sale.customer or create_customer()
    shipto = ShipTo.objects.create(
        customer=cust,
        company_name=cust.company_name,
        first_name=cust.first_name,
        last_name=cust.last_name,
        address1=cust.address1,
        city=cust.city,
        state=cust.state,
        zipcode=cust.zipcode,
        phone1=cust.phone1,
        phone2=cust.phone2,
        email=cust.email,
        website=cust.website,
        notes=cust.notes,
        active=cust.active,
    )

    status = JobStatus.objects.filter(name__iexact=status_name).first()
    if not status:
        status = JobStatus.objects.create(name=status_name)

    # super simple workorder number for tests
    wo = Workorder.objects.create(
        customer=cust,
        ship_to=shipto,
        hr_customer=cust.company_name,
        workorder="WO-TEST-1",
        internal_company="Office Supplies",
        quote="0",
        description=sale.notes or "",
        workorder_status=status,
        subtotal="0",
        tax="0",
        workorder_total="0",
    )
    sale.workorder = wo
    sale.save(update_fields=["workorder"])
    return wo