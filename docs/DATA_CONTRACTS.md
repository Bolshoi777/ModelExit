# DATA_CONTRACTS — precise, inspectable expectations

## Input file JSONL format
Each line is an independent JSON object, e.g.:
```json
{"id":"S01","text":"Please send an invoice for order #4521.","expected":{"category":"billing","priority":"low","needs_human":false,"order_id":"4521"},"pair_id":"P01","dimension":"original","source":"synthetic"}
```
All fields mandatory except `pair_id` / `dimension` for user files. `id` unique, UTF-8, <=3,000 chars/ticket; no empty `text`; max 12 evaluated by default. Expected data must be independently supplied, never predicted by model.

CSV input requires columns: `id`, `text`, `category`, `priority`, `needs_human`; `order_id`, `pair_id`, and `dimension` are optional. A missing or empty `order_id` maps to null. Parse `needs_human` (`true/false/1/0`), reject ambiguous booleans and unknown enums, and show clear validation errors with row number.

## Model output schema
```json
{"category":"billing","priority":"medium","needs_human":false,"order_id":"4521"}
```
Untrusted outputs MUST parse into known enums, boolean and nullable string; extra prose and invalid JSON count as failure. Do not automatically repair by sending more inference calls. Record error kind and truncated raw response.

## Gold-label policy
- `billing`: refunds, invoices, payments, charges.
- `technical`: software outages/errors, app feature failures.
- `account`: account access/security changes.
- `other`: general product enquiries unrelated to above.
- `high`: urgent service outages or acute security incidents (explicit), not ordinary refund discussions.
- `needs_human=true`: urgent/security-sensitive or multi-intent ambiguous cases requiring review. Not 'anything the AI feels uncertain about'.
- `order_id` only when an explicit recognizable identifier follows `order`, `order #` or an unambiguous order reference; others null.
The above policy is a synthetic-demo rubric only; do not market it as universal support triage guidelines.

## Test pair design
A `pair_id` groups original with one controlled meaning change, if present. Use `dimension` such as `original`, `negation`, `urgency`, `multi_intent`, `no_order_id`. Expectation can legitimately change! Never assume all transformations preserve labels.

## Result per case
```
{
  "id": "S01", "pair_id": "P01", "dimension": "original",
  "expected": {...}, "predicted": {...} | null,
  "field_correct": {"category": true, "priority": true, "needs_human": true, "order_id": true},
  "exact_match": true, "parse_error": null,
  "latency_ms": 1234, "model_id": "ACTUAL_ID"
}
```
Only assign `field_correct=true` for actual valid parsed output. For any inference error set false for all fields. `model_id` must be actual identifier.

## Aggregate metrics
- `exact_match = number_full_field_matches / N`.
- `category_accuracy = correct_categories / N` etc.
- `high_priority_recall = number of gold-high predicted high / number of gold-high`, else N/A.
- `critical_misses`: gold high or gold needs_human true where model misses `priority` or `needs_human`. Reason always show IDs.
- `invalid_response_rate = invalid_model_responses / N`.
- `paired_regressions`: within pair, original exact pass and edge exact fail. If original fails too, label `both_fail`, not regression.
- `latency`: measured wall clock per model call, not an advertised GPU benchmark.

## Output Passport fields
```
{
  "schema_version": "1.0", "created_at_utc": "...", "product": "ModelExit",
  "dataset": {"name": "...", "sha256": "...", "case_count": 12, "synthetic": true},
  "inference": {"provider": "LM Studio localhost", "model_id": "...", "base_url": "127.0.0.1", "temperature": 0, "max_tokens": 900},
  "metrics": {...}, "frontier": [...], "critical_miss_ids": [...],
  "decision": {"status": "...", "reasons": [...]},
  "limitations": ["Small synthetic workload; not a proof of production readiness", "Cloud cost values are user-provided estimates, if any"]
}
```
Never include secret API keys or assume a model licence. Add actual model and terms as verified by operator.

## Optional saved cloud baseline

The Run tab may accept a saved-response baseline for comparison; this is data import only and
does not call a cloud provider. JSONL rows require `id` plus either `response` / `raw_response` or
all four prediction fields. CSV requires `id` and `response`; `latency_ms` is optional. Response
values may be a JSON object or raw JSON text. Rows are matched to the currently loaded labelled
dataset by `id`, capped at 24, and scored against the same gold labels. Missing/extra IDs and
unknown latency values are disclosed. Baseline results never change the local readiness decision.
