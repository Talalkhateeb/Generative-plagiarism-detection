"""
Results — Views
UC-6: View Analysis Result + Download Plagiarism Report

GET /api/workspaces/{id}/results/
Returns all document results for the latest submission of this workspace.
Each document has its own score and sorted matched sources.
"""
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from .models import DocumentResult
from .serializers import DocumentResultSerializer, SubmissionResultSerializer
from apps.workspaces.models import Workspace
from apps.submissions.models import Submission
from apps.accounts.permissions import IsActiveUser


class ResultListView(APIView):
    """
    GET /api/workspaces/{id}/results/

    Returns the latest submission's results, with one entry per document.
    Response shape:
    {
      "submission_id": 5,
      "status": "completed",
      "document_results": [
        {
          "document_id": 1,
          "document_name": "thesis.pdf",
          "plagiarism_score": 23.5,
          "original_percentage": 76.5,
          "matched_sources": [
            { "source": "paper1.pdf", "match": 15.0, "color": "#ef4444" },
            { "source": "paper2.pdf", "match":  8.5, "color": "#f97316" }
          ],
          "highlighted_segments": [...]
        }
      ]
    }
    """
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get(self, request, pk):
        ws = get_object_or_404(Workspace, pk=pk, user=request.user)

        # Get the latest submission for this workspace
        submission = (
            Submission.objects
            .filter(workspace=ws)
            .prefetch_related(
                'document_results__document',
                'document_results__matched_sources__source',
            )
            .order_by('-created_at')
            .first()
        )

        if not submission:
            return Response(
                {'error': 'No submissions found. Please submit documents first.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if submission.status in ('pending', 'processing'):
            return Response(
                {'status': submission.status, 'message': 'Analysis in progress…'},
                status=status.HTTP_202_ACCEPTED
            )

        doc_results = submission.document_results.prefetch_related(
            'matched_sources__source', 'document'
        ).all()

        if not doc_results.exists():
            return Response(
                {'error': 'Analysis is not complete yet.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'submission_id':    submission.id,
            'status':           submission.status,
            'document_results': DocumentResultSerializer(doc_results, many=True).data,
        })


class ReportDownloadView(APIView):
    """
    GET /api/workspaces/{id}/report/
    UC-6 extend: Download full plagiarism report.
    Returns JSON containing all document results — frontend generates PDF from this.
    """
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get(self, request, pk):
        ws = get_object_or_404(Workspace, pk=pk, user=request.user)

        submission = (
            Submission.objects
            .filter(workspace=ws, status='completed')
            .order_by('-created_at')
            .first()
        )

        if not submission:
            return Response(
                {'error': 'No completed results available for download.'},
                status=status.HTTP_404_NOT_FOUND
            )

        doc_results = submission.document_results.prefetch_related(
            'matched_sources__source', 'document'
        ).all()

        report = {
            'workspace':    ws.name,
            'generated_at': submission.created_at.isoformat(),
            'documents':    [r.export_pdf_report() for r in doc_results],
        }

        if request.query_params.get('format') == 'json':
            response = HttpResponse(
                json.dumps(report, indent=2),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="veritas-report-{ws.id}.json"'
            return response

        return Response(report)
