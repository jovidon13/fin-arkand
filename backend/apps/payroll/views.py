"""
Thin payroll viewsets (ЗРП-01…05): parse → call service/selector → respond.

Reads require finance staff; writes (scheme/employee CRUD, running/approving/
paying payroll) require finance managers.
"""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import selectors, services
from .filters import EmployeeFilter, PayrollItemFilter, PayrollRunFilter
from .models import Employee, PayrollItem, PayrollRun, PayrollScheme
from .permissions import CanManageFinance, IsFinanceStaff
from .serializers import (
    EmployeeSerializer,
    EmployeeWriteSerializer,
    PayrollItemSerializer,
    PayrollRunSerializer,
    PayrollSchemeSerializer,
    RunPayrollSerializer,
)


class PayrollSchemeViewSet(viewsets.ModelViewSet):
    """CRUD for flexible salary schemes (ЗРП-03)."""

    queryset = PayrollScheme.objects.all()
    serializer_class = PayrollSchemeSerializer
    permission_classes = [CanManageFinance]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]


class EmployeeViewSet(viewsets.ModelViewSet):
    """CRUD for employees (ЗРП-02, ЗРП-03). Reads for finance staff, writes for managers."""

    queryset = Employee.objects.none()  # real qs comes from selectors
    filterset_class = EmployeeFilter
    search_fields = ["full_name"]
    ordering_fields = ["full_name", "base_salary", "created_at"]

    def get_queryset(self):
        return selectors.employees_qs()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return EmployeeWriteSerializer
        return EmployeeSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsFinanceStaff()]
        return [CanManageFinance()]


class PayrollRunViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Monthly payroll runs (ЗРП-01). Create → ``services.run_payroll``."""

    queryset = PayrollRun.objects.none()  # real qs comes from selectors
    serializer_class = PayrollRunSerializer
    filterset_class = PayrollRunFilter
    ordering_fields = ["year", "month", "created_at"]

    def get_queryset(self):
        return selectors.runs_qs()

    def get_permissions(self):
        if self.action in ("create", "approve", "pay"):
            return [CanManageFinance()]
        return [IsFinanceStaff()]

    def create(self, request, *args, **kwargs):
        payload = RunPayrollSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        # JSON object keys are strings — coerce to int employee ids for the engine.
        raw_metrics = data.get("metrics_by_employee") or {}
        metrics_by_employee = {int(k): v for k, v in raw_metrics.items()}
        run = services.run_payroll(
            year=data["year"],
            month=data["month"],
            actor=request.user,
            metrics_by_employee=metrics_by_employee,
        )
        return Response(PayrollRunSerializer(run).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        run = services.approve_payroll(run_id=pk, actor=request.user)
        return Response(PayrollRunSerializer(run).data)

    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        run = services.mark_paid(run_id=pk, actor=request.user)
        return Response(PayrollRunSerializer(run).data)

    @action(detail=True, methods=["get"])
    def items(self, request, pk=None):
        qs = selectors.items_qs().filter(run_id=pk)
        page = self.paginate_queryset(qs)
        if page is not None:
            data = PayrollItemSerializer(page, many=True).data
            return self.get_paginated_response(data)
        return Response(PayrollItemSerializer(qs, many=True).data)


class PayrollItemViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Read-only access to run line items (ЗРП-01)."""

    queryset = PayrollItem.objects.none()  # real qs comes from selectors
    serializer_class = PayrollItemSerializer
    filterset_class = PayrollItemFilter
    permission_classes = [IsFinanceStaff]
    ordering_fields = ["total_amount", "created_at"]

    def get_queryset(self):
        return selectors.items_qs()
