from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin
@admin.register(User)
class SunnyUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Sunny',{'fields':('role','agency')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Sunny',{'fields':('role','agency')}),)
    list_display = ('username','role','agency','is_active','is_staff')
    def get_readonly_fields(self,request,obj=None):
        # Prevent delegated user editing from silently granting superuser/full workspace.
        if request.user.is_superuser: return ()
        return ('is_superuser','is_staff','groups','user_permissions','role','agency')

admin.site.unregister(Group)
@admin.register(Group)
class SunnyGroupAdmin(GroupAdmin):
    def formfield_for_manytomany(self,db_field,request,**kwargs):
        if db_field.name=='permissions' and not request.user.is_superuser:
            from django.contrib.auth.models import Permission
            # Delegated group managers may only assign permissions they themselves hold.
            ids=[p.pk for p in Permission.objects.select_related('content_type') if request.user.has_perm(p.content_type.app_label+'.'+p.codename)]
            kwargs['queryset']=Permission.objects.filter(pk__in=ids)
        return super().formfield_for_manytomany(db_field,request,**kwargs)
