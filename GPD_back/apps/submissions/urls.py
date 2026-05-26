from django.urls import path
from .views import SubmissionDetailView, SubmissionHistoryView

urlpatterns = [
    path('history/', SubmissionHistoryView.as_view(), name='submission-history'),
    path('<int:pk>/', SubmissionDetailView.as_view(), name='submission-detail'),
]
