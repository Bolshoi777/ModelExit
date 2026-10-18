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

## Environment (public-safe summary)
- Windows 10/11-compatible local setup; machine-specific hardware is intentionally omitted from the public repository.
- Python: 3.11.6 in `.venv` (streamlit 1.66.0, pydantic 2.14.1, httpx 0.28.1, pytest 9.1.1)
- LM Studio: server "Running" at http://127.0.0.1:1234 (OpenAI-compatible `/v1`); version not recorded; operator-managed
- Model ID: `google/gemma-4-12b-qat` read from `GET /v1/models` (2026-10-18); LM Studio label "QAT", 7.15 GB; exact quantization format not captured
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

2026-10-18 (UTC+3) | Full suite re-run (operator-requested) | `.venv\Scripts\python.exe -m pytest tests/ -v` | 0.15 s | **PASS** (9/9) | 1 command | Complete deterministic set (G1 + G3 tests re-executed together as requested): all 6 core tests (JSONL/CSV import, correct prediction, critical miss blocks Ready, malformed JSON recorded, zero-denominator safety) and all 3 passport tests (JSON roundtrip + counts, dataset/model identification + warnings, meaningful Markdown) pass. No model, no network calls.

2026-10-18 (UTC+3) | Full live re-check (operator-requested; not a gate) | `run_cli.py --model "google/gemma-4-12b-qat" --cases 12 --out results/live_check` | 155.2 s | **PASS** (live path works end-to-end) / measured outcome NOT READY | 1 command, no retries | 11/12 calls succeeded; exact 6/12; S10 failed again (this time the model spent the whole 900-token budget on reasoning — `empty_content_reasoning_only`) → critical miss; frontier pattern identical to run `3521c8420411` (P01/P02/P04 stable_pass; P03/P05/P06 both_fail). First live run on the post-fix build: the passport records the failed call's measured time-to-failure (latency total 155,241 ms ≈ run elapsed 155.2 s; max 23,195 ms) and shows the singular grammar fix ("1 of 12 responses was invalid"). Artifacts: `results/live_check.*`; copies committed as `docs/evidence/postfix_cli_run_passport.*`.

2026-10-18 (UTC+3) | Final release review (checklist-based; no new runs) | Static review + existing gate logs (was: `ModelExit_RELEASE_CHECKLIST.md`) | — | Product side: **GO** | 0 runs | Filled the operator's release checklist from existing evidence. Fixed doc drift: `ARCHITECTURE.md` / `DATA_CONTRACTS.md` still said `max_tokens` 160 while the measured default is 900. Verified: no shell-exec/eval in code, loopback-only networking, no personal paths/secrets in tracked files, README/DEV-draft/passport consistency with RESULTS_LOG. Publication blockers are operator-only: GitHub repo, video, DEV post.

## Next task
Code and docs complete (incl. the fix pass above). Operator-only steps: (1) record the ~2:30 video per `docs/DEMO_SCRIPT.md` on the current build (LM Studio running; `streamlit run app.py`) — a fresh run may differ slightly from `3521c8420411`, and timeouts now also appear in the latency figures; (2) create the public GitHub repo and push (commands in `docs/PUBLISH_STEPS.md`); (3) fill the video + repo links in `templates/DEV_POST_DRAFT.md` and publish on DEV before the deadline.

## Post-review corrections (2026-10-18, UTC+3)

A focused static review found boundary issues outside the already completed G1–G4 gates. The
operator authorized one address check without model calls. Fixed: model output now requires all
four contract fields (including explicit `order_id: null`); `RunConfig` caps cases at 12, tokens at
4096 and per-call timeout at 25 seconds; LM Studio requests use a wall-clock deadline, disable
environment proxies and redirects, reject credentials/query/fragment and non-loopback hosts, and
validate response shapes; upload parsing caps files at 256 KiB and records duplicate/empty CSV
headers; replacing an upload uses a SHA-256 fingerprint and clears stale reports; an optional
12-case synthetic fixture was added at `samples/support_cases_extended.jsonl`.

Address check (one authorized run, no network/model calls; the CSV probe was run before the
compatibility adjustment described below):
`ADDRESS_CHECK_PASS Expected:missing-order-rejected; Predicted:missing-order-rejected; extended-jsonl:12-cases; csv-missing-order-rejected; url-rejected:example.com; url-rejected:user:pass@127.0.0.1:1234; url-rejected:127.0.0.1:0; timeout-over-25-rejected; runner-over-12-rejected`.

