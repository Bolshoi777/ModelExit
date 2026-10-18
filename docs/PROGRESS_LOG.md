# PROGRESS LOG (OpenCode updates after major milestones)

> The kit contains instructions, **not a finished application**. Every entry below starts NOT RUN. Change statuses ONLY based on actual code/run evidence.

## Stage status
| Stage | Status | Git commit | Verification | Blockers |
|---|---|---|---|---|
| A. Parser, evaluator, decision | DONE | `feat: add labelled workload and deterministic evaluation` | **G1 PASS** (6/6, 0.13 s; 1 fix + 1 rerun) | — |
| B. Real local LM Studio + UI | DONE | `fix: classify reasoning-model responses` (max_tokens fix) | **G2 PASS** (initial FAIL → 1 fix → rerun PASS: 6/6 calls, exact 4/6, invalid 0/6, 65.9 s) | — |
| C. Frontier + Passport | DONE | `feat: run local open-weight workload evaluation and export migration passport` + `fix: export per-case raw responses in the passport` | **G3 PASS** (3/3, 0.16 s first run; 3/3, 0.33 s rerun after the raw-export fix) | — |
| D. Windows README + video evidence | DONE; post-G4 small fix pass (static review, see gate log); video + public links = operator | `fix: export per-case raw responses in the passport` | **G4 PASS** — one UI journey: 12-case real run `3521c8420411`, JSON + MD passports downloaded through the UI and opened (measured outcome NOT READY; 177.7 s) | Recording/publishing by operator |
| E. English contest post published | NOT STARTED | — | Public link NOT AVAILABLE | Draft filled from real results in `templates/DEV_POST_DRAFT.md` |

## Environment (record only actual details)
- Windows version: Windows 11 Pro; CPU Intel i5-12600KF; RAM 31.9 GB
- Python: 3.11.6 in `.venv` (streamlit 1.66.0, pydantic 2.14.1, httpx 0.28.1, pytest 9.1.1)
- LM Studio: server "Running" at http://127.0.0.1:1234 (OpenAI-compatible `/v1`); version not recorded; operator-managed
- Model ID: `google/gemma-4-12b-qat` read from `GET /v1/models` (2026-10-18); LM Studio label "QAT", 7.15 GB; exact quantization format not captured
- GPU/RAM: NVIDIA GeForce RTX 3060 (VRAM variant not captured); RAM 31.9 GB
- Repo URL: local repo only; GitHub publication pending (operator)

