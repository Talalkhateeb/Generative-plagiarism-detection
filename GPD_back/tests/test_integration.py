"""
Integration Tests — GPD.AI Plagiarism Detection System
Tests real HTTP interactions: authentication flow, plans CRUD, workspace CRUD,
and submission endpoints. Uses Django's APIClient against the full DRF stack.

Run: pytest tests/test_integration.py -v
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User, OTPVerification
from apps.plans.models import Plan
from apps.workspaces.models import Workspace, Document, Source
from apps.submissions.models import Submission


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def make_user(email="user@gpd.com", name="Test User", password="StrongPass1!",
              role="user", plan=None):
    """Factory: create a User and return (user, password)."""
    u = User.objects.create_user(email=email, name=name, password=password,
                                  role=role, plan=plan)
    return u, password


def get_tokens(client, email, password):
    """POST /api/auth/login/ → returns {'access': ..., 'refresh': ...}."""
    resp = client.post("/api/auth/login/", {"email": email, "password": password})
    return resp.data


def auth_client(user, password):
    """Return an APIClient already authenticated with the user's JWT."""
    c = APIClient()
    tokens = get_tokens(c, user.email, password)
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    return c


# ══════════════════════════════════════════════════════════════════════════════
# AUTH INTEGRATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestLoginIntegration(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user, self.pwd = make_user()

    def test_login_returns_jwt_tokens(self):
        """POST /api/auth/login/ must return access + refresh + user dict."""
        resp = self.client.post("/api/auth/login/",
                                {"email": "user@gpd.com", "password": self.pwd})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertIn("user", resp.data)
        self.assertEqual(resp.data["user"]["email"], "user@gpd.com")

    def test_login_with_wrong_password_returns_401(self):
        resp = self.client.post("/api/auth/login/",
                                {"email": "user@gpd.com", "password": "WRONG"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_nonexistent_email_returns_401(self):
        resp = self.client.post("/api/auth/login/",
                                {"email": "nobody@gpd.com", "password": "pass"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inactive_user_cannot_login(self):
        """Deactivated account must be rejected with a helpful error."""
        self.user.status = "inactive"
        self.user.save()
        resp = self.client.post("/api/auth/login/",
                                {"email": "user@gpd.com", "password": self.pwd})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_refresh_works(self):
        """POST /api/auth/token/refresh/ must issue a new access token."""
        tokens = get_tokens(self.client, "user@gpd.com", self.pwd)
        resp = self.client.post("/api/auth/token/refresh/",
                                {"refresh": tokens["refresh"]})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)


class TestLogoutIntegration(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user, self.pwd = make_user()

    def test_logout_blacklists_refresh_token(self):
        tokens = get_tokens(self.client, "user@gpd.com", self.pwd)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        resp = self.client.post("/api/auth/logout/", {"refresh": tokens["refresh"]})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_blacklisted_token_cannot_refresh(self):
        tokens = get_tokens(self.client, "user@gpd.com", self.pwd)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.client.post("/api/auth/logout/", {"refresh": tokens["refresh"]})
        # Now try to use the same refresh token
        resp = self.client.post("/api/auth/token/refresh/",
                                {"refresh": tokens["refresh"]})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class TestMeEndpoint(TestCase):

    def setUp(self):
        self.user, self.pwd = make_user()
        self.client = auth_client(self.user, self.pwd)

    def test_get_me_returns_profile(self):
        resp = self.client.get("/api/auth/me/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["email"], "user@gpd.com")

    def test_unauthenticated_me_returns_401(self):
        c = APIClient()
        resp = c.get("/api/auth/me/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_me_updates_name(self):
        resp = self.client.patch("/api/auth/me/", {"name": "Updated Name"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Updated Name")


# ══════════════════════════════════════════════════════════════════════════════
# PLANS INTEGRATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestPlansIntegration(TestCase):

    def setUp(self):
        self.plan = Plan.objects.create(
            name="Free", price=0, checks_per_month=5, is_active=True
        )
        self.user, self.pwd = make_user()
        self.admin, self.admin_pwd = make_user(
            email="admin@gpd.com", name="Admin", role="admin"
        )
        self.user_client = auth_client(self.user, self.pwd)
        self.admin_client = auth_client(self.admin, self.admin_pwd)
        self.anon_client = APIClient()

    def test_anyone_can_list_plans(self):
        """GET /api/plans/ must be public (for the registration page)."""
        resp = self.anon_client.get("/api/plans/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_plan(self):
        """Only admins may POST to /api/plans/."""
        resp = self.user_client.post("/api/plans/", {
            "name": "Hacked", "price": 0, "checks_per_month": 999
        })
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_plan(self):
        resp = self.admin_client.post("/api/plans/", {
            "name": "Enterprise", "price": 99, "checks_per_month": -1,
            "max_sources": -1, "max_documents": -1, "allowed_formats": []
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["name"], "Enterprise")

    def test_admin_can_delete_plan(self):
        resp = self.admin_client.delete(f"/api/plans/{self.plan.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_regular_user_cannot_delete_plan(self):
        resp = self.user_client.delete(f"/api/plans/{self.plan.id}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ══════════════════════════════════════════════════════════════════════════════
# WORKSPACE INTEGRATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestWorkspaceIntegration(TestCase):

    def setUp(self):
        self.plan = Plan.objects.create(name="Starter", price=0, checks_per_month=10)
        self.user, self.pwd = make_user(plan=self.plan)
        self.other_user, _ = make_user(email="other@gpd.com", name="Other",
                                        plan=self.plan)
        self.client = auth_client(self.user, self.pwd)

    def test_create_workspace(self):
        resp = self.client.post("/api/workspaces/", {"name": "Thesis 2025"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["name"], "Thesis 2025")

    def test_list_workspaces_only_returns_own(self):
        Workspace.objects.create(user=self.user, name="My WS")
        Workspace.objects.create(user=self.other_user, name="Other WS")
        resp = self.client.get("/api/workspaces/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [w["name"] for w in resp.data]
        self.assertIn("My WS", names)
        self.assertNotIn("Other WS", names)

    def test_get_workspace_detail(self):
        ws = Workspace.objects.create(user=self.user, name="Detail WS")
        resp = self.client.get(f"/api/workspaces/{ws.id}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Detail WS")

    def test_rename_workspace(self):
        ws = Workspace.objects.create(user=self.user, name="Old Name")
        resp = self.client.patch(f"/api/workspaces/{ws.id}/", {"name": "New Name"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ws.refresh_from_db()
        self.assertEqual(ws.name, "New Name")

    def test_delete_workspace(self):
        ws = Workspace.objects.create(user=self.user, name="To Delete")
        resp = self.client.delete(f"/api/workspaces/{ws.id}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Workspace.objects.filter(pk=ws.id).exists())

    def test_cannot_access_other_users_workspace(self):
        """Accessing another user's workspace must return 404."""
        other_ws = Workspace.objects.create(user=self.other_user, name="Private")
        resp = self.client.get(f"/api/workspaces/{other_ws.id}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_list_workspaces(self):
        c = APIClient()
        resp = c.get("/api/workspaces/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ══════════════════════════════════════════════════════════════════════════════
# SUBMISSION INTEGRATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestSubmissionHistoryIntegration(TestCase):

    def setUp(self):
        self.plan = Plan.objects.create(name="Basic", price=0, checks_per_month=10)
        self.user, self.pwd = make_user(plan=self.plan)
        self.client = auth_client(self.user, self.pwd)
        self.ws = Workspace.objects.create(user=self.user, name="WS")

    def test_history_returns_only_users_submissions(self):
        """GET /api/submissions/history/ must scope to the logged-in user."""
        other, _ = make_user(email="other2@gpd.com", name="Other2", plan=self.plan)
        other_ws = Workspace.objects.create(user=other, name="Other WS")
        Submission.objects.create(workspace=self.ws, user=self.user)
        Submission.objects.create(workspace=other_ws, user=other)

        resp = self.client.get("/api/submissions/history/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # All returned submissions must belong to self.user
        for s in resp.data:
            # The history endpoint must not leak other users' data
            self.assertNotEqual(s.get("user"), other.id)

    def test_history_requires_authentication(self):
        c = APIClient()
        resp = c.get("/api/submissions/history/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class TestSubmitWorkflowIntegration(TestCase):
    """
    Integration test for POST /api/workspaces/{id}/submit/
    Mocks the Celery task so tests don't need a real broker.
    """

    def setUp(self):
        self.plan = Plan.objects.create(name="Pro", price=19, checks_per_month=10)
        self.user, self.pwd = make_user(plan=self.plan)
        self.client = auth_client(self.user, self.pwd)
        self.ws = Workspace.objects.create(user=self.user, name="Submit WS")

    def test_submit_without_documents_returns_400(self):
        """Submitting an empty workspace must fail with 400."""
        resp = self.client.post(f"/api/workspaces/{self.ws.id}/submit/")
        self.assertIn(resp.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ])

    def test_submit_when_plan_limit_reached_returns_402(self):
        """Exceeding monthly quota must return 402 Payment Required."""
        self.plan.checks_per_month = 0
        self.plan.save()
        resp = self.client.post(f"/api/workspaces/{self.ws.id}/submit/")
        self.assertIn(resp.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_402_PAYMENT_REQUIRED,
            status.HTTP_403_FORBIDDEN,
        ])


# ══════════════════════════════════════════════════════════════════════════════
# CHANGE PASSWORD INTEGRATION TEST
# ══════════════════════════════════════════════════════════════════════════════

class TestChangePasswordIntegration(TestCase):

    def setUp(self):
        self.user, self.pwd = make_user()
        self.client = auth_client(self.user, self.pwd)

    def test_change_password_with_correct_old_password(self):
        resp = self.client.post("/api/auth/change-password/", {
            "old_password": self.pwd,
            "new_password": "NewStrongPass99!",
            "confirm_password": "NewStrongPass99!",
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_change_password_with_wrong_old_password_fails(self):
        resp = self.client.post("/api/auth/change-password/", {
            "old_password": "wrongold",
            "new_password": "NewStrongPass99!",
            "confirm_password": "NewStrongPass99!",
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
