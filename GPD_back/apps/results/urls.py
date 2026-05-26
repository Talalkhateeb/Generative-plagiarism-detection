# Results URLs are mounted on workspaces (see workspaces/urls.py)
# This file is kept for completeness
from django.urls import path
from .views import ResultListView, ReportDownloadView, AIResultCallbackView

urlpatterns = [
    path('',        ResultListView.as_view(),    name='results'),
    path('report/', ReportDownloadView.as_view(), name='report'),
    path('callback/', AIResultCallbackView.as_view(), name='ai-callback'),  # NEW
]
