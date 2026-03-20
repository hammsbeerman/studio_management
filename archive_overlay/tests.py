from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import ArchiveAssetOverlay


class ArchiveOverlaySmokeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="test")
        self.client.login(username="tester", password="test")

    def test_search_page_loads(self):
        response = self.client.get(reverse("archive_overlay:search"))
        self.assertEqual(response.status_code, 200)
