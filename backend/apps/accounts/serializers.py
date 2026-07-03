from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Role, User


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "code", "name"]


class UserSerializer(serializers.ModelSerializer):
    role_code = serializers.CharField(read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True, default=None)
    business_name = serializers.CharField(source="business.name", read_only=True, default=None)
    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "full_name", "email",
            "phone", "role", "role_code", "role_name", "business", "business_name",
            "is_active",
        ]


class MeSerializer(UserSerializer):
    is_finance_staff = serializers.BooleanField(read_only=True)
    can_manage_finance = serializers.BooleanField(read_only=True)
    is_owner = serializers.BooleanField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            "is_finance_staff", "can_manage_finance", "is_owner", "is_superuser",
        ]


class ArkandTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT login that also returns the current user profile in the response."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role_code
        token["name"] = user.get_full_name() or user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = MeSerializer(self.user).data
        return data
