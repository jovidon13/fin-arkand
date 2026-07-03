"""
Audit trail. Every money/status change is written here (financial invariant:
audit — who, what, when, before/after). Records are append-only.
"""
from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
        related_name="audit_entries",
    )
    action = models.CharField(max_length=100, db_index=True)  # e.g. "transfer.approved"

    content_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL
    )
    object_id = models.CharField(max_length=64, null=True, blank=True)
    target = GenericForeignKey("content_type", "object_id")

    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    meta = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("Запись аудита")
        verbose_name_plural = _("Журнал аудита")
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self) -> str:
        return f"{self.action} @ {self.created_at:%Y-%m-%d %H:%M}"

    # -- write API ----------------------------------------------------------- #
    @classmethod
    def record(
        cls,
        actor,
        action: str,
        target: models.Model | None = None,
        *,
        before: Any = None,
        after: Any = None,
        meta: Any = None,
    ) -> AuditLog:
        """Append an audit entry. Call inside the same transaction as the change."""
        ct = None
        oid = None
        if target is not None and target.pk is not None:
            ct = ContentType.objects.get_for_model(target.__class__)
            oid = str(target.pk)
        return cls.objects.create(
            actor=actor if getattr(actor, "pk", None) else None,
            action=action,
            content_type=ct,
            object_id=oid,
            before=before,
            after=after,
            meta=meta,
        )
