# Django imports
from django.test import TestCase
from django.utils import timezone

# Module imports
from plane.db.models import User
from plane.license.models import Instance

# The auth URL (not using reverse() because the name "sign-in"
# is duplicated across app and space URL patterns).
SIGN_IN_URL = "/auth/sign-in/"


class SignInEndpointTests(TestCase):
    """Tests for the redirect-based sign-in auth flow."""

    def setUp(self):
        self.client.defaults["HTTP_USER_AGENT"] = "plane/test"
        self.client.defaults["REMOTE_ADDR"] = "10.10.10.10"

        # Create instance (required for auth endpoints)
        self.instance = Instance.objects.create(
            instance_name="test",
            instance_id="test-instance",
            current_version="0.24.1",
            last_checked_at=timezone.now(),
            is_setup_done=True,
        )

        self.user = User.objects.create(email="user@plane.so")
        self.user.set_password("user@123")
        self.user.save()

    def test_without_data_redirects(self):
        response = self.client.post(SIGN_IN_URL, {})
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            "REQUIRED_EMAIL_PASSWORD_SIGN_IN",
            response.url,
        )

    def test_invalid_email_redirects(self):
        response = self.client.post(
            SIGN_IN_URL,
            {"email": "useremail.com", "password": "user@123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("INVALID_EMAIL_SIGN_IN", response.url)

    def test_wrong_password_redirects(self):
        response = self.client.post(
            SIGN_IN_URL,
            {"email": "user@plane.so", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("sign-in", response.url)

    def test_nonexistent_user_redirects(self):
        response = self.client.post(
            SIGN_IN_URL,
            {"email": "nobody@plane.so", "password": "x"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("USER_DOES_NOT_EXIST", response.url)

    def test_successful_login_redirects(self):
        response = self.client.post(
            SIGN_IN_URL,
            {"email": "user@plane.so", "password": "user@123"},
        )
        self.assertEqual(response.status_code, 302)
        # Successful login redirects without error params
        self.assertNotIn("error_code", response.url)

    def test_unconfigured_instance_redirects(self):
        """Without a configured instance, all auth redirects."""
        self.instance.is_setup_done = False
        self.instance.save()

        response = self.client.post(
            SIGN_IN_URL,
            {"email": "user@plane.so", "password": "user@123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("INSTANCE_NOT_CONFIGURED", response.url)
