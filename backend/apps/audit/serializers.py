from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.get_full_name", read_only=True, default=None)
    target_type = serializers.CharField(source="content_type.model", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "id", "action", "actor", "actor_name", "target_type", "object_id",
            "before", "after", "meta", "created_at",
        ]
