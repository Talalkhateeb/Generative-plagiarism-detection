from django.urls import path
from .views import (
    WorkspaceListCreateView, WorkspaceDetailView,
    SourceListCreateView, SourceDeleteView,
    DocumentListCreateView, DocumentDeleteView,
)
# Submission and Result views are imported from their own apps
from apps.submissions.views import SubmitView
from apps.results.views import ResultListView, ReportDownloadView

urlpatterns = [
    # Workspace CRUD
    path('',                    WorkspaceListCreateView.as_view(),  name='workspace-list'),
    path('<int:pk>/',           WorkspaceDetailView.as_view(),      name='workspace-detail'),

    # Sources
    path('<int:pk>/sources/',               SourceListCreateView.as_view(), name='source-list'),
    path('<int:pk>/sources/<int:src_id>/',  SourceDeleteView.as_view(),     name='source-delete'),

    # Documents
    path('<int:pk>/documents/',              DocumentListCreateView.as_view(), name='document-list'),
    path('<int:pk>/documents/<int:doc_id>/', DocumentDeleteView.as_view(),     name='document-delete'),

    # Analysis
    path('<int:pk>/submit/',  SubmitView.as_view(),         name='workspace-submit'),
    path('<int:pk>/results/', ResultListView.as_view(),     name='workspace-results'),
    path('<int:pk>/report/',  ReportDownloadView.as_view(), name='workspace-report'),
]
