"""
Workspaces — Views
UC-3: Workspace Management (add, edit, delete, upload sources)
UC-4: Submit Documents (plan check, type check, send to AI)
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Workspace, Source, Document
from .serializers import (
    WorkspaceListSerializer, WorkspaceDetailSerializer,
    WorkspaceCreateSerializer, WorkspaceRenameSerializer,
    SourceUploadSerializer, DocumentUploadSerializer, SourceSerializer, DocumentSerializer
)
from apps.accounts.permissions import IsActiveUser, IsUserRole


class WorkspaceMixin:
    """Ensure workspace belongs to logged-in user."""
    def get_user_workspace(self, pk):
        return get_object_or_404(Workspace, pk=pk, user=self.request.user)


#  Workspace CRUD 
class WorkspaceListCreateView(WorkspaceMixin, generics.ListCreateAPIView):
    """
    GET  /api/workspaces/  → list user's workspaces
    POST /api/workspaces/  → create new workspace (UC-3)
    """
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get_queryset(self):
        return Workspace.objects.filter(user=self.request.user).prefetch_related('sources', 'documents')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WorkspaceCreateSerializer
        return WorkspaceListSerializer


class WorkspaceDetailView(WorkspaceMixin, APIView):
    """
    GET    /api/workspaces/{id}/  → full workspace detail
    PATCH  /api/workspaces/{id}/  → rename workspace
    DELETE /api/workspaces/{id}/  → delete workspace
    """
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get(self, request, pk):
        ws = self.get_user_workspace(pk)
        return Response(WorkspaceDetailSerializer(ws).data)

    def patch(self, request, pk):
        ws = self.get_user_workspace(pk)
        serializer = WorkspaceRenameSerializer(ws, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        ws = self.get_user_workspace(pk)
        ws.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Sources 
class SourceListCreateView(WorkspaceMixin, APIView):
    """
    GET  /api/workspaces/{id}/sources/  → list sources
    POST /api/workspaces/{id}/sources/  → upload source (UC-3)
    """
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get(self, request, pk):
        ws = self.get_user_workspace(pk)
        return Response(SourceSerializer(ws.sources.all(), many=True).data)

    def post(self, request, pk):
        ws = self.get_user_workspace(pk)

        # Check plan: max_sources limit
        user_plan = request.user.plan
        if user_plan and user_plan.max_sources != -1:
            if ws.sources.count() >= user_plan.max_sources:
                return Response(
                    {'error': f'Source limit reached ({user_plan.max_sources}). Upgrade your plan.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = SourceUploadSerializer(
            data=request.data, context={'workspace': ws}
        )
        serializer.is_valid(raise_exception=True)
        source = serializer.save()
        return Response(SourceSerializer(source).data, status=status.HTTP_201_CREATED)


class SourceDeleteView(WorkspaceMixin, APIView):
    """DELETE /api/workspaces/{id}/sources/{src_id}/"""
    permission_classes = [IsAuthenticated, IsActiveUser]

    def delete(self, request, pk, src_id):
        ws = self.get_user_workspace(pk)
        source = get_object_or_404(Source, pk=src_id, workspace=ws)
        # Delete from MinIO storage
        from minio_client import delete_file
        delete_file(source.file_key)
        source.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Documents 
class DocumentListCreateView(WorkspaceMixin, APIView):
    """
    GET  /api/workspaces/{id}/documents/  → list documents
    POST /api/workspaces/{id}/documents/  → upload document (UC-4)
    """
    permission_classes = [IsAuthenticated, IsActiveUser]

    def get(self, request, pk):
        ws = self.get_user_workspace(pk)
        return Response(DocumentSerializer(ws.documents.all(), many=True).data)

    def post(self, request, pk):
        ws = self.get_user_workspace(pk)

        # Check plan: max_documents limit
        user_plan = request.user.plan
        if user_plan and user_plan.max_documents != -1:
            if ws.documents.count() >= user_plan.max_documents:
                return Response(
                    {'error': f'Document limit reached ({user_plan.max_documents}). Upgrade your plan.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = DocumentUploadSerializer(
            data=request.data, context={'workspace': ws}
        )
        serializer.is_valid(raise_exception=True)
        doc = serializer.save()
        return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)


class DocumentDeleteView(WorkspaceMixin, APIView):
    """DELETE /api/workspaces/{id}/documents/{doc_id}/"""
    permission_classes = [IsAuthenticated, IsActiveUser]

    def delete(self, request, pk, doc_id):
        ws = self.get_user_workspace(pk)
        doc = get_object_or_404(Document, pk=doc_id, workspace=ws)
        # Delete from MinIO storage
        from minio_client import delete_file
        delete_file(doc.file_key)
        doc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
