# LOGIC_RULES.md

## RGSS Phoenix v4 — Logic Blueprint (Authoritative)

**Status:** Canonical • Phase 3.2 Artifact
**Last Updated:** 2026-02-06
**Authority Thread:** Phoenix / Superagent (this system)

---

## 0. Purpose & Scope

This document defines the **authoritative logic rules** that govern how Phoenix evaluates income, work activity, and safety for a **blind SSDI beneficiary** who is a **W‑2 officer of an S‑Corp** with **K‑1 distributions** and a **personal trust** (Scenario B).

This file is the **single blueprint** between:

* External law & policy (SSA / IRS), and
* Future Python implementation.

❗ **No production code may be written unless it conforms exactly to this file.** rgss-phoenix-core/
├─ .gitignore
├─ config/
│  └─ env.example
├─ core/              # empty, pending Python
├─ data/              # schemas only (no runtime data)
├─ docs/
│  ├─ AUTHORITY_SOURCES.md   # CANON
│  ├─ LOGIC_RULES.md         # CANON (Phase 3.2 complete)
│  ├─ AI_STACK.md            # reference only
│  ├─ DEVICE_INVENTORY.md    # reference only
│  ├─ OPEN_QUESTIONS.md      # reference only
│  ├─ SNAPSHOT_STRATEGY.md   # reference only
├─ logs/
│  └─ .gitkeep
└─ snapshots/
   └─ .gitkeep

---

## 1. Golden Principles (Non‑Negotiable)

1. **Single Authority Rule**

   * Phoenix is the sole decision authority.
   * Google Sheets is the sole **financial Source of Truth**.
   * No other system may override Phoenix determinations.

2. **SSDI‑First Safety**

   * All logic prioritizes SSDI eligibility preservation.
   * IRS optimization is advisory only.

3. **No Automation of Human Decisions**

   * Phoenix may **warn**, **flag**, and **explain**.
   * Phoenix may **never** auto‑adjust salary, distributions, or trust transfers.

4. **Explainability Over Optimization**

   * Every decision must be human‑explainable to SSA.

---

## 2. Benefit & Regulatory Context (Locked)

* **Benefit Type:** SSDI (Title II)
* **Blind Status:** Yes
* **SSI Rules:** ❌ Do not apply
* **Applicable Expense Framework:**

  * ✅ IRWE — *POMS DI 10520.000*
  * ✅ Blind Self‑Employment Evaluation — *POMS DI 10515.005*

❌ **SSI Blind Work Expenses (BWE) must never be used.**

---

## 3. Income Classification Rules

### 3.1 Wage Income (W‑2)

* Definition: Salary paid via payroll as a corporate officer.
* Source: Google Sheets entries where `Type = W2`.
* Treatment:

  * Included in SGA evaluation.
  * Subject to IRWE subtraction (if enabled).

### 3.2 Distributions (K‑1 / Owner Draws)

* Definition: Non‑wage shareholder distributions.
* Source: Google Sheets entries where `Type = DIST`.
* Treatment:

  * ❌ Never counted as wages.
  * ❌ Never directly included in SGA dollar calculations.
  * ⚠️ May trigger **work‑activity risk review** if owner intervention exists.

### 3.3 Trust Transfers

* Default Flow (Locked):

  * **S‑Corp → Owner → Trust** (Scenario B)
* Treatment:

  * Trust transfers are **post‑income allocations**, not earnings.
  * Phoenix tracks totals for governance only.

---

## 4. IRWE (Impairment‑Related Work Expenses)

### 4.1 Eligibility

IRWE deductions apply **only if**:

* Expense is directly related to the impairment, AND
* Paid out‑of‑pocket by the beneficiary, AND
* Properly documented.

### 4.2 Allowed IRWE Categories (Non‑Exhaustive)

* Transportation related to impairment
* Reader services
* Visual aids / assistive devices
* Other SSA‑approved impairment‑related costs

### 4.3 Explicitly Disallowed

* ❌ Federal or state income taxes
* ❌ Generic meals
* ❌ Non‑impairment business expenses

### 4.4 Logic Rule

```
Countable_Earnings = Gross_W2_Wages − IRWE_Total
```

IRWE subtraction is **config‑gated**:

* If IRWE is disabled → use gross W‑2
* If IRWE is enabled → subtract only documented IRWE

---

## 5. SGA Safety Evaluation (Blind SSDI)

### 5.1 Threshold

* **SGA_LIMIT_BLIND** (year‑locked; updated only during January governance window)

### 5.2 Rule

```
IF Countable_Earnings > SGA_LIMIT_BLIND
THEN ALERT_CRITICAL
```

* Alert = **Human intervention required**
* Phoenix does not change values automatically.

---

## 6. Reasonable Compensation (IRS — Advisory Only)

### 6.1 Variable

* `MIN_REASONABLE_COMP`

### 6.2 Rule

```
IF Annual_W2 < MIN_REASONABLE_COMP
THEN WARN_IRS_AUDIT_RISK
```

* Warning only.
* No enforcement.
* No SSA impact.

---

## 7. Work Activity & Actor Attribution

### 7.1 Actor Field (Required)

Every ledger entry must declare:

* `PHOENIX`
* `OWNER`
* `NOTARY_AGENT`

### 7.2 Human Intervention Minutes

* Required for OWNER‑attributed entries.
* `0` indicates full AI autonomy.

### 7.3 Risk Flag

```
IF Actor = OWNER AND HumanInterventionMinutes > 0
THEN FLAG_WORK_ACTIVITY_REVIEW
```

This flag is informational and narrative‑supporting, not punitive.

---

## 8. Data Source of Truth (Locked)

* **Primary Authority:** Google Sheets
* **Role:** Sole numeric source for Phoenix calculations
* **Sync:** On‑demand execution

Secondary sources (bank, accounting software) are **non‑authoritative** and used only for reconciliation.

---

## 9. Required Sheet Schema (Minimum)

| Column                   | Purpose                                |
| ------------------------ | -------------------------------------- |
| Date                     | Transaction date                       |
| Type                     | W2 / IRWE / DIST / EXP                 |
| Amount                   | Numeric                                |
| Description              | Human‑readable                         |
| Category                 | Salary / Transportation / Distribution |
| Actor                    | PHOENIX / OWNER / NOTARY_AGENT         |
| HumanInterventionMinutes | 0 if autonomous                        |
| EvidenceLink             | Required for IRWE                      |
| Notes                    | Optional                               |

---

## 10. Explicit Prohibitions

Phoenix must **never**:

* Auto‑adjust salary
* Auto‑adjust distributions
* Auto‑transfer funds
* Deduct non‑IRWE expenses
* Assume IRWE exists
* Treat Sheets formulas as authoritative

---

## 11. Change Control

* Logic changes allowed **only** during:

  * January governance window, OR
  * Emergency authority override
* All changes must be documented.

---

## 12. Completion Statement

This document completes **Phase 3.2 — Logic Scaffold**.

Python implementation may proceed **only** if it conforms to this file in full.

---

**End of Document**
