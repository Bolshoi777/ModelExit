# PROGRESS LOG (OpenCode updates after major milestones)

> The kit contains instructions, **not a finished application**. Every entry below starts NOT RUN. Change statuses ONLY based on actual code/run evidence.

## Stage status
| Stage | Status | Git commit | Verification | Blockers |
|---|---|---|---|---|
| A. Parser, evaluator, decision | DONE | `feat: add labelled workload and deterministic evaluation` | **G1 PASS** (6/6, 0.13 s; 1 fix + 1 rerun) | — |
| B. Real local LM Studio + UI | CODE WRITTEN (lm_client, runner, app.py, run_cli.py) | pending | G2 NOT RUN — LM Studio server was down on 2026-10-16 | Operator must start LM Studio |
| C. Frontier + Passport | CODE WRITTEN (frontier, passport, UI tabs) | pending | G3 NOT RUN | — |
| D. Windows README + video evidence | NOT STARTED | — | G4 NOT RUN | — |
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

## Next task
Stage B gate G2: real LM Studio run of 6 cases (operator starts server, loads model) — then Stage C gate G3 and Stage D README/polish.
