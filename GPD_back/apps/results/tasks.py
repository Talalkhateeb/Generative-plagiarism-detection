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
import time
import requests

logger = logging.getLogger(__name__)
from django.conf import settings

AI_MODEL_URL = settings.AI_MODEL_URL
STORAGE_URL  = settings.STORAGE_SERVICE_URL
POLL_INTERVAL    = 3     # seconds between polls
POLL_MAX_RETRIES = 40    # 40 × 3s = 2 minutes max wait


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
        "result_callback_url": f"{STORAGE_URL}/result",
    }

    r = requests.post(AI_MODEL_URL, json=payload, timeout=30)
    r.raise_for_status()
    return True


def _poll_result(submission_id: int, document_id: int) -> dict:
    """
    Poll storage service until AI model posts the result.
    Returns result dict when ready.
    Raises TimeoutError if not ready after POLL_MAX_RETRIES.
    """
    for attempt in range(POLL_MAX_RETRIES):
        try:
            r = requests.get(
                f"{STORAGE_URL}/result/{submission_id}/{document_id}",
                timeout=10
            )
            if r.status_code == 200:
                return r.json()
            # 404 means not ready yet — keep polling
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)

    raise TimeoutError(
        f"Result not available after {POLL_MAX_RETRIES * POLL_INTERVAL}s "
        f"for submission {submission_id}, document {document_id}"
    )


def _build_segments(analysis: dict) -> list:
    """Convert AI highlighted_paragraphs to frontend segments format."""
    paragraphs = analysis.get('highlighted_paragraphs', [])
    if not paragraphs:
        return [{'text': 'Analysis complete. See matched sources above.', 'highlight': False}]
    return [
        {
            'text':             p.get('text', ''),
            'highlight':        True,
            'source':           p.get('source', ''),
            'match_percentage': p.get('match_percentage', 0),
        }
        for p in paragraphs
    ]


from celery import shared_task
from apps.submissions.models import Submission
from apps.results.models import DocumentResult, MatchedSource
from apps.workspaces.models import Source


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
            # Step 1: send to AI model (AI fetches files from MinIO)
            _send_to_ai(submission_id, document, sources)

            # Step 2: poll until AI posts result to storage service
            analysis = _poll_result(submission_id, document.id)

            # Step 3: save result to SQL DB
            doc_result = DocumentResult.objects.create(
                submission=submission,
                workspace=submission.workspace,
                document=document,
                plagiarism_score=analysis['plagiarism_score'],
                original_percentage=round(100 - analysis['plagiarism_score'], 1),
                highlighted_text='',
                segments_json=_build_segments(analysis),
            )

            # Save matched sources sorted by match % descending
            matched = sorted(
                analysis.get('matched_sources', []),
                key=lambda x: x['match_percentage'],
                reverse=True
            )
            for ms in matched:
                source = next((s for s in sources if s.name == ms['source_name']), None)
                if source:
                    MatchedSource.objects.create(
                        result=doc_result,
                        source=source,
                        match_percentage=ms['match_percentage'],
                    )

        # Mark complete
        submission.status = 'completed'
        submission.workspace.status = 'analyzed'
        submission.workspace.save(update_fields=['status'])
        submission.save(update_fields=['status'])

        logger.info(f'Submission #{submission_id} completed — {len(documents)} documents analyzed')
        return {'status': 'completed', 'documents_analyzed': len(documents)}

    except Exception as exc:
        logger.error(f'Analysis failed for submission #{submission_id}: {exc}')
        try:
            Submission.objects.filter(pk=submission_id).update(status='failed')
        except Exception:
            pass
        raise self.retry(exc=exc, countdown=60)
