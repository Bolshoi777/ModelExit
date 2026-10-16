"""Bounded dataset import from JSONL/CSV with strict validation.

Rules (DATA_CONTRACTS.md):
- JSONL: one JSON object per non-empty line; mandatory fields ``id``, ``text``,
  ``expected``; optional ``pair_id``, ``dimension``, ``source``.
- CSV: columns ``id``, ``text``, ``category``, ``priority``, ``needs_human``,
  optional ``order_id``, ``pair_id``, ``dimension``.
- Unique ``id``, non-empty ``text`` (<= 3000 chars), known enums, unambiguous
  booleans. Errors carry line/row numbers.
- Hard cap: 24 cases accepted for upload; evaluation is bounded separately
  (default 12, see ``bound_cases``).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ValidationError

from .contracts import Expected, SupportCase, parse_bool_strict

MAX_UPLOAD_CASES = 24
DEFAULT_EVAL_CASES = 12
SMALL_EVAL_CASES = 6


class DatasetError(ValueError):
    """Raised when a dataset cannot be accepted. Message contains row info."""


class Dataset(BaseModel):
    """A validated, bounded set of labelled cases plus its provenance."""

    name: str
    sha256: str
    synthetic: bool
    cases: list[SupportCase]

    @property
    def case_count(self) -> int:
        return len(self.cases)


def sha256_hex(data: bytes) -> str:
    """SHA-256 of the exact file bytes; integrity check only, no security claim."""
    return hashlib.sha256(data).hexdigest()


def _first_error(exc: ValidationError) -> str:
    first = exc.errors()[0]
    location = ".".join(str(part) for part in first.get("loc", ())) or "record"
    return f"{location}: {first.get('msg', 'invalid value')}"


def _finalize(cases: list[SupportCase], name: str, data: bytes, synthetic: bool) -> Dataset:
    if not cases:
        raise DatasetError("dataset contains no cases")
    if len(cases) > MAX_UPLOAD_CASES:
        raise DatasetError(
            f"dataset has {len(cases)} cases; the maximum accepted is {MAX_UPLOAD_CASES}"
        )
    ids = [case.id for case in cases]
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    if duplicates:
        raise DatasetError(f"duplicate case ids: {', '.join(duplicates)}")
    return Dataset(name=name, sha256=sha256_hex(data), synthetic=synthetic, cases=cases)


def _format_errors(errors: list[str]) -> str:
    shown = errors[:5]
    suffix = f"\n(+{len(errors) - 5} more problems)" if len(errors) > 5 else ""
    return "\n".join(shown) + suffix


def load_jsonl_bytes(data: bytes, name: str, synthetic: bool = False) -> Dataset:
    """Parse a JSONL dataset; raise DatasetError with line numbers on problems."""
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DatasetError(f"{name}: not valid UTF-8 ({exc})") from exc

    cases: list[SupportCase] = []
    errors: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            errors.append(f"line {lineno}: invalid JSON ({exc.msg})")
            continue
        if not isinstance(payload, dict):
            errors.append(f"line {lineno}: record must be a JSON object")
            continue
        try:
            cases.append(SupportCase.model_validate(payload))
        except ValidationError as exc:
            errors.append(f"line {lineno}: {_first_error(exc)}")

    if errors:
        raise DatasetError(f"{name}: validation failed:\n{_format_errors(errors)}")
    return _finalize(cases, name, data, synthetic)


def load_csv_bytes(data: bytes, name: str, synthetic: bool = False) -> Dataset:
    """Parse a CSV dataset; raise DatasetError with row/line numbers on problems."""
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DatasetError(f"{name}: not valid UTF-8 ({exc})") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise DatasetError(f"{name}: empty CSV file")

    columns = {field.strip().lower(): field for field in reader.fieldnames if field}
    required = ("id", "text", "category", "priority", "needs_human")
    missing = [column for column in required if column not in columns]
    if missing:
        raise DatasetError(f"{name}: missing required columns: {', '.join(missing)}")

    def get(row: dict[str, Any], column: str) -> str:
        raw = row.get(columns[column])
        return raw.strip() if isinstance(raw, str) else ""

    cases: list[SupportCase] = []
    errors: list[str] = []
    for row_index, row in enumerate(reader, start=1):
        line_number = row_index + 1  # header occupies line 1
        try:
            expected = Expected(
                category=get(row, "category"),
                priority=get(row, "priority"),
                needs_human=parse_bool_strict(get(row, "needs_human")),
                order_id=get(row, "order_id") if "order_id" in columns else None,
            )
            case = SupportCase(
                id=get(row, "id"),
                text=row.get(columns["text"], ""),
                expected=expected,
                pair_id=get(row, "pair_id") if "pair_id" in columns else None,
                dimension=get(row, "dimension") if "dimension" in columns else None,
                source="uploaded",
            )
        except ValidationError as exc:
            errors.append(f"row {row_index} (line {line_number}): {_first_error(exc)}")
            continue
        except ValueError as exc:
            errors.append(f"row {row_index} (line {line_number}): {exc}")
            continue
        cases.append(case)

    if errors:
        raise DatasetError(f"{name}: validation failed:\n{_format_errors(errors)}")
    return _finalize(cases, name, data, synthetic)


def load_dataset_bytes(data: bytes, name: str, synthetic: bool = False) -> Dataset:
    """Load a dataset, choosing the parser by file name / first byte."""
    lowered = name.lower()
    if lowered.endswith(".jsonl") or lowered.endswith(".ndjson"):
        return load_jsonl_bytes(data, name, synthetic=synthetic)
    if lowered.endswith(".csv"):
        return load_csv_bytes(data, name, synthetic=synthetic)
    first_char = ""
    for char in data.decode("utf-8-sig", errors="replace"):
        if not char.isspace():
            first_char = char
            break
    if first_char == "{":
        return load_jsonl_bytes(data, name, synthetic=synthetic)
    return load_csv_bytes(data, name, synthetic=synthetic)


def load_dataset_path(path: Path, synthetic: bool = False) -> Dataset:
    """Load a dataset from disk; the file's exact bytes are hashed."""
    data = path.read_bytes()
    return load_dataset_bytes(data, name=str(path.name), synthetic=synthetic)


def samples_dir() -> Path:
    """Directory holding the bundled synthetic fixtures."""
    return Path(__file__).resolve().parent.parent / "samples"


def bundled_sample_path() -> Path:
    return samples_dir() / "support_cases.jsonl"


def load_bundled_sample() -> Dataset:
    """The bundled synthetic workload, clearly labelled as synthetic."""
    path = bundled_sample_path()
    data = path.read_bytes()
    return load_jsonl_bytes(data, name="samples/support_cases.jsonl", synthetic=True)


def bound_cases(cases: list[SupportCase], max_cases: int = DEFAULT_EVAL_CASES) -> list[SupportCase]:
    """Deterministically bound a run to the first ``max_cases`` cases."""
    if max_cases < 1:
        raise ValueError("max_cases must be >= 1")
    return list(cases)[:max_cases]
