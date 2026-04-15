from django.contrib import admin

# Register your models here.

from django.contrib.auth.admin import UserAdmin
from .models import User, ActivityLog


class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'branch', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('InvoSmart Info', {
            'fields': ('role', 'branch')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('InvoSmart Info', {
            'fields': ('role', 'branch')
        }),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(ActivityLog)
