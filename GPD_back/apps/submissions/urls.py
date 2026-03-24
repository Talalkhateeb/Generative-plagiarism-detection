from django.urls import path
from .views import SubmissionHistoryView

urlpatterns = [
    path('history/', SubmissionHistoryView.as_view(), name='submission-history'),
]
