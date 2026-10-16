"""Headless bounded evaluation — same core as the UI, for reproducible logs.

Examples (PowerShell, from the repo root):
    .\\.venv\\Scripts\\python.exe run_cli.py --list-models
    .\\.venv\\Scripts\\python.exe run_cli.py --model "<exact id>" --cases 6
    .\\.venv\\Scripts\\python.exe run_cli.py --model "<exact id>" --cases 12 --out results/run1

The CLI makes no cloud calls and performs no retries; it exits with code 2 when
the server is unreachable or no call succeeded.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from modelexit.dataset import bound_cases, load_bundled_sample, load_dataset_path
from modelexit.lm_client import DEFAULT_BASE_URL, LMStudioClient, LMStudioError
from modelexit.passport import build_passport, passport_to_json, passport_to_markdown
from modelexit.runner import RunConfig, run_evaluation

MAX_EVAL_CASES = 12


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bounded ModelExit evaluation against a local LM Studio server."
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"default {DEFAULT_BASE_URL}")
    parser.add_argument("--model", help="Exact model id from GET /v1/models (required to run)")
    parser.add_argument("--cases", type=int, default=MAX_EVAL_CASES, help="cases to evaluate (capped at 12)")
    parser.add_argument("--dataset", help="path to CSV/JSONL; default: bundled synthetic sample")
    parser.add_argument("--synthetic", action="store_true", help="declare the dataset as synthetic fixtures")
    parser.add_argument("--timeout", type=float, default=25.0, help="seconds per model call (default 25)")
    parser.add_argument("--out", help="output prefix for .json/.md passports, e.g. results/g2_run")
    parser.add_argument("--list-models", action="store_true", help="list models and exit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = LMStudioClient(args.base_url, timeout_s=args.timeout)

    try:
        models = client.list_models()
    except LMStudioError as exc:
        print(f"LM Studio unavailable: [{exc.kind}] {exc.message}")
        return 2

    print(f"Server OK: {args.base_url}")
    for model in models:
        marker = "  <== requested" if model.id == args.model else ""
        print(f"  - {model.id}{marker}")
    if args.list_models:
        return 0

    if not args.model:
        print("--model is required to run an evaluation (choose one of the ids above).")
        return 2
    if args.model not in {m.id for m in models}:
        print(
            f"WARNING: '{args.model}' is not in the server's model list; "
            "the call may fail — verify the id from GET /v1/models."
        )

    dataset = (
        load_dataset_path(Path(args.dataset), synthetic=args.synthetic)
        if args.dataset
        else load_bundled_sample()
    )
    max_cases = max(1, min(args.cases, MAX_EVAL_CASES))
    cases = bound_cases(dataset.cases, max_cases)
    print(
        f"Dataset: {dataset.name} · sha256 {dataset.sha256[:16]}… · "
        f"evaluating {len(cases)} of {dataset.case_count} cases"
    )

    config = RunConfig(
        base_url=args.base_url,
        model_id=args.model,
        max_cases=max_cases,
        timeout_s=args.timeout,
    )

    def on_progress(done: int, total: int, outcome) -> None:
        verdict = "PASS" if outcome.exact_match else ("INVALID" if outcome.invalid else "FAIL")
        print(f"  [{done}/{total}] {outcome.case.id}: {verdict} ({outcome.latency_ms} ms)")

    report = run_evaluation(
        cases,
        config,
        dataset_name=dataset.name,
        dataset_sha256=dataset.sha256,
        dataset_synthetic=dataset.synthetic,
        client=client,
        progress_callback=on_progress,
    )

    metrics = report.metrics
    recall = "N/A" if metrics.high_priority_recall is None else f"{metrics.high_priority_recall:.1%}"
    print("---")
    print(f"Model: {args.model}")
    print(f"Run id: {report.run_id} · status: {report.status} · elapsed {report.elapsed_s:.1f}s")
    print(f"Exact match: {metrics.exact_matches}/{metrics.total_cases}")
    print(
        f"Invalid responses: {metrics.invalid_responses} "
        f"(call errors {metrics.inference_errors}, parse errors {metrics.parse_errors})"
    )
    print(f"High-priority recall: {recall} (gold-high cases: {metrics.gold_high_count})")
    print(f"Critical misses: {', '.join(metrics.critical_miss_ids) or 'none'}")
    print(f"Decision: {report.decision.status}")
    for reason in report.decision.reasons:
        print(f"  - {reason}")

    if args.out:
        passport = build_passport(report)
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        json_path = out.with_suffix(".json")
        md_path = out.with_suffix(".md")
        json_path.write_text(passport_to_json(passport), encoding="utf-8")
        md_path.write_text(passport_to_markdown(passport), encoding="utf-8")
        print(f"Passport written: {json_path} and {md_path}")

    return 0 if metrics.successful_calls > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
