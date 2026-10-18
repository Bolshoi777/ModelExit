"""Optional cloud-baseline comparison for an existing local evaluation.

The baseline is a saved response file, never a live provider call. Gold labels
always come from the already loaded labelled dataset and local readiness remains
the sole source of the migration decision.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .contracts import SupportCase
from .dataset import MAX_UPLOAD_BYTES, MAX_UPLOAD_CASES
from .evaluator import CaseOutcome, compute_metrics, evaluate_case

if TYPE_CHECKING:
    from .runner import RunRecord


class ComparisonError(ValueError):
    """Raised when a saved baseline cannot be safely matched to labelled cases."""


class BaselineRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    raw_response: Optional[str] = None
    latency_ms: Optional[int] = Field(default=None, ge=0)


class CloudBaseline(BaseModel):
    name: str
    sha256: str
    synthetic: bool = False
    rows: list[BaselineRow]


class SideMetrics(BaseModel):
    total_cases: int
    exact_matches: int
    exact_match_rate: Optional[float]
    field_correct_counts: dict[str, int]
    field_accuracy: dict[str, Optional[float]]
    invalid_responses: int
    critical_case_count: int
    critical_pass_count: int
    critical_miss_ids: list[str]
    known_latency_count: int
    total_latency_ms: int
    average_latency_ms: Optional[float]
    max_latency_ms: Optional[int]


class ComparisonCase(BaseModel):
    case_id: str
    text: str
    local_exact_match: bool
    cloud_exact_match: bool
    local_invalid: bool
    cloud_invalid: bool
    local_field_correct: dict[str, bool]
    cloud_field_correct: dict[str, bool]
    local_predicted: Optional[dict[str, Any]] = None
    cloud_predicted: Optional[dict[str, Any]] = None
    cloud_error: Optional[str] = None
    cloud_latency_ms: Optional[int] = None


class ComparisonReport(BaseModel):
    baseline_name: str
    baseline_sha256: str
    baseline_synthetic: bool
    matched_case_count: int
    baseline_row_count: int
    missing_local_case_ids: list[str]
    extra_baseline_case_ids: list[str]
    local: SideMetrics
    cloud: SideMetrics
    exact_match_delta_points: Optional[float]
    local_wrong_cloud_right: list[ComparisonCase]
    cloud_wrong_local_right: list[ComparisonCase]
    both_wrong: list[ComparisonCase]
    cases: list[ComparisonCase]
    warnings: list[str] = []


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _short_error(exc: Exception) -> str:
    return str(exc).splitlines()[0][:240]


def _parse_latency(value: Any, location: str) -> Optional[int]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ComparisonError(f"{location}: latency_ms must be a non-negative integer") from exc
    if number < 0:
        raise ComparisonError(f"{location}: latency_ms must be a non-negative integer")
    return number


def _response_to_raw(value: Any, location: str) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    raise ComparisonError(f"{location}: response must be a JSON object, string or null")


def _row_from_payload(payload: dict[str, Any], location: str) -> BaselineRow:
    case_id = payload.get("id", payload.get("case_id"))
    if not isinstance(case_id, str) or not case_id.strip():
        raise ComparisonError(f"{location}: id must be a non-empty string")
    if "response" in payload:
        raw = _response_to_raw(payload.get("response"), location)
    elif "raw_response" in payload:
        raw = _response_to_raw(payload.get("raw_response"), location)
    elif all(field in payload for field in ("category", "priority", "needs_human", "order_id")):
        raw = json.dumps(
            {field: payload[field] for field in ("category", "priority", "needs_human", "order_id")},
            ensure_ascii=False,
            separators=(",", ":"),
        )
    else:
        raise ComparisonError(f"{location}: add response (JSON/text) or all four prediction fields")
    try:
        return BaselineRow(
            case_id=case_id.strip(),
            raw_response=raw,
            latency_ms=_parse_latency(payload.get("latency_ms"), location),
        )
    except ValidationError as exc:
        raise ComparisonError(f"{location}: {_short_error(exc)}") from exc


def _finalize(rows: list[BaselineRow], name: str, data: bytes, synthetic: bool = False) -> CloudBaseline:
    if not rows:
        raise ComparisonError(f"{name}: no baseline rows found")
    if len(rows) > MAX_UPLOAD_CASES:
        raise ComparisonError(f"{name}: maximum {MAX_UPLOAD_CASES} baseline rows accepted")
    ids = [row.case_id for row in rows]
    duplicates = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    if duplicates:
        raise ComparisonError(f"{name}: duplicate case ids: {', '.join(duplicates)}")
    return CloudBaseline(name=name, sha256=_sha256(data), synthetic=synthetic, rows=rows)


def load_baseline_jsonl_bytes(data: bytes, name: str, synthetic: bool = False) -> CloudBaseline:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ComparisonError(f"{name}: file exceeds the 256 KiB upload limit")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ComparisonError(f"{name}: not valid UTF-8") from exc
    rows: list[BaselineRow] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if len(rows) >= MAX_UPLOAD_CASES:
            raise ComparisonError(f"{name}: maximum {MAX_UPLOAD_CASES} baseline rows accepted")
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ComparisonError(f"{name}: line {line_no}: invalid JSON ({exc.msg})") from exc
        if not isinstance(payload, dict):
            raise ComparisonError(f"{name}: line {line_no}: record must be an object")
        rows.append(_row_from_payload(payload, f"line {line_no}"))
    return _finalize(rows, name, data, synthetic=synthetic)


def load_baseline_csv_bytes(data: bytes, name: str, synthetic: bool = False) -> CloudBaseline:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ComparisonError(f"{name}: file exceeds the 256 KiB upload limit")
    try:
        text = data.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or "id" not in {f.strip().lower() for f in reader.fieldnames if f}:
            raise ComparisonError(f"{name}: CSV requires an id column")
        columns = {field.strip().lower(): field for field in reader.fieldnames if field and field.strip()}
        if len(columns) != len(reader.fieldnames):
            raise ComparisonError(f"{name}: CSV headers must be non-empty and unique")
        rows: list[BaselineRow] = []
        for row_no, row in enumerate(reader, start=2):
            if len(rows) >= MAX_UPLOAD_CASES:
                raise ComparisonError(f"{name}: maximum {MAX_UPLOAD_CASES} baseline rows accepted")
            payload = {key: row.get(source) for key, source in columns.items()}
            rows.append(_row_from_payload(payload, f"row {row_no}"))
    except csv.Error as exc:
        raise ComparisonError(f"{name}: invalid CSV ({exc})") from exc
    return _finalize(rows, name, data, synthetic=synthetic)


def load_baseline_bytes(data: bytes, name: str, synthetic: bool = False) -> CloudBaseline:
    lowered = name.lower()
    if lowered.endswith((".jsonl", ".ndjson")):
        return load_baseline_jsonl_bytes(data, name, synthetic=synthetic)
    if lowered.endswith(".csv"):
        return load_baseline_csv_bytes(data, name, synthetic=synthetic)
    first = next((char for char in data.decode("utf-8-sig", errors="replace") if not char.isspace()), "")
    return (
        load_baseline_jsonl_bytes(data, name, synthetic=synthetic)
        if first == "{"
        else load_baseline_csv_bytes(data, name, synthetic=synthetic)
    )


def _side_metrics(outcomes: list[CaseOutcome], known_latency_ids: set[str]) -> SideMetrics:
    metrics = compute_metrics(outcomes)
    known = [o.latency_ms for o in outcomes if o.case.id in known_latency_ids]
    return SideMetrics(
        total_cases=metrics.total_cases,
        exact_matches=metrics.exact_matches,
        exact_match_rate=metrics.exact_match_rate,
        field_correct_counts=dict(metrics.field_correct_counts),
        field_accuracy=dict(metrics.field_accuracy),
        invalid_responses=metrics.invalid_responses,
        critical_case_count=metrics.critical_case_count,
        critical_pass_count=metrics.critical_pass_count,
        critical_miss_ids=list(metrics.critical_miss_ids),
        known_latency_count=len(known),
        total_latency_ms=sum(known),
        average_latency_ms=(sum(known) / len(known)) if known else None,
        max_latency_ms=max(known) if known else None,
    )


def _comparison_case(local: CaseOutcome, cloud: CaseOutcome, cloud_latency_ms: Optional[int]) -> ComparisonCase:
    error = None
    if cloud.inference_error is not None:
        error = f"{cloud.inference_error.kind}: {cloud.inference_error.message}"
    elif cloud.parse_error is not None:
        error = cloud.parse_error
    return ComparisonCase(
        case_id=local.case.id,
        text=local.case.text,
        local_exact_match=local.exact_match,
        cloud_exact_match=cloud.exact_match,
        local_invalid=local.invalid,
        cloud_invalid=cloud.invalid,
        local_field_correct=dict(local.field_correct),
        cloud_field_correct=dict(cloud.field_correct),
        local_predicted=local.predicted.model_dump() if local.predicted else None,
        cloud_predicted=cloud.predicted.model_dump() if cloud.predicted else None,
        cloud_error=error,
        cloud_latency_ms=cloud_latency_ms,
    )


def compare_run(run: "RunRecord", baseline: CloudBaseline) -> ComparisonReport:
    local_by_id = {outcome.case.id: outcome for outcome in run.outcomes}
    baseline_by_id = {row.case_id: row for row in baseline.rows}
    matched_ids = [case_id for case_id in local_by_id if case_id in baseline_by_id]
    missing = [case_id for case_id in local_by_id if case_id not in baseline_by_id]
    extra = [case_id for case_id in baseline_by_id if case_id not in local_by_id]
    cloud_outcomes: list[CaseOutcome] = []
    cloud_latency_ids: set[str] = set()
    cases: list[ComparisonCase] = []
    for case_id in matched_ids:
        local = local_by_id[case_id]
        row = baseline_by_id[case_id]
        cloud = evaluate_case(
            local.case,
            raw_response=row.raw_response,
            latency_ms=row.latency_ms or 0,
            model_id="cloud-baseline",
        )
        cloud_outcomes.append(cloud)
        if row.latency_ms is not None:
            cloud_latency_ids.add(case_id)
        cases.append(_comparison_case(local, cloud, row.latency_ms))
    local_matched = [local_by_id[case_id] for case_id in matched_ids]
    report_cases = {case.case_id: case for case in cases}
    local_wrong_cloud_right = [report_cases[c] for c in matched_ids if not local_by_id[c].exact_match and report_cases[c].cloud_exact_match]
    cloud_wrong_local_right = [report_cases[c] for c in matched_ids if not report_cases[c].cloud_exact_match and local_by_id[c].exact_match]
    both_wrong = [report_cases[c] for c in matched_ids if not local_by_id[c].exact_match and not report_cases[c].cloud_exact_match]
    local_metrics = _side_metrics(local_matched, {outcome.case.id for outcome in local_matched})
    cloud_metrics = _side_metrics(cloud_outcomes, cloud_latency_ids)
    origin = "synthetic fixture" if baseline.synthetic else "user-provided saved-response file"
    warnings = [
        f"Cloud baseline is a {origin}; ModelExit made no cloud API calls.",
        "This comparison is descriptive evidence on the matched sample, not proof of safety or generalization.",
    ]
    if missing:
        warnings.append(f"Baseline is missing {len(missing)} locally evaluated case(s): {', '.join(missing)}.")
    if extra:
        warnings.append(f"Baseline contains {len(extra)} case(s) not in this local run: {', '.join(extra)}.")
    delta = None
    if local_metrics.exact_match_rate is not None and cloud_metrics.exact_match_rate is not None:
        delta = (local_metrics.exact_match_rate - cloud_metrics.exact_match_rate) * 100
    return ComparisonReport(
        baseline_name=baseline.name,
        baseline_sha256=baseline.sha256,
        baseline_synthetic=baseline.synthetic,
        matched_case_count=len(matched_ids),
        baseline_row_count=len(baseline.rows),
        missing_local_case_ids=missing,
        extra_baseline_case_ids=extra,
        local=local_metrics,
        cloud=cloud_metrics,
        exact_match_delta_points=delta,
        local_wrong_cloud_right=local_wrong_cloud_right,
        cloud_wrong_local_right=cloud_wrong_local_right,
        both_wrong=both_wrong,
        cases=cases,
        warnings=warnings,
    )
