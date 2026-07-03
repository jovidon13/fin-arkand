from rest_framework import mixins, viewsets

from apps.accounts.permissions import IsFinanceStaff

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Read-only audit trail — finance staff / owners / admin."""

    queryset = AuditLog.objects.select_related("actor", "content_type").all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsFinanceStaff]
    filterset_fields = ["action", "actor", "content_type"]
    search_fields = ["action"]
    ordering_fields = ["created_at"]
