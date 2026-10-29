from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    role = models.CharField(max_length=16, choices=[('admin','Quản trị'),('operator','Vận hành nội bộ'),('agency','Đại lý'),('counter','Nhân viên bán vé tại quầy')], default='agency')
    agency = models.ForeignKey('agencies.Agency', null=True, blank=True, on_delete=models.PROTECT)
