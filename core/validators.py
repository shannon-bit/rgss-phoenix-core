from __future__ import annotations

from dataclasses import asdict
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable, List, Tuple

from .models import LedgerRow, LedgerType, Actor


class ValidationError(Exception):
    """Hard-stop validation error (must not proceed to calculations)."""


TWOPLACES = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def ensure_decimal(x) -> Decimal:
    try:
        if isinstance(x, Decimal):
            return x
        return Decimal(str(x))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValidationError(f"Amount is not a valid decimal: {x!r}") from e


def validate_row(row: LedgerRow) -> None:
    if not isinstance(row.date, date):
        raise ValidationError("Row.date must be a datetime.date")

    if row.type not in LedgerType:
        raise ValidationError(f"Invalid row.type: {row.type}")

    if row.actor not in Actor:
        raise ValidationError(f"Invalid row.actor: {row.actor}")

    if not isinstance(row.human_intervention_minutes, int) or row.human_intervention_minutes < 0:
        raise ValidationError("HumanInterventionMinutes must be an integer >= 0")

    amt = ensure_decimal(row.amount)
    _ = quantize_money(amt)

    if row.type == LedgerType.IRWE:
        if not (row.evidence_link or "").strip():
            raise ValidationError("IRWE entry requires EvidenceLink (hard gate)")


def validate_rows(rows: Iterable[LedgerRow]) -> List[LedgerRow]:
    rows_list = list(rows)
    for r in rows_list:
        validate_row(r)
    return rows_list


def validate_month_string(month: str) -> Tuple[int, int]:
    if not isinstance(month, str) or len(month) != 7 or month[4] != "-":
        raise ValidationError("month must be in 'YYYY-MM' format")
    try:
        y = int(month[0:4])
        m = int(month[5:7])
    except ValueError as e:
        raise ValidationError("month must be in 'YYYY-MM' format (numeric)") from e
    if m < 1 or m > 12:
        raise ValidationError("month month-part must be 01..12")
    if y < 1900 or y > 3000:
        raise ValidationError("month year-part out of bounds")
    return y, m


def safe_config_snapshot(cfg) -> dict:
    return asdict(cfg)
