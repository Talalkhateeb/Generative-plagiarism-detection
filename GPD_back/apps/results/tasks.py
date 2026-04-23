"""
AI Model Integration — Celery Task
===================================
New flow with Storage Microservice:

  1. Django stores files in MinIO via Storage Service
  2. SQL DB stores only file_key (MinIO path)
  3. Celery sends workspace_id + doc_ids + source_ids to AI via RabbitMQ
  4. AI fetches files from MinIO using presigned URLs
  5. AI stores results back in MinIO via Storage Service POST /result
  6. Celery polls Storage Service GET /result until ready
  7. Celery saves result to SQL DB
"""
import logging
import requests
from celery import shared_task
from apps.submissions.models import Submission
from apps.results.models import DocumentResult, MatchedSource
from apps.workspaces.models import Source

logger = logging.getLogger(__name__)
from django.conf import settings

AI_MODEL_URL = settings.AI_MODEL_URL
STORAGE_URL  = settings.STORAGE_SERVICE_URL


def _get_presigned_url(file_key: str) -> str:
    """Get a presigned download URL from storage service."""
    r = requests.get(f"{STORAGE_URL}/file/{file_key}", params={"expires_minutes": 120})
    r.raise_for_status()
    return r.json()["url"]


def _send_to_ai(submission_id: int, document, sources) -> bool:
    """
    Send analysis request to AI Model.
    Sends: workspace_id, doc id, source ids, and presigned URLs.
    AI fetches files from MinIO directly — no file bytes sent here.
    Returns True if AI accepted the request.
    """
    payload = {
        "submission_id":  submission_id,
        "document_id":    document.id,
        "document_name":  document.name,
        "document_url":   _get_presigned_url(document.file_key),
        "sources": [
            {
                "source_id":   s.id,
                "source_name": s.name,
                "source_url":  _get_presigned_url(s.file_key),
            }
            for s in sources
        ],
        # Where AI should POST the result when done
        "result_callback_url": f"{settings.DJANGO_BASE_URL}/api/results/callback/",
    }

    r = requests.post(AI_MODEL_URL, json=payload, timeout=30)
    r.raise_for_status()
    return True





@shared_task(bind=True, max_retries=3)
def analyze_submission(self, submission_id: int):
    """
    UC-5: Analyze Submission using AI Model.
    Triggered by RabbitMQ via send_docs().

    For each document:
      1. Send doc + source URLs to AI Model
      2. Poll storage service for result
      3. Save DocumentResult to SQL DB
    """
    try:
        submission = Submission.objects.select_related('workspace').get(pk=submission_id)
        submission.status = 'processing'
        submission.save(update_fields=['status'])

        documents = list(submission.documents.all())
        sources   = list(submission.sources.all())

        if not documents:
            raise ValueError('No documents in submission')
        if not sources:
            raise ValueError('No sources in submission')

        for document in documents:
            # Fire-and-forget — AI will POST back to /api/results/callback/
            _send_to_ai(submission_id, document, sources)

        # return is OUTSIDE the loop — all documents sent first
        logger.info(f'Submission #{submission_id} sent to AI — {len(documents)} docs queued')
        return {'status': 'processing', 'documents_queued': len(documents)}

    except Exception as exc:
        logger.error(f'Failed sending submission #{submission_id}: {exc}')
        try:
            Submission.objects.filter(pk=submission_id).update(status='failed')
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)