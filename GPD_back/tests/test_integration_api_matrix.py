from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status

from apps.plans.models import Plan
from apps.results.models import DocumentResult
from apps.submissions.models import Submission


@pytest.mark.django_db
def test_plans_list_is_public_and_excludes_inactive(api_client, plan, inactive_plan):
    response = api_client.get("/api/plans/")

    assert response.status_code == status.HTTP_200_OK
    names = {item["name"] for item in response.data["results"]}
    assert plan.name in names
    assert inactive_plan.name not in names


@pytest.mark.django_db
def test_admin_can_create_update_and_delete_plan(admin_client):
    create_response = admin_client.post(
        "/api/plans/",
        {
            "name": "Enterprise",
            "price": "49.99",
            "checks_per_month": 100,
            "max_sources": 50,
            "max_documents": 20,
            "allowed_formats": ["pdf", "docx", "txt"],
            "is_active": True,
        },
        format="json",
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    created = Plan.objects.get(name="Enterprise")

    patch_response = admin_client.patch(
        f"/api/plans/{created.id}/",
        {"checks_per_month": 150, "is_active": False},
        format="json",
    )

    assert patch_response.status_code == status.HTTP_200_OK
    created.refresh_from_db()
    assert created.checks_per_month == 150
    assert created.is_active is False

    delete_response = admin_client.delete(f"/api/plans/{created.id}/")

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert not Plan.objects.filter(pk=created.id).exists()


@pytest.mark.django_db
def test_non_admin_cannot_create_plan(auth_client):
    response = auth_client.post(
        "/api/plans/",
        {
            "name": "Blocked",
            "price": "9.99",
            "checks_per_month": 10,
            "max_sources": 5,
            "max_documents": 3,
            "allowed_formats": ["pdf"],
            "is_active": True,
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_workspace_list_and_create(auth_client, workspace):
    response = auth_client.get("/api/workspaces/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["name"] == workspace.name

    create_response = auth_client.post("/api/workspaces/", {"name": "Created Workspace"}, format="json")

    assert create_response.status_code == status.HTTP_201_CREATED
    assert create_response.data["name"] == "Created Workspace"


@pytest.mark.django_db
def test_workspace_detail_patch_and_delete(auth_client, workspace):
    detail_response = auth_client.get(f"/api/workspaces/{workspace.id}/")
    assert detail_response.status_code == status.HTTP_200_OK
    assert detail_response.data["name"] == workspace.name

    patch_response = auth_client.patch(
        f"/api/workspaces/{workspace.id}/",
        {"name": "Renamed Workspace"},
        format="json",
    )
    assert patch_response.status_code == status.HTTP_200_OK
    workspace.refresh_from_db()
    assert workspace.name == "Renamed Workspace"

    delete_response = auth_client.delete(f"/api/workspaces/{workspace.id}/")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_workspace_endpoints_are_scoped_to_owner(auth_client, other_workspace):
    response = auth_client.get(f"/api/workspaces/{other_workspace.id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_source_upload_list_and_delete(auth_client, workspace):
    upload = SimpleUploadedFile("source.txt", b"example source", content_type="text/plain")

    with patch("minio_client.upload_source", return_value={"file_key": "sources/1/source.txt", "file_size": 14}):
        create_response = auth_client.post(
            f"/api/workspaces/{workspace.id}/sources/",
            {"file": upload, "author": "Tester"},
            format="multipart",
        )

    assert create_response.status_code == status.HTTP_201_CREATED
    source_id = create_response.data["id"]

    list_response = auth_client.get(f"/api/workspaces/{workspace.id}/sources/")
    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.data[0]["name"] == "source.txt"

    with patch("minio_client.delete_file") as mocked_delete:
        delete_response = auth_client.delete(f"/api/workspaces/{workspace.id}/sources/{source_id}/")

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    mocked_delete.assert_called_once()


@pytest.mark.django_db
def test_document_upload_list_and_delete(auth_client, workspace):
    upload = SimpleUploadedFile("document.pdf", b"example document", content_type="application/pdf")

    with patch("minio_client.upload_document", return_value={"file_key": "documents/1/document.pdf", "file_size": 16}):
        create_response = auth_client.post(
            f"/api/workspaces/{workspace.id}/documents/",
            {"file": upload},
            format="multipart",
        )

    assert create_response.status_code == status.HTTP_201_CREATED
    document_id = create_response.data["id"]

    list_response = auth_client.get(f"/api/workspaces/{workspace.id}/documents/")
    assert list_response.status_code == status.HTTP_200_OK
    assert list_response.data[0]["name"] == "document.pdf"

    with patch("minio_client.delete_file") as mocked_delete:
        delete_response = auth_client.delete(f"/api/workspaces/{workspace.id}/documents/{document_id}/")

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    mocked_delete.assert_called_once()


@pytest.mark.django_db
def test_submit_endpoint_rejects_too_few_sources(auth_client, workspace, source_one, document_one):
    response = auth_client.post(
        f"/api/workspaces/{workspace.id}/submit/",
        {"source_ids": [source_one.id], "document_ids": [document_one.id]},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["error"] == "Minimum 2 sources required for analysis."


@pytest.mark.django_db
def test_submit_endpoint_creates_submission_and_updates_workspace(
    auth_client,
    workspace,
    source_one,
    source_two,
    document_one,
):
    with patch.object(Submission, "send_docs", autospec=True) as mocked_send_docs:
        response = auth_client.post(
            f"/api/workspaces/{workspace.id}/submit/",
            {"source_ids": [source_one.id, source_two.id], "document_ids": [document_one.id]},
            format="json",
        )

    assert response.status_code == status.HTTP_201_CREATED
    workspace.refresh_from_db()
    created = Submission.objects.get(pk=response.data["id"])
    assert workspace.status == "pending"
    assert workspace.total_uploads_today == 1
    assert created.sources.count() == 2
    assert created.documents.count() == 1
    mocked_send_docs.assert_called_once_with(created)


@pytest.mark.django_db
def test_submission_history_returns_only_current_users_submissions(
    auth_client,
    submission,
    admin_user,
    other_workspace,
):
    other_submission = Submission.objects.create(workspace=other_workspace, user=admin_user, status="completed")

    response = auth_client.get("/api/submissions/history/")

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data["results"]] == [submission.id]


@pytest.mark.django_db
def test_results_endpoint_returns_404_without_submissions(auth_client, workspace):
    response = auth_client.get(f"/api/workspaces/{workspace.id}/results/")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_results_endpoint_returns_processing_status(auth_client, submission):
    submission.status = "processing"
    submission.save(update_fields=["status"])

    response = auth_client.get(f"/api/workspaces/{submission.workspace.id}/results/")

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.data["status"] == "processing"


@pytest.mark.django_db
def test_results_endpoint_returns_completed_analysis(auth_client, completed_submission):
    response = auth_client.get(f"/api/workspaces/{completed_submission.workspace.id}/results/")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "completed"
    assert response.data["document_results"][0]["document_name"] == "document-one.pdf"


@pytest.mark.django_db
def test_report_endpoint_returns_json_download(auth_client, completed_submission):
    response = auth_client.get(f"/api/workspaces/{completed_submission.workspace.id}/report/?format=json")

    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Type"] == "application/json"
    assert "attachment;" in response["Content-Disposition"]


@pytest.mark.django_db
def test_ai_callback_saves_result_and_completes_submission(auth_client, submission):
    response = auth_client.post(
        "/api/results/callback/",
        {
            "submission_id": submission.id,
            "document_id": submission.documents.first().id,
            "plagiarism_score": 31.0,
            "matched_sources": [
                {"source_name": submission.sources.first().name, "match_percentage": 18.0},
                {"source_name": submission.sources.last().name, "match_percentage": 9.0},
            ],
            "highlighted_paragraphs": [{"text": "Example", "highlight": True}],
        },
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    submission.refresh_from_db()
    submission.workspace.refresh_from_db()
    result = DocumentResult.objects.get(submission=submission)
    assert submission.status == "completed"
    assert submission.workspace.status == "analyzed"
    assert result.plagiarism_score == 31.0
    assert result.matched_sources.count() == 2


@pytest.mark.django_db
def test_auth_profile_patch_logout_refresh_and_change_password(api_client, auth_client, user):
    patch_response = auth_client.patch(
        "/api/auth/me/",
        {"name": "Updated Name", "email": "updated@example.com"},
        format="json",
    )
    assert patch_response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.name == "Updated Name"
    assert user.email == "updated@example.com"

    login_response = api_client.post(
        "/api/auth/login/",
        {"email": "updated@example.com", "password": "StrongPass123!"},
        format="json",
    )
    assert login_response.status_code == status.HTTP_200_OK

    refresh_response = api_client.post(
        "/api/auth/token/refresh/",
        {"refresh": login_response.data["refresh"]},
        format="json",
    )
    assert refresh_response.status_code == status.HTTP_200_OK
    assert "access" in refresh_response.data

    change_password_response = auth_client.post(
        "/api/auth/change-password/",
        {
            "current_password": "StrongPass123!",
            "new_password": "NewStrongPass123!",
            "confirm_password": "NewStrongPass123!",
        },
        format="json",
    )
    assert change_password_response.status_code == status.HTTP_200_OK

    relogin_response = api_client.post(
        "/api/auth/login/",
        {"email": "updated@example.com", "password": "NewStrongPass123!"},
        format="json",
    )
    assert relogin_response.status_code == status.HTTP_200_OK

    logout_response = auth_client.post(
        "/api/auth/logout/",
        {"refresh": relogin_response.data["refresh"]},
        format="json",
    )
    assert logout_response.status_code == status.HTTP_200_OK
