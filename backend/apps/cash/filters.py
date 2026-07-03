import django_filters as filters

from .models import CashOperation


class CashOperationFilter(filters.FilterSet):
    """List filters for cash operations (КАС-02): register, kind, method, date range."""

    date_from = filters.DateFilter(field_name="occurred_on", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="occurred_on", lookup_expr="lte")

    class Meta:
        model = CashOperation
        fields = ["register", "kind", "method", "date_from", "date_to"]
