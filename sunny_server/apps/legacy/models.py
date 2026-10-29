import uuid
from django.db import models
from .permission_names import PERMISSIONS
class Workspace(models.Model):
    data = models.JSONField(default=dict)
    revision = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        permissions = PERMISSIONS
class Attachment(models.Model):
    key = models.CharField(max_length=200, unique=True)
    file = models.FileField(upload_to='campaigns/%Y/%m/')
    name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)

class CounterTicketBatch(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    owner = models.ForeignKey('accounts.User',on_delete=models.PROTECT)
    booking_id = models.CharField(max_length=120)
    source_name = models.CharField(max_length=255)
    source_hash = models.CharField(max_length=64)
    rows = models.JSONField(default=list)
    selected = models.JSONField(default=list)
    output_hash = models.CharField(max_length=64,blank=True)
    customer_email = models.EmailField(blank=True)
    email_state = models.CharField(max_length=16,default='idle')
    emailed_at = models.DateTimeField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['owner','booking_id','source_hash'],name='unique_counter_source')]

class CounterIssuedQR(models.Model):
    qr_hash = models.CharField(max_length=64,primary_key=True)
    booking_id = models.CharField(max_length=120)
    batch = models.ForeignKey(CounterTicketBatch,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
