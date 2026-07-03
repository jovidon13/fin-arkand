from django.contrib import admin

from .models import Debt, Settlement, Transfer


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = [
        "id", "occurred_on", "from_business", "to_business", "amount",
        "status", "is_barter", "approved_at",
    ]
    list_filter = ["status", "is_barter", "from_business", "to_business"]
    search_fields = ["description"]
    date_hierarchy = "occurred_on"
    autocomplete_fields = ["from_business", "to_business"]


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = [
        "id", "occurred_on", "debtor", "creditor", "amount",
        "outstanding", "status", "is_barter",
    ]
    list_filter = ["status", "is_barter", "debtor", "creditor"]
    search_fields = ["debtor__name", "creditor__name"]
    date_hierarchy = "occurred_on"
    autocomplete_fields = ["debtor", "creditor", "source_transfer"]


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ["id", "occurred_on", "debt", "kind", "amount", "counter_debt"]
    list_filter = ["kind"]
    date_hierarchy = "occurred_on"
    autocomplete_fields = ["debt", "counter_debt"]
