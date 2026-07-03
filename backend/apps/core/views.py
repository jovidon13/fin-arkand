from rest_framework import mixins, viewsets

from apps.accounts.permissions import IsFinanceStaff

from .filters import BusinessFilter, SiteObjectFilter
from .models import Business, City, ExpenseCategory, SiteObject
from .serializers import (
    BusinessSerializer,
    CitySerializer,
    ExpenseCategorySerializer,
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
