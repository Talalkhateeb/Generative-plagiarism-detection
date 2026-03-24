from rest_framework import serializers
from .models import Submission
from apps.workspaces.serializers import SourceSerializer, DocumentSerializer


class SubmissionListSerializer(serializers.ModelSerializer):
    """
    Returned after POST /submit/ and in workspace detail.
    Includes per-document results so frontend can show them immediately.
    """
    sources         = SourceSerializer(many=True, read_only=True)
    documents       = DocumentSerializer(many=True, read_only=True)
    date            = serializers.DateTimeField(source='created_at')
    document_results = serializers.SerializerMethodField()

    class Meta:
        model  = Submission
        fields = ['id', 'date', 'status', 'sources', 'documents', 'document_results']

    def get_document_results(self, obj):
        from apps.results.serializers import DocumentResultSerializer
        return DocumentResultSerializer(
            obj.document_results.prefetch_related('matched_sources__source', 'document').all(),
            many=True
        ).data


class SubmissionHistorySerializer(serializers.ModelSerializer):
    """UC-10: History entry — includes workspace info + per-document results."""
    workspace_id     = serializers.IntegerField(source='workspace.id', read_only=True)
    workspace_name   = serializers.CharField(source='workspace.name', read_only=True)
    date             = serializers.DateTimeField(source='created_at')
    document_results = serializers.SerializerMethodField()

    class Meta:
        model  = Submission
        fields = ['id', 'workspace_id', 'workspace_name', 'date', 'status', 'document_results']

    def get_document_results(self, obj):
        from apps.results.serializers import DocumentResultSerializer
        return DocumentResultSerializer(
            obj.document_results.prefetch_related('matched_sources__source', 'document').all(),
            many=True
        ).data
