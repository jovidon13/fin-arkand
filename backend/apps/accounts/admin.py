from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ["username", "get_full_name", "role", "business", "is_active"]
    list_filter = ["role", "business", "is_active", "is_superuser"]
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("ARKAND", {"fields": ("role", "business", "phone")}),
    )
