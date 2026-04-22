from django.db import models

class Document(models.Model):
    user_id = models.IntegerField()  # later you can link to User model
    file_name = models.CharField(max_length=255)
    file_url = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return self.file_name