# ModelExit — Exit Passport

**Decision: NEEDS REVIEW** · run `b2d608e91866` · 2026-10-18T14:29:18+00:00 · status: completed_with_errors

## Dataset

- Name: `final_cases.jsonl`
- SHA-256: `3aa79b254bb9f530e7ae387c9dccfdf67970d2d26faef5ee52f9963ef9c091f8`
- Cases evaluated: 12 of 12 requested
- Synthetic fixture: yes

## Local inference

- Provider: LM Studio (localhost, OpenAI-compatible)
- Endpoint: `http://127.0.0.1:1234/v1`
- Model requested: `google/gemma-4-12b-qat`
- Model id(s) reported by server: `google/gemma-4-12b-qat`
- Settings: temperature=0.0, max_tokens=900, timeout=25.0s per call, no automatic retries
- Calls succeeded: 11 / 12 · run elapsed 158.515s

## Measured results

| Metric | Value |
|---|---|
| Exact match (all 4 fields) | 58% (7/12) |
| Field accuracy: `category` | 75% (9/12) |
| Field accuracy: `priority` | 92% (11/12) |
| Field accuracy: `needs_human` | 75% (9/12) |
| Field accuracy: `order_id` | 92% (11/12) |
| High-priority recall | 100% (3/3) |
| needs_human recall | 100% (4/4) |
| Critical cases passed | 4 / 4 |
| Invalid responses (call or parse errors) | 1 / 12 |
| Latency (total / average / max) | 158502 ms / 13208 ms / 24427 ms |

Latency is measured wall-clock per model call; failed calls contribute their time-to-failure, not zero.

## Critical misses

None — no critical case missed.

## Failure Frontier (curated pairs actually evaluated)

### Pair `VP01` — original_only

- Original: `V01` [original] PASS: category=billing, priority=low, needs_human=False, order_id=501
- No changed case found for this pair.

### Pair `VP02` — original_only

- Original: `V02` [original] FAIL: category=billing, priority=medium, needs_human=True, order_id=502
- No changed case found for this pair.

### Pair `VP03` — original_only

- Original: `V03` [original] PASS: category=technical, priority=high, needs_human=True, order_id=None
- No changed case found for this pair.

### Pair `VP04` — original_only

- Original: `V04` [original] PASS: category=technical, priority=medium, needs_human=False, order_id=None
- No changed case found for this pair.

### Pair `VP05` — original_only

- Original: `V05` [original] FAIL: INVALID — empty_content_reasoning_only: The model returned only a reasoning channel (3626 chars) and no final answer (finish_reason='length'). This usually means the output hit max_tokens before the answer; raise max_tokens or use a non-reasoning model.
- No changed case found for this pair.

### Pair `VP06` — original_only

- Original: `V06` [security_urgency] PASS: category=account, priority=high, needs_human=True, order_id=None
- No changed case found for this pair.

### Pair `VP07` — original_only

- Original: `V07` [suspicious_activity] PASS: category=account, priority=high, needs_human=True, order_id=None
- No changed case found for this pair.

### Pair `VP08` — original_only

- Original: `V08` [ambiguous_multi_intent] PASS: category=billing, priority=medium, needs_human=True, order_id=503
- No changed case found for this pair.

### Pair `VP09` — original_only

- Original: `V09` [negation] PASS: category=billing, priority=low, needs_human=False, order_id=504
- No changed case found for this pair.

### Pair `VP10` — original_only

- Original: `V10` [no_order_id] FAIL: category=billing, priority=medium, needs_human=True, order_id=None
- No changed case found for this pair.

### Pair `VP11` — changed_only

- Original: —
- Changed: `V11` [general_question] FAIL: category=billing, priority=low, needs_human=False, order_id=None
- Changed: `V12` [instruction_injection] FAIL: category=billing, priority=low, needs_human=False, order_id=None
- No 'original' side in this pair (dimension='original').

## Decision and reasons

- 1 of 12 responses was missing or malformed (parse errors: 0, call errors: 1); results are incomplete. Exact-match 7/12.

Rule applied: READY FOR LIMITED PILOT requires: at least 10 labelled cases, zero critical-case misses on priority/needs_human (critical = gold priority 'high' or needs_human true), exact-match >= 85%, and zero invalid responses. Any critical miss => NOT READY. Fewer than 10 valid cases => INSUFFICIENT EVIDENCE. This is an MVP heuristic on a small synthetic workload, not a scientifically calibrated safety guarantee.

## Limitations and warnings

- ⚠ Dataset is a bundled synthetic fixture; it is not real customer data.
- ⚠ 1 of 12 responses was invalid (call errors: 1, parse errors: 0).
- Small labelled workload (bundled cases are synthetic fixtures), not proof of production readiness, generalization or market demand.
- The readiness rule is a transparent MVP heuristic on this fixture; it is not a scientifically calibrated safety guarantee.
- Only four extractions are scored (category, priority, needs_human, order_id); tone, policy text and downstream actions are out of scope.
- The Failure Frontier shows curated paired cases that were actually evaluated; it does not claim to discover every possible failure mode.
- Any cloud-cost comparison would be a user-provided estimate, never an invoice or a measured commercial benchmark.

Per-case raw responses (truncated to 600 chars) are preserved in the JSON passport for audit.

## Cloud vs Local Comparison

Baseline: `synthetic_cloud_baseline.jsonl` · matched cases: 12 / 12 · origin: synthetic fixture · saved responses only; no cloud API call was made.

| Metric | Local | Cloud baseline |
|---|---:|---:|
| Exact match | 58% (7/12) | 58% (7/12) |
| Invalid responses | 1 / 12 | 1 / 12 |
| Critical misses | 0 | 2 |
| Average known latency | 13208.5 ms | 900.0 ms |

- Local wrong / cloud right: 3
- Cloud wrong / local right: 3
- Both wrong: 2
- Warning: Cloud baseline is a synthetic fixture; ModelExit made no cloud API calls.
- Warning: This comparison is descriptive evidence on the matched sample, not proof of safety or generalization.
