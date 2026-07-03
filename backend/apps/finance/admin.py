from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "id", "occurred_on", "business", "kind", "category", "amount",
        "method", "status", "is_barter",
    ]
    list_filter = ["kind", "status", "method", "is_barter", "business"]
    search_fields = ["counterparty", "note"]
    date_hierarchy = "occurred_on"
    autocomplete_fields = ["business", "category", "site_object"]
