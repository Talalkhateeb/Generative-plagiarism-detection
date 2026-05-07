from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import OTPVerification
from apps.plans.models import Plan
from apps.results.models import DocumentResult, MatchedSource
from apps.submissions.models import Submission
from apps.workspaces.models import Document, Source, Workspace


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
def workspace(user):
    return Workspace.objects.create(user=user, name="Main Workspace")


@pytest.fixture
def other_workspace(admin_user):
    return Workspace.objects.create(user=admin_user, name="Other Workspace")


@pytest.fixture
def source_one(workspace):
    return Source.objects.create(
        workspace=workspace,
        file_key="sources/1/source-one.pdf",
        name="source-one.pdf",
        size=2048,
        ext="PDF",
        author="Author One",
    )


@pytest.fixture
def source_two(workspace):
    return Source.objects.create(
        workspace=workspace,
        file_key="sources/1/source-two.pdf",
        name="source-two.pdf",
        size=3072,
        ext="PDF",
        author="Author Two",
    )


@pytest.fixture
def document_one(workspace):
    return Document.objects.create(
        workspace=workspace,
        file_key="documents/1/document-one.pdf",
        name="document-one.pdf",
        size=4096,
        ext="PDF",
    )


@pytest.fixture
def document_two(workspace):
    return Document.objects.create(
        workspace=workspace,
        file_key="documents/1/document-two.docx",
        name="document-two.docx",
        size=5120,
        ext="DOCX",
    )


@pytest.fixture
def submission(workspace, user, source_one, source_two, document_one):
    item = Submission.objects.create(workspace=workspace, user=user, status="pending")
    item.sources.set([source_one, source_two])
    item.documents.set([document_one])
    return item


@pytest.fixture
def completed_submission(submission, workspace, document_one, source_one, source_two):
    submission.status = "completed"
    submission.save(update_fields=["status"])
    result = DocumentResult.objects.create(
        submission=submission,
        workspace=workspace,
        document=document_one,
        plagiarism_score=23.5,
        original_percentage=76.5,
        segments_json=[{"text": "Matched paragraph", "highlight": True, "source": source_one.name}],
    )
    MatchedSource.objects.create(result=result, source=source_one, match_percentage=15.0)
    MatchedSource.objects.create(result=result, source=source_two, match_percentage=8.5)
    return submission


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
