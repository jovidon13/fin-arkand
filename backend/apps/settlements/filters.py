import django_filters as filters

from .models import Debt, Transfer


class TransferFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="occurred_on", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="occurred_on", lookup_expr="lte")

    class Meta:
        model = Transfer
        fields = [
            "from_business", "to_business", "status", "is_barter",
            "date_from", "date_to",
        ]


class DebtFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="occurred_on", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="occurred_on", lookup_expr="lte")

    class Meta:
        model = Debt
        fields = [
            "debtor", "creditor", "status", "is_barter",
            "date_from", "date_to",
        ]
