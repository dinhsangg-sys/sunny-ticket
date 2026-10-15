from django.contrib import admin
from .models import AuditLog
@admin.register(AuditLog)
class AuditAdmin(admin.ModelAdmin):
    list_display = ('created_at','user','action','revision')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
