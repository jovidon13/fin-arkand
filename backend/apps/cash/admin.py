from django.contrib import admin

from .models import CashOperation, CashRegister


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "code", "business", "turnover_limit", "is_active"]
    list_filter = ["is_active", "business"]
    search_fields = ["name", "code"]
    autocomplete_fields = ["business"]
    filter_horizontal = ["responsible"]


@admin.register(CashOperation)
class CashOperationAdmin(admin.ModelAdmin):
    list_display = [
        "id", "occurred_on", "register", "kind", "amount", "method",
        "counterparty", "is_deleted",
    ]
    list_filter = ["kind", "method", "is_deleted", "register"]
    search_fields = ["counterparty", "note"]
    date_hierarchy = "occurred_on"
    autocomplete_fields = ["register", "finance_transaction"]
