# ModelExit — Exit Passport

**Decision: INSUFFICIENT EVIDENCE** · run `e95819ad13e7` · 2026-10-17T23:07:54+00:00 · status: completed

## Dataset

- Name: `samples/support_cases.jsonl`
- SHA-256: `a6d7b70d57b92d4f2868838af2de0f47684894dcc6919b4dc857a5a48faf369a`
- Cases evaluated: 6 of 6 requested
- Synthetic fixture: yes

## Local inference

- Provider: LM Studio (localhost, OpenAI-compatible)
- Endpoint: `http://127.0.0.1:1234/v1`
- Model requested: `google/gemma-4-12b-qat`
- Model id(s) reported by server: `google/gemma-4-12b-qat`
- Settings: temperature=0.0, max_tokens=900, timeout=25.0s per call, no automatic retries
- Calls succeeded: 6 / 6 · run elapsed 65.881s

## Measured results

| Metric | Value |
|---|---|
| Exact match (all 4 fields) | 67% (4/6) |
| Field accuracy: `category` | 100% (6/6) |
| Field accuracy: `priority` | 100% (6/6) |
| Field accuracy: `needs_human` | 67% (4/6) |
| Field accuracy: `order_id` | 100% (6/6) |
| High-priority recall | 100% (1/1) |
| needs_human recall | 100% (1/1) |
| Critical cases passed | 1 / 1 |
| Invalid responses (call or parse errors) | 0 / 6 |
| Latency (total / average / max) | 65877 ms / 10980 ms / 13005 ms |

## Critical misses

None — no critical case missed.

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

## Decision and reasons

- Only 6 labelled case(s) evaluated; 10 or more are required for a READY verdict. Exact match so far: 4/6 (67%); no critical misses.

Rule applied: READY FOR LIMITED PILOT requires: at least 10 labelled cases, zero critical-case misses on priority/needs_human (critical = gold priority 'high' or needs_human true), exact-match >= 85%, and zero invalid responses. Any critical miss => NOT READY. Fewer than 10 valid cases => INSUFFICIENT EVIDENCE. This is an MVP heuristic on a small synthetic workload, not a scientifically calibrated safety guarantee.

## Limitations and warnings

- ⚠ Dataset is a bundled synthetic fixture; it is not real customer data.
- Small labelled workload (bundled cases are synthetic fixtures), not proof of production readiness, generalization or market demand.
- The readiness rule is a transparent MVP heuristic on this fixture; it is not a scientifically calibrated safety guarantee.
- Only four extractions are scored (category, priority, needs_human, order_id); tone, policy text and downstream actions are out of scope.
- The Failure Frontier shows curated paired cases that were actually evaluated; it does not claim to discover every possible failure mode.
- Any cloud-cost comparison would be a user-provided estimate, never an invoice or a measured commercial benchmark.

Per-case raw responses (truncated to 600 chars) are preserved in the JSON passport for audit.
