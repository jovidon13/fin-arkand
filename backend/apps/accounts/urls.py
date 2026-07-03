from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ArkandTokenObtainPairView,
    RoleViewSet,
    UserViewSet,
    me_view,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("roles", RoleViewSet, basename="role")

urlpatterns = [
    path("auth/token", ArkandTokenObtainPairView.as_view(), name="token-obtain"),
    path("auth/token/refresh", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/me", me_view, name="auth-me"),
    *router.urls,
]
