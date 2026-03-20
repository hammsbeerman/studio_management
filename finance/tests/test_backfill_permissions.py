from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class BackfillPermissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            username="staff",
            password="pass1234",
            is_staff=True,
        )
        self.normal = User.objects.create_user(
            username="normal",
            password="pass1234",
        )

    def test_non_staff_cannot_run_backfill(self):
        self.client.login(username="normal", password="pass1234")
        response = self.client.post(reverse("finance:run_backfill_invoiceitem_ledger_locked"))
        self.assertIn(response.status_code, [302, 403])

    def test_staff_can_access_backfill_endpoint(self):
        self.client.login(username="staff", password="pass1234")
        response = self.client.post(reverse("finance:run_backfill_invoiceitem_ledger_locked"))
        self.assertNotEqual(response.status_code, 404)