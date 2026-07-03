from rest_framework import mixins, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Role, User
from .permissions import IsAdminRole
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
