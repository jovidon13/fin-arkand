"""Serializers for payroll: validation + response shape. Amounts are strings."""
from rest_framework import serializers

from .models import Employee, PayrollItem, PayrollRun, PayrollScheme


class PayrollSchemeSerializer(serializers.ModelSerializer):
    """Read/write representation of a flexible salary scheme (ЗРП-03)."""

    class Meta:
        model = PayrollScheme
        fields = [
            "id", "name", "description", "base_fixed", "rules", "is_active",
            "created_at", "updated_at",
        ]


class EmployeeSerializer(serializers.ModelSerializer):
    """Read representation of an employee (ЗРП-02, ЗРП-03)."""

    business_name = serializers.CharField(source="business.name", read_only=True)
    salary_type_display = serializers.CharField(
        source="get_salary_type_display", read_only=True
    )
    scheme_name = serializers.CharField(source="scheme.name", read_only=True, default=None)

    class Meta:
        model = Employee
        fields = [
            "id", "user", "full_name", "business", "business_name", "position",
            "salary_type", "salary_type_display", "base_salary", "is_salesperson",
            "scheme", "scheme_name", "is_active", "created_at", "updated_at",
        ]


class EmployeeWriteSerializer(serializers.ModelSerializer):
    """Write payload for creating/updating an employee."""

    class Meta:
        model = Employee
        fields = [
            "user", "full_name", "business", "position", "salary_type",
            "base_salary", "is_salesperson", "scheme", "is_active",
        ]


class PayrollItemSerializer(serializers.ModelSerializer):
    """Read representation of a run line; decimals rendered as strings."""

    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    base_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    bonus_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = PayrollItem
        fields = [
            "id", "run", "employee", "employee_name", "base_amount",
            "bonus_amount", "total_amount", "details", "metrics", "created_at",
        ]


class PayrollRunSerializer(serializers.ModelSerializer):
    """Read representation of a run with an items count (ЗРП-01)."""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    items_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = PayrollRun
        fields = [
            "id", "year", "month", "status", "status_display", "total",
            "items_count", "created_by", "approved_by", "approved_at",
            "paid_at", "created_at", "updated_at",
        ]


class RunPayrollSerializer(serializers.Serializer):
    """Write payload for ``services.run_payroll`` (ЗРП-01)."""

    year = serializers.IntegerField()
    month = serializers.IntegerField(min_value=1, max_value=12)
    metrics_by_employee = serializers.DictField(required=False, default=dict)
