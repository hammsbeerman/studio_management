from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from controls.models import Measurement
from customers.models import Customer
from inventory.models import InventoryLedger, InventoryMaster, Vendor
from inventory.models import RetailWorkorderItem  # from inventory/models.py
from onlinestore.models import StoreItemDetails
from retail.models import RetailSale, RetailSaleLine
from finance.models import InvoiceItem, AccountsPayable
from krueger.models import KruegerJobDetail
from inventory.models import Inventory as LegacyInventory



class UomAuditBulkArchiveUnusedTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(self.user)

        self.v = Vendor.objects.create(name="V", active=True, void=False, inventory_vendor=True)
        self.m_ea = Measurement.objects.create(name="EA")

        self.url_bulk = reverse("inventory:uom_audit_bulk_apply")
        self.url_admin = reverse("inventory:uom_audit_admin")

        # Minimal customer (many fields null=False but blank=True so empty string is fine)
        self.customer = Customer.objects.create(
            company_name="TestCo",
            first_name="",
            last_name="",
            address1="",
            address2="",
            city="",
            state="",
            zipcode="",
            phone1="",
            phone2="",
            email="",
            website="",
            notes="",
            po_number="",
            customer_number="",
            avg_days_to_pay="",
            tax_exempt=False,
            mail_bounced_back=False,
        )

    def _make_item(self, name):
        return InventoryMaster.objects.create(
            name=name,
            description="",
            primary_vendor=self.v,
            primary_vendor_part_number=None,
            primary_base_unit=None,
            units_per_base_unit=None,
            unit_cost=None,
            price_per_m=None,
            supplies=True,
            retail=True,
            non_inventory=False,
            online_store=True,
            not_grouped=False,
            grouped=False,
            high_price=None,
            active=True,
            retail_price=None,
            retail_markup_percent=None,
            retail_markup_flat=None,
            retail_category=None,
        )

    def _add_ledger(self, item):
        InventoryLedger.objects.create(
            inventory_item=item,
            qty_delta=Decimal("1.0000"),
            source_type="ADJUSTMENT",
            source_id="T1",
            note="test",
        )

    def _add_retail_line(self, item):
        sale = RetailSale.objects.create(
            cashier=self.user,
            customer=self.customer,
            customer_name="",
            internal_company="Office Supplies",
            status=RetailSale.STATUS_OPEN,
        )
        RetailSaleLine.objects.create(
            sale=sale,
            inventory=item,
            description=item.name,
            qty=Decimal("1.0000"),
            unit_price=Decimal("10.00"),
            tax_rate=Decimal("0.00"),
            sold_variation=None,
            is_gift_certificate=False,
        )

    def _add_workorder_ref(self, item):
        # workorder is nullable on RetailWorkorderItem
        RetailWorkorderItem.objects.create(
            workorder=None,
            sale=None,
            internal_company="Office Supplies",
            customer=self.customer,
            hr_customer="",
            inventory=item,
            description=item.name,
            quantity=Decimal("1.00"),
            unit_price=Decimal("1.00"),
            total_price=Decimal("1.00"),
            notes="",
        )

    def _add_online_store_ref(self, item):
        StoreItemDetails.objects.create(item=item)

    def test_bulk_archive_unused_preview_does_not_modify(self):
        unused = self._make_item("Unused")
        used_ledger = self._make_item("UsedLedger")
        self._add_ledger(used_ledger)

        next_url = self.url_admin + f"?vendor={self.v.id}&limit=200"

        resp = self.client.post(
            self.url_bulk,
            {
                "bulk_action": "archive_unused",
                "bulk_preview": "1",
                "next": next_url,
                # filter form bits (must be present for form.is_valid())
                "only_active": "on",
                "vendor": self.v.id,
                "name_contains": "",
                "limit": "200",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], next_url)

        unused.refresh_from_db()
        used_ledger.refresh_from_db()
        self.assertFalse(unused.non_inventory)
        self.assertFalse(used_ledger.non_inventory)

    def test_bulk_archive_unused_apply_archives_only_eligible(self):
        unused = self._make_item("Unused")
        used_ledger = self._make_item("UsedLedger")
        used_retail = self._make_item("UsedRetail")
        used_wo = self._make_item("UsedWO")
        used_online = self._make_item("UsedOnline")

        self._add_ledger(used_ledger)
        self._add_retail_line(used_retail)
        self._add_workorder_ref(used_wo)
        self._add_online_store_ref(used_online)

        resp = self.client.post(
            self.url_bulk,
            {
                "bulk_action": "archive_unused",
                "next": self.url_admin,
                # filter form bits
                "only_active": "on",
                "vendor": self.v.id,
                "name_contains": "",
                "limit": "200",
            },
        )
        self.assertEqual(resp.status_code, 302)

        unused.refresh_from_db()
        used_ledger.refresh_from_db()
        used_retail.refresh_from_db()
        used_wo.refresh_from_db()
        used_online.refresh_from_db()

        self.assertTrue(unused.non_inventory, "Unused item should be archived (non_inventory=True)")
        self.assertFalse(used_ledger.non_inventory, "Ledger usage should block archive")
        self.assertFalse(used_retail.non_inventory, "Retail usage should block archive")
        self.assertFalse(used_wo.non_inventory, "Workorder usage should block archive")
        self.assertFalse(used_online.non_inventory, "Online store usage should block archive")

def test_bulk_archive_unused_blocks_ap_invoice_items(self):
    item = self._make_item("UsedAP")

    ap = AccountsPayable.objects.create(
        vendor=self.v,
        invoice_number="INV-1",
        invoice_date="2026-01-01",
        due_date="2026-02-01",
        total=Decimal("10.00"),
        paid=False,
    )
    InvoiceItem.objects.create(
        vendor=self.v,
        invoice=ap,
        name="Line",
        internal_part_number=item,
        unit_price=None if not hasattr(InvoiceItem, "unit_price") else Decimal("1.00"),
        qty=Decimal("1.00"),
        ppm=False,
    )

    resp = self.client.post(
        self.url_bulk,
        {
            "bulk_action": "archive_unused",
            "only_active": "on",
            "vendor": self.v.id,
            "name_contains": "",
            "limit": "200",
            "next": self.url_admin,
        },
    )
    self.assertEqual(resp.status_code, 302)

    item.refresh_from_db()
    self.assertFalse(item.non_inventory)

def test_bulk_archive_unused_blocks_job_materials(self):
    item = self._make_item("UsedJobMaterial")

    # create legacy Inventory row pointing to InventoryMaster
    legacy = LegacyInventory.objects.create(
        name="Legacy Paper",
        internal_part_number=item,
        retail_item=True,
    )

    # KruegerJobDetail requires a bunch of non-null fields in your model.
    # Create the minimum set that are null=False / blank=False.
    KruegerJobDetail.objects.create(
        workorder=None,
        hr_workorder="WO-1",
        workorder_item="1",
        internal_company="Krueger Printing",
        customer=self.customer,
        hr_customer="TestCo",
        side_1_inktype="B/W",
        side_2_inktype="None",
        paper_stock=legacy,
        packaging=None,
    )

    resp = self.client.post(
        self.url_bulk,
        {
            "bulk_action": "archive_unused",
            "only_active": "on",
            "vendor": self.v.id,
            "name_contains": "",
            "limit": "200",
            "next": self.url_admin,
        },
    )
    self.assertEqual(resp.status_code, 302)

    item.refresh_from_db()
    self.assertFalse(item.non_inventory)