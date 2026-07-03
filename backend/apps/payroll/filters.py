"""django-filter FilterSets for payroll list endpoints."""
import django_filters as filters

from .models import Employee, PayrollItem, PayrollRun


class EmployeeFilter(filters.FilterSet):
    class Meta:
        model = Employee
        fields = ["business", "salary_type", "is_salesperson", "is_active"]


class PayrollRunFilter(filters.FilterSet):
    class Meta:
        model = PayrollRun
        fields = ["year", "month", "status"]


class PayrollItemFilter(filters.FilterSet):
    class Meta:
        model = PayrollItem
        fields = ["run", "employee"]
