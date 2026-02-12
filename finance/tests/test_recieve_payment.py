from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from customers.models import Customer
from workorders.models import Workorder
from finance.models import Payments, WorkorderPayment, PaymentType


class ReceivePaymentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="tester", password="pass")

        cls.customer = Customer.objects.create(company_name="Acme Co", active=True)

        # PaymentForm requires payment_type
        cls.payment_type = PaymentType.objects.create(name="Cash")

    def setUp(self):
        self.client.login(username="tester", password="pass")

    def _post(self, *, amount, workorders, modal="0"):
        date_str = timezone.localdate().strftime("%m/%d/%Y")

        payload = {
            "modal": modal,
            "customer": str(self.customer.pk),
            "payment_type": str(self.payment_type.pk),
            "amount": f"{Decimal(amount):.2f}",
            "memo": "test payment",
            "date": date_str,

            # selected invoices
            "payment": [str(w.pk) for w in workorders],

            # optional fields your view reads
            "check_number": "",
            "giftcard_number": "",
            "refunded_invoice_number": "",
        }

        url = reverse("finance:recieve_payment")
        return self.client.post(url, data=payload)

    def _make_workorder(self, open_balance):
        next_num = str(Workorder.objects.count() + 1000)  # unique per test run
        """
        Minimal Workorder factory; add required fields here if your model demands more.
        """
        return Workorder.objects.create(
            customer=self.customer,
            workorder=next_num,
            billed=1,
            completed=1,
            quote=0,
            void=0,
            paid_in_full=0,
            open_balance=Decimal(open_balance),
            total_balance=Decimal(open_balance),
            amount_paid=Decimal("0.00"),
            date_billed=timezone.now(),
        )

    def test_rejects_when_amount_less_than_sum_of_selected_balances(self):
        w1 = self._make_workorder("50.00")
        w2 = self._make_workorder("25.00")

        resp = self._post(amount="60.00", workorders=[w1, w2])  # needs 75
        self.assertEqual(resp.status_code, 302)

        # should redirect to open_invoices_recieve_payment(pk, msg=1)
        expected = reverse("finance:open_invoices_recieve_payment", kwargs={"pk": self.customer.pk, "msg": 1})
        self.assertTrue(resp["Location"].endswith(expected))

        self.assertEqual(Payments.objects.count(), 0)
        self.assertEqual(WorkorderPayment.objects.count(), 0)

    def test_records_workorderpayment_amount_as_applied_amount_not_invoice_total(self):
        w1 = self._make_workorder("50.00")
        w2 = self._make_workorder("25.00")

        resp = self._post(amount="75.00", workorders=[w1, w2])
        self.assertEqual(resp.status_code, 204)

        w1.refresh_from_db()
        w2.refresh_from_db()

        self.assertEqual(w1.open_balance, Decimal("0.00"))
        self.assertEqual(w2.open_balance, Decimal("0.00"))
        self.assertEqual(int(w1.paid_in_full), 1)
        self.assertEqual(int(w2.paid_in_full), 1)
        self.assertIsNotNone(w1.date_paid)
        self.assertIsNotNone(w2.date_paid)

        self.assertEqual(Payments.objects.count(), 1)
        pay = Payments.objects.first()

        rows = list(
            WorkorderPayment.objects
            .filter(payment_id=pay.pk)
            .order_by("workorder_id")
            .values_list("workorder_id", "payment_amount")
        )
        self.assertEqual(rows, [(w1.pk, Decimal("50.00")), (w2.pk, Decimal("25.00"))])

        pay.refresh_from_db()
        self.assertEqual(pay.available, Decimal("0.00"))

    def test_overpayment_sets_available_remainder(self):
        w1 = self._make_workorder("40.00")

        resp = self._post(amount="50.00", workorders=[w1])
        self.assertEqual(resp.status_code, 204)

        pay = Payments.objects.first()
        pay.refresh_from_db()
        self.assertEqual(pay.available, Decimal("10.00"))

        hist = WorkorderPayment.objects.get(workorder_id=w1.pk, payment_id=pay.pk)
        self.assertEqual(hist.payment_amount, Decimal("40.00"))