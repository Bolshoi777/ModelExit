"""Typed contracts and conservative parsing for ModelExit.

Everything that comes back from the local model is untrusted input. Parsing is
strict first (a pure JSON object); if that fails there is exactly ONE bounded
recovery attempt: extract the first balanced ``{...}`` object from surrounding
text. Anything else is recorded as a parse failure — never "repaired" with
extra model calls.

Canonicalization rules (see DATA_CONTRACTS.md):
- categorical enums (``category``, ``priority``): trim whitespace + lowercase;
- ``order_id``: trim only; empty string becomes ``null``; integers are kept as
  their digits; floats/booleans are rejected;
- ``needs_human``: strict boolean, tolerating only ``true/false/1/0``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

CATEGORIES: tuple[str, ...] = ("billing", "technical", "account", "other")
PRIORITIES: tuple[str, ...] = ("low", "medium", "high")
FIELDS: tuple[str, ...] = ("category", "priority", "needs_human", "order_id")

MAX_TICKET_CHARS = 3000
MAX_RAW_RESPONSE_CHARS = 600


def utc_now_iso() -> str:
    """UTC timestamp used in every exported artifact."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _canon_categorical(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("must be a string")
    return value.strip().lower()


def parse_bool_strict(value: Any) -> bool:
    """Accept only unambiguous booleans for human/CSV input.

    ``True``/``False``, ``1``/``0`` and the strings ``"true"``/``"false"``
    (case-insensitive, surrounding whitespace ignored). Everything else —
    including ``"yes"``/``"no"`` — is rejected as ambiguous.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        token = value.strip().lower()
        if token in ("true", "1"):
            return True
        if token in ("false", "0"):
            return False
    raise ValueError("needs_human must be an unambiguous boolean (true/false/1/0)")


class Expected(BaseModel):
    """Gold labels provided with the dataset. Never produced by the model."""

    model_config = ConfigDict(extra="forbid")

    category: str
    priority: str
    needs_human: bool
    order_id: Optional[str]

    @field_validator("category")
    @classmethod
    def _check_category(cls, value: Any) -> str:
        value = _canon_categorical(value)
        if value not in CATEGORIES:
            raise ValueError(f"unknown category {value!r}; expected one of {', '.join(CATEGORIES)}")
        return value

    @field_validator("priority")
    @classmethod
    def _check_priority(cls, value: Any) -> str:
        value = _canon_categorical(value)
        if value not in PRIORITIES:
            raise ValueError(f"unknown priority {value!r}; expected one of {', '.join(PRIORITIES)}")
        return value

    @field_validator("needs_human", mode="before")
    @classmethod
    def _check_needs_human(cls, value: Any) -> bool:
        return parse_bool_strict(value)

    @field_validator("order_id", mode="before")
    @classmethod
    def _trim_order_id(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, str):
            raise ValueError("order_id must be a string or null")
        value = value.strip()
        return value or None


class SupportCase(BaseModel):
    """One labelled support ticket loaded from JSONL/CSV."""

    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    expected: Expected
    pair_id: Optional[str] = None
    dimension: Optional[str] = None
    source: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def _check_id(cls, value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("id must be a non-empty string")
        return value.strip()

    @field_validator("text", mode="before")
    @classmethod
    def _check_text(cls, value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("text must be a non-empty string")
        if len(value) > MAX_TICKET_CHARS:
            raise ValueError(f"text exceeds {MAX_TICKET_CHARS} characters")
        return value

    @field_validator("pair_id", "dimension", "source", mode="before")
    @classmethod
    def _trim_optional(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("must be a string or null")
        value = value.strip()
        return value or None


class Predicted(BaseModel):
    """Parsed model output, canonicalized per DATA_CONTRACTS.

    Unknown extra keys are ignored (the four contract fields are still what
    gets scored); there is no partial credit for prose.
    """

    model_config = ConfigDict(extra="ignore")

    category: str
    priority: str
    needs_human: bool
    order_id: Optional[str]

    @field_validator("category")
    @classmethod
    def _check_category(cls, value: Any) -> str:
        value = _canon_categorical(value)
        if value not in CATEGORIES:
            raise ValueError(f"unknown category {value!r}")
        return value

    @field_validator("priority")
    @classmethod
    def _check_priority(cls, value: Any) -> str:
        value = _canon_categorical(value)
        if value not in PRIORITIES:
            raise ValueError(f"unknown priority {value!r}")
        return value

    @field_validator("needs_human", mode="before")
    @classmethod
    def _check_needs_human(cls, value: Any) -> bool:
        return parse_bool_strict(value)

    @field_validator("order_id", mode="before")
    @classmethod
    def _canon_order_id(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, bool):
            raise ValueError("order_id must be a string, number or null")
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            raise ValueError("order_id must not be a float")
        if not isinstance(value, str):
            raise ValueError("order_id must be a string, number or null")
        value = value.strip()
        return value or None


ParseMode = Literal["strict", "extracted", "failed"]


class ParsedOutput(BaseModel):
    """Result of parsing one raw model response."""

    ok: bool
    parse_mode: ParseMode
    prediction: Optional[Predicted] = None
    error: Optional[str] = None


def _first_balanced_object(text: str) -> Optional[str]:
    """Return the first balanced {...} substring, ignoring braces in strings."""
    start = text.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            else:
                if char == '"':
                    in_string = True
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : index + 1]
        start = text.find("{", start + 1)
    return None


def _validation_summary(exc: ValidationError) -> str:
    """Short, one-line description of the first validation problem."""
    first = exc.errors()[0]
    location = ".".join(str(part) for part in first.get("loc", ())) or "output"
    return f"{location}: {first.get('msg', 'invalid value')}"


def parse_model_output(raw: Optional[str]) -> ParsedOutput:
    """Parse one raw model response into a :class:`Predicted` value.

    Returns ``ok=False`` with a short error string when no valid JSON object
    with the required fields can be recovered. The raw text is never altered
    and never sent back to the model.
    """
    if raw is None or not raw.strip():
        return ParsedOutput(ok=False, parse_mode="failed", error="empty response")

    text = raw.strip()
    payload: Optional[dict[str, Any]] = None
    mode: ParseMode = "strict"

    try:
        candidate = json.loads(text)
    except json.JSONDecodeError:
        extracted = _first_balanced_object(text)
        if extracted is None:
            return ParsedOutput(ok=False, parse_mode="failed", error="no JSON object found in response")
        try:
            candidate = json.loads(extracted)
        except json.JSONDecodeError as exc:
            return ParsedOutput(
                ok=False,
                parse_mode="failed",
                error=f"extracted JSON object could not be parsed ({exc.msg})",
            )
        mode = "extracted"

    if not isinstance(candidate, dict):
        return ParsedOutput(ok=False, parse_mode="failed", error="top-level JSON value is not an object")

    payload = candidate
    try:
        prediction = Predicted.model_validate(payload)
    except ValidationError as exc:
        return ParsedOutput(ok=False, parse_mode="failed", error=_validation_summary(exc))

    return ParsedOutput(ok=True, parse_mode=mode, prediction=prediction)


def truncate_raw(raw: Optional[str]) -> Optional[str]:
    """Truncate a raw response for storage/export (privacy + noise control)."""
    if raw is None:
        return None
    raw = raw.strip()
    if len(raw) <= MAX_RAW_RESPONSE_CHARS:
        return raw
    return raw[:MAX_RAW_RESPONSE_CHARS] + "…[truncated]"
