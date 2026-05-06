from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import OTPVerification
from apps.plans.models import Plan


User = get_user_model()


@pytest.fixture
def plan():
    return Plan.objects.create(
        name="Starter",
        price="0.00",
        checks_per_month=10,
        max_sources=5,
        max_documents=3,
        allowed_formats=["pdf", "docx", "txt"],
        is_active=True,
    )


@pytest.fixture
def premium_plan():
    return Plan.objects.create(
        name="Pro",
        price="19.99",
        checks_per_month=50,
        max_sources=20,
        max_documents=10,
        allowed_formats=["pdf", "docx", "txt"],
        is_active=True,
    )


@pytest.fixture
def inactive_plan():
    return Plan.objects.create(
        name="Legacy",
        price="9.99",
        checks_per_month=25,
        max_sources=10,
        max_documents=5,
        allowed_formats=["pdf"],
        is_active=False,
    )


@pytest.fixture
def user(plan):
    return User.objects.create_user(
        email="user@example.com",
        name="Normal User",
        password="StrongPass123!",
        plan=plan,
        role="user",
        status="active",
        is_email_verified=True,
    )


@pytest.fixture
def inactive_user(plan):
    return User.objects.create_user(
        email="inactive@example.com",
        name="Inactive User",
        password="StrongPass123!",
        plan=plan,
        role="user",
        status="inactive",
        is_email_verified=True,
    )


@pytest.fixture
def admin_user(plan):
    return User.objects.create_user(
        email="admin@example.com",
        name="Admin User",
        password="StrongPass123!",
        plan=plan,
        role="admin",
        status="active",
        is_email_verified=True,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def otp_payload(plan):
    return {
        "name": "New User",
        "email": "newuser@example.com",
        "password": "StrongPass123!",
        "confirm_password": "StrongPass123!",
        "plan_id": plan.id,
    }


@pytest.fixture
def unused_otp():
    def _create(email="newuser@example.com", code="123456", minutes_ago=0, is_used=False):
        otp = OTPVerification.objects.create(email=email, code=code, is_used=is_used)
        if minutes_ago:
            OTPVerification.objects.filter(pk=otp.pk).update(
                created_at=timezone.now() - timedelta(minutes=minutes_ago)
            )
            otp.refresh_from_db()
        return otp

    return _create


@pytest.fixture
def mock_send_mail():
    with patch("django.core.mail.send_mail", return_value=1) as mocked:
        yield mocked

