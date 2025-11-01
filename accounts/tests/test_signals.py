from django.test import TestCase
from django.contrib.auth import get_user_model

from accounts.models import Profile

User = get_user_model()


class ProfileSignalTests(TestCase):
    def test_profile_auto_created_on_user_create(self):
        u = User.objects.create_user(username="p1", password="x")
        self.assertTrue(Profile.objects.filter(user=u).exists())