from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.models import OTPVerification
from apps.accounts.serializers import (
    ChangePasswordSerializer,
    ResendOTPSerializer,
    SendOTPSerializer,
    VerifyOTPAndRegisterSerializer,
)
from apps.accounts.views import DeleteAccountView, GPDTokenObtainSerializer, UpgradePlanView


User = get_user_model()


def test_send_otp_serializer_rejects_existing_email(user, plan):
    serializer = SendOTPSerializer(
        data={
            "name": "Another User",
            "email": user.email,
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "plan_id": plan.id,
        }
    )

    assert not serializer.is_valid()
    assert serializer.errors["email"] == ["An account with this email already exists."]


def test_send_otp_serializer_rejects_mismatched_passwords(plan):
    serializer = SendOTPSerializer(
        data={
            "name": "Mismatch User",
            "email": "mismatch@example.com",
            "password": "StrongPass123!",
            "confirm_password": "WrongPass123!",
            "plan_id": plan.id,
        }
    )

    assert not serializer.is_valid()
    assert serializer.errors["confirm_password"] == ["Passwords do not match."]


def test_send_otp_serializer_rejects_invalid_plan_id():
    serializer = SendOTPSerializer(
        data={
            "name": "Planless User",
            "email": "planless@example.com",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "plan_id": 999999,
        }
    )

    assert not serializer.is_valid()
    assert serializer.errors["plan_id"] == ["Selected plan does not exist."]


def test_verify_otp_and_register_serializer_rejects_invalid_code(plan):
    serializer = VerifyOTPAndRegisterSerializer(
        data={
            "name": "New User",
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "plan_id": plan.id,
            "otp_code": "654321",
        }
    )

    assert not serializer.is_valid()
    assert serializer.errors["otp_code"] == ["Invalid verification code."]


def test_verify_otp_and_register_serializer_rejects_expired_code(plan, unused_otp):
    unused_otp(code="123456", minutes_ago=11)
    serializer = VerifyOTPAndRegisterSerializer(
        data={
            "name": "New User",
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "plan_id": plan.id,
            "otp_code": "123456",
        }
    )

    assert not serializer.is_valid()
    assert serializer.errors["otp_code"] == [
        "Verification code has expired. Please request a new one."
    ]


def test_verify_otp_and_register_serializer_creates_user_with_valid_code(plan, unused_otp):
    otp = unused_otp(code="123456")
    serializer = VerifyOTPAndRegisterSerializer(
        data={
            "name": "Verified User",
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "plan_id": plan.id,
            "otp_code": "123456",
        }
    )

    assert serializer.is_valid(), serializer.errors
    created_user = serializer.create_user()

    otp.refresh_from_db()
    assert created_user.email == "newuser@example.com"
    assert created_user.is_email_verified is True
    assert created_user.plan == plan
    assert otp.is_used is True


def test_resend_otp_serializer_generates_fresh_code_and_invalidates_previous(plan, unused_otp, mock_send_mail):
    previous_otp = unused_otp(code="111111")
    serializer = ResendOTPSerializer(
        data={
            "name": "Resend User",
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "plan_id": plan.id,
        }
    )

    assert serializer.is_valid(), serializer.errors
    new_code = serializer.send_otp()

    previous_otp.refresh_from_db()
    new_otp = OTPVerification.objects.filter(email="newuser@example.com").latest("created_at")
    assert previous_otp.is_used is True
    assert new_otp.code == new_code
    assert new_otp.code != "111111"
    mock_send_mail.assert_called_once()


def test_change_password_serializer_rejects_wrong_current_password(user):
    request = RequestFactory().post("/api/auth/change-password/")
    request.user = user
    serializer = ChangePasswordSerializer(
        data={
            "current_password": "WrongPass123!",
            "new_password": "NewStrongPass123!",
            "confirm_password": "NewStrongPass123!",
        },
        context={"request": request},
    )

    assert not serializer.is_valid()
    assert serializer.errors["current_password"] == ["Current password is incorrect."]


def test_change_password_serializer_rejects_mismatched_new_passwords(user):
    request = RequestFactory().post("/api/auth/change-password/")
    request.user = user
    serializer = ChangePasswordSerializer(
        data={
            "current_password": "StrongPass123!",
            "new_password": "NewStrongPass123!",
            "confirm_password": "MismatchPass123!",
        },
        context={"request": request},
    )

    assert not serializer.is_valid()
    assert serializer.errors["confirm_password"] == ["Passwords do not match."]


def test_upgrade_plan_view_rejects_missing_plan_id(user):
    request = APIRequestFactory().patch("/api/auth/me/upgrade-plan/", {}, format="json")
    force_authenticate(request, user=user)
    response = UpgradePlanView.as_view()(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "plan_id is required."


def test_upgrade_plan_view_rejects_nonexistent_plan(user):
    request = APIRequestFactory().patch(
        "/api/auth/me/upgrade-plan/",
        {"plan_id": 999999},
        format="json",
    )
    force_authenticate(request, user=user)
    response = UpgradePlanView.as_view()(request)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["error"] == "Selected plan does not exist."


def test_upgrade_plan_view_updates_user_plan(user, premium_plan):
    request = APIRequestFactory().patch(
        "/api/auth/me/upgrade-plan/",
        {"plan_id": premium_plan.id},
        format="json",
    )
    force_authenticate(request, user=user)
    response = UpgradePlanView.as_view()(request)

    user.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert response.data["user"]["plan"] == premium_plan.name
    assert user.plan == premium_plan


def test_delete_account_view_rejects_missing_password(user):
    request = APIRequestFactory().delete("/api/auth/me/delete/", {}, format="json")
    force_authenticate(request, user=user)
    response = DeleteAccountView.as_view()(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "Password is required to delete your account."


def test_delete_account_view_rejects_wrong_password(user):
    request = APIRequestFactory().delete(
        "/api/auth/me/delete/",
        {"password": "WrongPass123!"},
        format="json",
    )
    force_authenticate(request, user=user)
    response = DeleteAccountView.as_view()(request)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "Incorrect password."


def test_delete_account_view_deletes_account(user):
    request = APIRequestFactory().delete(
        "/api/auth/me/delete/",
        {"password": "StrongPass123!"},
        format="json",
    )
    force_authenticate(request, user=user)
    response = DeleteAccountView.as_view()(request)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not User.objects.filter(pk=user.pk).exists()


def test_gpd_token_obtain_serializer_blocks_inactive_user(inactive_user):
    serializer = GPDTokenObtainSerializer(
        data={"email": inactive_user.email, "password": "StrongPass123!"}
    )

    assert not serializer.is_valid()
    assert serializer.errors["non_field_errors"] == [
        "Your account has been deactivated by an administrator."
    ]


def test_gpd_token_obtain_serializer_returns_tokens_for_valid_login(user):
    serializer = GPDTokenObtainSerializer(
        data={"email": user.email, "password": "StrongPass123!"}
    )

    assert serializer.is_valid(), serializer.errors
    assert "access" in serializer.validated_data
    assert "refresh" in serializer.validated_data
    assert serializer.validated_data["user"]["email"] == user.email
