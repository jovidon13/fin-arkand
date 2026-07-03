from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "actor", "content_type", "object_id", "created_at"]
    list_filter = ["action", "content_type"]
    search_fields = ["action", "object_id"]
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):  # append-only
        return False

    def has_change_permission(self, request, obj=None):
        return False
