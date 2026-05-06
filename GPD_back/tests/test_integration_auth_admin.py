import pytest
from django.contrib.auth import get_user_model
from rest_framework import status

from apps.accounts.models import OTPVerification


User = get_user_model()


@pytest.mark.django_db
def test_send_otp_endpoint_validates_and_creates_otp_record(api_client, otp_payload, mock_send_mail):
    response = api_client.post("/api/auth/register/send-otp/", otp_payload, format="json")

    otp = OTPVerification.objects.get(email=otp_payload["email"])
    assert response.status_code == status.HTTP_200_OK
    assert response.data["message"] == f'Verification code sent to {otp_payload["email"]}. Check your inbox.'
    assert len(otp.code) == 6
    mock_send_mail.assert_called_once()


@pytest.mark.django_db
def test_send_otp_endpoint_rejects_existing_email(api_client, otp_payload, user, mock_send_mail):
    otp_payload["email"] = user.email

    response = api_client.post("/api/auth/register/send-otp/", otp_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["email"] == ["An account with this email already exists."]
    mock_send_mail.assert_not_called()


@pytest.mark.django_db
def test_verify_otp_endpoint_creates_account_and_returns_jwt(api_client, otp_payload, mock_send_mail):
    send_response = api_client.post("/api/auth/register/send-otp/", otp_payload, format="json")
    assert send_response.status_code == status.HTTP_200_OK
    otp = OTPVerification.objects.get(email=otp_payload["email"])

    verify_payload = {
        "name": otp_payload["name"],
        "email": otp_payload["email"],
        "password": otp_payload["password"],
        "plan_id": otp_payload["plan_id"],
        "otp_code": otp.code,
    }
    response = api_client.post("/api/auth/register/verify-otp/", verify_payload, format="json")

    created_user = User.objects.get(email=otp_payload["email"])
    otp.refresh_from_db()
    assert response.status_code == status.HTTP_201_CREATED
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["user"]["email"] == created_user.email
    assert created_user.is_email_verified is True
    assert otp.is_used is True


@pytest.mark.django_db
def test_login_endpoint_returns_tokens_for_valid_user(api_client, user):
    response = api_client.post(
        "/api/auth/login/",
        {"email": user.email, "password": "StrongPass123!"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["user"]["email"] == user.email


@pytest.mark.django_db
def test_login_endpoint_blocks_inactive_account(api_client, inactive_user):
    response = api_client.post(
        "/api/auth/login/",
        {"email": inactive_user.email, "password": "StrongPass123!"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.data["detail"] == "No active account found with the given credentials"


@pytest.mark.django_db
def test_me_endpoint_requires_authentication(api_client):
    response = api_client.get("/api/auth/me/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_me_endpoint_returns_authenticated_user_data(auth_client, user):
    response = auth_client.get("/api/auth/me/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["email"] == user.email
    assert response.data["name"] == user.name
    assert response.data["plan"] == user.plan.name


@pytest.mark.django_db
def test_upgrade_plan_endpoint_updates_plan(auth_client, user, premium_plan):
    response = auth_client.patch(
        "/api/auth/me/upgrade-plan/",
        {"plan_id": premium_plan.id},
        format="json",
    )

    user.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert response.data["user"]["plan"] == premium_plan.name
    assert user.plan == premium_plan


@pytest.mark.django_db
def test_delete_account_endpoint_removes_user(auth_client, user):
    response = auth_client.delete(
        "/api/auth/me/delete/",
        {"password": "StrongPass123!"},
        format="json",
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not User.objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_admin_accounts_search_filters_by_name_and_email(admin_client, plan):
    User.objects.create_user(
        email="alice@example.com",
        name="Alice Johnson",
        password="StrongPass123!",
        plan=plan,
        role="user",
        status="active",
        is_email_verified=True,
    )
    User.objects.create_user(
        email="bob@example.com",
        name="Bob Carter",
        password="StrongPass123!",
        plan=plan,
        role="user",
        status="active",
        is_email_verified=True,
    )

    by_name = admin_client.get("/api/admin/accounts/?search=Alice")
    by_email = admin_client.get("/api/admin/accounts/?search=bob@example.com")

    assert by_name.status_code == status.HTTP_200_OK
    assert [item["email"] for item in by_name.data["results"]] == ["alice@example.com"]
    assert [item["email"] for item in by_email.data["results"]] == ["bob@example.com"]


@pytest.mark.django_db
def test_admin_account_patch_changes_status_only(admin_client, user):
    response = admin_client.patch(
        f"/api/admin/accounts/{user.id}/",
        {"status": "inactive", "name": "Hacked Name"},
        format="json",
    )

    user.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert user.status == "inactive"
    assert user.name == "Normal User"
    assert response.data["status"] == "inactive"
    assert response.data["name"] == "Normal User"
