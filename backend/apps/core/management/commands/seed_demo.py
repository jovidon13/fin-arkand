"""
Seed realistic demo data for the ARKAND holding finance CRM.

Idempotent for reference data & users (get_or_create). Operational data
(transactions, cash ops, transfers/debts, payroll, approvals) is created once —
guarded by an existence check — so re-running does not duplicate money records.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --reset   # wipe operational data first
"""
from __future__ import annotations

import datetime as dt
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Role, RoleCode
from apps.approvals import services as approval_services
from apps.approvals.models import ApprovalRequest
from apps.cash import services as cash_services
from apps.cash.models import CashRegister
from apps.core.enums import (
    BusinessKind,
    PayMethod,
    SettlementKind,
    TxKind,
    TxStatus,
    VoteValue,
)
from apps.core.models import Business, City, ExpenseCategory, SiteObject
from apps.finance import services as finance_services
from apps.finance.models import Transaction
from apps.payroll import services as payroll_services
from apps.payroll.models import Employee, PayrollScheme
from apps.settlements import services as settlement_services

User = get_user_model()
PASSWORD = "arkand2026"

BUSINESSES = [
    ("developer", "Застройщик", BusinessKind.DEVELOPER, 50000),
    ("design", "Проектная компания", BusinessKind.DESIGN, 30000),
    ("concrete", "Бетонный завод", BusinessKind.CONCRETE_PLANT, 40000),
    ("crushing", "Щебёночный завод", BusinessKind.CRUSHING_PLANT, 40000),
    ("supply", "Снабжение", BusinessKind.SUPPLY, 20000),
    ("finance", "Финансовый отдел", BusinessKind.FINANCE, 0),
]

CATEGORIES = [
    ("materials", "Закупка сырья / материалов"),
    ("salary", "Зарплата"),
    ("taxes", "Налоги"),
    ("electricity", "Электроэнергия"),
    ("repair", "Ремонт техники"),
    ("transport", "Транспорт"),
    ("other", "Прочее"),
]


