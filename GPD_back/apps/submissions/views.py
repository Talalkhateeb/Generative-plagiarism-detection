"""
Submissions — Views
UC-4: Submit Documents
  - Check plan limit (check_plan)
  - Check document types (check_doc_type)
  - Save submission
  - Send to AI Model (via message broker simulation)
UC-10: View Submission History
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Submission
from .serializers import SubmissionListSerializer, SubmissionHistorySerializer
from apps.workspaces.models import Workspace
from apps.accounts.permissions import IsActiveUser


class SubmitView(APIView):
    """
    POST /api/workspaces/{id}/submit/
    Full UC-4 flow: validate plan → validate types → create submission → send to AI
    Body: { source_ids: [1,2,...], document_ids: [1,2,...] }
    """
    permission_classes = [IsAuthenticated, IsActiveUser]

    def post(self, request, pk):
        ws = get_object_or_404(Workspace, pk=pk, user=request.user)

<<<<<<< HEAD
        source_ids   = request.data.get('source_ids', [])
        document_ids = request.data.get('document_ids', [])
=======
        try:
            source_ids = {int(item) for item in request.data.get('source_ids', [])}
            document_ids = {int(item) for item in request.data.get('document_ids', [])}
        except (TypeError, ValueError):
            return Response(
                {'error': 'Source and document IDs must be valid integers.'},
                status=status.HTTP_400_BAD_REQUEST
            )
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0

        if not source_ids or len(source_ids) < 2:
            return Response(
                {'error': 'Minimum 2 sources required for analysis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not document_ids:
            return Response(
                {'error': 'At least 1 document to check is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

<<<<<<< HEAD
        # Create submission
        submission = Submission.objects.create(workspace=ws, user=request.user)
        submission.sources.set(ws.sources.filter(id__in=source_ids))
        submission.documents.set(ws.documents.filter(id__in=document_ids))

        # UC-4 Step 2: Check plan limitation
        allowed, plan_msg = submission.check_plan()
        if not allowed:
            submission.delete()
            return Response({'error': plan_msg}, status=status.HTTP_403_FORBIDDEN)
=======
        sources = list(ws.sources.filter(id__in=source_ids))
        documents = list(ws.documents.filter(id__in=document_ids))

        if len(sources) != len(source_ids):
            return Response(
                {'error': 'One or more selected sources were not found in this workspace.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if len(documents) != len(document_ids):
            return Response(
                {'error': 'One or more selected documents were not found in this workspace.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # UC-4 Step 2: Check plan limitation
        plan = request.user.plan
        if not plan:
            return Response(
                {'error': 'No subscription plan. Please select a plan.'},
                status=status.HTTP_403_FORBIDDEN
            )
        remaining = plan.get_availability(request.user)
        if remaining != -1 and remaining <= 0:
            return Response(
                {'error': f'Monthly limit reached ({plan.checks_per_month} checks). Upgrade your plan.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create submission only after the selected files and plan are valid.
        submission = Submission.objects.create(workspace=ws, user=request.user)
        submission.sources.set(sources)
        submission.documents.set(documents)
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0

        # UC-4 Step 3: Check document types
        valid, type_msg = submission.check_doc_type()
        if not valid:
            submission.delete()
            return Response({'error': type_msg}, status=status.HTTP_400_BAD_REQUEST)

        # Update workspace
        ws.status = 'pending'
        ws.save(update_fields=['status'])
        submission.update_total_loads_today()

        # UC-4 Step 4: Send to AI Model (via message broker)
        submission.send_docs()

        return Response(
            SubmissionListSerializer(submission).data,
            status=status.HTTP_201_CREATED
        )


class SubmissionHistoryView(generics.ListAPIView):
    """
    GET /api/submissions/history/
    UC-10: View submission history — all user's submissions across workspaces.
    """
    serializer_class   = SubmissionHistorySerializer
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_queryset(self):
        return Submission.objects.filter(
            user=self.request.user
        ).select_related('workspace').prefetch_related(
            'document_results__matched_sources__source',
            'document_results__document',
        ).order_by('-created_at')
<<<<<<< HEAD
=======


class SubmissionDetailView(generics.RetrieveAPIView):
    """
    GET /api/submissions/{id}/
    Returns one exact submission for the current user, including document results.
    """
    serializer_class = SubmissionHistorySerializer
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_queryset(self):
        return Submission.objects.filter(
            user=self.request.user
        ).select_related('workspace').prefetch_related(
            'document_results__matched_sources__source',
            'document_results__document',
            'sources',
            'documents',
        )
>>>>>>> 1cd9214f7b497c4ad019fd155e3b385cffbdc6f0
