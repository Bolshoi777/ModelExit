"""Failure Frontier: curated paired cases, compared honestly.

The bundled dataset groups an *original* case with one controlled meaning
change (negation, urgency, multi-intent, missing order id, instruction
injection) under a shared ``pair_id``. This module reports what actually
happened on both sides — it never claims to have automatically discovered all
failure modes.

Labels for a pair (DATA_CONTRACTS.md):
- ``stable_pass``: both sides exact-match;
- ``regression``: original passed, changed side failed;
- ``improvement``: original failed, changed side passed;
- ``both_fail``: neither side matched (not a regression);
- ``mixed_partial``: at least one side produced valid output but neither side
  matched exactly and it is not a clean original-fail/changed-pass case.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from .evaluator import CaseOutcome


class PairSide(BaseModel):
    """Compact view of one side of a curated pair."""

    case_id: str
    dimension: Optional[str] = None
    text: str
    expected: dict
    predicted: Optional[dict] = None
    exact_match: bool
    field_correct: dict[str, bool]
    critical: bool
    critical_miss: bool
    invalid: bool
    error: Optional[str] = None
    latency_ms: int = 0


class PairReport(BaseModel):
    pair_id: str
    original: Optional[PairSide] = None
    changed: list[PairSide] = []
    label: str
    note: str = ""


def _side(outcome: CaseOutcome) -> PairSide:
    error: Optional[str] = None
    if outcome.inference_error is not None:
        error = f"{outcome.inference_error.kind}: {outcome.inference_error.message}"
    elif outcome.parse_error is not None:
        error = f"parse_error: {outcome.parse_error}"

    return PairSide(
        case_id=outcome.case.id,
        dimension=outcome.case.dimension,
        text=outcome.case.text,
        expected=outcome.case.expected.model_dump(),
        predicted=outcome.predicted.model_dump() if outcome.predicted is not None else None,
        exact_match=outcome.exact_match,
        field_correct=dict(outcome.field_correct),
        critical=outcome.critical,
        critical_miss=outcome.critical_miss,
        invalid=outcome.invalid,
        error=error,
        latency_ms=outcome.latency_ms,
    )


def _classify(original: Optional[PairSide], changed: list[PairSide]) -> tuple[str, str]:
    if original is None:
        if all(side.invalid for side in changed):
            return "changed_only_invalid", "No 'original' side in this pair and every changed case failed."
        return "changed_only", "No 'original' side in this pair (dimension='original')."
    if not changed:
        return "original_only", "No changed case found for this pair."

    any_invalid_changed = any(side.invalid for side in changed)
    changed_pass = any(side.exact_match for side in changed)
    changed_fail = any((not side.exact_match) for side in changed)

    if original.exact_match and changed_pass and not changed_fail:
        label, note = "stable_pass", "Original and changed case(s) all passed exactly."
    elif original.exact_match and changed_fail:
        label = "regression"
        failed_ids = ", ".join(side.case_id for side in changed if not side.exact_match)
        note = f"Original passed; changed case(s) {failed_ids} failed."
        if any_invalid_changed:
            note += " At least one changed side was malformed, not merely wrong."
    elif (not original.exact_match) and changed_pass:
        label, note = "improvement", "Original failed; the changed case(s) passed exactly."
    else:
        label, note = "both_fail", "Neither side matched exactly (not a regression)."

    critical_notes = [
        side.case_id for side in changed if side.critical_miss
    ]
    if critical_notes:
        note += f" Critical miss in: {', '.join(critical_notes)}."
    return label, note


def build_frontier(outcomes: list[CaseOutcome]) -> list[PairReport]:
    """Group evaluated cases by pair_id and classify each curated pair."""
    grouped: dict[str, list[CaseOutcome]] = {}
    for outcome in outcomes:
        pair_id = outcome.case.pair_id
        if not pair_id:
            continue
        grouped.setdefault(pair_id, []).append(outcome)

    reports: list[PairReport] = []
    for pair_id in sorted(grouped):
        members = grouped[pair_id]
        original_outcome = next(
            (o for o in members if (o.case.dimension or "").strip().lower() == "original"),
            None,
        )
        if original_outcome is None and len(members) == 1:
            original_outcome = members[0]
        changed_outcomes = [o for o in members if o is not original_outcome]

        original = _side(original_outcome) if original_outcome is not None else None
        changed = [_side(o) for o in changed_outcomes]
        label, note = _classify(original, changed)
        reports.append(PairReport(pair_id=pair_id, original=original, changed=changed, label=label, note=note))
    return reports


def frontier_summary(reports: list[PairReport]) -> dict[str, int]:
    """Counts by label for the headline UI line."""
    summary: dict[str, int] = {}
    for report in reports:
        summary[report.label] = summary.get(report.label, 0) + 1
    return summary