class Command(BaseCommand):
    help = "Наполнить БД демо-данными холдинга ARKAND"

    def add_arguments(self, parser) -> None:
        parser.add_argument("--reset", action="store_true", help="Очистить операционные данные")

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        if options["reset"]:
            self._reset()

        roles = self._roles()
        businesses = self._businesses()
        cats = self._categories()
        self._cities_objects(businesses)
        users = self._users(roles, businesses)

        admin = users["admin"]

        if Transaction.objects.exists():
            self.stdout.write(self.style.WARNING("Операционные данные уже есть — пропуск. "
                                                 "Используйте --reset для пересоздания."))
            self._print_credentials()
            return

        self._finance_ops(businesses, cats, users)
        registers = self._cash(businesses, users)
        self._cash_ops(registers, users)
        self._settlements(businesses, admin)
        self._payroll(businesses, admin)
        self._approvals(businesses, cats, users)

        self.stdout.write(self.style.SUCCESS("✓ Демо-данные ARKAND созданы."))
        self._print_credentials()

    # --------------------------------------------------------------------- #
    def _reset(self) -> None:
        from apps.approvals.models import ApprovalVote
        from apps.cash.models import CashOperation
        from apps.payroll.models import PayrollItem, PayrollRun
        from apps.settlements.models import Debt, Settlement, Transfer

        for model in (Settlement, Debt, Transfer, CashOperation, PayrollItem,
                      PayrollRun, ApprovalVote, ApprovalRequest, Transaction):
            model.objects.all().delete()
            if hasattr(model, "all_objects"):
                model.all_objects.all().delete()
        self.stdout.write(self.style.WARNING("Операционные данные очищены."))

    def _roles(self) -> dict[str, Role]:
        out = {}
        for code, label in RoleCode.choices:
            out[code] = Role.objects.get_or_create(code=code, defaults={"name": label})[0]
        return out

    def _businesses(self) -> dict[str, Business]:
        out = {}
        for code, name, kind, limit in BUSINESSES:
            out[code] = Business.objects.get_or_create(
                code=code,
                defaults={"name": name, "kind": kind, "expense_limit": Decimal(limit)},
            )[0]
        return out

    def _categories(self) -> dict[str, ExpenseCategory]:
        out = {}
        for code, name in CATEGORIES:
            out[code] = ExpenseCategory.objects.get_or_create(
                code=code, defaults={"name": name}
            )[0]
        return out

    def _cities_objects(self, businesses: dict[str, Business]) -> None:
        dushanbe = City.objects.get_or_create(name="Душанбе")[0]
        City.objects.get_or_create(name="Худжанд")
        SiteObject.objects.get_or_create(
            name="ЖК Сафо, 12 этажей",
            defaults={"business": businesses["developer"], "city": dushanbe,
                      "address": "ул. Рудаки, 120"},
        )
        SiteObject.objects.get_or_create(
            name="Коттедж Довуди",
            defaults={"business": businesses["design"], "city": dushanbe,
                      "address": "мкр. Зарафшон"},
        )

    def _users(self, roles, businesses) -> dict[str, User]:
        def mk(username, first, last, role_code, business=None, **extra):
            u, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first, "last_name": last,
                    "role": roles[role_code],
                    "business": business,
                    **extra,
                },
            )
            if created:
                u.set_password(PASSWORD)
                u.save()
            return u

        users = {
            "sohib": mk("sohib", "Сохиб", "", RoleCode.OWNER, businesses["developer"]),
            "iftikhor": mk("iftikhor", "Ифтихор", "", RoleCode.OWNER, businesses["concrete"]),
            "dovud": mk("dovud", "Довуд", "", RoleCode.OWNER, businesses["design"]),
            "chief": mk("chief", "Главный", "Бухгалтер", RoleCode.CHIEF_ACCOUNTANT,
                        businesses["finance"]),
            "buh1": mk("buh1", "Бухгалтер", "Первый", RoleCode.ACCOUNTANT, businesses["finance"]),
            "buh2": mk("buh2", "Бухгалтер", "Второй", RoleCode.ACCOUNTANT, businesses["finance"]),
            "cashier_dev": mk("cashier_dev", "Кассир", "Застройщик", RoleCode.CASHIER,
                              businesses["developer"]),
            "cashier_des": mk("cashier_des", "Кассир", "Проектная", RoleCode.CASHIER,
                              businesses["design"]),
        }
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={"first_name": "Администратор", "role": roles[RoleCode.ADMIN],
                      "is_staff": True, "is_superuser": True},
        )
        if created:
            admin.set_password(PASSWORD)
            admin.save()
        users["admin"] = admin
        return users

    # --------------------------------------------------------------------- #
    def _finance_ops(self, businesses, cats, users) -> None:
        today = timezone.now().date()
        buh = users["buh1"]

        def tx(biz, kind, amount, cat=None, method=PayMethod.CASH, status=TxStatus.CONFIRMED,
               days=0, counterparty="", barter=False, source=""):
            return finance_services.create_transaction(
                business_id=businesses[biz].id, kind=kind, amount=Decimal(amount),
                method=method, occurred_on=today - dt.timedelta(days=days), actor=buh,
                category_id=cats[cat].id if cat else None, counterparty=counterparty,
                is_barter=barter, source=source, status=status,
            )

        # Доходы
        tx("developer", TxKind.INCOME, 284500, method=PayMethod.TRANSFER,
           counterparty="Продажа квартир", source="external_sales", days=3)
        tx("concrete", TxKind.INCOME, 96200, counterparty="ООО Стройка", days=2)
        tx("crushing", TxKind.INCOME, 54300, counterparty="Частный клиент", days=1)
        tx("design", TxKind.INCOME, 42000, method=PayMethod.TRANSFER,
           counterparty="Договор проектирования", days=5)
        # Ожидает подтверждения (ФНС-01)
        tx("concrete", TxKind.INCOME, 31000, counterparty="Наличная отгрузка",
           status=TxStatus.PENDING, days=0)
        # Расходы по статьям (ФНС-02)
        tx("developer", TxKind.EXPENSE, 96200, cat="materials", counterparty="Цемент+", days=4)
        tx("concrete", TxKind.EXPENSE, 18400, cat="electricity", days=6)
        tx("crushing", TxKind.EXPENSE, 22750, cat="transport", counterparty="Солярка", days=3)
        tx("design", TxKind.EXPENSE, 12000, cat="salary", days=7)
        tx("concrete", TxKind.EXPENSE, 8600, cat="repair", counterparty="Ремонт БСУ", days=8)

    def _cash(self, businesses, users) -> dict[str, CashRegister]:
        reg_dev, _ = CashRegister.objects.get_or_create(
            code="cash-developer",
            defaults={"business": businesses["developer"], "name": "Касса застройщика",
                      "turnover_limit": Decimal(150000)},
        )
        reg_des, _ = CashRegister.objects.get_or_create(
            code="cash-design",
            defaults={"business": businesses["design"], "name": "Касса проектной",
                      "turnover_limit": Decimal(80000)},
        )
        reg_dev.responsible.add(users["cashier_dev"])
        reg_des.responsible.add(users["cashier_des"])
        return {"dev": reg_dev, "des": reg_des}

    def _cash_ops(self, registers, users) -> None:
        today = timezone.now().date()
        cash_services.add_operation(
            register_id=registers["dev"].id, kind=TxKind.INCOME, amount=Decimal(45000),
            method=PayMethod.CASH, occurred_on=today - dt.timedelta(days=2),
            actor=users["cashier_dev"], counterparty="Первый взнос", note="Аванс по квартире",
        )
        cash_services.add_operation(
            register_id=registers["dev"].id, kind=TxKind.EXPENSE, amount=Decimal(12000),
            method=PayMethod.CASH, occurred_on=today - dt.timedelta(days=1),
            actor=users["cashier_dev"], counterparty="Хозтовары",
        )
        cash_services.add_operation(
            register_id=registers["des"].id, kind=TxKind.INCOME, amount=Decimal(20000),
            method=PayMethod.CASH, occurred_on=today, actor=users["cashier_des"],
            counterparty="Оплата надзора",
        )

    def _settlements(self, businesses, admin) -> None:
        today = timezone.now().date()
        # Щебёночный завод отгрузил щебень бетонному (бартер/долг) — ХОЛ-30 / БАР-01
        t1 = settlement_services.create_transfer(
            from_business_id=businesses["crushing"].id,
            to_business_id=businesses["concrete"].id,
            amount=Decimal(38000), occurred_on=today - dt.timedelta(days=5), actor=admin,
            description="Отгрузка щебня на бетонный завод", is_barter=True,
        )
        debt1 = settlement_services.approve_transfer(transfer_id=t1.id, actor=admin)
        # Частичный возврат (БАР-03)
        settlement_services.settle_debt(
            debt_id=debt1.id, kind=SettlementKind.REPAYMENT, amount=Decimal(15000),
            actor=admin, occurred_on=today - dt.timedelta(days=1), note="Частичный возврат",
        )
        # Бетонный поставил бетон застройщику — ещё один долг
        t2 = settlement_services.create_transfer(
            from_business_id=businesses["concrete"].id,
            to_business_id=businesses["developer"].id,
            amount=Decimal(60000), occurred_on=today - dt.timedelta(days=4), actor=admin,
            description="Товарный бетон на объект ЖК Сафо",
        )
        settlement_services.approve_transfer(transfer_id=t2.id, actor=admin)

    def _payroll(self, businesses, admin) -> None:
        # Схемы бонусов (ЗРП-04 / ЗРП-05)
        factory_scheme, _ = PayrollScheme.objects.get_or_create(
            name="Продажник завода (фикс + 10% от продаж)",
            defaults={"base_fixed": Decimal(3000),
                      "rules": [{"type": "percent_of_sales", "percent": 10}]},
        )
        dev_scheme, _ = PayrollScheme.objects.get_or_create(
            name="Продажник застройщика (за квартиру)",
            defaults={"base_fixed": Decimal(3000),
                      "rules": [{"type": "per_unit", "metric": "apartments",
                                 "rate": 500, "threshold": 10, "threshold_rate": 1000}]},
        )
        e1, _ = Employee.objects.get_or_create(
            full_name="Менеджер по продажам (бетон)",
            defaults={"business": businesses["concrete"], "base_salary": Decimal(3000),
                      "is_salesperson": True, "scheme": factory_scheme, "position": "Продажник"},
        )
        e2, _ = Employee.objects.get_or_create(
            full_name="Менеджер по продажам (застройщик)",
            defaults={"business": businesses["developer"], "base_salary": Decimal(3000),
                      "is_salesperson": True, "scheme": dev_scheme, "position": "Продажник"},
        )
        Employee.objects.get_or_create(
            full_name="Прораб объекта",
            defaults={"business": businesses["developer"], "base_salary": Decimal(4500),
                      "salary_type": "object", "position": "Прораб"},
        )
        now = timezone.now()
        run = payroll_services.run_payroll(
            year=now.year, month=now.month, actor=admin,
            metrics_by_employee={
                e1.id: {"sales": 80000},      # 3000 + 10% * 80000 = 11000
                e2.id: {"apartments": 12},    # 3000 + 12 * 1000 = 15000
            },
        )
        payroll_services.approve_payroll(run_id=run.id, actor=admin)

    def _approvals(self, businesses, cats, users) -> None:
        today = timezone.now().date()
        # Крупная закупка выше лимита застройщика (50000) → согласие 3 владельцев (ХОЛ-22)
        req = approval_services.create_request(
            business_id=businesses["developer"].id, amount=Decimal(120000),
            purpose="Закупка арматуры на объект", actor=users["chief"], occurred_on=today,
            category_id=cats["materials"].id,
            description="Партия арматуры для монолитных работ",
        )
        # Два владельца одобрили, третий ещё нет → заявка ждёт (ХОЛ-23)
        approval_services.cast_vote(request_id=req.id, owner=users["sohib"],
                                    value=VoteValue.APPROVE, comment="Согласен")
        approval_services.cast_vote(request_id=req.id, owner=users["iftikhor"],
                                    value=VoteValue.APPROVE)
        # Мелкая закупка в пределах лимита → автоодобрение (ХОЛ-24)
        approval_services.create_request(
            business_id=businesses["design"].id, amount=Decimal(8000),
            purpose="Канцелярия и печать чертежей", actor=users["chief"], occurred_on=today,
            category_id=cats["other"].id,
        )

    def _print_credentials(self) -> None:
        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO(f"Учётные записи (пароль у всех: {PASSWORD}):"))
        for line in [
            "  admin        — Администратор (superuser)",
            "  sohib        — Владелец (финансы/застройщик)",
            "  iftikhor     — Владелец (заводы)",
            "  dovud        — Владелец (проектная)",
            "  chief        — Главный бухгалтер",
            "  buh1 / buh2  — Бухгалтеры",
            "  cashier_dev  — Кассир застройщика",
            "  cashier_des  — Кассир проектной",
        ]:
            self.stdout.write(line)
