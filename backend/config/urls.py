"""
Root URL configuration.

Every domain app exposes ``apps.<app>.urls`` with a DRF router. They are all
mounted under the versioned ``/api/v1/`` prefix (API convention, design doc §07).
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


def healthz(_request):
    """Unauthenticated liveness probe for the platform (Railway health check)."""
    return JsonResponse({"status": "ok"})

api_v1 = [
    path("", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.finance.urls")),
    path("", include("apps.cash.urls")),
    path("", include("apps.settlements.urls")),
    path("", include("apps.payroll.urls")),
    path("", include("apps.approvals.urls")),
    path("", include("apps.reports.urls")),
    path("", include("apps.audit.urls")),
]

urlpatterns = [
    path("healthz", healthz),
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1, "api"), namespace="v1")),
    # OpenAPI schema + Swagger UI
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
