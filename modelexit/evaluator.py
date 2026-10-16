"""Deterministic scoring of model outputs against gold labels.

Design rules (SPEC.md / DATA_CONTRACTS.md):
- compare each field exactly after the canonicalization done in ``contracts``;
- an invalid or failed response is a recorded failure, never a pass;
- all metrics report their denominators; recall is ``None`` ("N/A") when the
  gold denominator is zero — no division by zero, ever;
- ``critical_case`` is derived from GOLD labels only: priority == "high" or
  needs_human is True. A miss on priority or needs_human for such a case
  blocks a READY recommendation.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from .contracts import FIELDS, ParsedOutput, Predicted, SupportCase, parse_model_output, truncate_raw


class InferenceError(BaseModel):
    """A transport/protocol-level failure (connection, timeout, HTTP, empty)."""

    kind: str
    message: str


class CaseOutcome(BaseModel):
    """Everything recorded for one evaluated case."""

    case: SupportCase
    raw_response: Optional[str] = None
    parse_mode: str = "failed"
    parse_error: Optional[str] = None
    predicted: Optional[Predicted] = None
    inference_error: Optional[InferenceError] = None
    field_correct: dict[str, bool]
    exact_match: bool
    latency_ms: int = 0
    model_id: str = ""
    critical: bool = False
    critical_miss: bool = False

    @property
    def invalid(self) -> bool:
        """True when the model call or its JSON output failed."""
        return self.inference_error is not None or self.parse_error is not None


def is_critical(case: SupportCase) -> bool:
    """Critical-case definition uses GOLD labels, not the prediction."""
    return case.expected.priority == "high" or case.expected.needs_human


def _order_id_equal(predicted: Optional[str], expected: Optional[str]) -> bool:
    # Values are already trimmed by the contracts layer; compare exactly.
    return predicted == expected


def evaluate_case(
    case: SupportCase,
    raw_response: Optional[str],
    latency_ms: int,
    model_id: str,
    inference_error: Optional[InferenceError] = None,
) -> CaseOutcome:
    """Score one case. The raw response is stored truncated for export."""
    if inference_error is not None:
        parsed = ParsedOutput(ok=False, parse_mode="failed", error=inference_error.message)
    else:
        parsed = parse_model_output(raw_response)

    predicted = parsed.prediction if parsed.ok else None
    field_correct = {field: False for field in FIELDS}
    if predicted is not None:
        field_correct = {
            "category": predicted.category == case.expected.category,
            "priority": predicted.priority == case.expected.priority,
            "needs_human": predicted.needs_human == case.expected.needs_human,
            "order_id": _order_id_equal(predicted.order_id, case.expected.order_id),
        }
    exact_match = predicted is not None and all(field_correct.values())

    critical = is_critical(case)
    # An invalid response counts as a miss on both critical fields.
    critical_miss = critical and not (
        field_correct["priority"] and field_correct["needs_human"]
    )

    parse_error = parsed.error if (inference_error is None and not parsed.ok) else None

    return CaseOutcome(
        case=case,
        raw_response=truncate_raw(raw_response),
        parse_mode=parsed.parse_mode,
        parse_error=parse_error,
        predicted=predicted,
        inference_error=inference_error,
        field_correct=field_correct,
        exact_match=exact_match,
        latency_ms=latency_ms,
        model_id=model_id,
        critical=critical,
        critical_miss=critical_miss,
    )


class Metrics(BaseModel):
    """Aggregate metrics; every rate carries its denominator implicitly."""

    total_cases: int = 0
    successful_calls: int = 0
    inference_errors: int = 0
    parse_errors: int = 0
    invalid_responses: int = 0
    exact_matches: int = 0
    exact_match_rate: Optional[float] = None
    field_correct_counts: dict[str, int] = {}
    field_accuracy: dict[str, Optional[float]] = {}
    gold_high_count: int = 0
    high_priority_recall: Optional[float] = None
    gold_needs_human_count: int = 0
    needs_human_recall: Optional[float] = None
    critical_case_count: int = 0
    critical_pass_count: int = 0
    critical_miss_ids: list[str] = []
    total_latency_ms: int = 0
    avg_latency_ms: Optional[float] = None
    max_latency_ms: int = 0


def _rate(numerator: int, denominator: int) -> Optional[float]:
    return (numerator / denominator) if denominator else None


def compute_metrics(outcomes: list[CaseOutcome]) -> Metrics:
    """Aggregate outcomes over ALL cases, counting model errors as failures."""
    total = len(outcomes)
    if total == 0:
        return Metrics(
            field_correct_counts={f: 0 for f in FIELDS},
            field_accuracy={f: None for f in FIELDS},
        )

    field_counts = {field: sum(1 for o in outcomes if o.field_correct[field]) for field in FIELDS}
    field_accuracy = {field: _rate(field_counts[field], total) for field in FIELDS}

    exact_matches = sum(1 for o in outcomes if o.exact_match)
    successful = sum(1 for o in outcomes if o.inference_error is None)
    inference_errors = total - successful
    parse_errors = sum(1 for o in outcomes if o.parse_error is not None)
    invalid = sum(1 for o in outcomes if o.invalid)

    gold_high = [o for o in outcomes if o.case.expected.priority == "high"]
    gold_needs_human = [o for o in outcomes if o.case.expected.needs_human]

    critical = [o for o in outcomes if o.critical]
    critical_misses = [o.case.id for o in critical if o.critical_miss]

    latencies = [o.latency_ms for o in outcomes]
    total_latency = sum(latencies)

    return Metrics(
        total_cases=total,
        successful_calls=successful,
        inference_errors=inference_errors,
        parse_errors=parse_errors,
        invalid_responses=invalid,
        exact_matches=exact_matches,
        exact_match_rate=_rate(exact_matches, total),
        field_correct_counts=field_counts,
        field_accuracy=field_accuracy,
        gold_high_count=len(gold_high),
        high_priority_recall=_rate(
            sum(1 for o in gold_high if o.field_correct["priority"]), len(gold_high)
        ),
        gold_needs_human_count=len(gold_needs_human),
        needs_human_recall=_rate(
            sum(1 for o in gold_needs_human if o.field_correct["needs_human"]),
            len(gold_needs_human),
        ),
        critical_case_count=len(critical),
        critical_pass_count=sum(1 for o in critical if not o.critical_miss),
        critical_miss_ids=critical_misses,
        total_latency_ms=total_latency,
        avg_latency_ms=(total_latency / total) if total else None,
        max_latency_ms=max(latencies) if latencies else 0,
    )
