from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from customers.models import Customer
from inventory.models import InventoryMaster, InventoryRetailPrice
from inventory.services.pricing import (
    ensure_retail_pricing,
    get_effective_retail_price,
    compute_retail_price,
)
from retail.models import RetailSale, RetailSaleLine


User = get_user_model()


class PosPricingWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass1234")
        self.client.login(username="tester", password="pass1234")

        self.customer = Customer.objects.create(
            company_name="POS Customer",
            customer_number="POS1",
        )

        self.item = InventoryMaster.objects.create(
            name="POS Widget",
            unit_cost=Decimal("10.00"),
            retail_markup_percent=Decimal("50.00"),
            non_inventory=False,   # ✅ required
            supplies=True,         # if your model defaults to True anyway, this is just explicit
            retail=True,           # same deal
        )

    def _make_sale(self):
        return RetailSale.objects.create(
            customer=self.customer,
            cashier=self.user,             # if required
            internal_company="Office Supplies",
            tax_exempt=False,
            tax_rate=Decimal("0.055"),
            is_refund=False,
        )

    def test_add_line_from_inventory_uses_effective_price(self):
        # baseline pricing
        rp = ensure_retail_pricing(self.item)
        rp.override_price = Decimal("12.00")
        rp.save()

        sale = self._make_sale()

        url = reverse("retail:add_line_from_inventory", args=[sale.pk, self.item.pk])
        resp = self.client.post(url, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)

        line = sale.lines.get()
        self.assertEqual(
            line.unit_price,
            get_effective_retail_price(self.item),
        )
        self.assertEqual(line.unit_price, Decimal("12.00"))

    def test_sale_update_line_price_sets_override_when_flagged(self):
        sale = self._make_sale()

        # Start with a line using computed pricing
        rp = ensure_retail_pricing(self.item)
        initial_price = get_effective_retail_price(self.item)

        line = RetailSaleLine.objects.create(
            sale=sale,
            inventory=self.item,
            description="Widget line",
            qty=Decimal("1.00"),
            unit_price=initial_price,
            tax_rate=Decimal("0.055"),
        )

        new_price = Decimal("14.25")

        url = reverse(
            "retail:sale_update_line_price",
            kwargs={"sale_pk": sale.pk, "line_pk": line.pk},
        )
        resp = self.client.post(
            url,
            {
                "qty": "1.00",
                "unit_price": str(new_price),
                "update_default_price": "on",
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(resp.status_code, 200)

        # override_price should now be set on the pricing row
        rp = InventoryRetailPrice.objects.get(inventory=self.item)
        self.assertEqual(rp.override_price, new_price)
        self.assertEqual(get_effective_retail_price(self.item), new_price)