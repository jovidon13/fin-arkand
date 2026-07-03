"""
Core models: base abstractions + holding reference data (Часть 0).

Financial invariants live here as base classes so every money-bearing model
inherits soft-delete + timestamps consistently.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .enums import BusinessKind


# --------------------------------------------------------------------------- #
# Abstract base models
# --------------------------------------------------------------------------- #
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self) -> SoftDeleteQuerySet:
        return self.filter(is_deleted=False)

    def dead(self) -> SoftDeleteQuerySet:
        return self.filter(is_deleted=True)


class AliveManager(models.Manager):
    """Default manager — hides soft-deleted rows (financial records are never
    physically deleted; they are marked, for reporting and history)."""

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    objects = AliveManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def soft_delete(self, actor=None) -> None:
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = actor
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at"])


class MoneyBaseModel(TimeStampedModel, SoftDeleteModel):
    """Base for money-bearing records: timestamps + soft-delete."""

    class Meta:
        abstract = True


# --------------------------------------------------------------------------- #
# Holding reference data (Часть 0)
# --------------------------------------------------------------------------- #
class Business(TimeStampedModel):
    """A holding business or shared department (ХОЛ-01)."""

    code = models.SlugField(unique=True, help_text=_("Стабильный машинный код"))
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=32, choices=BusinessKind.choices)
    # ХОЛ-20: per-business expense limit; ХОЛ-21 threshold below is the "large" cut-off.
    expense_limit = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        help_text=_("Порог 'крупно/мелко': расход выше требует согласования владельцев"),
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Бизнес")
        verbose_name_plural = _("Бизнесы")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class City(TimeStampedModel):
    """Cross-cutting 'city' dimension (ХОЛ-06)."""

    name = models.CharField(max_length=120, unique=True)

    class Meta:
        verbose_name = _("Город")
        verbose_name_plural = _("Города")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class SiteObject(TimeStampedModel):
    """Cross-cutting 'object' dimension (ХОЛ-06) — a construction/site object."""

    name = models.CharField(max_length=200)
    city = models.ForeignKey(City, null=True, blank=True, on_delete=models.PROTECT,
                             related_name="objects_at")
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name="site_objects")
    address = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Объект")
        verbose_name_plural = _("Объекты")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ExpenseCategory(TimeStampedModel):
    """Expense article (ФНС-02): материалы, зарплата, налоги, электроэнергия,
    ремонт техники, транспорт, прочее …"""

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Статья расходов")
        verbose_name_plural = _("Статьи расходов")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class IdempotencyKey(models.Model):
    """Idempotency guard: a repeated request must not create a second money
    operation (financial invariant — idempotency)."""

    key = models.CharField(max_length=200)
    scope = models.CharField(max_length=120)
    # Primary key of the object created by the guarded request, so a repeated
    # request can return the original instead of creating a duplicate.
    result_pk = models.PositiveBigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Ключ идемпотентности")
        verbose_name_plural = _("Ключи идемпотентности")
        constraints = [
            models.UniqueConstraint(fields=["scope", "key"], name="uq_idempotency_scope_key")
        ]

    def __str__(self) -> str:
        return f"{self.scope}:{self.key}"
