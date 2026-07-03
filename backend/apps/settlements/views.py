"""Thin viewsets for settlements: parse → call service/selector → respond."""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.selectors import parse_period

from . import selectors, services
from .filters import DebtFilter, TransferFilter
from .models import Debt, Settlement, Transfer
from .permissions import CanManageFinance, IsFinanceStaff
from .serializers import (
    ApproveSerializer,
    DebtSerializer,
    RejectSerializer,
    SettlementSerializer,
    SettleSerializer,
    TransferCreateSerializer,
    TransferSerializer,
)


class TransferViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Inter-business transfers (БАР-01 / ХОЛ-30). Thin → services/selectors."""

    queryset = Transfer.objects.none()  # real qs comes from selectors
    serializer_class = TransferSerializer
    filterset_class = TransferFilter
    search_fields = ["description"]
    ordering_fields = ["occurred_on", "amount", "created_at"]

    def get_queryset(self):
        return selectors.transfers_qs()

    def get_permissions(self):
        if self.action in ("create", "approve", "reject"):
            return [CanManageFinance()]
        return [IsFinanceStaff()]

    def create(self, request, *args, **kwargs):
        payload = TransferCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        transfer = services.create_transfer(
            from_business_id=data["from_business"],
            to_business_id=data["to_business"],
            amount=data["amount"],
            occurred_on=data["occurred_on"],
            actor=request.user,
            description=data["description"],
            is_barter=data["is_barter"],
        )
        return Response(TransferSerializer(transfer).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Approve the transfer and auto-book the debt (БАР-01 / ХОЛ-30)."""
        s = ApproveSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        debt = services.approve_transfer(transfer_id=pk, actor=request.user)
        return Response(DebtSerializer(debt).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        s = RejectSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        transfer = services.reject_transfer(
            transfer_id=pk, actor=request.user, reason=s.validated_data["reason"]
        )
        return Response(TransferSerializer(transfer).data)


class DebtViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Debts (БАР-02). Read-only + settle/registry actions."""

    queryset = Debt.objects.none()
    serializer_class = DebtSerializer
    filterset_class = DebtFilter
    ordering_fields = ["occurred_on", "amount", "outstanding", "created_at"]

    def get_queryset(self):
        return selectors.debts_qs()

    def get_permissions(self):
        if self.action == "settle":
            return [CanManageFinance()]
        return [IsFinanceStaff()]

    @action(detail=True, methods=["post"])
    def settle(self, request, pk=None):
        """Close (fully/partially) a debt (БАР-03)."""
        s = SettleSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        settlement = services.settle_debt(
            debt_id=pk,
            kind=data["kind"],
            amount=data["amount"],
            actor=request.user,
            occurred_on=data["occurred_on"],
            counter_debt_id=data.get("counter_debt"),
            note=data["note"],
        )
        return Response(
            SettlementSerializer(settlement).data, status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["get"])
    def registry(self, request):
        """Transparent debt register (БАР-02, feeds ФНС-12)."""
        date_from, date_to = parse_period(request.query_params)
        include_settled = request.query_params.get("include_settled") in ("1", "true", "True")
        rows = selectors.debt_registry(
            date_from=date_from, date_to=date_to, include_settled=include_settled
        )
        return Response(rows)


class SettlementViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Debt closings (БАР-03). Read-only."""

    queryset = Settlement.objects.none()
    serializer_class = SettlementSerializer
    permission_classes = [IsFinanceStaff]
    ordering_fields = ["occurred_on", "amount", "created_at"]

    def get_queryset(self):
        return selectors.settlements_qs()
