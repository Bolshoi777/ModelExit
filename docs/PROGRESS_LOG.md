# PROGRESS LOG (OpenCode updates after major milestones)

> The kit contains instructions, **not a finished application**. Every entry below starts NOT RUN. Change statuses ONLY based on actual code/run evidence.

## Stage status
| Stage | Status | Git commit | Verification | Blockers |
|---|---|---|---|---|
| A. Parser, evaluator, decision | DONE | `feat: add labelled workload and deterministic evaluation` | **G1 PASS** (6/6, 0.13 s; 1 fix + 1 rerun) | — |
| B. Real local LM Studio + UI | DONE | `fix: classify reasoning-model responses` (max_tokens fix) | **G2 PASS** (initial FAIL → 1 fix → rerun PASS: 6/6 calls, exact 4/6, invalid 0/6, 65.9 s) | — |
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
- Dataset source: synthetic examples (bundled `samples/support_cases.jsonl`, sha256 a6d7b70d57b92d4f…)
- N cases: 6 (G2 gate run, 2026-10-18; final 12-case evidence at G4)
- Exact-match: 4/6 (67%)
- High-priority recall (denominator): 1/1 (100%); needs_human recall 1/1 (100%)
- Critical miss IDs: none
- JSON parse errors: 0/6; call errors 0/6
- Latency (sample/method): average 10,980 ms, max 13,005 ms per call; 65.9 s for 6 calls (wall clock)
- Failures observed: S05/S06 both predicted needs_human=true where gold is false (pair P03 `both_fail`); all other fields correct
- Demo evidence link: pending video (G4)

## Gate invocation log (append only)
Date/time | Gate | Command | Duration | Outcome | Re-run count | Details
---|---|---|---|---|---|---
2026-10-16 | G1 | `.venv\Scripts\python.exe -m pytest tests/test_core.py -q` | 0.13 s | **PASS** | 1 fix + 1 rerun | 6 tests: JSONL/CSV import validation, correct prediction, critical miss blocks Ready, malformed JSON recorded + critical-malformed blocks Ready, zero-denominator safety. First run 5/6: single malformed non-critical case returns INSUFFICIENT (rule), test expectation fixed and reason text now discloses invalid count.
2026-10-16 | G3 | `.venv\Scripts\python.exe -m pytest tests/test_passport.py -q` | 0.16 s | **PASS** | 0 (first run) | 3 tests: passport JSON round-trip + measured counts, dataset/model identification + synthetic warning, Markdown export non-blank with decision/model/frontier. Runs use an explicitly test-only simulator client; the app never uses it.
2026-10-16 | UI boot check (non-gate, no model) | `streamlit run app.py` + browser load/interactions | ~2 min | **PASS** | 2 boots (1 fix: `use_container_width` → `width` API) | Rendered Run/Failures/Passport tabs; connection section shows honest manual-id fallback when server is down; bundled sample loads (12 cases + SHA-256 + synthetic label); Failures/Passport empty states correct; zero console errors; after the width-API fix the server log is free of deprecation warnings. No model calls involved (LM Studio was down).

2026-10-18 (UTC+3) | G2 (initial) | `run_cli.py --model "google/gemma-4-12b-qat" --cases 6 --out results/g2_run` | 14.1 s | **FAIL** | — | All 3 attempted calls returned HTTP 200 with empty `message.content`; runner stopped after 3 consecutive `empty_response` failures; decision NOT READY (honest, no fake pass). One diagnostic probe showed the model is a reasoning model: 157 reasoning tokens consumed the whole 160-token budget (`finish_reason=length`).
2026-10-18 (UTC+3) | G2 (rerun, 1 fix) | same command | 65.9 s | **PASS** | 1 (post-fix) | Fix (measured): `max_tokens` 160 → 900 (13.5 s/call probe at 900) + explicit `empty_content_reasoning_only` classification. Rerun: 6/6 genuine LM Studio calls succeeded; exact 4/6 (67%); high-priority recall 1/1; needs_human recall 1/1; invalid responses 0/6; no critical misses; S05/S06 over-triggered needs_human (P03 `both_fail`); decision INSUFFICIENT EVIDENCE (6 < 10 cases) — correct rule behavior. Artifacts: `results/g2_run.json` + `.md`.

## Next task
Stage D gate G4: one manual UI journey — launch Streamlit, load bundled sample, 12-case real run, inspect Failures/Frontier, download and open JSON + Markdown passports; then record video and fill DEV post with the 12-case numbers.
