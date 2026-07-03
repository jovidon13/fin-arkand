from rest_framework.routers import DefaultRouter

from .views import ApprovalRequestViewSet

router = DefaultRouter(trailing_slash=False)
router.register("approval-requests", ApprovalRequestViewSet, basename="approval-request")

urlpatterns = router.urls
