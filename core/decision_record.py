from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Any

from .models import DecisionRecord


def to_dict(record: DecisionRecord) -> Dict[str, Any]:
    """
    Convert a DecisionRecord to a JSON-serializable dict.
    (No file writes here; adapters decide where to store snapshots.)
    """
    d = asdict(record)

    def _walk(x):
        if isinstance(x, dict):
            return {k: _walk(v) for k, v in x.items()}
        if isinstance(x, list):
            return [_walk(v) for v in x]
        try:
            from decimal import Decimal
            if isinstance(x, Decimal):
                return str(x)
        except Exception:
            pass
        return x

    return _walk(d)
