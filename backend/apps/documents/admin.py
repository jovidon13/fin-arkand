from django.contrib import admin

from .models import OperationDocument


@admin.register(OperationDocument)
class OperationDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "doc_type", "content_type", "object_id", "uploaded_by", "created_at")
    list_filter = ("doc_type", "content_type")
    search_fields = ("original_name", "note")
