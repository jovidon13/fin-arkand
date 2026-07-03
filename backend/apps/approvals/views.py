"""Thin viewset for approvals (ХОЛ-20…24): parse → service/selector → respond."""
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import selectors, services
from .filters import ApprovalRequestFilter
from .models import ApprovalRequest
from .permissions import CanManageFinance, IsFinanceStaff, IsOwner
from .serializers import (
    ApprovalRequestSerializer,
    CastVoteSerializer,
    CreateRequestSerializer,
)


class ApprovalRequestViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Large-expense approval requests (ХОЛ-20…24). Thin → services/selectors."""

    queryset = ApprovalRequest.objects.none()  # real qs comes from selectors
    serializer_class = ApprovalRequestSerializer
    filterset_class = ApprovalRequestFilter
    search_fields = ["purpose", "description"]
    ordering_fields = ["occurred_on", "amount", "created_at"]

    def get_queryset(self):
        return selectors.requests_qs()

    def get_permissions(self):
        if self.action == "create":
            return [CanManageFinance()]
        if self.action == "vote":
            return [IsOwner()]
        return [IsFinanceStaff()]

    def create(self, request, *args, **kwargs):
        payload = CreateRequestSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        req = services.create_request(
            business_id=data["business"],
            amount=data["amount"],
            purpose=data["purpose"],
            actor=request.user,
            occurred_on=data["occurred_on"],
            category_id=data.get("category"),
            description=data["description"],
        )
        return Response(ApprovalRequestSerializer(req).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def vote(self, request, pk=None):
        """Owner casts a vote on a pending request (ХОЛ-22/23)."""
        s = CastVoteSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        req = services.cast_vote(
            request_id=pk,
            owner=request.user,
            value=s.validated_data["value"],
            comment=s.validated_data["comment"],
        )
        return Response(ApprovalRequestSerializer(req).data)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        """Requests awaiting a decision. For owners, only those they must still
        vote on (ХОЛ-22); for other finance staff, all pending requests."""
        user = request.user
        if getattr(user, "is_owner", False) and not user.is_superuser:
            qs = selectors.pending_for_owner(user)
        else:
            qs = selectors.pending_requests()
        qs = self.filter_queryset(qs)
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(ApprovalRequestSerializer(page, many=True).data)
        return Response(ApprovalRequestSerializer(qs, many=True).data)
