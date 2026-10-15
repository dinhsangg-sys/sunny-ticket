from django.db import models
class Agency(models.Model):
    legacy_id = models.CharField(max_length=120, unique=True)
    name = models.CharField(max_length=255)
    def __str__(self): return self.name
