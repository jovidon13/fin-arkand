from django.contrib import admin

from .models import ApprovalRequest, ApprovalVote


class ApprovalVoteInline(admin.TabularInline):
    model = ApprovalVote
    extra = 0
    autocomplete_fields = ["owner"]
    readonly_fields = ["created_at"]


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = [
        "id", "occurred_on", "business", "purpose", "amount", "status",
        "required_votes", "decided_at",
    ]
    list_filter = ["status", "business", "category"]
    search_fields = ["purpose", "description"]
    date_hierarchy = "occurred_on"
    autocomplete_fields = ["business", "category", "requested_by"]
    inlines = [ApprovalVoteInline]


@admin.register(ApprovalVote)
class ApprovalVoteAdmin(admin.ModelAdmin):
    list_display = ["id", "request", "owner", "value", "created_at"]
    list_filter = ["value"]
    autocomplete_fields = ["request", "owner"]
