from django.contrib import admin

from .models import Business, City, ExpenseCategory, SiteObject


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "kind", "expense_limit", "is_active"]
    list_filter = ["kind", "is_active"]
    search_fields = ["name", "code"]


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(SiteObject)
class SiteObjectAdmin(admin.ModelAdmin):
    list_display = ["name", "business", "city", "is_active"]
    list_filter = ["business", "city", "is_active"]
    search_fields = ["name", "address"]


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_active"]
    search_fields = ["name", "code"]
