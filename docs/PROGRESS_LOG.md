# PROGRESS LOG (OpenCode updates after major milestones)

> The kit contains instructions, **not a finished application**. Every entry below starts NOT RUN. Change statuses ONLY based on actual code/run evidence.

## Stage status
| Stage | Status | Git commit | Verification | Blockers |
|---|---|---|---|---|
| A. Parser, evaluator, decision | DONE | `feat: add labelled workload and deterministic evaluation` | **G1 PASS** (6/6, 0.13 s; 1 fix + 1 rerun) | — |
| B. Real local LM Studio + UI | CODE COMPLETE (lm_client, runner, app.py, run_cli.py); UI full 3-tab build | see Stage C commit | G2 NOT RUN — LM Studio server was down on 2026-10-16 | Operator must start LM Studio + load model |
| C. Frontier + Passport | DONE | `feat: run local open-weight workload evaluation and export migration passport` | **G3 PASS** (3/3, 0.16 s, first run) | — |
| D. Windows README + video evidence | IN PROGRESS — README/LICENSE rewritten; docs/ reorg; CSV sample; DEMO_SCRIPT.md; PUBLISH_STEPS.md; DEV post draft; UI boot verified (no model) | `fix: replace deprecated use_container_width with width API` | G4 NOT RUN | Depends on G2 |
| E. English contest post published | NOT STARTED | — | Public link NOT AVAILABLE | — |

## Environment (record only actual details)
- Windows version: Windows 11 Pro; CPU Intel i5-12600KF; RAM 31.9 GB
- Python: 3.11.6 in `.venv` (streamlit 1.66.0, pydantic 2.14.1, httpx 0.28.1, pytest 9.1.1)
- LM Studio version: unknown (server not started during Stage A)
- Model ID and quantization: pending G2 (will be read from `GET /v1/models`)
- GPU/RAM if operator discloses: NVIDIA GeForce RTX 3060; RAM 31.9 GB (detected, operator may confirm)
- Repo URL: local repo only; GitHub publication pending

## Measured results (no invented figures)
- Dataset source: synthetic examples (bundled sample) / actual provided gold set:
- N cases:
- Exact-match:
- High-priority recall (denominator):
- Critical miss IDs:
- JSON parse errors:
- Latency (sample/method):
- Demo evidence link:

## Gate invocation log (append only)
Date/time | Gate | Command | Duration | Outcome | Re-run count | Details
---|---|---|---|---|---|---
2026-10-16 | G1 | `.venv\Scripts\python.exe -m pytest tests/test_core.py -q` | 0.13 s | **PASS** | 1 fix + 1 rerun | 6 tests: JSONL/CSV import validation, correct prediction, critical miss blocks Ready, malformed JSON recorded + critical-malformed blocks Ready, zero-denominator safety. First run 5/6: single malformed non-critical case returns INSUFFICIENT (rule), test expectation fixed and reason text now discloses invalid count.
2026-10-16 | G3 | `.venv\Scripts\python.exe -m pytest tests/test_passport.py -q` | 0.16 s | **PASS** | 0 (first run) | 3 tests: passport JSON round-trip + measured counts, dataset/model identification + synthetic warning, Markdown export non-blank with decision/model/frontier. Runs use an explicitly test-only simulator client; the app never uses it.
2026-10-16 | UI boot check (non-gate, no model) | `streamlit run app.py` + browser load/interactions | ~2 min | **PASS** | 2 boots (1 fix: `use_container_width` → `width` API) | Rendered Run/Failures/Passport tabs; connection section shows honest manual-id fallback when server is down; bundled sample loads (12 cases + SHA-256 + synthetic label); Failures/Passport empty states correct; zero console errors; after the width-API fix the server log is free of deprecation warnings. No model calls involved (LM Studio was down).

## Next task
Stage B gate G2: operator starts LM Studio and loads a model; then run 6 real cases via `run_cli.py --cases 6` and the Streamlit UI, inspect failures honestly (no cloud, no mocks) before G4.
