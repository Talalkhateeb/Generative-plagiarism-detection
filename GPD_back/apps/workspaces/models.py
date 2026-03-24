"""
Workspaces App — Models
Class Diagram: workspaceMangt(-name, -u_id, -createdAt, -document d[], -sources sr[], -id, -total_uploads_today)
UC-3: Workspace Management
"""
from django.db import models
from django.conf import settings


class Workspace(models.Model):
    """
    workspaceMangt in class diagram.
    Belongs to a user. Contains sources and documents.
    """
    STATUS_CHOICES = [
        ('draft',    'Draft'),
        ('pending',  'Pending Analysis'),
        ('analyzed', 'Analyzed'),
    ]
    user               = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workspaces'
    )
    name               = models.CharField(max_length=255)
    status             = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    total_uploads_today = models.IntegerField(default=0)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

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


def source_upload_path(instance, filename):
    return f'workspaces/{instance.workspace.id}/sources/{filename}'


def document_upload_path(instance, filename):
    return f'workspaces/{instance.workspace.id}/documents/{filename}'


class Source(models.Model):
    """
    Class Diagram: source(-author, -content_snippet)
    Reference files uploaded to compare against.
    """
    workspace   = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='sources')
    file        = models.FileField(upload_to=source_upload_path)
    name        = models.CharField(max_length=255)           # original filename
    size        = models.PositiveBigIntegerField(default=0)  # bytes
    ext         = models.CharField(max_length=10)            # PDF, DOCX, etc.
    author      = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Source: {self.name} in {self.workspace.name}'

    def formatted_size(self):
        if self.size > 1024 * 1024:
            return f'{self.size / (1024*1024):.1f} MB'
        return f'{self.size // 1024} KB'


class Document(models.Model):
    """
    Class Diagram: document(-id, -type, -path, -size, -upload_date, -role)
    The file submitted for plagiarism checking.
    """
    ROLE_CHOICES = [('check', 'Document to Check')]

    workspace   = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='documents')
    file        = models.FileField(upload_to=document_upload_path)
    name        = models.CharField(max_length=255)
    size        = models.PositiveBigIntegerField(default=0)
    ext         = models.CharField(max_length=10)
    role        = models.CharField(max_length=10, choices=ROLE_CHOICES, default='check')
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Document: {self.name} in {self.workspace.name}'

    def validate_format(self):
        """Class Diagram: +validate_format()"""
        allowed = ['.pdf', '.docx', '.doc', '.txt']
        import os
        _, ext = os.path.splitext(self.name)
        return ext.lower() in allowed

    def formatted_size(self):
        if self.size > 1024 * 1024:
            return f'{self.size / (1024*1024):.1f} MB'
        return f'{self.size // 1024} KB'
