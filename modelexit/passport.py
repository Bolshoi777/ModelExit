"""Exit Passport export: JSON + Markdown with full provenance.

Every exported passport contains the factual run status, dataset identity
(name + SHA-256), the actual model id(s) reported by the local server, settings,
timestamp, measured counts with denominators, the curated Failure Frontier and
explicit limitations. No invented values, no secrets.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from .contracts import MAX_RAW_RESPONSE_CHARS
from .comparison import ComparisonReport
from .evaluator import CaseOutcome
from .frontier import PairReport, build_frontier
from .runner import RunRecord

SCHEMA_VERSION = "1.0"
PRODUCT = "ModelExit"

LIMITATIONS: list[str] = [
    "Small labelled workload (bundled cases are synthetic fixtures), not proof of production "
    "readiness, generalization or market demand.",
    "The readiness rule is a transparent MVP heuristic on this fixture; it is not a "
    "scientifically calibrated safety guarantee.",
    "Only four extractions are scored (category, priority, needs_human, order_id); tone, policy "
    "text and downstream actions are out of scope.",
    "The Failure Frontier shows curated paired cases that were actually evaluated; it does not "
    "claim to discover every possible failure mode.",
    "Any cloud-cost comparison would be a user-provided estimate, never an invoice or a "
    "measured commercial benchmark.",
]


def _rate_block(correct: int, total: int) -> dict[str, Any]:
    return {
        "correct": correct,
        "total": total,
        "rate": (correct / total) if total else None,
    }


def _case_record(outcome: CaseOutcome) -> dict[str, Any]:
    """Per-case audit record, including the truncated raw model output.

    SPEC.md (item 4) requires the raw response to be stored per case; this
    record makes it part of the exported passport instead of living only in
    the UI session.
    """
    error: Optional[str] = None
    if outcome.inference_error is not None:
        error = f"{outcome.inference_error.kind}: {outcome.inference_error.message}"
    elif outcome.parse_error is not None:
        error = f"parse_error: {outcome.parse_error}"
    return {
        "case_id": outcome.case.id,
        "pair_id": outcome.case.pair_id,
        "dimension": outcome.case.dimension,
        "text": outcome.case.text,
        "expected": outcome.case.expected.model_dump(),
        "predicted": outcome.predicted.model_dump() if outcome.predicted is not None else None,
        "exact_match": outcome.exact_match,
        "field_correct": dict(outcome.field_correct),
        "critical": outcome.critical,
        "critical_miss": outcome.critical_miss,
        "invalid": outcome.invalid,
        "error": error,
        "latency_ms": outcome.latency_ms,
        "raw_response": outcome.raw_response,
    }


def build_passport(run: RunRecord, comparison: Optional[ComparisonReport] = None) -> dict[str, Any]:
    """Assemble the passport dict from a completed RunRecord."""
    metrics = run.metrics
    model_ids = sorted({o.model_id for o in run.outcomes if o.model_id})

    warnings: list[str] = []
    if run.dataset_synthetic:
        warnings.append("Dataset is a bundled synthetic fixture; it is not real customer data.")
    if run.stopped_early:
        warnings.append(run.stop_reason or "Run stopped early after consecutive inference failures.")
    if metrics.invalid_responses:
        verb = "was" if metrics.invalid_responses == 1 else "were"
        warnings.append(
            f"{metrics.invalid_responses} of {metrics.total_cases} responses {verb} invalid "
            f"(call errors: {metrics.inference_errors}, parse errors: {metrics.parse_errors})."
        )
    if len(model_ids) > 1:
        warnings.append(f"Server reported multiple model ids during the run: {', '.join(model_ids)}.")

    frontier = build_frontier(run.outcomes)

    passport: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "product": PRODUCT,
        "created_at_utc": run.created_at_utc,
        "run_id": run.run_id,
        "run_status": run.status,
        "dataset": {
            "name": run.dataset_name,
            "sha256": run.dataset_sha256,
            "case_count_evaluated": run.cases_evaluated,
            "case_count_requested": run.cases_requested,
            "synthetic": run.dataset_synthetic,
        },
        "inference": {
            "provider": "LM Studio (localhost, OpenAI-compatible)",
            "base_url": run.config.base_url,
            "model_id_requested": run.config.model_id,
            "model_ids_reported": model_ids,
            "temperature": run.config.temperature,
            "max_tokens": run.config.max_tokens,
            "timeout_s_per_call": run.config.timeout_s,
            "calls_succeeded": metrics.successful_calls,
            "calls_total": metrics.total_cases,
        },
        "metrics": {
            "total_cases": metrics.total_cases,
            "exact_match": _rate_block(metrics.exact_matches, metrics.total_cases),
            "field_accuracy": {
                field: _rate_block(metrics.field_correct_counts.get(field, 0), metrics.total_cases)
                for field in ("category", "priority", "needs_human", "order_id")
            },
            "high_priority_recall": _rate_block(
                int(round((metrics.high_priority_recall or 0) * metrics.gold_high_count)),
                metrics.gold_high_count,
            ),
            "needs_human_recall": _rate_block(
                int(round((metrics.needs_human_recall or 0) * metrics.gold_needs_human_count)),
                metrics.gold_needs_human_count,
            ),
            "invalid_responses": metrics.invalid_responses,
            "inference_errors": metrics.inference_errors,
            "parse_errors": metrics.parse_errors,
            "critical_cases": {
                "total": metrics.critical_case_count,
                "passed": metrics.critical_pass_count,
                "miss_ids": list(metrics.critical_miss_ids),
            },
            "latency_ms": {
                "total": metrics.total_latency_ms,
                "average": metrics.avg_latency_ms,
                "max": metrics.max_latency_ms,
            },
            "run_elapsed_s": round(run.elapsed_s, 3),
        },
        "frontier": [report.model_dump() for report in frontier],
        "cases": [_case_record(outcome) for outcome in run.outcomes],
        "critical_miss_ids": list(metrics.critical_miss_ids),
        "decision": {
            "status": run.decision.status,
            "reasons": list(run.decision.reasons),
            "rule": run.decision.rule,
        },
        "limitations": list(LIMITATIONS),
        "warnings": warnings,
    }
    if comparison is not None:
        passport["cloud_comparison"] = comparison.model_dump()
    return passport


def passport_to_json(passport: dict[str, Any]) -> str:
    return json.dumps(passport, indent=2, ensure_ascii=False)


def _fmt_pct(block: dict[str, Any]) -> str:
    rate = block.get("rate")
    if rate is None:
        return f"N/A ({block.get('correct', 0)}/{block.get('total', 0)})"
    return f"{rate:.0%} ({block.get('correct', 0)}/{block.get('total', 0)})"


def _exact_block(side: dict[str, Any]) -> dict[str, Any]:
    return {
        "correct": side["exact_matches"],
        "total": side["total_cases"],
        "rate": side["exact_match_rate"],
    }


def _fmt_side(side: Optional[dict[str, Any]]) -> str:
    if side is None:
        return "—"
    predicted = side.get("predicted")
    if side.get("invalid"):
        outcome = f"INVALID — {side.get('error') or 'no parsed output'}"
    elif predicted is None:
        outcome = "no parsed output"
    else:
        outcome = (
            f"category={predicted.get('category')}, priority={predicted.get('priority')}, "
            f"needs_human={predicted.get('needs_human')}, order_id={predicted.get('order_id')}"
        )
    mark = "PASS" if side.get("exact_match") else "FAIL"
    return f"`{side.get('case_id')}` [{side.get('dimension') or '—'}] {mark}: {outcome}"


def passport_to_markdown(passport: dict[str, Any]) -> str:
    """Render the passport as a human-readable audit document."""
    metrics = passport["metrics"]
    dataset = passport["dataset"]
    inference = passport["inference"]
    decision = passport["decision"]

    lines: list[str] = []
    lines.append("# ModelExit — Exit Passport")
    lines.append("")
    lines.append(
        f"**Decision: {decision['status']}** · run `{passport['run_id']}` · "
        f"{passport['created_at_utc']} · status: {passport['run_status']}"
    )
    lines.append("")
    lines.append("## Dataset")
    lines.append("")
    lines.append(f"- Name: `{dataset['name']}`")
    lines.append(f"- SHA-256: `{dataset['sha256']}`")
    lines.append(
        f"- Cases evaluated: {dataset['case_count_evaluated']} of {dataset['case_count_requested']} requested"
    )
    lines.append(f"- Synthetic fixture: {'yes' if dataset['synthetic'] else 'no / not declared'}")
    lines.append("")
    lines.append("## Local inference")
    lines.append("")
    lines.append(f"- Provider: {inference['provider']}")
    lines.append(f"- Endpoint: `{inference['base_url']}`")
    lines.append(f"- Model requested: `{inference['model_id_requested']}`")
    reported = inference["model_ids_reported"] or ["(none — no successful call)"]
    lines.append(f"- Model id(s) reported by server: {', '.join('`' + m + '`' for m in reported)}")
    lines.append(
        f"- Settings: temperature={inference['temperature']}, max_tokens={inference['max_tokens']}, "
        f"timeout={inference['timeout_s_per_call']}s per call, no automatic retries"
    )
    lines.append(
        f"- Calls succeeded: {inference['calls_succeeded']} / {inference['calls_total']} · "
        f"run elapsed {metrics['run_elapsed_s']}s"
    )
    lines.append("")
    lines.append("## Measured results")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Exact match (all 4 fields) | {_fmt_pct(metrics['exact_match'])} |")
    for field, block in metrics["field_accuracy"].items():
        lines.append(f"| Field accuracy: `{field}` | {_fmt_pct(block)} |")
    lines.append(f"| High-priority recall | {_fmt_pct(metrics['high_priority_recall'])} |")
    lines.append(f"| needs_human recall | {_fmt_pct(metrics['needs_human_recall'])} |")
    lines.append(
        f"| Critical cases passed | {metrics['critical_cases']['passed']} / "
        f"{metrics['critical_cases']['total']} |"
    )
    lines.append(
        f"| Invalid responses (call or parse errors) | {metrics['invalid_responses']} / "
        f"{metrics['total_cases']} |"
    )
    lines.append(
        f"| Latency (total / average / max) | {metrics['latency_ms']['total']} ms / "
        f"{'N/A' if metrics['latency_ms']['average'] is None else round(metrics['latency_ms']['average'])} ms / "
        f"{metrics['latency_ms']['max']} ms |"
    )
    lines.append("")
    lines.append(
        "Latency is measured wall-clock per model call; failed calls contribute their "
        "time-to-failure, not zero."
    )
    lines.append("")

    miss_ids = passport["critical_miss_ids"]
    lines.append("## Critical misses")
    lines.append("")
    lines.append(", ".join(f"`{i}`" for i in miss_ids) if miss_ids else "None — no critical case missed.")
    lines.append("")

    lines.append("## Failure Frontier (curated pairs actually evaluated)")
    lines.append("")
    frontier = passport["frontier"]
    if not frontier:
        lines.append("No paired cases were part of this run.")
    for pair in frontier:
        lines.append(f"### Pair `{pair['pair_id']}` — {pair['label']}")
        lines.append("")
        lines.append(f"- Original: {_fmt_side(pair.get('original'))}")
        for side in pair.get("changed", []):
            lines.append(f"- Changed: {_fmt_side(side)}")
        lines.append(f"- {pair['note']}")
        lines.append("")

    lines.append("## Decision and reasons")
    lines.append("")
    for reason in decision["reasons"]:
        lines.append(f"- {reason}")
    lines.append("")
    lines.append(f"Rule applied: {decision['rule']}")
    lines.append("")

    lines.append("## Limitations and warnings")
    lines.append("")
    for warning in passport["warnings"]:
        lines.append(f"- ⚠ {warning}")
    for limitation in passport["limitations"]:
        lines.append(f"- {limitation}")
    lines.append("")
    lines.append(
        "Per-case raw responses (truncated to "
        f"{MAX_RAW_RESPONSE_CHARS} chars) are preserved in the JSON passport for audit."
    )
    lines.append("")
    comparison = passport.get("cloud_comparison")
    if comparison:
        lines.append("## Cloud vs Local Comparison")
        lines.append("")
        lines.append(
            f"Baseline: `{comparison['baseline_name']}` · matched cases: "
            f"{comparison['matched_case_count']} / {comparison['baseline_row_count']} · "
            f"origin: {'synthetic fixture' if comparison['baseline_synthetic'] else 'user-provided saved responses'} · "
            "saved responses only; no cloud API call was made."
        )
        lines.append("")
        lines.append("| Metric | Local | Cloud baseline |")
        lines.append("|---|---:|---:|")
        lines.append(
            f"| Exact match | {_fmt_pct(_exact_block(comparison['local']))} | "
            f"{_fmt_pct(_exact_block(comparison['cloud']))} |"
        )
        lines.append(
            f"| Invalid responses | {comparison['local']['invalid_responses']} / {comparison['local']['total_cases']} | "
            f"{comparison['cloud']['invalid_responses']} / {comparison['cloud']['total_cases']} |"
        )
        lines.append(
            f"| Critical misses | {len(comparison['local']['critical_miss_ids'])} | {len(comparison['cloud']['critical_miss_ids'])} |"
        )
        lines.append(
            f"| Average known latency | {comparison['local']['average_latency_ms'] if comparison['local']['average_latency_ms'] is not None else 'N/A'} ms | "
            f"{comparison['cloud']['average_latency_ms'] if comparison['cloud']['average_latency_ms'] is not None else 'N/A'} ms |"
        )
        lines.append("")
        lines.append(
            f"- Local wrong / cloud right: {len(comparison['local_wrong_cloud_right'])}"
        )
        lines.append(
            f"- Cloud wrong / local right: {len(comparison['cloud_wrong_local_right'])}"
        )
        lines.append(f"- Both wrong: {len(comparison['both_wrong'])}")
        for warning in comparison["warnings"]:
            lines.append(f"- Warning: {warning}")
        lines.append("")
    return "\n".join(lines)
