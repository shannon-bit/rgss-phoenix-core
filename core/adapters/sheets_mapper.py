from __future__ import annotations

from datetime import datetime, date
from typing import Dict, Any, List

from core.models import LedgerRow, LedgerType, Actor
from core.validators import ValidationError, ensure_decimal, quantize_money

# Canonical minimum columns from LOGIC_RULES.md
REQUIRED_COLUMNS = [
    "Date",
    "Type",
    "Amount",
    "Description",
    "Category",
    "Actor",
    "HumanInterventionMinutes",
    "EvidenceLink",
    "Notes",  # optional content, but canonical schema includes the column
]


def _parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValidationError(f"Invalid Date: {value!r}")


def _parse_enum(enum_cls, value: Any, field_name: str):
    s = str(value).strip()
    try:
        return enum_cls(s)
    except Exception as e:
        raise ValidationError(f"Invalid {field_name}: {value!r}") from e


def map_sheet_row_to_ledger_row(row: Dict[str, Any]) -> LedgerRow:
    # Hard gate: required columns must exist
    for col in REQUIRED_COLUMNS[:-1]:  # Notes content optional, but column expected in canonical sheet
        if col not in row:
            raise ValidationError(f"Missing required column: {col}")

    d = _parse_date(row["Date"])
    t = _parse_enum(LedgerType, row["Type"], "Type")
    amt = quantize_money(ensure_decimal(row["Amount"]))
    desc = str(row["Description"]).strip()
    cat = str(row["Category"]).strip()
    actor = _parse_enum(Actor, row["Actor"], "Actor")

    try:
        him = int(str(row["HumanInterventionMinutes"]).strip())
    except Exception as e:
        raise ValidationError("HumanInterventionMinutes must be an integer") from e
    if him < 0:
        raise ValidationError("HumanInterventionMinutes must be >= 0")

    ev = str(row.get("EvidenceLink", "") or "").strip()
    notes = str(row.get("Notes", "") or "").strip()

    # Belt + suspenders: enforce IRWE evidence hard gate here too
    if t == LedgerType.IRWE and not ev:
        raise ValidationError("IRWE entry requires EvidenceLink (hard gate)")

    return LedgerRow(
        date=d,
        type=t,
        amount=amt,
        description=desc,
        category=cat,
        actor=actor,
        human_intervention_minutes=him,
        evidence_link=ev,
        notes=notes,
    )


def map_sheet_rows(rows: List[Dict[str, Any]]) -> List[LedgerRow]:
    return [map_sheet_row_to_ledger_row(r) for r in rows]
