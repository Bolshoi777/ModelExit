# ModelExit — Exit Passport

**Decision: NOT READY** · run `8fe376dc3951` · 2026-10-18T09:50:14+00:00 · status: completed_with_errors

## Dataset

- Name: `samples/support_cases.jsonl`
- SHA-256: `a6d7b70d57b92d4f2868838af2de0f47684894dcc6919b4dc857a5a48faf369a`
- Cases evaluated: 12 of 12 requested
- Synthetic fixture: yes

## Local inference

- Provider: LM Studio (localhost, OpenAI-compatible)
- Endpoint: `http://127.0.0.1:1234/v1`
- Model requested: `google/gemma-4-12b-qat`
- Model id(s) reported by server: `google/gemma-4-12b-qat`
- Settings: temperature=0.0, max_tokens=900, timeout=25.0s per call, no automatic retries
- Calls succeeded: 11 / 12 · run elapsed 155.248s

## Measured results

| Metric | Value |
|---|---|
| Exact match (all 4 fields) | 50% (6/12) |
| Field accuracy: `category` | 75% (9/12) |
| Field accuracy: `priority` | 92% (11/12) |
| Field accuracy: `needs_human` | 67% (8/12) |
| Field accuracy: `order_id` | 92% (11/12) |
| High-priority recall | 100% (2/2) |
| needs_human recall | 67% (2/3) |
| Critical cases passed | 2 / 3 |
| Invalid responses (call or parse errors) | 1 / 12 |
| Latency (total / average / max) | 155241 ms / 12937 ms / 23195 ms |

Latency is measured wall-clock per model call; failed calls contribute their time-to-failure, not zero.

## Critical misses

`S10`

## Failure Frontier (curated pairs actually evaluated)

### Pair `P01` — stable_pass

- Original: `S01` [original] PASS: category=billing, priority=low, needs_human=False, order_id=4521
- Changed: `S02` [negation] PASS: category=billing, priority=low, needs_human=False, order_id=4521
- Original and changed case(s) all passed exactly.

### Pair `P02` — stable_pass

- Original: `S03` [original] PASS: category=technical, priority=high, needs_human=True, order_id=None
- Changed: `S04` [urgency_removed] PASS: category=technical, priority=low, needs_human=False, order_id=None
- Original and changed case(s) all passed exactly.

### Pair `P03` — both_fail

- Original: `S05` [original] FAIL: category=billing, priority=medium, needs_human=True, order_id=8182
- Changed: `S06` [no_order_id] FAIL: category=billing, priority=medium, needs_human=True, order_id=None
- Neither side matched exactly (not a regression).

### Pair `P04` — stable_pass

- Original: `S07` [original] PASS: category=account, priority=low, needs_human=False, order_id=None
- Changed: `S08` [security_urgency] PASS: category=account, priority=high, needs_human=True, order_id=None
- Original and changed case(s) all passed exactly.

### Pair `P05` — both_fail

- Original: `S09` [original] FAIL: category=billing, priority=medium, needs_human=True, order_id=9300
- Changed: `S10` [multi_intent] FAIL: INVALID — empty_content_reasoning_only: The model returned only a reasoning channel (3342 chars) and no final answer (finish_reason='length'). This usually means the output hit max_tokens before the answer; raise max_tokens or use a non-reasoning model.
- Neither side matched exactly (not a regression). Critical miss in: S10.

### Pair `P06` — both_fail

- Original: `S11` [original] FAIL: category=billing, priority=low, needs_human=False, order_id=None
- Changed: `S12` [instruction_injection] FAIL: category=billing, priority=low, needs_human=False, order_id=None
- Neither side matched exactly (not a regression).

## Decision and reasons

- Critical miss on 1 of 3 critical cases: S10 (priority/needs_human). A critical miss always blocks a READY recommendation.

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
