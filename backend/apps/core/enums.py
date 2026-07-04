"""Shared enumerations used across finance domains (see CONTRACT.md §1.4)."""
from django.db import models
from django.utils.translation import gettext_lazy as _


class BusinessKind(models.TextChoices):
    DEVELOPER = "developer", _("Застройщик")
    DESIGN = "design", _("Проектная компания")
    CONCRETE_PLANT = "concrete_plant", _("Бетонный завод")
    CRUSHING_PLANT = "crushing_plant", _("Щебёночный завод")
    SUPPLY = "supply", _("Снабжение")
    FINANCE = "finance", _("Финансы")


class TxKind(models.TextChoices):
    INCOME = "income", _("Приход")
    EXPENSE = "expense", _("Расход")


class PayMethod(models.TextChoices):
    CASH = "cash", _("Наличные")
    TRANSFER = "transfer", _("Перевод")


class TxStatus(models.TextChoices):
    DRAFT = "draft", _("Черновик")
    PENDING = "pending", _("Ожидает проверки бухгалтера")
    AWAITING_OWNER = "awaiting_owner", _("Ожидает подтверждения владельца")
    CONFIRMED = "confirmed", _("Подтверждён")
    REJECTED = "rejected", _("Отклонён")
    VOID = "void", _("Аннулирован")


class DocumentType(models.TextChoices):
    """Photo/scan of a document attached to a money operation (фото документов)."""

    RECEIPT = "receipt", _("Чек")
    INVOICE = "invoice", _("Счёт")
    CONTRACT = "contract", _("Договор")
    WAYBILL = "waybill", _("Накладная")
    OTHER = "other", _("Прочее")


class ExternalDebtDirection(models.TextChoices):
    """Дебиторская / кредиторская задолженность с внешними контрагентами."""

    RECEIVABLE = "receivable", _("Нам должны")   # дебиторка — кто должен компании
    PAYABLE = "payable", _("Мы должны")          # кредиторка — кому должна компания


class DebtStatus(models.TextChoices):
    OPEN = "open", _("Открыт")
    PARTIALLY_SETTLED = "partially_settled", _("Частично закрыт")
    SETTLED = "settled", _("Закрыт")


class SettlementKind(models.TextChoices):
    NETTING = "netting", _("Взаимозачёт")
    REPAYMENT = "repayment", _("Возврат")
    BARTER = "barter", _("Бартер")


class TransferStatus(models.TextChoices):
    PENDING = "pending", _("Ожидает одобрения")
    APPROVED = "approved", _("Одобрена")
    REJECTED = "rejected", _("Отклонена")


class ApprovalStatus(models.TextChoices):
    PENDING = "pending", _("Ожидает")
    APPROVED = "approved", _("Одобрено")
    REJECTED = "rejected", _("Отклонено")


class VoteValue(models.TextChoices):
    APPROVE = "approve", _("Добро")
    REJECT = "reject", _("Нет")


class PayrollStatus(models.TextChoices):
    DRAFT = "draft", _("Черновик")
    CALCULATED = "calculated", _("Рассчитана")
    APPROVED = "approved", _("Утверждена")
    PAID = "paid", _("Выплачена")


class EmployeeSalaryType(models.TextChoices):
    OBJECT = "object", _("Объектный")
    ADMIN = "admin", _("Административный")
