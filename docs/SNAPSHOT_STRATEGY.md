# SNAPSHOT_STRATEGY.md

This document describes how Phoenix stores immutable decision artifacts for audit, governance, and explainability.

## DecisionRecord Snapshots (Phoenix v4)

Phoenix core produces a `DecisionRecord` for each evaluation run. Adapters are responsible for persisting snapshots; core never writes files.

### Snapshot Format
- File type: JSON
- Contents: serialized `DecisionRecord` (see `core/decision_record.py`)

### Snapshot Location Convention
Store under:

`snapshots/YYYY/MM/decision_record_YYYY-MM_<timestamp>.json`

Example:
`snapshots/2026/02/decision_record_2026-02_2026-02-06T20-15-30.json`

### Governance Notes
- Snapshots support auditability and January governance diffs.
- Snapshots must never contain secrets (tokens, credentials).
