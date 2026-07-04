from rest_framework.routers import DefaultRouter

from .views import (
    DebtViewSet,
    ExternalDebtViewSet,
    SettlementViewSet,
    TransferViewSet,
)

router = DefaultRouter(trailing_slash=False)
router.register("transfers", TransferViewSet, basename="transfer")
router.register("debts", DebtViewSet, basename="debt")
router.register("settlements", SettlementViewSet, basename="settlement")
router.register("external-debts", ExternalDebtViewSet, basename="external-debt")

urlpatterns = router.urls