The CSV compatibility path intentionally keeps `order_id` optional and maps an empty or absent
column to `null`; the model response contract still requires the field explicitly. G1–G4 were not
rerun, and no additional LM Studio call was made.

## Operator-requested full judge-style run (2026-10-18, UTC+3)

One complete current-build UI journey was executed with LM Studio running: `Check connection` →
real model list (18 ids) → selected `google/gemma-4-12b-qat` → `Load bundled sample` →
`Run Local Evaluation` for 12 cases → `Failures` → `Passport` → JSON and Markdown downloads.

Result: run `de197dba9128`, 12/12 cases evaluated, 11/12 calls succeeded, 6/12 exact (50%),
high-priority recall 2/2 (100%), `needs_human` recall 2/3 (67%), critical cases passed 2/3,
invalid 1/12, elapsed 146.5 s, decision `NOT READY`. S10 was the single critical miss and was
classified as `empty_content_reasoning_only` after 23.5 s; no retry occurred. Frontier summary:
P01/P02/P04 `stable_pass`, P03/P05/P06 `both_fail`.

Passport downloads were opened and parsed. Evidence: `docs/evidence/final_ui_run_passport_de197dba9128.json`
and `docs/evidence/final_ui_run_passport_de197dba9128.md`; JSON contains 12 per-case records,
the actual model id, dataset hash, warnings, metrics, frontier and decision.

## Extended fixture + UI polish (2026-10-18, UTC+3)

Added a restrained visual layer in `app.py`: neutral background, consistent spacing, typography,
metric cards, tabs and status surfaces; removed decorative emoji from the decision/frontier labels.
No product logic or evaluation rule changed.

The new `samples/support_cases_extended.jsonl` was uploaded through the UI as synthetic data and
run against the real `google/gemma-4-12b-qat` model. The first run exposed one metadata issue in
EP03 (both records lacked an `original` dimension), so E06 was corrected to `original` and the
run was repeated once. Final run: `6afe7d0265ea`, 12/12 evaluated, 11/12 successful calls,
exact 7/12 (58%), high-priority recall 2/2 (100%), `needs_human` recall 3/4 (75%), critical
cases 3/4, invalid 1/12, elapsed 185.0 s, decision `NOT READY`. Frontier: EP01 improvement,
EP02 stable_pass, EP03 both_fail, EP04 improvement, EP05 regression, EP06 stable_pass.

Evidence: `docs/evidence/extended_ui_run_passport_6afe7d0265ea.json` and `.md`. The export has
12 per-case records, actual model id, corrected dataset hash, warnings and decision.

## Optional Cloud vs Local Comparison (2026-10-18, UTC+3)

Added `modelexit/comparison.py` and optional UI/passport integration. Users can upload saved
cloud responses as CSV/JSONL (`id`, `response`/`raw_response`, optional `latency_ms`); the file is
parsed locally and never sent to a provider. The comparison uses the same labelled cases and
does not alter the local readiness decision. It reports side-by-side exact/field accuracy,
invalid responses, critical misses, known latency, and directional disagreements.

Address check (one run, four cases, no network/model calls):
`COMPARISON_ADDRESS_CHECK_PASS {'matched': 4, 'local_wrong_cloud_right': ['C02'], 'cloud_wrong_local_right': ['C01'], 'both_wrong': ['C04'], 'cloud_invalid': 1, 'local_critical_misses': ['C04'], 'cloud_latency_known': 3}`.

UI boot smoke after the change: Streamlit rendered the optional baseline uploader after loading
the bundled dataset; no server log errors. Full pytest suite was not run.

## Final integration experiment (2026-10-18, UTC+3)

Per operator request, one full current-build UI experiment was completed with a new 12-case
synthetic workload and a 12-row synthetic saved-response baseline. LM Studio reported 18 models;
the selected real model was `google/gemma-4-12b-qat`. Run `b2d608e91866`: 12/12 cases,
11/12 successful calls, exact 7/12, high recall 3/3, needs_human recall 4/4, critical 4/4,
invalid 1/12 (`V05` reasoning-only response), elapsed 158.5 s, decision `NEEDS REVIEW`.

Comparison matched 12/12 IDs: local 7/12 exact vs synthetic baseline 7/12; local wrong/cloud
right `V05,V10,V11`; cloud wrong/local right `V04,V07,V08`; baseline critical misses `V07,V08`.
The baseline was synthetic and made no provider calls. Artifacts are in
`validation/final_experiment/`; final report status is **GO WITH LIMITATIONS**. No full pytest
suite or second inference run was performed.