## Measured results (no invented figures) — reference run `3521c8420411` (UI, 12 cases)
- Dataset: synthetic bundled `samples/support_cases.jsonl` (sha256 a6d7b70d…f369a); status completed_with_errors; calls succeeded 11/12 (1 timeout S10, no retry; 0 parse errors)
- Exact-match: 6/12 (50%); fields: category 9/12, priority 11/12, needs_human 8/12, order_id 11/12
- Recall: high-priority 2/2 (100%); needs_human 2/3 (67%); critical cases passed 2/3 — miss `S10`
- Decision: NOT READY (critical miss S10) — honest measured outcome, not an app failure
- Frontier: P01/P02/P04 stable_pass; P03 both_fail (needs_human over-triggered on billing disputes); P05 both_fail (+ timeout); P06 both_fail (category error; injection did not hijack S12's structured output)
- Latency: total 152,515 ms / avg 12,710 ms / max 21,828 ms; wall run 177.7 s
- G2 gate run `e95819ad13e7` (6 cases): exact 4/6, invalid 0/6, recall 1/1, 65.9 s — artifacts `docs/evidence/g2_gate_passport.json/.md`
- Evidence: `docs/evidence/g4_ui_run_passport.json/.md` (downloaded via UI buttons during G4; exported before the `cases[]` raw-export fix)
- Demo evidence link: video pending (operator)

## Gate invocation log (append only)
Date/time | Gate | Command | Duration | Outcome | Re-run count | Details
---|---|---|---|---|---|---
2026-10-16 | G1 | `.venv\Scripts\python.exe -m pytest tests/test_core.py -q` | 0.13 s | **PASS** | 1 fix + 1 rerun | 6 tests: JSONL/CSV import validation, correct prediction, critical miss blocks Ready, malformed JSON recorded + critical-malformed blocks Ready, zero-denominator safety. First run 5/6: single malformed non-critical case returns INSUFFICIENT (rule), test expectation fixed and reason text now discloses invalid count.
2026-10-16 | G3 | `.venv\Scripts\python.exe -m pytest tests/test_passport.py -q` | 0.16 s | **PASS** | 0 (first run) | 3 tests: passport JSON round-trip + measured counts, dataset/model identification + synthetic warning, Markdown export non-blank with decision/model/frontier. Runs use an explicitly test-only simulator client; the app never uses it.
2026-10-16 | UI boot check (non-gate, no model) | `streamlit run app.py` + browser load/interactions | ~2 min | **PASS** | 2 boots (1 fix: `use_container_width` → `width` API) | Rendered Run/Failures/Passport tabs; connection section shows honest manual-id fallback when server is down; bundled sample loads (12 cases + SHA-256 + synthetic label); Failures/Passport empty states correct; zero console errors; after the width-API fix the server log is free of deprecation warnings. No model calls involved (LM Studio was down).

2026-10-18 (UTC+3) | G2 (initial) | `run_cli.py --model "google/gemma-4-12b-qat" --cases 6 --out results/g2_run` | 14.1 s | **FAIL** | — | All 3 attempted calls returned HTTP 200 with empty `message.content`; runner stopped after 3 consecutive `empty_response` failures; decision NOT READY (honest, no fake pass). One diagnostic probe showed the model is a reasoning model: 157 reasoning tokens consumed the whole 160-token budget (`finish_reason=length`).
2026-10-18 (UTC+3) | G2 (rerun, 1 fix) | same command | 65.9 s | **PASS** | 1 (post-fix) | Fix (measured): `max_tokens` 160 → 900 (13.5 s/call probe at 900) + explicit `empty_content_reasoning_only` classification. Rerun: 6/6 genuine LM Studio calls succeeded; exact 4/6 (67%); high-priority recall 1/1; needs_human recall 1/1; invalid responses 0/6; no critical misses; S05/S06 over-triggered needs_human (P03 `both_fail`); decision INSUFFICIENT EVIDENCE (6 < 10 cases) — correct rule behavior. Artifacts: `results/g2_run.json` + `.md`.
2026-10-18 (UTC+3) | G3 (rerun, 1 fix) | `.venv\Scripts\python.exe -m pytest tests/test_passport.py -q` | 0.33 s | **PASS** | 1 (post-fix) | Found that the Markdown footer claimed raw responses are preserved in the JSON passport while the export omitted them (SPEC.md item 4 requires storing the raw response per case). Fix: added a `cases[]` section with per-case records incl. truncated raw output (≤600 chars) + matching assertions. 3/3 tests pass.
2026-10-18 (UTC+3) | G4 (release journey, one pass) | Streamlit UI via browser: Check connection → Load bundled sample → Run "12 cases" → Failures tab → Passport tab → download JSON + MD | 177.7 s run + ~2 min interactions | **PASS** (journey) / measured outcome NOT READY | 0 | Real 12-case run `3521c8420411` on `google/gemma-4-12b-qat`: 11/12 calls ok (S10 hit the 25 s cap, no retry), exact 6/12 (50%), critical miss S10 → NOT READY per rule. Frontier: P01/P02/P04 stable_pass; P03/P05/P06 both_fail. Both passports downloaded through the UI buttons, copied to `docs/evidence/`, opened and verified.

2026-10-18 (UTC+3) | Fix pass after static review (operator-authorized; not a gate) | `.venv\Scripts\python.exe -m pytest tests/test_core.py tests/test_passport.py -q` | 0.18 s | **PASS** (9/9) | 1 targeted command | Five findings fixed: (1) the runner recorded `latency_ms=0` for failed calls, so the 25 s S10 timeout was missing from the latency stats (G4 total 152.5 s vs 177.7 s wall time) — failed calls now record their measured time-to-failure; (2) switching the case-source radio kept a stale loaded dataset (app.py now clears it via `on_change`); (3) exported-text grammar ("1 of 12 responses was invalid"); (4) the timeout error message now names the read/connect limits instead of only the read value; (5) the Markdown passport now states the latency definition. UI boot check after restart (non-gate, no model calls): radio up→down switches with 0 exceptions, bundled sample loads (12 cases + SHA-256), "Check connection" → "Connected — 18 model(s)", Run button enabled.

## Next task
Code and docs complete (incl. the fix pass above). Operator-only steps: (1) record the ~2:30 video per `docs/DEMO_SCRIPT.md` on the current build (LM Studio running; `streamlit run app.py`) — a fresh run may differ slightly from `3521c8420411`, and timeouts now also appear in the latency figures; (2) create the public GitHub repo and push (commands in `docs/PUBLISH_STEPS.md`); (3) fill the video + repo links in `templates/DEV_POST_DRAFT.md` and publish on DEV before the deadline.
