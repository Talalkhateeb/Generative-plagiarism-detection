# conftest.py — shared fixtures and Django configuration for pytest
import django
import os
import pytest

# ── Point pytest-django at your settings module ───────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GPD_Back.settings")


@pytest.fixture(scope="session")
def django_db_setup():
    """Use in-memory SQLite for all tests — no external DB needed."""
    pass


# ── Helpers shared across test modules ───────────────────────────────────────

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def basic_plan(db):
    from apps.plans.models import Plan
    return Plan.objects.create(
        name="Basic", price=9.99, checks_per_month=10, is_active=True
    )


@pytest.fixture
def regular_user(db, basic_plan):
    from apps.accounts.models import User
    return User.objects.create_user(
        email="fixture_user@gpd.com",
        name="Fixture User",
        password="FixturePass1!",
        plan=basic_plan,
    )


@pytest.fixture
def admin_user(db):
    from apps.accounts.models import User
    return User.objects.create_user(
        email="fixture_admin@gpd.com",
        name="Fixture Admin",
        password="AdminPass1!",
        role="admin",
    )


@pytest.fixture
def auth_api_client(regular_user, api_client):
    """APIClient pre-authenticated as regular_user."""
    resp = api_client.post(
        "/api/auth/login/",
        {"email": regular_user.email, "password": "FixturePass1!"},
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return api_client


@pytest.fixture
def admin_api_client(admin_user, api_client):
    """APIClient pre-authenticated as admin_user."""
    resp = api_client.post(
        "/api/auth/login/",
        {"email": admin_user.email, "password": "AdminPass1!"},
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return api_client
