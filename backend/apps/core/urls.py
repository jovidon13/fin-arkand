from rest_framework.routers import DefaultRouter

from .views import (
    BusinessViewSet,
    CityViewSet,
    ExpenseCategoryViewSet,
    SiteObjectViewSet,
)

router = DefaultRouter()
router.register("businesses", BusinessViewSet, basename="business")
router.register("cities", CityViewSet, basename="city")
router.register("site-objects", SiteObjectViewSet, basename="site-object")
router.register("expense-categories", ExpenseCategoryViewSet, basename="expense-category")

urlpatterns = router.urls
