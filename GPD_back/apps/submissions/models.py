"""
Submissions App — Models
Class Diagram: submissionMangt(-id, -w_id, -u_id, -date, -status, -messageBroker b, -document d[], -sources s[])
UC-4: Submit Documents, UC-5: Analyze using AI Model, UC-10: View History
"""
from django.db import models
from django.conf import settings


class Submission(models.Model):
    """
    submissionMangt in class diagram.
    Created when user submits documents for analysis (UC-4).
    Linked to workspace, user, sources, and documents.
    """
    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('processing', 'Processing'),
        ('completed',  'Completed'),
        ('failed',     'Failed'),
    ]

    workspace = models.ForeignKey(
        'workspaces.Workspace', on_delete=models.CASCADE, related_name='submissions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions'
    )
    # Snapshot of files at submission time (many-to-many through the workspace)
    sources   = models.ManyToManyField('workspaces.Source',   blank=True)
    documents = models.ManyToManyField('workspaces.Document', blank=True)

    status     = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    # Message broker tracking (class diagram: -messageBroker b)
    task_id = models.CharField(max_length=255, blank=True, null=True,
                                help_text='Celery/RabbitMQ task ID')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Submission #{self.id} — {self.workspace.name} ({self.status})'

    def check_plan(self):
        """
        Class Diagram: +check_plan(w_id, u_id)
        Sequence Diagram: check_plan(w_id, u_id) → return_plan(u_id)
        Returns (allowed: bool, message: str)
        """
        plan = self.user.plan
        if not plan:
            return False, 'No subscription plan. Please select a plan.'
        remaining = plan.get_availability(self.user)
        if remaining == -1:
            return True, 'Unlimited'
        if remaining <= 0:
            return False, f'Monthly limit reached ({plan.checks_per_month} checks). Upgrade your plan.'
        return True, f'{remaining} checks remaining this month.'

    def check_doc_type(self):
        """
        Class Diagram: +check_doc_type(w_id, d)
        Returns (valid: bool, message: str)
        """
        import os
        allowed = ['.pdf', '.docx', '.doc', '.txt']
        for doc in self.documents.all():
            _, ext = os.path.splitext(doc.name)
            if ext.lower() not in allowed:
                return False, f'Unsupported file type: {doc.name}'
        return True, 'All files valid.'

    def update_total_loads_today(self):
        """Class Diagram: +update_total_loads_today(w_id)"""
        ws = self.workspace
        ws.total_uploads_today += 1
        ws.save(update_fields=['total_uploads_today'])

    def send_docs(self):
        """
        Class Diagram: +send_docs(w_id, d, s, b)
        Sequence Diagram: sends docs to message broker (RabbitMQ) → AI Model

        MOCK MODE (active): Returns fake AI result instantly so you can test
        without RabbitMQ or a real AI model running.

        TO SWITCH TO PRODUCTION: comment out _create_mock_result() and
        uncomment the Celery block below.
        """
        # ── MOCK MODE (use this while AI model is not ready) ──────────────────
        self._create_mock_result()

        # ── PRODUCTION MODE (uncomment when AI model + RabbitMQ are ready) ───
        # from apps.results.tasks import analyze_submission
        # result = analyze_submission.delay(self.id)
        # self.task_id = result.id
        # self.save(update_fields=['task_id'])

    def _create_mock_result(self):
        """
        Mock mode — called instead of Celery when AI model is not ready.
        Creates one DocumentResult per document, each with its own
        plagiarism score and ranked matched sources.
        """
        from apps.results.models import DocumentResult, MatchedSource
        import random

        documents = list(self.documents.all())
        sources   = list(self.sources.all())

        for document in documents:
            score = round(random.uniform(5, 45), 1)

            doc_result = DocumentResult.objects.create(
                submission=self,
                workspace=self.workspace,
                document=document,
                plagiarism_score=score,
                original_percentage=round(100 - score, 1),
                highlighted_text=self._generate_mock_highlighted_text(score),
            )

            # Distribute score across sources — sorted most suspicious first
            remaining = score
            shuffled = sources[:]
            random.shuffle(shuffled)
            matches = []
            for i, src in enumerate(shuffled):
                if remaining <= 0:
                    matches.append((src, 0.0))
                    continue
                if i == len(shuffled) - 1:
                    match = round(remaining, 1)
                else:
                    match = round(random.uniform(0.5, max(0.5, remaining * 0.6)), 1)
                matches.append((src, match))
                remaining = round(remaining - match, 1)

            # Save sorted by match desc (most suspicious first)
            for src, match in sorted(matches, key=lambda x: x[1], reverse=True):
                MatchedSource.objects.create(
                    result=doc_result, source=src, match_percentage=match
                )

        self.status = 'completed'
        self.workspace.status = 'analyzed'
        self.workspace.save(update_fields=['status'])
        self.save(update_fields=['status'])

    def _generate_mock_highlighted_text(self, score):
        base = (
            'The fundamental principles explored in this paper align closely with '
            'established research in the field. The methodology demonstrates rigorous '
            'analysis and builds upon prior literature to develop novel contributions.'
        )
        return base
