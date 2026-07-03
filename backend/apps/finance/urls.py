from rest_framework.routers import DefaultRouter

from .views import ProfitViewSet, TransactionViewSet

router = DefaultRouter()
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("finance/profit", ProfitViewSet, basename="finance-profit")

urlpatterns = router.urls
