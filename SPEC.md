# ModelExit — Product Specification (48-hour MVP)

## Product promise
**ModelExit — know where your app can safely leave paid AI behind.** A locally run, open-weight-model-powered test bench that checks one narrow business workload against trusted expectations and produces a failure-aware migration recommendation and reproducible Exit Passport.

## Audience and business use
- Indie developer / small SaaS using expensive cloud classification/extraction for customer-support tickets.
- Decision: Is a **specific** local model reliable enough for a **limited pilot** on *this* task? Identify where human review remains mandatory.
- Plausible offer: paid migration-readiness assessment for a small SaaS, with a clear exported handoff report. Proposed business model is hypothetical until independently validated.

## Main scenario ONLY (no generic AI benchmarking suite)
Input: CSV or JSONL containing short customer-support messages and expected structured labels.
Output from local LLM: `{category, priority, needs_human, order_id}`.
Categories: `billing`, `technical`, `account`, `other`.
Priorities: `low`, `medium`, `high`.
`needs_human`: true/false. `order_id`: string or null.
All validation is against **provided gold labels**, not another language-model opinion.

## Mandatory flow (P0)
1. Dashboard shows connection to configurable local LM Studio endpoint (`http://localhost:1234/v1`), chosen model ID and connection/error state.
2. User loads built-in sample JSONL (synthetic, visibly labelled) OR uploads limited CSV/JSONL with trusted labels.
3. Click `Run Local Evaluation`; run bounded batch max 12 cases, no automatic retry; visible count/completion and elapsed time.
4. For each case: store model's raw response, parsed response or parse error, elapsed ms, expected labels, per-field pass/fail and error description.
5. Aggregate field accuracy **among all cases**, exact-match accuracy, malformed JSON rate, `high` priority recall (report `N/A` if no positives), and count (no invented population generalization). Show all denominators.
6. Show curated `Failure Frontier`: cases sharing a `pair_id`, inspect both and their individual outcomes; no synthetic claim of automatic discovery of all failure modes.
7. Decision card using declared rules: `READY FOR LIMITED PILOT` only if all critical high-priority and `needs_human=true` cases pass AND exact-match >= 85% for at least 10 labelled cases; `NOT READY` for any missed critical case; otherwise `INSUFFICIENT EVIDENCE` / `MANUAL REVIEW`. Threshold is an **MVP heuristic**, not a scientifically calibrated safety guarantee. Do not call any class globally safe.
8. Export **Exit Passport** JSON and Markdown with run metadata, tests, results, failures, recommendation, caveats and model fingerprint/ID.
9. Publish code/README and explain how to run without paid tokens/API.

## Major measurable novelty
- **Failure Frontier:** curated counterfactual tests clustered by semantic dimension (`negation`, `urgency`, `multi_intent`, `no_order_id`), not average accuracy alone.
- **Selective Exit:** transparent rule that refuses a recommendation on critical misses; does not automatically forward dangerous traffic.
- **Exit Passport:** replayable evaluation, auditability of assumptions, no fabricated cloud comparison.
- The system's open-weight LLM does real extraction/classification, not simply style editing. Removing LLM inference would break its main product flow.

## P1 only if P0 done early
- Economics view with optional user-supplied cloud per-token prices, expected token counts, volume, electricity and hardware assumptions. Show **estimated** numbers with formulas and sources; missing values => not calculable.
- Optional human-confirmation workflow for ambiguous gold labels.
- Optional second small fixture dataset; not required.

## Explicitly excluded
- Live interaction with commercial paid APIs; automatic source rewriting; 100-model leaderboards; automated model downloads; unbounded LLM-generated test cases; user accounts; multi-tenant hosting; training and fine-tuning; agent memory/RAG; CSV handling of large production databases; production traffic routing; auto-sent customer messages.

## User interface (English, Windows browser via Streamlit)
Three sections maximum:
- **Run:** model connection, source of cases, Run button, bounded progress.
- **Failures:** metrics with denominators, per-case table, paired frontier comparison, case details.
- **Passport:** recommendation with reasons, metadata, export/download.
Style: clean dark-neutral or light-neutral, with clear failure coloring, readable on 1366×768, no elaborate charts needed.

## Acceptance criteria
1. Python venv install succeeds from documented requirements on typical Windows 10/11 Python 3.11+.
2. Local OpenAI-compatible `/v1/models` and `/v1/chat/completions` are used and HTTP errors are shown honestly.
3. At least 8 (target 12) bundled synthetic labelled cases with clearly stated origins and edge-case pairs.
4. Complete run has finite duration: <=12 calls, <=25s/call, max 8 min including overhead, no hidden retries.
5. Clear parse-error handling, no silent fake passes.
6. Critical failure handling and denominators correct.
7. Downloadable Passport contains factual model name, dataset name/hash, evaluation timestamp, results and limitations.
8. GitHub readme has launch steps, screenshots or real video, honest limitations; DEV post submitted before deadline.

## Evidence standard
- `SUCCESS` claim only backed by live run or logged output.
- Synthetic dataset is **not** independent proof of market demand or generalization.
- If no external user tests the product, describe prospective buyer as hypothesis.
- A limited benchmark does not prove actual cloud-model equivalence.
