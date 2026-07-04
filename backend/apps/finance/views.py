from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.permissions import IsOwner
from apps.core.money import stringify
from apps.core.selectors import parse_period

from . import selectors, services
from .filters import TransactionFilter
from .models import Transaction
from .permissions import CanManageFinance, IsFinanceStaff
from .serializers import (
    ConfirmSerializer,
    RejectSerializer,
    TransactionCreateSerializer,
    TransactionSerializer,
)


class TransactionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Income/expense ledger (ФНС-01…04). Thin viewset → services/selectors."""

    queryset = Transaction.objects.none()  # real qs comes from selectors
    serializer_class = TransactionSerializer
    filterset_class = TransactionFilter
    search_fields = ["counterparty", "note"]
    ordering_fields = ["occurred_on", "amount", "created_at"]

    def get_queryset(self):
        return selectors.transactions_qs()

    def get_permissions(self):
        # Owners give the final «крупная» confirmation (шаг владельца); финансисты
        # create/check/reject/void and may also confirm directly.
        if self.action == "confirm":
            return [(CanManageFinance | IsOwner)()]
        if self.action in ("create", "check", "reject", "void"):
            return [CanManageFinance()]
        return [IsFinanceStaff()]

    def create(self, request, *args, **kwargs):
        payload = TransactionCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        tx = services.create_transaction(
            business_id=data["business"],
            kind=data["kind"],
            amount=data["amount"],
            method=data["method"],
            occurred_on=data["occurred_on"],
            actor=request.user,
            category_id=data.get("category"),
            site_object_id=data.get("site_object"),
            counterparty=data["counterparty"],
            note=data["note"],
            is_barter=data["is_barter"],
            source=data["source"],
            is_disbursement=data["is_disbursement"],
            recipient_manager_id=data.get("recipient_manager"),
            status=data["status"],
            idempotency_key=request.headers.get("Idempotency-Key"),
        )
        return Response(TransactionSerializer(tx).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def check(self, request, pk=None):
        """Accountant check (проверил бухгалтер) — второй шаг цепочки."""
        s = ConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        key = s.validated_data["idempotency_key"] or request.headers.get("Idempotency-Key")
        tx = services.check_transaction(tx_id=pk, actor=request.user, idempotency_key=key)
        return Response(TransactionSerializer(tx).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        s = ConfirmSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        # Крупную операцию (выше порога бизнеса) подтверждает ТОЛЬКО владелец —
        # бухгалтер не может обойти шаг владельца, даже имея право confirm.
        tx0 = selectors.transactions_qs().filter(pk=pk).first()
        user = request.user
        if (
            tx0 is not None
            and tx0.requires_owner
            and not (user.is_owner or user.is_superuser)
        ):
            raise PermissionDenied(
                "Крупную операцию подтверждает только владелец (шаг владельца)."
            )
        key = s.validated_data["idempotency_key"] or request.headers.get("Idempotency-Key")
        tx = services.confirm_transaction(tx_id=pk, actor=request.user, idempotency_key=key)
        return Response(TransactionSerializer(tx).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        s = RejectSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        tx = services.reject_transaction(
            tx_id=pk, actor=request.user, reason=s.validated_data["reason"]
        )
        return Response(TransactionSerializer(tx).data)

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        s = RejectSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        tx = services.void_transaction(
            tx_id=pk, actor=request.user, reason=s.validated_data["reason"]
        )
        return Response(TransactionSerializer(tx).data)


class ProfitViewSet(viewsets.ViewSet):
    """Profit per business over a period (ФНС-04)."""

    permission_classes = [IsFinanceStaff]

    def list(self, request):
        date_from, date_to = parse_period(request.query_params)
        rows = selectors.profit_by_business(date_from=date_from, date_to=date_to)
        return Response(stringify(rows))
