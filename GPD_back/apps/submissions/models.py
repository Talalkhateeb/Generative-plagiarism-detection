"""
Submissions app models.

UC-4: Submit Documents
UC-5: Analyze using AI model
UC-10: View History
"""
from django.conf import settings
from django.db import models


class Submission(models.Model):
    """
    Created when a user submits documents for analysis.
    Linked to workspace, user, sources, and documents.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    workspace = models.ForeignKey(
        'workspaces.Workspace',
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    sources = models.ManyToManyField('workspaces.Source', blank=True)
    documents = models.ManyToManyField('workspaces.Document', blank=True)

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    task_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Celery/RabbitMQ task ID',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Submission #{self.id} - {self.workspace.name} ({self.status})'

    def check_plan(self):
        """Return whether the user's current plan allows another check."""
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
        """Validate the submitted document extensions."""
        import os

        allowed = ['.pdf', '.docx', '.doc', '.txt']
        for doc in self.documents.all():
            _, ext = os.path.splitext(doc.name)
            if ext.lower() not in allowed:
                return False, f'Unsupported file type: {doc.name}'
        return True, 'All files valid.'

    def update_total_loads_today(self):
        """Increment the workspace daily upload counter."""
        ws = self.workspace
        ws.total_uploads_today += 1
        ws.save(update_fields=['total_uploads_today'])

    def send_docs(self):
        """Queue the submission for real AI analysis."""
        from apps.results.tasks import analyze_submission

        result = analyze_submission.delay(self.id)
        self.task_id = result.id
        self.save(update_fields=['task_id'])
