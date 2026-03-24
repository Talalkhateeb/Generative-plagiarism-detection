"""
Workspaces — Serializers
Matching React frontend types: Workspace, Source, Document
"""
import os
from rest_framework import serializers
from .models import Workspace, Source, Document


class SourceSerializer(serializers.ModelSerializer):
    """Maps to { id, name, size, ext } in React frontend."""
    size = serializers.SerializerMethodField()

    class Meta:
        model  = Source
        fields = ['id', 'name', 'size', 'ext', 'author', 'uploaded_at']

    def get_size(self, obj):
        return obj.formatted_size()


class DocumentSerializer(serializers.ModelSerializer):
    """Maps to { id, name, size, ext } in React frontend."""
    size = serializers.SerializerMethodField()

    class Meta:
        model  = Document
        fields = ['id', 'name', 'size', 'ext', 'upload_date']

    def get_size(self, obj):
        return obj.formatted_size()


class WorkspaceListSerializer(serializers.ModelSerializer):
    """Compact view for workspace list page."""
    sources_count   = serializers.ReadOnlyField()
    documents_count = serializers.ReadOnlyField()

    class Meta:
        model  = Workspace
        fields = ['id', 'name', 'status', 'sources_count', 'documents_count', 'created_at']
        read_only_fields=['id','status','created_at']

class WorkspaceDetailSerializer(serializers.ModelSerializer):
    """Full workspace detail — includes sources, documents, submission history."""
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
        return SubmissionListSerializer(
            obj.submissions.all(), many=True, read_only=True
        ).data


class WorkspaceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Workspace
        fields = ['id','name','status','created_at']
        read_only_fields= ['id','status','created_at']

    def create(self, validated_data):
        return Workspace.objects.create(
            user=self.context['request'].user,
            **validated_data
        )


class WorkspaceRenameSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Workspace
        fields = ['name']


class SourceUploadSerializer(serializers.ModelSerializer):
    """For POST /api/workspaces/{id}/sources/"""
    file = serializers.FileField()

    class Meta:
        model  = Source
        fields = ['file', 'author']

    def validate_file(self, value):
        allowed_ext = ['.pdf', '.docx', '.doc', '.txt']
        _, ext = os.path.splitext(value.name)
        if ext.lower() not in allowed_ext:
            raise serializers.ValidationError(
                f'Unsupported file type "{ext}". Allowed: {", ".join(allowed_ext)}'
            )
        return value

    def create(self, validated_data):
        file = validated_data['file']
        _, ext = os.path.splitext(file.name)
        return Source.objects.create(
            workspace=self.context['workspace'],
            file=file,
            name=file.name,
            size=file.size,
            ext=ext.lstrip('.').upper(),
            author=validated_data.get('author', ''),
        )


class DocumentUploadSerializer(serializers.ModelSerializer):
    """For POST /api/workspaces/{id}/documents/"""
    file = serializers.FileField()

    class Meta:
        model  = Document
        fields = ['file']

    def validate_file(self, value):
        allowed_ext = ['.pdf', '.docx', '.doc', '.txt']
        _, ext = os.path.splitext(value.name)
        if ext.lower() not in allowed_ext:
            raise serializers.ValidationError(
                f'Unsupported file type "{ext}". Allowed: {", ".join(allowed_ext)}'
            )
        return value

    def create(self, validated_data):
        file = validated_data['file']
        _, ext = os.path.splitext(file.name)
        return Document.objects.create(
            workspace=self.context['workspace'],
            file=file,
            name=file.name,
            size=file.size,
            ext=ext.lstrip('.').upper(),
        )
