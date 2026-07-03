"""
Request-level idempotency for money-creating operations (financial invariant).

CONTRACT §1.2: a repeated request must not create a second money operation.
Transition ops (confirm / approve) are idempotent via a status check; *create*
ops have no status to check, so they de-duplicate on a client-supplied
``Idempotency-Key`` recorded in ``core.IdempotencyKey``.

Call :func:`run_idempotent` inside the operation's ``@transaction.atomic`` block:
the key row and the money row commit together, so a half-finished request leaves
no key behind.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from django.db import IntegrityError, transaction

from .exceptions import DomainError
from .models import IdempotencyKey

T = TypeVar("T")


def run_idempotent(*, scope: str, key: str | None, create: Callable[[], T], fetch: Callable[[int], T]) -> T:
    """Run ``create`` at most once per ``(scope, key)``.

    * ``key`` falsy → no de-duplication, just ``create()`` (the header is optional).
    * key already recorded → return ``fetch(result_pk)`` — the original object.
    * otherwise → record the key, run ``create()``, store its pk, return it.

    A concurrent duplicate loses the unique-constraint race and is resolved to the
    winner's stored result rather than inserting a second money row.
    """
    if not key:
        return create()

    existing = IdempotencyKey.objects.filter(scope=scope, key=key).first()
    if existing is not None:
        return _resolve(existing, fetch)

    # Claim the key first (before creating the money row) inside a savepoint so a
    # concurrent duplicate collides here instead of inserting a second row.
    try:
        with transaction.atomic():
            record = IdempotencyKey.objects.create(scope=scope, key=key)
    except IntegrityError:
        existing = IdempotencyKey.objects.filter(scope=scope, key=key).first()
        if existing is not None:
            return _resolve(existing, fetch)
        raise

    obj = create()
    record.result_pk = obj.pk
    record.save(update_fields=["result_pk"])
    return obj


def _resolve(record: IdempotencyKey, fetch: Callable[[int], T]) -> T:
    if record.result_pk is None:
        # A concurrent request holds the key but hasn't committed its result yet.
        raise DomainError(
            "duplicate_request",
            "Идентичный запрос уже обрабатывается",
            status_code=409,
        )
    return fetch(record.result_pk)
