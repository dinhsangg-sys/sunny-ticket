from django.db import models
class Workspace(models.Model):
    data = models.JSONField(default=dict)
    revision = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
class Attachment(models.Model):
    key = models.CharField(max_length=200, unique=True)
    file = models.FileField(upload_to='campaigns/%Y/%m/')
    name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
