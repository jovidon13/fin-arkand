"""Serializers for operation documents (фото документов)."""
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from apps.core.enums import DocumentType

from .models import OperationDocument

#: Operations a document may be attached to → their app_label.model.
ALLOWED_TARGETS = {
    "transaction": ("finance", "transaction"),
    "cashoperation": ("cash", "cashoperation"),
    "transfer": ("settlements", "transfer"),
    "externaldebt": ("settlements", "externaldebt"),
}


class OperationDocumentSerializer(serializers.ModelSerializer):
    doc_type_display = serializers.CharField(source="get_doc_type_display", read_only=True)
    file_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(
        source="uploaded_by.get_full_name", read_only=True, default=None
    )
    operation_type = serializers.CharField(source="content_type.model", read_only=True)

    class Meta:
        model = OperationDocument
        fields = [
            "id", "doc_type", "doc_type_display", "file", "file_url",
            "original_name", "note", "operation_type", "object_id",
            "uploaded_by", "uploaded_by_name", "created_at",
        ]
        read_only_fields = ["uploaded_by", "original_name"]

    def get_file_url(self, obj) -> str | None:
        if not obj.file:
            return None
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url


class OperationDocumentCreateSerializer(serializers.Serializer):
    """Multipart upload payload. ``target`` names the operation kind."""

    target = serializers.ChoiceField(choices=sorted(ALLOWED_TARGETS.keys()))
    object_id = serializers.IntegerField(min_value=1)
    doc_type = serializers.ChoiceField(choices=DocumentType.choices, default=DocumentType.OTHER)
    file = serializers.FileField()
    note = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        app_label, model = ALLOWED_TARGETS[attrs["target"]]
        try:
            ct = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist as exc:  # pragma: no cover - defensive
            raise serializers.ValidationError(
                {"target": "Неизвестный тип операции"}
            ) from exc
        model_cls = ct.model_class()
        if not model_cls._default_manager.filter(pk=attrs["object_id"]).exists():
            raise serializers.ValidationError({"object_id": "Операция не найдена"})
        attrs["content_type"] = ct
        return attrs
