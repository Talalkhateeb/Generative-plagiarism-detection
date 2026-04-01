"""
AI Model Integration — Celery Task
Runs per submission. Loops over every document and produces
an independent DocumentResult with its own score and matched sources.

Flow (matches Sequence Diagram):
  submissionMangt → MSG broker (RabbitMQ) → Celery worker (here)
    → for each document:
        AI model compares doc vs all sources
        → plagiarism_score, matched_sources[]
        → DocumentResult saved
    → submission.status = 'completed'
    → workspace.status  = 'analyzed'

Your partner replaces _analyze_one_document() with the real AI call.
Everything else stays the same.
"""
import logging
import random
import time

logger = logging.getLogger(__name__)


def _analyze_one_document(document, sources):
    """
    ──  IMPLEMENTATION ──────────────────────────────────────
    Replace this function body with the real AI model call.

    Expected return:
    {
      'plagiarism_score': float (0-100),
      'matched_sources': [
          {'source_id': int, 'match_percentage': float},
          ...   ← sorted descending by match_percentage
      ],
      'highlighted_text': str   (optional)
    }
    ── REAL AI CALL will look something like: ───────────────────"""
    response = ai_client.analyze(
          document_path=document.file.path,
          source_paths=[s.file.path for s in sources],
      )
    return response
    """
    time.sleep(1)   # simulate processing time — remove in production

    # Generate a random score per document ()
    total_score = round(random.uniform(5, 45), 1)

    # Distribute score across sources ()
    matched = []
    remaining = total_score
    sources_list = list(sources)
    random.shuffle(sources_list)

    for i, src in enumerate(sources_list):
        if remaining <= 0:
            matched.append({'source_id': src.id, 'match_percentage': 0.0})
            continue
        if i == len(sources_list) - 1:
            match = round(remaining, 1)
        else:
            match = round(random.uniform(0.5, max(0.5, remaining * 0.6)), 1)
        matched.append({'source_id': src.id, 'match_percentage': match})
        remaining = round(remaining - match, 1)

    # Sort most suspicious first
    matched.sort(key=lambda x: x['match_percentage'], reverse=True)

    return {
        'plagiarism_score': total_score,
        'matched_sources':  matched,
        'highlighted_text': (
            'The following passages were identified as potentially plagiarised. '
            'Please review the matched sources for details.'
        ),
    }"""


from celery import shared_task
from apps.submissions.models import Submission
from apps.results.models import DocumentResult, MatchedSource
from apps.workspaces.models import Source


@shared_task(bind=True, max_retries=3)
def analyze_submission(self, submission_id: int):
    """
    UC-5: Analyze Submission using AI Model.
    Called by send_docs() — either via Celery (production) or directly ( mode).

    For each document in the submission:
      1. Run AI analysis against all sources
      2. Save DocumentResult with score + matched sources
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

        # ── Analyze each document independently ────────────────────────────
        for document in documents:
            analysis = _analyze_one_document(document, sources)

            # Create DocumentResult
            doc_result = DocumentResult.objects.create(
                submission=submission,
                workspace=submission.workspace,
                document=document,
                plagiarism_score=analysis['plagiarism_score'],
                original_percentage=round(100 - analysis['plagiarism_score'], 1),
                highlighted_text=analysis.get('highlighted_text', ''),
            )

            # Save matched sources (already sorted most suspicious first)
            for ms_data in analysis['matched_sources']:
                try:
                    source = Source.objects.get(pk=ms_data['source_id'])
                    MatchedSource.objects.create(
                        result=doc_result,
                        source=source,
                        match_percentage=ms_data['match_percentage'],
                    )
                except Source.DoesNotExist:
                    continue

        # ── Mark submission and workspace complete ─────────────────────────
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
