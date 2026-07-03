"""Thin cash viewsets — parse → call service/selector → respond (КАС-01…04)."""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.exceptions import DomainError

from . import selectors, services
from .filters import CashOperationFilter
from .models import CashOperation, CashRegister
from .permissions import (
    CanManageFinance,
    CashRegisterScoped,
    IsAdminRole,
    IsOwner,
)
from .serializers import (
    CashOperationCreateSerializer,
    CashOperationSerializer,
    CashRegisterSerializer,
    SetLimitSerializer,
)


class CashRegisterViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Cash registers (КАС-01). Visibility follows the isolation rule (КАС-04)."""

    queryset = CashRegister.objects.none()  # real qs comes from selectors
    serializer_class = CashRegisterSerializer
    filterset_fields = ["business", "is_active"]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        return selectors.registers_visible_to(self.request.user)

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update"):
            return [(IsAdminRole | CanManageFinance)()]
        if self.action == "set_limit":
            return [(IsOwner | IsAdminRole)()]
        # Reads: finance staff/owners see all; a cashier sees only their own
        # register(s). Isolation (КАС-04) is enforced by the filtered queryset
        # in get_queryset() plus object-level CashRegisterScoped on retrieve.
        return [CashRegisterScoped()]

    @action(detail=True, methods=["post"])
    def set_limit(self, request, pk=None):
        """Change the turnover limit of a register (КАС-03)."""
        s = SetLimitSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        register = services.set_turnover_limit(
            register_id=pk, limit=s.validated_data["limit"], actor=request.user
        )
        return Response(CashRegisterSerializer(register).data)

    @action(detail=True, methods=["get"])
    def balance(self, request, pk=None):
        """Current balance of a register (income − expense)."""
        self.get_object()  # enforces visibility/404 via the filtered queryset
        return Response({"register": int(pk), "balance": str(selectors.register_balance(pk))})


class CashOperationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Cash operations (КАС-02). Restricted to registers visible to the user (КАС-04)."""

    queryset = CashOperation.objects.none()
    serializer_class = CashOperationSerializer
    filterset_class = CashOperationFilter
    permission_classes = [CashRegisterScoped]
    search_fields = ["counterparty", "note"]
    ordering_fields = ["occurred_on", "amount", "created_at"]

    def get_queryset(self):
        visible = selectors.registers_visible_to(self.request.user)
        return selectors.operations_qs().filter(register__in=visible)

    def create(self, request, *args, **kwargs):
        payload = CashOperationCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data

        # КАС-04: a cashier may only post to a register they are responsible for.
        register = CashRegister.objects.filter(pk=data["register"]).first()
        if register is None:
            raise DomainError("cash_register_not_found", "Касса не найдена",
                              status_code=status.HTTP_404_NOT_FOUND)
        if not register.is_visible_to(request.user):
            raise DomainError(
                "cash_forbidden",
                "Нет доступа к этой кассе (КАС-04)",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        op = services.add_operation(
            register_id=data["register"],
            kind=data["kind"],
            amount=data["amount"],
            method=data["method"],
            occurred_on=data["occurred_on"],
            actor=request.user,
            counterparty=data["counterparty"],
            note=data["note"],
            idempotency_key=request.headers.get("Idempotency-Key"),
        )
        return Response(CashOperationSerializer(op).data, status=status.HTTP_201_CREATED)
