"""
Workspaces App — Models
Files stored in MinIO via Storage Microservice.
Only file_key (MinIO path) stored in SQL DB — not the actual file.
"""
from django.db import models
from django.conf import settings


class Workspace(models.Model):
    STATUS_CHOICES = [
        ('draft',    'Draft'),
        ('pending',  'Pending Analysis'),
        ('analyzed', 'Analyzed'),
    ]
    user                = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workspaces'
    )
    name                = models.CharField(max_length=255)
    status              = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    total_uploads_today = models.IntegerField(default=0)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.user.name})'

    @property
    def sources_count(self):
        return self.sources.count()

    @property
    def documents_count(self):
        return self.documents.count()


class Source(models.Model):
    """
    Reference file uploaded to compare against.
    file_key = MinIO path e.g. 'sources/1/uuid.pdf'
    """
    workspace   = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='sources')
    file_key    = models.CharField(max_length=500)   # MinIO path — stored in SQL DB
    name        = models.CharField(max_length=255)   # original filename
    size        = models.PositiveBigIntegerField(default=0)
    ext         = models.CharField(max_length=10)
    author      = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Source: {self.name} in {self.workspace.name}'

    def get_download_url(self):
        """Get presigned URL from storage service."""
        from minio_client import get_file_url
        return get_file_url(self.file_key)

    def formatted_size(self):
        if self.size > 1024 * 1024:
            return f'{self.size / (1024*1024):.1f} MB'
        return f'{self.size // 1024} KB'


class Document(models.Model):
    """
    Document submitted for plagiarism checking.
    file_key = MinIO path e.g. 'documents/1/uuid.pdf'
    """
    workspace   = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='documents')
    file_key    = models.CharField(max_length=500)   # MinIO path — stored in SQL DB
    name        = models.CharField(max_length=255)
    size        = models.PositiveBigIntegerField(default=0)
    ext         = models.CharField(max_length=10)
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Document: {self.name} in {self.workspace.name}'

    def get_download_url(self):
        """Get presigned URL from storage service."""
        from minio_client import get_file_url
        return get_file_url(self.file_key)

    def validate_format(self):
        allowed = ['.pdf', '.docx', '.doc', '.txt']
        import os
        _, ext = os.path.splitext(self.name)
        return ext.lower() in allowed

    def formatted_size(self):
        if self.size > 1024 * 1024:
            return f'{self.size / (1024*1024):.1f} MB'
        return f'{self.size // 1024} KB'
