from rest_framework import mixins, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Role, RoleCode, User
from .permissions import IsAdminRole, IsFinanceStaff
from .serializers import (
    ArkandTokenObtainPairSerializer,
    MeSerializer,
    RoleSerializer,
    UserSerializer,
)


class ArkandTokenObtainPairView(TokenObtainPairView):
    serializer_class = ArkandTokenObtainPairSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Current authenticated user profile + capabilities."""
    return Response(MeSerializer(request.user).data)


@api_view(["GET"])
@permission_classes([IsFinanceStaff])
def owners_view(request):
    """Руководители (владельцы) — for the «выдача руководителю» recipient picker.

    Readable by all finance staff (not just admins) since accountants create
    disbursements. Returns a lightweight id/name list."""
    owners = User.objects.filter(role__code=RoleCode.OWNER, is_active=True).order_by(
        "first_name", "last_name", "username"
    )
    return Response([
        {"id": u.id, "full_name": u.get_full_name() or u.username, "username": u.username}
        for u in owners
    ])


class UserViewSet(viewsets.ModelViewSet):
    """User management — administrator only."""

    queryset = User.objects.select_related("role", "business").all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
    filterset_fields = ["role", "business", "is_active"]
    search_fields = ["username", "first_name", "last_name", "email"]
    ordering_fields = ["username", "date_joined"]


class RoleViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
