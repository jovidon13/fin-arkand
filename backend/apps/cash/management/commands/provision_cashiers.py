"""
Provision cashiers per holding direction with strict per-direction access.

Каждое направление со схем холдинга получает свою кассу и кассира, который
видит и заводит операции ТОЛЬКО по своей кассе (изоляция КАС-04). Команда
идемпотентна — её можно безопасно запускать на боевой базе: существующие
пользователи/кассы не пересоздаются и пароли не перезаписываются.

Направления (со схем «Схемы по бизнесам»):
    Застройщик · Проектная · Бетонный завод · Щебёночный завод · Снабжение · Финансы

Usage:
    python manage.py provision_cashiers
    python manage.py provision_cashiers --password 'СвойПароль'
"""
from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Role, RoleCode
from apps.cash.models import CashRegister
from apps.core.models import Business

User = get_user_model()

DEFAULT_PASSWORD = "arkand2026"

#: Полный ростер касс/кассиров по направлениям холдинга.
#: username, Имя, Фамилия/направление, код бизнеса, код кассы, название кассы, лимит оборота
CASHIER_ROSTER: list[tuple[str, str, str, str, str, str, int]] = [
    ("cashier_dev",       "Кассир",        "Застройщик",       "developer", "cash-developer",       "Касса застройщика",         150000),
    ("cashier_dev_sales", "Кассир продаж", "Застройщик",       "developer", "cash-developer-sales", "Касса продаж застройщика",  300000),
    ("cashier_des",       "Кассир",        "Проектная",        "design",    "cash-design",          "Касса проектной",            80000),
    ("cashier_con",       "Кассир",        "Бетонный завод",   "concrete",  "cash-concrete",        "Касса бетонного завода",    120000),
    ("cashier_cru",       "Кассир",        "Щебёночный завод", "crushing",  "cash-crushing",        "Касса щебёночного завода",  120000),
    ("cashier_sup",       "Кассир",        "Снабжение",        "supply",    "cash-supply",          "Касса снабжения",           200000),
    ("cashier_fin",       "Кассир",        "Финансы",          "finance",   "cash-finance",         "Центральная касса",              0),
]


def ensure_cashiers(password: str = DEFAULT_PASSWORD, stdout=None) -> dict[str, CashRegister]:
    """Idempotently create cashier users + their registers and link them.

    Returns a dict of register-code → CashRegister for callers (e.g. seed).
    A cashier is attached only to their own register — access isolation is then
    enforced by ``CashRegister.is_visible_to`` in selectors/permissions (КАС-04).
    """
    role, _ = Role.objects.get_or_create(
        code=RoleCode.CASHIER, defaults={"name": RoleCode.CASHIER.label}
    )
    businesses = {b.code: b for b in Business.objects.all()}
    registers: dict[str, CashRegister] = {}

    for username, first, last, biz_code, reg_code, reg_name, limit in CASHIER_ROSTER:
        business = businesses.get(biz_code)
        if business is None:
            if stdout:
                stdout.write(f"  ⚠ пропуск {username}: бизнес «{biz_code}» не найден")
            continue

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"first_name": first, "last_name": last,
                      "role": role, "business": business},
        )
        if created:
            user.set_password(password)
            user.save()
        else:
            # keep role/business in sync without touching the password
            changed = False
            if user.role_id != role.id:
                user.role = role
                changed = True
            if user.business_id != business.id:
                user.business = business
                changed = True
            if changed:
                user.save(update_fields=["role", "business"])

        register, _ = CashRegister.objects.get_or_create(
            code=reg_code,
            defaults={"business": business, "name": reg_name,
                      "turnover_limit": Decimal(limit)},
        )
        # Кассир отвечает только за свою кассу (доступ только по направлению).
        register.responsible.add(user)
        registers[reg_code] = register
        if stdout:
            mark = "＋" if created else "·"
            stdout.write(f"  {mark} {username:18} → {reg_name}")

    return registers


class Command(BaseCommand):
    help = "Создать кассиров и кассы по направлениям холдинга (изоляция по направлению)"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--password", default=DEFAULT_PASSWORD,
            help="Пароль для НОВЫХ кассиров (существующим не меняется)",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.HTTP_INFO("Провижининг кассиров по направлениям:"))
        registers = ensure_cashiers(password=options["password"], stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS(
            f"✓ Готово. Касс задействовано: {len(registers)}."
        ))
        self.stdout.write(
            "Каждый кассир видит и заводит операции только по своей кассе (КАС-04)."
        )
