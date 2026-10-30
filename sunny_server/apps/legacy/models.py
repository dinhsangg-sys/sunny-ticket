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
    email_subject = models.CharField(max_length=200,blank=True)
    email_body = models.TextField(blank=True)
    email_state = models.CharField(max_length=16,default='idle')
    emailed_at = models.DateTimeField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    booking_version = models.PositiveIntegerField(default=1)
    superseded_at = models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['owner','booking_id','source_hash'],name='unique_counter_source')]

class CounterIssuedQR(models.Model):
    qr_hash = models.CharField(max_length=64,primary_key=True)
    booking_id = models.CharField(max_length=120)
    batch = models.ForeignKey(CounterTicketBatch,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class SePayIntent(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    owner = models.ForeignKey('accounts.User',on_delete=models.PROTECT)
    booking_id = models.CharField(max_length=120)
    booking_code = models.CharField(max_length=120)
    booking_version = models.PositiveIntegerField()
    booking_fingerprint = models.CharField(max_length=64)
    code = models.CharField(max_length=40,unique=True)
    amount = models.DecimalField(max_digits=18,decimal_places=2)
    bank_code = models.CharField(max_length=64)
    gateway = models.CharField(max_length=64)
    account_number = models.CharField(max_length=64)
    account_name = models.CharField(max_length=160)
    mode = models.CharField(max_length=8,default='test')
    state = models.CharField(max_length=20,default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    paid_at = models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['booking_id'],condition=models.Q(state='pending'),name='one_pending_sepay_intent')]

class SePayTransaction(models.Model):
    transaction_id = models.CharField(max_length=64,primary_key=True)
    intent = models.ForeignKey(SePayIntent,null=True,blank=True,on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=18,decimal_places=2)
    gateway = models.CharField(max_length=64)
    account_number = models.CharField(max_length=64)
    content = models.TextField(blank=True)
    reference_code = models.CharField(max_length=160,blank=True)
    transaction_at = models.DateTimeField(null=True,blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=20,default='review')
    reason = models.CharField(max_length=240,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['intent'],condition=models.Q(state='applied'),name='one_applied_sepay_transaction')]
