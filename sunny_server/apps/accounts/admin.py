from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
@admin.register(User)
class SunnyUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Sunny',{'fields':('role','agency')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Sunny',{'fields':('role','agency')}),)
    list_display = ('username','role','agency','is_active','is_staff')
