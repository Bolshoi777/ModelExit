"""Serial, bounded evaluation runner shared by the Streamlit UI and the CLI.

Guarantees (SPEC.md acceptance criteria):
- at most ``max_cases`` model calls, strictly serial, 1 in-flight request;
- no automatic retries; each call bounded by the client timeout;
- early stop after 3 *consecutive inference failures of the same kind*
  (connection/timeout/HTTP) so a dead server cannot burn the whole budget —
  this is failure detection, not a retry;
- parse errors do NOT stop the run: malformed model output is part of what the
  app measures;
- every outcome is stored, successes and failures alike.
"""

from __future__ import annotations

import time
import uuid
from typing import Callable, Iterable, Optional

from pydantic import BaseModel

from .contracts import SupportCase, utc_now_iso
from .decision import Decision, decide
from .evaluator import CaseOutcome, InferenceError, Metrics, compute_metrics, evaluate_case
from .lm_client import DEFAULT_BASE_URL, LMStudioClient, LMStudioError

CONSECUTIVE_FAILURE_LIMIT = 3

ProgressCallback = Callable[[int, int, CaseOutcome], None]


class RunConfig(BaseModel):
    """Everything that shapes a run; stored verbatim in the passport."""

    base_url: str = DEFAULT_BASE_URL
    model_id: str = ""
    max_cases: int = 12
    temperature: float = 0.0
    max_tokens: int = 900
    timeout_s: float = 25.0


class RunRecord(BaseModel):
    """Full, replayable record of one evaluation run."""

    run_id: str
    created_at_utc: str
    dataset_name: str
    dataset_sha256: str
    dataset_synthetic: bool
    cases_evaluated: int
    cases_requested: int
    config: RunConfig
    outcomes: list[CaseOutcome]
    metrics: Metrics
    decision: Decision
    elapsed_s: float
    stopped_early: bool = False
    stop_reason: Optional[str] = None

    @property
    def status(self) -> str:
        if self.stopped_early:
            return "aborted_after_consecutive_failures"
        if self.metrics.invalid_responses > 0:
            return "completed_with_errors"
        return "completed"


def run_evaluation(
    cases: Iterable[SupportCase],
    config: RunConfig,
    dataset_name: str,
    dataset_sha256: str,
    dataset_synthetic: bool,
    client: Optional[LMStudioClient] = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> RunRecord:
    """Run the bounded serial evaluation and return a complete record.

    ``client`` can be injected in unit tests; in production it is a real
    LM Studio client. Nothing here retries a failed call.
    """
    cases = list(cases)
    client = client or LMStudioClient(config.base_url, timeout_s=config.timeout_s)

    outcomes: list[CaseOutcome] = []
    consecutive_kind: Optional[str] = None
    consecutive_count = 0
    stopped_early = False
    stop_reason: Optional[str] = None

    started = time.perf_counter()
    total = len(cases)
    for index, case in enumerate(cases):
        try:
            result = client.chat_classify(
                config.model_id,
                case.text,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            outcome = evaluate_case(
                case,
                raw_response=result.raw_text,
                latency_ms=result.latency_ms,
                model_id=result.model_id or config.model_id,
            )
            consecutive_kind, consecutive_count = None, 0
        except LMStudioError as exc:
            outcome = evaluate_case(
                case,
                raw_response=None,
                latency_ms=0,
                model_id=config.model_id,
                inference_error=InferenceError(kind=exc.kind, message=exc.message),
            )
            if exc.kind == consecutive_kind:
                consecutive_count += 1
            else:
                consecutive_kind, consecutive_count = exc.kind, 1
        except Exception as exc:  # unexpected client bug: recorded, never hidden
            outcome = evaluate_case(
                case,
                raw_response=None,
                latency_ms=0,
                model_id=config.model_id,
                inference_error=InferenceError(kind="unexpected_error", message=str(exc)),
            )
            consecutive_kind, consecutive_count = "unexpected_error", consecutive_count + 1

        outcomes.append(outcome)
        if progress_callback is not None:
            progress_callback(index + 1, total, outcome)

        if consecutive_count >= CONSECUTIVE_FAILURE_LIMIT:
            stopped_early = True
            stop_reason = (
                f"Stopped after {consecutive_count} consecutive inference failures "
                f"of kind '{consecutive_kind}' at case {case.id}; remaining cases were "
                "not attempted (no retries)."
            )
            break

    elapsed_s = time.perf_counter() - started
    metrics = compute_metrics(outcomes)
    decision = decide(metrics, outcomes)

    return RunRecord(
        run_id=uuid.uuid4().hex[:12],
        created_at_utc=utc_now_iso(),
        dataset_name=dataset_name,
        dataset_sha256=dataset_sha256,
        dataset_synthetic=dataset_synthetic,
        cases_evaluated=len(outcomes),
        cases_requested=total,
        config=config,
        outcomes=outcomes,
        metrics=metrics,
        decision=decision,
        elapsed_s=elapsed_s,
        stopped_early=stopped_early,
        stop_reason=stop_reason,
    )
