from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class AccountsViewsTests(TestCase):
    def setUp(self):
        self.url_login = reverse("accounts:login")
        self.url_logout = reverse("accounts:logout")
        self.url_update_pw = reverse("accounts:update_password") 
        User = get_user_model()
        self.user = User.objects.create_user("u1", password="oldpass", email="u1@example.com")

    def test_login_success(self):
        url = reverse("accounts:login")
        resp = self.client.post(url, {"username": "u1", "password": "oldpass"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["user"].is_authenticated)

    def test_login_failure(self):
        url = reverse("accounts:login")
        resp = self.client.post(url, {"username": "u1", "password": "nope"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Invalid username or password")

    def test_password_change_requires_login(self):
        url = reverse("accounts:update_password")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)  # redirected to login

    def test_password_change_flow(self):
        self.client.login(username="u1", password="oldpass")
        url = reverse("accounts:update_password")
        resp = self.client.post(url, {
            "old_password": "oldpass",
            "new_password1": "newpass12345",
            "new_password2": "newpass12345",
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.client.logout()
        ok = self.client.login(username="u1", password="newpass12345")
        self.assertTrue(ok)

    def test_logout(self):
        self.client.login(username="u1", password="oldpass")
        url = reverse("accounts:logout")
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.context["user"].is_authenticated)

    def test_login_get_redirects_if_authenticated(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url_login)
        # decorator redirects authenticated users to dashboard
        self.assertEqual(resp.status_code, 302)

    def test_logout_get_renders_page(self):
        resp = self.client.get(self.url_logout)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "logout", html=False)

    def test_logout_post_logs_out_and_redirects(self):
        self.client.force_login(self.user)
        resp = self.client.post(self.url_logout, follow=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp["Location"])

    def test_update_password_flow(self):
        self.client.force_login(self.user)
        # GET form
        resp = self.client.get(self.url_update_pw)
        self.assertEqual(resp.status_code, 200)
        # POST new password
        new_pw = "Newpass123!"
        resp = self.client.post(
            self.url_update_pw,
            {"new_password1": new_pw, "new_password2": new_pw},
        )
        self.assertEqual(resp.status_code, 302)
        # ensure password actually changed
        user = authenticate(username="u1", password=new_pw)
        self.assertIsNotNone(user)