"""
Workspaces — Serializers
Upload goes to Storage Microservice, only file_key saved in SQL DB.
"""
import os
from rest_framework import serializers
from .models import Workspace, Source, Document


class SourceSerializer(serializers.ModelSerializer):
    size = serializers.SerializerMethodField()

    class Meta:
        model  = Source
        fields = ['id', 'name', 'size', 'ext', 'author', 'uploaded_at']

    def get_size(self, obj):
        return obj.formatted_size()


class DocumentSerializer(serializers.ModelSerializer):
    size = serializers.SerializerMethodField()

    class Meta:
        model  = Document
        fields = ['id', 'name', 'size', 'ext', 'upload_date']

    def get_size(self, obj):
        return obj.formatted_size()


class WorkspaceListSerializer(serializers.ModelSerializer):
    sources_count   = serializers.ReadOnlyField()
    documents_count = serializers.ReadOnlyField()

    class Meta:
        model  = Workspace
        fields = ['id', 'name', 'status', 'sources_count', 'documents_count', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']


class WorkspaceDetailSerializer(serializers.ModelSerializer):
    sources_count   = serializers.ReadOnlyField()
    documents_count = serializers.ReadOnlyField()
    sources         = SourceSerializer(many=True, read_only=True)
    documents       = DocumentSerializer(many=True, read_only=True)
    submissions     = serializers.SerializerMethodField()

    class Meta:
        model  = Workspace
        fields = [
            'id', 'name', 'status', 'sources_count', 'documents_count',
            'sources', 'documents', 'submissions', 'created_at',
        ]

    def get_submissions(self, obj):
        from apps.submissions.serializers import SubmissionListSerializer
        return SubmissionListSerializer(obj.submissions.all(), many=True).data


class WorkspaceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Workspace
        fields = ['id', 'name', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

    def create(self, validated_data):
        return Workspace.objects.create(
            user=self.context['request'].user,
            **validated_data
        )


class WorkspaceRenameSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Workspace
        fields = ['name']


class SourceUploadSerializer(serializers.Serializer):
    """Uploads file to Storage Microservice, saves file_key in DB."""
    file   = serializers.FileField()
    author = serializers.CharField(required=False, default='')

    ALLOWED = ['.pdf', '.docx', '.doc', '.txt']

    def validate_file(self, value):
        _, ext = os.path.splitext(value.name)
        if ext.lower() not in self.ALLOWED:
            raise serializers.ValidationError(
                f'Unsupported type "{ext}". Allowed: {", ".join(self.ALLOWED)}'
            )
        return value

    def save(self):
        from minio_client import upload_source
        ws   = self.context['workspace']
        file = self.validated_data['file']
        _, ext = os.path.splitext(file.name)

        # Upload to storage microservice → get file_key back
        result = upload_source(workspace_id=ws.id, file=file)

        return Source.objects.create(
            workspace=ws,
            file_key=result['file_key'],
            name=file.name,
            size=result['file_size'],
            ext=ext.lstrip('.').upper(),
            author=self.validated_data.get('author', ''),
        )


class DocumentUploadSerializer(serializers.Serializer):
    """Uploads file to Storage Microservice, saves file_key in DB."""
    file = serializers.FileField()

    ALLOWED = ['.pdf', '.docx', '.doc', '.txt']

    def validate_file(self, value):
        _, ext = os.path.splitext(value.name)
        if ext.lower() not in self.ALLOWED:
            raise serializers.ValidationError(
                f'Unsupported type "{ext}". Allowed: {", ".join(self.ALLOWED)}'
            )
        return value

    def save(self):
        from minio_client import upload_document
        ws   = self.context['workspace']
        file = self.validated_data['file']
        _, ext = os.path.splitext(file.name)

        # Upload to storage microservice → get file_key back
        result = upload_document(workspace_id=ws.id, file=file)

        return Document.objects.create(
            workspace=ws,
            file_key=result['file_key'],
            name=file.name,
            size=result['file_size'],
            ext=ext.lstrip('.').upper(),
        )
