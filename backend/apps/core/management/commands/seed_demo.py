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
    ("disbursement", "Выдача руководителю"),
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
        self._external_debts(businesses, users)
        self._payroll(businesses, admin)
        self._approvals(businesses, cats, users)

        self.stdout.write(self.style.SUCCESS("✓ Демо-данные ARKAND созданы."))
        self._print_credentials()

    # --------------------------------------------------------------------- #
    def _reset(self) -> None:
        from apps.approvals.models import ApprovalVote
        from apps.cash.models import CashOperation
        from apps.documents.models import OperationDocument
        from apps.payroll.models import PayrollItem, PayrollRun
        from apps.settlements.models import Debt, ExternalDebt, Settlement, Transfer

        for model in (OperationDocument, Settlement, Debt, ExternalDebt, Transfer,
                      CashOperation, PayrollItem, PayrollRun, ApprovalVote,
                      ApprovalRequest, Transaction):
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
            "cashier_con": mk("cashier_con", "Кассир", "Бетонный завод", RoleCode.CASHIER,
                              businesses["concrete"]),
            "cashier_cru": mk("cashier_cru", "Кассир", "Щебёночный завод", RoleCode.CASHIER,
                              businesses["crushing"]),
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
               days=0, counterparty="", barter=False, source="", is_disbursement=False,
               recipient=None):
            return finance_services.create_transaction(
                business_id=businesses[biz].id, kind=kind, amount=Decimal(amount),
                method=method, occurred_on=today - dt.timedelta(days=days), actor=buh,
                category_id=cats[cat].id if cat else None, counterparty=counterparty,
                is_barter=barter, source=source, status=status,
                is_disbursement=is_disbursement,
                recipient_manager_id=recipient.id if recipient else None,
            )

        # 📈 Сегодняшние подтверждённые операции — для плиток «за сегодня»
        tx("concrete", TxKind.INCOME, 96000, counterparty="Отгрузка бетона (сегодня)", days=0)
        tx("crushing", TxKind.EXPENSE, 22750, cat="transport", counterparty="Солярка (сегодня)",
           days=0)
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
        # 💵 Выдача денег руководителю (owner) — Сохиб получил на оперативные расходы.
        tx("developer", TxKind.EXPENSE, 25000, is_disbursement=True,
           recipient=users["sohib"], counterparty="Выдача руководителю", days=1)

        # Двухэтапное согласование в действии (менеджер → бухгалтер → владелец):
        # мелкая операция ждёт проверки бухгалтера …
        tx("design", TxKind.EXPENSE, 6000, cat="transport", counterparty="ГСМ",
           status=TxStatus.PENDING, days=0)
        # … а крупный расход застройщика (выше лимита 50 000) прошёл проверку
        # бухгалтера и теперь ждёт подтверждения владельца.
        big = tx("developer", TxKind.EXPENSE, 88000, cat="materials",
                 counterparty="Партия арматуры", status=TxStatus.PENDING, days=0)
        finance_services.check_transaction(tx_id=big.id, actor=buh)

        # Дополнительная история за месяц по всем бизнесам — чтобы отчёты, графики
        # и таблицы были наполнены данными (детерминированно, без random).
        extra = [
            # biz, kind, amount, cat, days, counterparty
            ("developer", TxKind.INCOME, 190000, None, 10, "Продажа квартиры"),
            ("developer", TxKind.EXPENSE, 43000, "materials", 12, "Кирпич"),
            ("developer", TxKind.EXPENSE, 15500, "transport", 14, "Доставка"),
            ("developer", TxKind.INCOME, 220000, None, 18, "Продажа квартиры"),
            ("concrete", TxKind.INCOME, 78000, None, 9, "Отгрузка бетона М250"),
            ("concrete", TxKind.INCOME, 61000, None, 15, "Отгрузка бетона М300"),
            ("concrete", TxKind.EXPENSE, 26000, "materials", 11, "Цемент навалом"),
            ("concrete", TxKind.EXPENSE, 9400, "electricity", 16, "Электроэнергия БСУ"),
            ("crushing", TxKind.INCOME, 47000, None, 8, "Щебень фр. 20-40"),
            ("crushing", TxKind.INCOME, 39500, None, 13, "Песок строительный"),
            ("crushing", TxKind.EXPENSE, 31000, "transport", 10, "Солярка"),
            ("crushing", TxKind.EXPENSE, 12800, "electricity", 17, "Электричество дробилки"),
            ("design", TxKind.INCOME, 55000, None, 6, "Договор 50/30/20 — этап 1"),
            ("design", TxKind.INCOME, 33000, None, 19, "Авторский надзор"),
            ("design", TxKind.EXPENSE, 18000, "salary", 12, "Зарплата проектировщиков"),
            ("supply", TxKind.EXPENSE, 21000, "materials", 7, "Централизованная закупка"),
        ]
        for biz, kind, amount, cat, days, cp in extra:
            method = PayMethod.TRANSFER if kind == TxKind.INCOME and days % 2 == 0 else PayMethod.CASH
            tx(biz, kind, amount, cat=cat, method=method, days=days, counterparty=cp)

    def _cash(self, businesses, users) -> dict[str, CashRegister]:
        # Единый источник касс/кассиров по направлениям (изоляция по направлению,
        # КАС-04). Та же логика доступна на проде командой `provision_cashiers`.
        from apps.cash.management.commands.provision_cashiers import ensure_cashiers
        regs = ensure_cashiers()
        return {
            "dev": regs["cash-developer"], "des": regs["cash-design"],
            "con": regs["cash-concrete"], "cru": regs["cash-crushing"],
            "dev_sales": regs["cash-developer-sales"],
            "sup": regs["cash-supply"], "fin": regs["cash-finance"],
        }

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
        # Кассиры бетонного и щебёночного заводов ведут свою часть (несколько касс).
        cash_services.add_operation(
            register_id=registers["con"].id, kind=TxKind.INCOME, amount=Decimal(64000),
            method=PayMethod.CASH, occurred_on=today, actor=users["cashier_con"],
            counterparty="Отгрузка бетона М300",
        )
        cash_services.add_operation(
            register_id=registers["cru"].id, kind=TxKind.INCOME, amount=Decimal(38500),
            method=PayMethod.CASH, occurred_on=today - dt.timedelta(days=1),
            actor=users["cashier_cru"], counterparty="Щебень фр. 5-20",
        )
        # Новые направления: продажи застройщика, снабжение, центральная касса.
        # Actor — ответственный кассир своей кассы (изоляция по направлению).
        cashier_sales = User.objects.get(username="cashier_dev_sales")
        cashier_sup = User.objects.get(username="cashier_sup")
        cashier_fin = User.objects.get(username="cashier_fin")
        cash_services.add_operation(
            register_id=registers["dev_sales"].id, kind=TxKind.INCOME, amount=Decimal(120000),
            method=PayMethod.CASH, occurred_on=today, actor=cashier_sales,
            counterparty="Продажа квартиры", note="Первый взнос",
        )
        cash_services.add_operation(
            register_id=registers["sup"].id, kind=TxKind.EXPENSE, amount=Decimal(34000),
            method=PayMethod.CASH, occurred_on=today, actor=cashier_sup,
            counterparty="Закупка материалов",
        )
        cash_services.add_operation(
            register_id=registers["fin"].id, kind=TxKind.INCOME, amount=Decimal(50000),
            method=PayMethod.CASH, occurred_on=today, actor=cashier_fin,
            counterparty="Инкассация из касс направлений",
        )

        # Наполняем каждую кассу историей за неделю (у каждого кассира — своя
        # часть), чтобы у любого кассира на «Кассах» были данные.
        by_reg = {
            "dev": users["cashier_dev"], "des": users["cashier_des"],
            "con": users["cashier_con"], "cru": users["cashier_cru"],
            "dev_sales": cashier_sales, "sup": cashier_sup, "fin": cashier_fin,
        }
        extra_ops = [
            ("dev", TxKind.INCOME, 30000, 4, "Доплата по договору"),
            ("dev", TxKind.EXPENSE, 8000, 5, "Канцелярия"),
            ("des", TxKind.INCOME, 15000, 3, "Оплата надзора"),
            ("des", TxKind.EXPENSE, 5000, 6, "Печать чертежей"),
            ("con", TxKind.INCOME, 22000, 2, "Отгрузка бетона М200"),
            ("con", TxKind.EXPENSE, 8000, 4, "Ремонт миксера"),
            ("cru", TxKind.INCOME, 41000, 3, "Щебень фр. 20-40"),
            ("cru", TxKind.EXPENSE, 9000, 5, "ГСМ"),
            ("dev_sales", TxKind.INCOME, 95000, 4, "Продажа квартиры"),
            ("sup", TxKind.EXPENSE, 18000, 2, "Закупка инструмента"),
            ("fin", TxKind.EXPENSE, 22000, 3, "Выдача в кассы направлений"),
        ]
        for reg_key, kind, amount, days, cp in extra_ops:
            cash_services.add_operation(
                register_id=registers[reg_key].id, kind=kind, amount=Decimal(amount),
                method=PayMethod.CASH, occurred_on=today - dt.timedelta(days=days),
                actor=by_reg[reg_key], counterparty=cp,
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

    def _external_debts(self, businesses, users) -> None:
        """Дебиторка / кредиторка с внешними контрагентами (кто должен компании /
        кому должна компания) — отдельный блок на дашборде."""
        from apps.core.enums import ExternalDebtDirection
        today = timezone.now().date()
        chief = users["chief"]

        def ext(direction, counterparty, amount, biz=None, days=0):
            return settlement_services.create_external_debt(
                direction=direction, counterparty=counterparty, amount=Decimal(amount),
                occurred_on=today - dt.timedelta(days=days), actor=chief,
                business_id=businesses[biz].id if biz else None,
            )

        # Кто должен компании (дебиторка)
        ext(ExternalDebtDirection.RECEIVABLE, "ООО «Стройка»", 480000, biz="concrete", days=12)
        ext(ExternalDebtDirection.RECEIVABLE, "Арканд Девелопмент", 1200000,
            biz="developer", days=20)
        ext(ExternalDebtDirection.RECEIVABLE, "Частный клиент", 30000, biz="crushing", days=5)
        # Кому должна компания (кредиторка)
        ext(ExternalDebtDirection.PAYABLE, "Цементный завод", 650000, biz="concrete", days=9)
        ext(ExternalDebtDirection.PAYABLE, "Поставщик топлива", 220000, biz="crushing", days=7)

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
            "  cashier_dev        — Кассир застройщика",
            "  cashier_dev_sales  — Кассир продаж застройщика",
            "  cashier_des        — Кассир проектной",
            "  cashier_con        — Кассир бетонного завода",
            "  cashier_cru        — Кассир щебёночного завода",
            "  cashier_sup        — Кассир снабжения",
            "  cashier_fin        — Кассир центральной кассы (финансы)",
        ]:
            self.stdout.write(line)
