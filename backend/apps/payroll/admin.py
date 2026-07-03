from django.contrib import admin

from .models import Employee, PayrollItem, PayrollRun, PayrollScheme


@admin.register(PayrollScheme)
class PayrollSchemeAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "base_fixed", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        "id", "full_name", "business", "salary_type", "base_salary",
        "is_salesperson", "scheme", "is_active",
    ]
    list_filter = ["salary_type", "is_salesperson", "is_active", "business"]
    search_fields = ["full_name", "position"]
    autocomplete_fields = ["business", "scheme", "user"]


@admin.register(PayrollRun)
class PayrollRunAdmin(admin.ModelAdmin):
    list_display = ["id", "year", "month", "status", "total", "approved_at", "paid_at"]
    list_filter = ["status", "year", "month"]
    search_fields = ["year", "month"]


@admin.register(PayrollItem)
class PayrollItemAdmin(admin.ModelAdmin):
    list_display = [
        "id", "run", "employee", "base_amount", "bonus_amount", "total_amount",
    ]
    list_filter = ["run"]
    search_fields = ["employee__full_name"]
    autocomplete_fields = ["run", "employee"]
