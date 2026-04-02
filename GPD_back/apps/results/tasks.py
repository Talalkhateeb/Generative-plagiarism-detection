"""
AI Model Integration — Celery Task

Architecture (Option B — supervisor's choice):
  1. Files stored on Django server disk
  2. File URLs stored in SQL DB
  3. Only DOCUMENT ID sent via RabbitMQ to Celery
  4. Celery calls AI Model API with file bytes (multipart)
  5. AI Model returns score + matched sources + highlighted paragraphs
  6. Results saved to DB

Flow:
  submissionMangt → RabbitMQ → Celery worker (here)
    → for each document:
        send file bytes to AI Model API
        → plagiarism_score, matched_sources[], highlighted_paragraphs[]
        → DocumentResult saved
    → submission.status = 'completed'
"""
import logging
import requests

logger = logging.getLogger(__name__)

# ── AI Model API config ───────────────────────────────────────────────────────
# Set this to your partner's PC IP and port
AI_MODEL_URL = 'http://AI_MODEL_IP:8001/analyze'
# e.g. 'http://192.168.1.20:8001/analyze'  (same WiFi)
# e.g. 'https://abc123.ngrok.io/analyze'   (different network)


def _analyze_one_document(document, sources, submission_id):
    """
    Sends one document + all sources to the AI Model API.
    Receives plagiarism score, matched sources, and highlighted paragraphs.

    What we send (multipart/form-data):
      - document_id   : int    → DB id of the document
      - document_name : str    → filename e.g. "thesis.pdf"
      - document      : file   → actual file bytes
      - sources       : files  → list of source file bytes

    What we receive (JSON):
    {
      "plagiarism_score": 23.5,
      "matched_sources": [
        {"source_name": "paper1.pdf", "match_percentage": 15.0},
        {"source_name": "paper2.pdf", "match_percentage": 8.5}
      ],
      "highlighted_paragraphs": [
        {
          "text": "The fundamental principles...",
          "source": "paper1.pdf",
          "match_percentage": 15.0
        }
      ]
    }

    Your partner implements the AI logic — this function just calls her API.
    """
    try:
        # Open document file
        doc_file = open(document.file.path, 'rb')

        # Build multipart request
        files = [
            ('document', (document.name, doc_file, 'application/octet-stream')),
        ]
        for src in sources:
            files.append(('sources', (src.name, open(src.file.path, 'rb'), 'application/octet-stream')))

        # Send metadata as form data
        data = {
            'document_id':   document.id,
            'document_name': document.name,
            'submission_id': submission_id,
        }

        response = requests.post(
            AI_MODEL_URL,
            files=files,
            data=data,
            timeout=120,   # 2 minutes max
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        raise Exception(f'Cannot connect to AI Model at {AI_MODEL_URL}. Is it running?')
    except requests.exceptions.Timeout:
        raise Exception('AI Model took too long to respond (>120s)')
    except Exception as e:
        raise Exception(f'AI Model error: {str(e)}')


from celery import shared_task
from apps.submissions.models import Submission
from apps.results.models import DocumentResult, MatchedSource
from apps.workspaces.models import Source


@shared_task(bind=True, max_retries=3)
def analyze_submission(self, submission_id: int):
    """
    UC-5: Analyze Submission using AI Model.

    Triggered by send_docs() via RabbitMQ.
    For each document → calls AI Model API → saves DocumentResult.
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
            # Call AI Model API
            analysis = _analyze_one_document(document, sources, submission_id)

            # Save DocumentResult
            doc_result = DocumentResult.objects.create(
                submission=submission,
                workspace=submission.workspace,
                document=document,
                plagiarism_score=analysis['plagiarism_score'],
                original_percentage=round(100 - analysis['plagiarism_score'], 1),
                highlighted_text='',
                # Store highlighted paragraphs as JSON for frontend
                segments_json=_build_segments(analysis),
            )

            # Save matched sources sorted by match % descending
            matched = sorted(
                analysis.get('matched_sources', []),
                key=lambda x: x['match_percentage'],
                reverse=True
            )
            for ms in matched:
                # Find source by name
                source = next(
                    (s for s in sources if s.name == ms['source_name']),
                    None
                )
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


def _build_segments(analysis):
    """
    Converts AI model highlighted_paragraphs into frontend segments format.
    Each highlighted paragraph shows which source it matched.

    Frontend renders these as highlighted blocks — not the full document.
    """
    paragraphs = analysis.get('highlighted_paragraphs', [])
    if not paragraphs:
        return [{'text': 'Analysis complete. See matched sources above.', 'highlight': False}]

    segments = []
    for p in paragraphs:
        segments.append({
            'text':             p.get('text', ''),
            'highlight':        True,
            'source':           p.get('source', ''),
            'match_percentage': p.get('match_percentage', 0),
        })
    return segments
