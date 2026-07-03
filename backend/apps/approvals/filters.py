import django_filters as filters

from .models import ApprovalRequest


class ApprovalRequestFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="occurred_on", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="occurred_on", lookup_expr="lte")

    class Meta:
        model = ApprovalRequest
        fields = ["business", "status", "category", "date_from", "date_to"]
