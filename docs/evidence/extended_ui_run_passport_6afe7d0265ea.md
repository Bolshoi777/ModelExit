# ModelExit — Exit Passport

**Decision: NOT READY** · run `6afe7d0265ea` · 2026-10-18T13:54:28+00:00 · status: completed_with_errors

## Dataset

- Name: `support_cases_extended.jsonl`
- SHA-256: `1e71589007f40c0dbab5e9837b8f6932b1ef194456e12424f26668c301888e28`
- Cases evaluated: 12 of 12 requested
- Synthetic fixture: yes

## Local inference

- Provider: LM Studio (localhost, OpenAI-compatible)
- Endpoint: `http://127.0.0.1:1234/v1`
- Model requested: `google/gemma-4-12b-qat`
- Model id(s) reported by server: `google/gemma-4-12b-qat`
- Settings: temperature=0.0, max_tokens=900, timeout=25.0s per call, no automatic retries
- Calls succeeded: 11 / 12 · run elapsed 185.017s

## Measured results

| Metric | Value |
|---|---|
| Exact match (all 4 fields) | 58% (7/12) |
| Field accuracy: `category` | 67% (8/12) |
| Field accuracy: `priority` | 83% (10/12) |
| Field accuracy: `needs_human` | 67% (8/12) |
| Field accuracy: `order_id` | 92% (11/12) |
| High-priority recall | 100% (3/3) |
| needs_human recall | 75% (3/4) |
| Critical cases passed | 3 / 4 |
| Invalid responses (call or parse errors) | 1 / 12 |
| Latency (total / average / max) | 185003 ms / 15417 ms / 23977 ms |

Latency is measured wall-clock per model call; failed calls contribute their time-to-failure, not zero.

## Critical misses

`E05`

## Failure Frontier (curated pairs actually evaluated)

### Pair `EP01` — improvement

- Original: `E01` [original] FAIL: category=billing, priority=medium, needs_human=True, order_id=1101
- Changed: `E02` [scope_change] PASS: category=billing, priority=low, needs_human=False, order_id=1101
- Original failed; the changed case(s) passed exactly.

### Pair `EP02` — stable_pass

- Original: `E03` [original] PASS: category=technical, priority=high, needs_human=True, order_id=None
- Changed: `E04` [urgency_removed] PASS: category=technical, priority=low, needs_human=False, order_id=None
- Original and changed case(s) all passed exactly.

### Pair `EP03` — both_fail

- Original: `E06` [original] FAIL: category=billing, priority=low, needs_human=False, order_id=None
- Changed: `E05` [sensitive_change] FAIL: category=billing, priority=low, needs_human=False, order_id=None
- Neither side matched exactly (not a regression). Critical miss in: E05.

### Pair `EP04` — improvement

- Original: `E07` [original] FAIL: INVALID — empty_content_reasoning_only: The model returned only a reasoning channel (3457 chars) and no final answer (finish_reason='length'). This usually means the output hit max_tokens before the answer; raise max_tokens or use a non-reasoning model.
- Changed: `E08` [fraud_urgency] PASS: category=billing, priority=high, needs_human=True, order_id=7712
- Original failed; the changed case(s) passed exactly.

### Pair `EP05` — regression

- Original: `E09` [original] PASS: category=other, priority=low, needs_human=False, order_id=None
- Changed: `E10` [instruction_injection] FAIL: category=technical, priority=low, needs_human=True, order_id=None
- Original passed; changed case(s) E10 failed.

### Pair `EP06` — stable_pass

- Original: `E11` [original] PASS: category=account, priority=medium, needs_human=False, order_id=None
- Changed: `E12` [security_urgency] PASS: category=account, priority=high, needs_human=True, order_id=None
- Original and changed case(s) all passed exactly.

## Decision and reasons

- Critical miss on 1 of 4 critical cases: E05 (priority/needs_human). A critical miss always blocks a READY recommendation.

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
