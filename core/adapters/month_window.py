from __future__ import annotations

from datetime import date
from typing import Tuple

from core.validators import validate_month_string


def month_key(d: date) -> str:
    """Return 'YYYY-MM' for a given date."""
    return f"{d.year:04d}-{d.month:02d}"


def parse_target_month(target_month: str) -> Tuple[int, int]:
    """Validate and parse 'YYYY-MM' -> (year, month)."""
    y, m = validate_month_string(target_month)
    return y, m
