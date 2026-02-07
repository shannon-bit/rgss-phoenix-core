from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any, List


class LedgerType(str, Enum):
    W2 = "W2"
    IRWE = "IRWE"
    DIST = "DIST"
    EXP = "EXP"


class Actor(str, Enum):
    PHOENIX = "PHOENIX"
    OWNER = "OWNER"
    NOTARY_AGENT = "NOTARY_AGENT"


class Severity(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    CRITICAL = "CRITICAL"
    HARD_ERROR = "HARD_ERROR"


class FlagCode(str, Enum):
    FLAG_WORK_ACTIVITY_REVIEW = "FLAG_WORK_ACTIVITY_REVIEW"


class AlertCode(str, Enum):
    ALERT_CRITICAL_SGA_EXCEEDED = "ALERT_CRITICAL_SGA_EXCEEDED"
    WARN_IRS_AUDIT_RISK = "WARN_IRS_AUDIT_RISK"


@dataclass(frozen=True)
class LedgerRow:
    """
    Canonical ledger row (minimum schema) as defined in LOGIC_RULES.md.
    """
    date: date
    type: LedgerType
    amount: Decimal
    description: str
    category: str
    actor: Actor
    human_intervention_minutes: int
    evidence_link: str = ""
    notes: str = ""


@dataclass(frozen=True)
class PhoenixConfig:
    """
    Config values used by the rules. No external loading is done here.
    """
    # Governance-locked
    sga_limit_blind: Decimal

    # Feature gate
    irwe_enabled: bool = False

    # Advisory-only
    min_reasonable_comp: Optional[Decimal] = None

    # Timezone for interpretation (used by adapters; stored here for decision records)
    timezone: str = "America/Denver"


@dataclass(frozen=True)
class Flag:
    code: FlagCode
    severity: Severity = Severity.INFO
    message: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Alert:
    code: AlertCode
    severity: Severity
    message: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MonthlyMetrics:
    month: str  # "YYYY-MM"
    gross_w2: Decimal
    irwe_total_documented: Decimal
    countable_earnings: Decimal
    dist_total: Decimal
    sga_limit_blind: Decimal
    sga_headroom: Decimal


@dataclass(frozen=True)
class Explainability:
    """
    SSA-friendly narrative payload (structured).
    """
    month: str
    rules_applied: List[str]
    measurements: Dict[str, Any]
    conclusions: List[str]
    next_actions: List[str]


@dataclass(frozen=True)
class DecisionRecord:
    """
    Full machine-readable run output for audit/governance.
    """
    month: str
    config_snapshot: Dict[str, Any]
    input_summary: Dict[str, Any]
    metrics: MonthlyMetrics
    flags: List[Flag]
    alerts: List[Alert]
    explain: Explainability
