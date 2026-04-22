"""
Plans App — Models
Class Diagram: plan_mangt(-name, -id, -daily_limit)
UC-7: Select Subscription Plan, UC-8: Plans Management (Admin)
"""
from django.db import models


class Plan(models.Model):
    """
    Subscription plan. Maps to plan_mangt in class diagram.
    daily_limit → renamed to checks_per_month for clarity.
    """
    name               = models.CharField(max_length=50, unique=True)
    price              = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    checks_per_month   = models.IntegerField(default=10, help_text='-1 means unlimited')
    max_sources        = models.IntegerField(default=5,  help_text='-1 means unlimited')
    max_documents      = models.IntegerField(default=3,  help_text='-1 means unlimited')
    allowed_formats    = models.JSONField(default=list, help_text='e.g. ["pdf","docx","txt"]')
    is_active          = models.BooleanField(default=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f'{self.name} (${self.price}/mo)'

    def get_availability(self, user):
        """
        Class Diagram: +get_availability(U_id)
        Returns remaining checks for user this month.
        """
        from apps.submissions.models import Submission
        from django.utils import timezone
        now = timezone.now()
        if self.checks_per_month == -1:
            return -1  # unlimited
        month_count = Submission.objects.filter(
            user=user,
            status='completed',
            created_at__year=now.year,
            created_at__month=now.month,
        ).count()
        return max(0, self.checks_per_month - month_count)
