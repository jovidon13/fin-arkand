"""
Фото документов операций — при каждой денежной операции можно прикрепить
фото/скан чека, счёта, договора или накладной.

An ``OperationDocument`` attaches to any money operation (finance transaction,
cash operation, transfer …) via a generic relation, so one model serves every
domain. Files are soft-deleted with their parent operation logic; the file
itself lives under ``MEDIA_ROOT`` (local now; S3-compatible storage later).
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.enums import DocumentType
from apps.core.models import TimeStampedModel


class OperationDocument(TimeStampedModel):
    """A single attached document (фото/скан) tied to a money operation."""

    doc_type = models.CharField(
        max_length=16, choices=DocumentType.choices, default=DocumentType.OTHER,
        db_index=True,
    )
    file = models.FileField(upload_to="documents/%Y/%m/")
    original_name = models.CharField(max_length=255, blank=True)
    note = models.CharField(max_length=300, blank=True)

    # Generic link to the operation the document belongs to.
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    operation = GenericForeignKey("content_type", "object_id")

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
        related_name="uploaded_documents",
    )

    class Meta:
        verbose_name = _("Документ операции")
        verbose_name_plural = _("Документы операций")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_doc_type_display()} → {self.content_type.model}#{self.object_id}"
