from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsFinanceStaff, IsOwner

from . import services
from .filters import BusinessFilter, SiteObjectFilter
from .models import Business, City, ExpenseCategory, SiteObject
from .serializers import (
    BusinessSerializer,
    CitySerializer,
    ExpenseCategorySerializer,
    SetExpenseLimitSerializer,
    SiteObjectSerializer,
)


class ReferenceViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Read-only reference data available to any authenticated finance user."""

    permission_classes = [IsFinanceStaff]


class BusinessViewSet(ReferenceViewSet):
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    filterset_class = BusinessFilter
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]

    def get_permissions(self):
        # ХОЛ-21: only owners may change the «крупно/мелко» threshold/limit.
        if self.action == "set_expense_limit":
            return [IsOwner()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], url_path="expense-limit")
    def set_expense_limit(self, request, pk=None):
        """Change the business expense threshold (ХОЛ-21) — owners only."""
        s = SetExpenseLimitSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        business = services.set_expense_limit(
            business_id=pk, limit=s.validated_data["expense_limit"], actor=request.user
        )
        return Response(BusinessSerializer(business).data)


class CityViewSet(ReferenceViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    search_fields = ["name"]


class SiteObjectViewSet(ReferenceViewSet):
    queryset = SiteObject.objects.select_related("city", "business").all()
    serializer_class = SiteObjectSerializer
    filterset_class = SiteObjectFilter
    search_fields = ["name", "address"]


class ExpenseCategoryViewSet(ReferenceViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    search_fields = ["name", "code"]
