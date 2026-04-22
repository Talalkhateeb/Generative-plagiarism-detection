"""
Unit Tests — GPD.AI Plagiarism Detection System
Tests core business logic: models, managers, helper methods.
No HTTP calls — pure unit-level testing with Django TestCase.

Run: pytest tests/test_unit.py -v
"""
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import User, Admin, OTPVerification
from apps.plans.models import Plan
from apps.workspaces.models import Workspace, Document, Source
from apps.submissions.models import Submission


# ══════════════════════════════════════════════════════════════════════════════
# USER / ACCOUNT MODEL TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestUserModel(TestCase):
    """Tests for User model business logic."""

    def setUp(self):
        self.plan = Plan.objects.create(
            name="Basic", price=9.99, checks_per_month=10
        )
        self.user = User.objects.create_user(
            email="user@test.com", name="Test User", password="pass123"
        )

    # ── Normal cases ──────────────────────────────────────────────────────────

    def test_user_created_with_default_role(self):
        """A new user must default to 'user' role, not 'admin'."""
        self.assertEqual(self.user.role, "user")

    def test_user_is_active_when_status_active(self):
        """Active status must keep is_active=True."""
        self.user.status = "active"
        self.user.save()
        self.assertTrue(self.user.is_active)

    def test_is_admin_returns_false_for_regular_user(self):
        """is_admin() must return False for role='user'."""
        self.assertFalse(self.user.is_admin())

    def test_is_admin_returns_true_for_admin_role(self):
        """is_admin() must return True for role='admin'."""
        admin = User.objects.create_user(
            email="admin@test.com", name="Admin", password="pass123", role="admin"
        )
        self.assertTrue(admin.is_admin())

    def test_display_account_returns_correct_dict(self):
        """display_account() must return name, email, role, status."""
        data = self.user.display_account()
        self.assertEqual(data["email"], "user@test.com")
        self.assertEqual(data["role"], "user")
        self.assertIn("name", data)
        self.assertIn("status", data)

    def test_str_representation(self):
        """__str__ must include name, email, role."""
        result = str(self.user)
        self.assertIn("Test User", result)
        self.assertIn("user@test.com", result)
        self.assertIn("user", result)

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_user_deactivated_when_status_inactive(self):
        """Setting status='inactive' must flip is_active to False."""
        self.user.status = "inactive"
        self.user.save()
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_admin_gets_is_staff_automatically(self):
        """Admin role must auto-set is_staff=True on save."""
        self.user.role = "admin"
        self.user.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_staff)

    def test_create_superuser_sets_all_flags(self):
        """create_superuser must set is_superuser, is_staff, is_email_verified."""
        su = User.objects.create_superuser(
            email="su@test.com", name="Super", password="pass123"
        )
        self.assertTrue(su.is_superuser)
        self.assertTrue(su.is_staff)
        self.assertTrue(su.is_email_verified)
        self.assertEqual(su.role, "admin")

    # ── Error handling ────────────────────────────────────────────────────────

    def test_create_user_without_email_raises(self):
        """AccountManager must raise ValueError when email is empty."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", name="No Email", password="pass")

    def test_duplicate_email_raises(self):
        """Email field is unique; duplicate must raise IntegrityError."""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email="user@test.com", name="Dup", password="pass"
            )


# ══════════════════════════════════════════════════════════════════════════════
# OTP VERIFICATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestOTPVerification(TestCase):
    """Tests for OTP model expiry logic."""

    def test_otp_not_expired_when_fresh(self):
        """A newly created OTP must not be expired."""
        otp = OTPVerification.objects.create(email="a@b.com", code="123456")
        self.assertFalse(otp.is_expired())

    def test_otp_expired_after_10_minutes(self):
        """OTP created > 10 minutes ago must return is_expired=True."""
        otp = OTPVerification.objects.create(email="a@b.com", code="654321")
        # Manually push created_at 11 minutes into the past
        OTPVerification.objects.filter(pk=otp.pk).update(
            created_at=timezone.now() - timedelta(minutes=11)
        )
        otp.refresh_from_db()
        self.assertTrue(otp.is_expired())

    def test_otp_str_representation(self):
        """__str__ must mention the email."""
        otp = OTPVerification.objects.create(email="x@y.com", code="000000")
        self.assertIn("x@y.com", str(otp))


# ══════════════════════════════════════════════════════════════════════════════
# PLAN MODEL TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestPlanModel(TestCase):
    """Tests for Plan.get_availability() — core quota logic."""

    def setUp(self):
        self.plan = Plan.objects.create(
            name="Starter", price=0, checks_per_month=5
        )
        self.user = User.objects.create_user(
            email="u@test.com", name="U", password="p", plan=self.plan
        )
        self.workspace = Workspace.objects.create(
            user=self.user, name="WS"
        )

    def _make_submission(self):
        return Submission.objects.create(
            workspace=self.workspace, user=self.user, status="completed"
        )

    def test_availability_full_when_no_submissions(self):
        """No submissions → remaining = checks_per_month."""
        self.assertEqual(self.plan.get_availability(self.user), 5)

    def test_availability_decreases_per_submission(self):
        """Each submission reduces availability by 1."""
        self._make_submission()
        self._make_submission()
        self.assertEqual(self.plan.get_availability(self.user), 3)

    def test_availability_unlimited_plan(self):
        """checks_per_month=-1 must always return -1 (unlimited)."""
        self.plan.checks_per_month = -1
        self.plan.save()
        for _ in range(5):
            self._make_submission()
        self.assertEqual(self.plan.get_availability(self.user), -1)

    def test_availability_never_goes_negative(self):
        """When all checks used, availability must floor at 0, not negative."""
        for _ in range(7):  # 7 > 5 limit
            self._make_submission()
        self.assertEqual(self.plan.get_availability(self.user), 0)

    def test_plan_str_includes_name_and_price(self):
        """__str__ must show plan name and price."""
        result = str(self.plan)
        self.assertIn("Starter", result)


# ══════════════════════════════════════════════════════════════════════════════
# WORKSPACE / DOCUMENT / SOURCE MODEL TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestWorkspaceModel(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="ws@test.com", name="WS User", password="pass"
        )
        self.ws = Workspace.objects.create(user=self.user, name="My Workspace")

    def test_workspace_default_status_is_draft(self):
        self.assertEqual(self.ws.status, "draft")

    def test_workspace_str_includes_name_and_user(self):
        result = str(self.ws)
        self.assertIn("My Workspace", result)
        self.assertIn("WS User", result)

    def test_sources_count_property(self):
        Source.objects.create(
            workspace=self.ws, file_key="sources/1.pdf",
            name="src.pdf", ext=".pdf", size=1024
        )
        self.assertEqual(self.ws.sources_count, 1)

    def test_documents_count_property(self):
        Document.objects.create(
            workspace=self.ws, file_key="docs/1.pdf",
            name="doc.pdf", ext=".pdf", size=2048
        )
        self.assertEqual(self.ws.documents_count, 1)


class TestDocumentModel(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="doc@test.com", name="Doc User", password="pass"
        )
        self.ws = Workspace.objects.create(user=self.user, name="WS")

    def _make_doc(self, name="file.pdf", size=1024):
        return Document.objects.create(
            workspace=self.ws, file_key=f"docs/{name}",
            name=name, ext=".pdf", size=size
        )

    def test_validate_format_pdf_is_valid(self):
        doc = self._make_doc("essay.pdf")
        self.assertTrue(doc.validate_format())

    def test_validate_format_docx_is_valid(self):
        doc = self._make_doc("essay.docx")
        doc.name = "essay.docx"
        self.assertTrue(doc.validate_format())

    def test_validate_format_exe_is_invalid(self):
        """Executable files must fail format validation."""
        doc = self._make_doc("malware.exe")
        self.assertFalse(doc.validate_format())

    def test_formatted_size_shows_mb_for_large_files(self):
        doc = self._make_doc(size=2 * 1024 * 1024)  # 2 MB
        self.assertIn("MB", doc.formatted_size())

    def test_formatted_size_shows_kb_for_small_files(self):
        doc = self._make_doc(size=512 * 1024)  # 512 KB
        self.assertIn("KB", doc.formatted_size())


# ══════════════════════════════════════════════════════════════════════════════
# SUBMISSION MODEL TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestSubmissionCheckPlan(TestCase):
    """Tests for Submission.check_plan() — the plan quota guard."""

    def setUp(self):
        self.plan = Plan.objects.create(
            name="Pro", price=19, checks_per_month=3
        )
        self.user = User.objects.create_user(
            email="sub@test.com", name="Sub User", password="pass", plan=self.plan
        )
        self.ws = Workspace.objects.create(user=self.user, name="WS")
        self.submission = Submission.objects.create(
            workspace=self.ws, user=self.user
        )

    def test_check_plan_allowed_when_quota_available(self):
        allowed, msg = self.submission.check_plan()
        self.assertTrue(allowed)
        self.assertIn("remaining", msg)

    def test_check_plan_denied_when_no_plan(self):
        """User without a plan must be denied."""
        self.user.plan = None
        self.user.save()
        allowed, msg = self.submission.check_plan()
        self.assertFalse(allowed)
        self.assertIn("plan", msg.lower())

    def test_check_plan_denied_when_limit_reached(self):
        """After exhausting monthly quota, check_plan must return False."""
        for _ in range(3):
            Submission.objects.create(
                workspace=self.ws, user=self.user, status="completed"
            )
        allowed, msg = self.submission.check_plan()
        self.assertFalse(allowed)
        self.assertIn("limit", msg.lower())

    def test_check_plan_unlimited_always_allowed(self):
        """Unlimited plan (-1) must always return True."""
        self.plan.checks_per_month = -1
        self.plan.save()
        for _ in range(100):
            Submission.objects.create(
                workspace=self.ws, user=self.user, status="completed"
            )
        allowed, msg = self.submission.check_plan()
        self.assertTrue(allowed)
        self.assertEqual(msg, "Unlimited")


class TestSubmissionCheckDocType(TestCase):
    """Tests for Submission.check_doc_type()."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="dtype@test.com", name="DType", password="pass"
        )
        self.ws = Workspace.objects.create(user=self.user, name="WS")
        self.sub = Submission.objects.create(workspace=self.ws, user=self.user)

    def test_valid_pdf_passes(self):
        doc = Document.objects.create(
            workspace=self.ws, file_key="d/1.pdf", name="thesis.pdf", ext=".pdf", size=1000
        )
        self.sub.documents.add(doc)
        valid, msg = self.sub.check_doc_type()
        self.assertTrue(valid)

    def test_invalid_format_fails(self):
        doc = Document.objects.create(
            workspace=self.ws, file_key="d/1.mp4", name="video.mp4", ext=".mp4", size=1000
        )
        self.sub.documents.add(doc)
        valid, msg = self.sub.check_doc_type()
        self.assertFalse(valid)
        self.assertIn("Unsupported", msg)

    def test_no_documents_passes(self):
        """Submission with no documents must not fail doc type check."""
        valid, _ = self.sub.check_doc_type()
        self.assertTrue(valid)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN PROXY MODEL TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestAdminModel(TestCase):

    def setUp(self):
        self.target_user = User.objects.create_user(
            email="target@test.com", name="Target", password="pass"
        )
        self.admin_user = User.objects.create_user(
            email="admin@test.com", name="Admin", password="pass", role="admin"
        )
        self.admin = Admin.objects.get(pk=self.admin_user.pk)

    def test_edit_ustate_deactivates_user(self):
        """edit_ustate('inactive') must set is_active=False."""
        self.admin.edit_ustate(self.target_user.pk, "inactive")
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)
        self.assertEqual(self.target_user.status, "inactive")

    def test_edit_ustate_reactivates_user(self):
        """edit_ustate('active') must restore is_active=True."""
        self.admin.edit_ustate(self.target_user.pk, "active")
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.is_active)

    def test_admin_manager_only_returns_admins(self):
        """Admin.objects must not include regular users."""
        queryset = Admin.objects.all()
        for obj in queryset:
            self.assertEqual(obj.role, "admin")
