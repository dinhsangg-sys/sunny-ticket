from django.contrib import admin
from .models import SePayIntent, SePayTransaction

@admin.register(SePayIntent)
class SePayIntentAdmin(admin.ModelAdmin):
    list_display=('booking_code','code','amount','mode','state','owner','created_at','expires_at')
    list_filter=('state','mode')
    search_fields=('booking_code','code')
    def has_add_permission(self,request):return False
    def has_change_permission(self,request,obj=None):return False
    def has_delete_permission(self,request,obj=None):return False

@admin.register(SePayTransaction)
class SePayTransactionAdmin(admin.ModelAdmin):
    list_display=('transaction_id','intent','amount','state','reason','received_at')
    list_filter=('state',)
    search_fields=('transaction_id','intent__booking_code','intent__code','reference_code')
    def has_add_permission(self,request):return False
    def has_change_permission(self,request,obj=None):return False
    def has_delete_permission(self,request,obj=None):return False
