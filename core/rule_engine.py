from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from .models import (
    LedgerRow,
    LedgerType,
    Actor,
    PhoenixConfig,
    Flag,
    FlagCode,
    Alert,
    AlertCode,
    Severity,
    MonthlyMetrics,
    Explainability,
    DecisionRecord,
)
from .validators import validate_rows, validate_month_string, ensure_decimal, quantize_money, safe_config_snapshot


def month_of(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _sum_amount(rows: List[LedgerRow]) -> Decimal:
    total = Decimal("0.00")
    for r in rows:
        total += quantize_money(ensure_decimal(r.amount))
    return quantize_money(total)


def evaluate_month(
    *,
    rows: List[LedgerRow],
    config: PhoenixConfig,
    target_month: str,
    annual_w2_ytd: Optional[Decimal] = None,
) -> DecisionRecord:
    validate_month_string(target_month)
    rows = validate_rows(rows)

    month_rows = [r for r in rows if month_of(r.date) == target_month]

    w2_rows = [r for r in month_rows if r.type == LedgerType.W2]
    irwe_rows = [r for r in month_rows if r.type == LedgerType.IRWE]
    dist_rows = [r for r in month_rows if r.type == LedgerType.DIST]

    gross_w2 = _sum_amount(w2_rows)

    if config.irwe_enabled:
        irwe_total = _sum_amount(irwe_rows)
    else:
        irwe_total = Decimal("0.00")

    countable = quantize_money(gross_w2 - irwe_total)

    dist_total = _sum_amount(dist_rows)

    sga_limit = quantize_money(ensure_decimal(config.sga_limit_blind))
    headroom = quantize_money(sga_limit - countable)

    flags: List[Flag] = []
    alerts: List[Alert] = []

    for r in month_rows:
        if r.actor == Actor.OWNER and r.human_intervention_minutes > 0:
            flags.append(
                Flag(
                    code=FlagCode.FLAG_WORK_ACTIVITY_REVIEW,
                    severity=Severity.INFO,
                    message="Owner-attributed entry with human intervention minutes > 0 (informational review flag).",
                    payload={
                        "date": r.date.isoformat(),
                        "type": r.type.value,
                        "amount": str(quantize_money(ensure_decimal(r.amount))),
                        "description": r.description,
                        "human_intervention_minutes": r.human_intervention_minutes,
                    },
                )
            )

    if countable > sga_limit:
        over_by = quantize_money(countable - sga_limit)
        alerts.append(
            Alert(
                code=AlertCode.ALERT_CRITICAL_SGA_EXCEEDED,
                severity=Severity.CRITICAL,
                message="Countable earnings exceed the blind SGA limit for the month. Human intervention required.",
                payload={
                    "month": target_month,
                    "countable_earnings": str(countable),
                    "sga_limit_blind": str(sga_limit),
                    "over_by": str(over_by),
                },
            )
        )

    if config.min_reasonable_comp is not None and annual_w2_ytd is not None:
        min_rc = quantize_money(ensure_decimal(config.min_reasonable_comp))
        annual_w2 = quantize_money(ensure_decimal(annual_w2_ytd))
        if annual_w2 < min_rc:
            alerts.append(
                Alert(
                    code=AlertCode.WARN_IRS_AUDIT_RISK,
                    severity=Severity.WARN,
                    message="Annual W-2 appears below minimum reasonable compensation (advisory only).",
                    payload={
                        "annual_w2_ytd": str(annual_w2),
                        "min_reasonable_comp": str(min_rc),
                        "shortfall": str(quantize_money(min_rc - annual_w2)),
                    },
                )
            )

    metrics = MonthlyMetrics(
        month=target_month,
        gross_w2=gross_w2,
        irwe_total_documented=irwe_total,
        countable_earnings=countable,
        dist_total=dist_total,
        sga_limit_blind=sga_limit,
        sga_headroom=headroom,
    )

    rules_applied = [
        "Income classification: W2 counted; DIST not counted toward SGA; Trust transfers are post-income allocations (tracked elsewhere).",
        "IRWE gate: if disabled -> 0; if enabled -> subtract documented IRWE only.",
        "SGA safety: if countable > SGA_LIMIT_BLIND -> ALERT_CRITICAL.",
        "Work activity attribution: OWNER with human_intervention_minutes > 0 -> FLAG_WORK_ACTIVITY_REVIEW.",
        "IRS reasonable compensation is advisory only.",
    ]

    conclusions = [
        f"Gross W-2 for {target_month}: ${gross_w2}",
        f"IRWE applied: {'YES' if config.irwe_enabled else 'NO'} (documented total: ${irwe_total})",
        f"Countable earnings for {target_month}: ${countable}",
        f"Blind SGA limit: ${sga_limit} (headroom: ${headroom})",
        f"Distributions tracked (not counted toward SGA): ${dist_total}",
    ]

    next_actions = []
    if any(a.code == AlertCode.ALERT_CRITICAL_SGA_EXCEEDED for a in alerts):
        next_actions.append("Stop and review planned work/income for the month; adjust decisions manually (Phoenix does not change values).")
    if any(a.code == AlertCode.WARN_IRS_AUDIT_RISK for a in alerts):
        next_actions.append("Discuss W-2 reasonable compensation with tax professional (advisory only; does not affect SSDI calculation).")
    if any(f.code == FlagCode.FLAG_WORK_ACTIVITY_REVIEW for f in flags):
        next_actions.append("Maintain narrative notes describing owner intervention/work activity to support SSA explainability if needed.")

    explain = Explainability(
        month=target_month,
        rules_applied=rules_applied,
        measurements={
            "gross_w2": str(gross_w2),
            "irwe_enabled": config.irwe_enabled,
            "irwe_total_documented": str(irwe_total),
            "countable_earnings": str(countable),
            "sga_limit_blind": str(sga_limit),
            "sga_headroom": str(headroom),
            "dist_total_tracked": str(dist_total),
        },
        conclusions=conclusions,
        next_actions=next_actions or ["No action required."],
    )

    record = DecisionRecord(
        month=target_month,
        config_snapshot=safe_config_snapshot(config),
        input_summary={
            "total_rows_received": len(rows),
            "rows_in_target_month": len(month_rows),
            "timezone": config.timezone,
        },
        metrics=metrics,
        flags=flags,
        alerts=alerts,
        explain=explain,
    )
    return record
