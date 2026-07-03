"""Validation + response shape for approvals (ХОЛ-20…24). No domain logic."""
from decimal import Decimal

from rest_framework import serializers

from apps.core.enums import VoteValue

from .models import ApprovalRequest, ApprovalVote


class ApprovalVoteSerializer(serializers.ModelSerializer):
    """Read representation of a single owner's vote."""

    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True, default=None)
    value_display = serializers.CharField(source="get_value_display", read_only=True)

    class Meta:
        model = ApprovalVote
        fields = ["id", "owner", "owner_name", "value", "value_display", "comment", "created_at"]


class ApprovalRequestSerializer(serializers.ModelSerializer):
    """Read representation. Amounts are strings (money-in-JSON contract)."""

    business_name = serializers.CharField(source="business.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    requested_by_name = serializers.CharField(
        source="requested_by.get_full_name", read_only=True, default=None
    )
    approvals_count = serializers.IntegerField(read_only=True)
    rejections_count = serializers.IntegerField(read_only=True)
    votes = ApprovalVoteSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = [
            "id", "business", "business_name", "amount", "purpose", "description",
            "category", "category_name", "status", "status_display",
            "required_votes", "approvals_count", "rejections_count",
            "requested_by", "requested_by_name", "decided_at", "occurred_on",
            "votes", "created_at",
        ]
        read_only_fields = ["status", "required_votes", "requested_by", "decided_at"]


class CreateRequestSerializer(serializers.Serializer):
    """Write payload → passed to ``services.create_request``."""

    business = serializers.IntegerField()
    amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=Decimal("0.01")
    )
    purpose = serializers.CharField(max_length=300)
    occurred_on = serializers.DateField()
    category = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")


class CastVoteSerializer(serializers.Serializer):
    """Write payload → passed to ``services.cast_vote``."""

    value = serializers.ChoiceField(choices=VoteValue.choices)
    comment = serializers.CharField(required=False, allow_blank=True, default="")
