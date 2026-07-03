from rest_framework.routers import DefaultRouter

from .views import (
    EmployeeViewSet,
    PayrollItemViewSet,
    PayrollRunViewSet,
    PayrollSchemeViewSet,
)

router = DefaultRouter(trailing_slash=False)
router.register("payroll-schemes", PayrollSchemeViewSet, basename="payroll-scheme")
router.register("employees", EmployeeViewSet, basename="employee")
router.register("payroll-runs", PayrollRunViewSet, basename="payroll-run")
router.register("payroll-items", PayrollItemViewSet, basename="payroll-item")

urlpatterns = router.urls
