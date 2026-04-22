"""
Storage Service Client
======================
Django calls this to upload/download/delete files via the Storage Microservice.
All file operations go through storage service at STORAGE_SERVICE_URL.
"""
import requests
import os

STORAGE_SERVICE_URL = os.getenv("STORAGE_SERVICE_URL", "http://127.0.0.1:8002")


def upload_source(workspace_id: int, file) -> dict:
    """Upload a source file. Returns {file_key, file_name, file_size}."""
    response = requests.post(
        f"{STORAGE_SERVICE_URL}/upload/source",
        params={"workspace_id": workspace_id},
        files={"file": (file.name, file, "application/octet-stream")},
    )
    response.raise_for_status()
    return response.json()


def upload_document(workspace_id: int, file) -> dict:
    """Upload a document file. Returns {file_key, file_name, file_size}."""
    response = requests.post(
        f"{STORAGE_SERVICE_URL}/upload/document",
        params={"workspace_id": workspace_id},
        files={"file": (file.name, file, "application/octet-stream")},
    )
    response.raise_for_status()
    return response.json()


def get_file_url(file_key: str, expires_minutes: int = 60) -> str:
    """Get a presigned download URL for a file."""
    response = requests.get(
        f"{STORAGE_SERVICE_URL}/file/{file_key}",
        params={"expires_minutes": expires_minutes},
    )
    response.raise_for_status()
    return response.json()["url"]
import logging
logger = logging.getLogger(__name__)

def delete_file(file_key: str):
    """Delete a file from storage."""
    try:
        requests.delete(f"{STORAGE_SERVICE_URL}/file/{file_key}",timeout=10)
    except Exception as e :
        logger.warning(f"Failed to delete file {file_key}:{e}")  # Don't fail if file doesn't exist


def get_result(submission_id: int, document_id: int) -> dict:
    """Fetch analysis result stored by AI model."""
    response = requests.get(
        f"{STORAGE_SERVICE_URL}/result/{submission_id}/{document_id}"
    )
    response.raise_for_status()
    return response.json()
