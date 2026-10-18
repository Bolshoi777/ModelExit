"""Conservative, transparent readiness policy.

This is an MVP heuristic, not a safety guarantee and not a deployment
endorsement. Every reason string carries exact measured counts so a reviewer
can audit the decision without trusting the model's own opinion.

Rules (ARCHITECTURE.md):
- NOT READY: any critical-case miss on ``priority`` or ``needs_human``
  (a case is critical when the GOLD label is priority=high or
  needs_human=true), or no successful model calls at all.
- READY FOR LIMITED PILOT: >= 10 labelled cases, zero critical-case misses,
  exact-match >= 0.85, zero invalid responses.
- INSUFFICIENT EVIDENCE: fewer than 10 labelled cases (without critical
  misses), or an empty run.
- NEEDS REVIEW: everything else.
"""

from __future__ import annotations

from pydantic import BaseModel

from .evaluator import CaseOutcome, Metrics

READY = "READY FOR LIMITED PILOT"
NOT_READY = "NOT READY"
INSUFFICIENT = "INSUFFICIENT EVIDENCE"
NEEDS_REVIEW = "NEEDS REVIEW"

MIN_CASES_FOR_READY = 10
MIN_EXACT_MATCH_FOR_READY = 0.85

RULE_TEXT = (
    "READY FOR LIMITED PILOT requires: at least 10 labelled cases, zero "
    "critical-case misses on priority/needs_human (critical = gold priority "
    "'high' or needs_human true), exact-match >= 85%, and zero invalid "
    "responses. Any critical miss => NOT READY. Fewer than 10 valid cases => "
    "INSUFFICIENT EVIDENCE. This is an MVP heuristic on a small synthetic "
    "workload, not a scientifically calibrated safety guarantee."
)


class Decision(BaseModel):
    status: str
    reasons: list[str]
    rule: str = RULE_TEXT


def _fmt_rate(value: float | None) -> str:
    return f"{value:.0%}" if value is not None else "N/A"


def decide(metrics: Metrics, outcomes: list[CaseOutcome]) -> Decision:
    """Apply the declared policy to measured metrics."""
    reasons: list[str] = []

    if metrics.total_cases == 0:
        return Decision(
            status=NOT_READY,
            reasons=["No cases were evaluated; nothing to recommend."],
        )

    if metrics.successful_calls == 0:
        error_kinds = sorted(
            {o.inference_error.kind for o in outcomes if o.inference_error is not None}
        )
        kinds = ", ".join(error_kinds) if error_kinds else "unknown"
        return Decision(
            status=NOT_READY,
            reasons=[
                f"0 of {metrics.total_cases} model calls succeeded "
                f"(error kinds: {kinds}); no evidence was produced."
            ],
        )

    if metrics.critical_miss_ids:
        miss_details = []
        for outcome in outcomes:
            if outcome.case.id in metrics.critical_miss_ids:
                wrong = [
                    field
                    for field in ("priority", "needs_human")
                    if not outcome.field_correct[field]
                ]
                miss_details.append(f"{outcome.case.id} ({'/'.join(wrong)})")
        reasons.append(
            f"Critical miss on {len(metrics.critical_miss_ids)} of "
            f"{metrics.critical_case_count} critical cases: {', '.join(miss_details)}. "
            "A critical miss always blocks a READY recommendation."
        )
        return Decision(status=NOT_READY, reasons=reasons)

    if metrics.total_cases < MIN_CASES_FOR_READY:
        invalid_note = ""
        if metrics.invalid_responses:
            verb = "was" if metrics.invalid_responses == 1 else "were"
            invalid_note = (
                f" {metrics.invalid_responses} of {metrics.total_cases} responses {verb} invalid "
                f"(call errors: {metrics.inference_errors}, parse errors: {metrics.parse_errors})."
            )
        reasons.append(
            f"Only {metrics.total_cases} labelled case(s) evaluated; "
            f"{MIN_CASES_FOR_READY} or more are required for a READY verdict. "
            f"Exact match so far: {metrics.exact_matches}/{metrics.total_cases} "
            f"({_fmt_rate(metrics.exact_match_rate)}); no critical misses.{invalid_note}"
        )
        return Decision(status=INSUFFICIENT, reasons=reasons)

    if metrics.invalid_responses == 0 and (
        metrics.exact_match_rate is not None
        and metrics.exact_match_rate >= MIN_EXACT_MATCH_FOR_READY
    ):
        reasons.append(
            f"Exact-match {metrics.exact_matches}/{metrics.total_cases} "
            f"({_fmt_rate(metrics.exact_match_rate)}) >= 85%; "
            f"{metrics.critical_pass_count}/{metrics.critical_case_count} critical cases passed; "
            "0 invalid responses. Valid only for this synthetic workflow — run a pilot "
            "with human review before removing cloud fallback."
        )
        return Decision(status=READY, reasons=reasons)

    if metrics.invalid_responses > 0:
        verb = "was" if metrics.invalid_responses == 1 else "were"
        reasons.append(
            f"{metrics.invalid_responses} of {metrics.total_cases} responses {verb} missing or "
            f"malformed (parse errors: {metrics.parse_errors}, call errors: "
            f"{metrics.inference_errors}); results are incomplete. "
            f"Exact-match {metrics.exact_matches}/{metrics.total_cases}."
        )
    else:
        reasons.append(
            f"Exact-match {metrics.exact_matches}/{metrics.total_cases} "
            f"({_fmt_rate(metrics.exact_match_rate)}) is below the 85% READY threshold; "
            "field-level failures need review before any migration."
        )
    return Decision(status=NEEDS_REVIEW, reasons=reasons)
