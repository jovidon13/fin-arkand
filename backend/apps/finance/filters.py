import django_filters as filters

from .models import Transaction


class TransactionFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="occurred_on", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="occurred_on", lookup_expr="lte")
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr="gte")
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr="lte")

    class Meta:
        model = Transaction
        fields = [
            "business", "kind", "category", "method", "status",
            "site_object", "is_barter", "date_from", "date_to",
            "min_amount", "max_amount",
        ]
