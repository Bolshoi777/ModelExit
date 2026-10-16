# TEST_POLICY.md — STRICT ANTI-INFINITE-TEST RULES

## Why this file exists
The operator explicitly wants OpenCode to build substantial functionality before tests, and avoid the previous project's endless testing/refactoring loops. **A finished, honest MVP on time outranks extreme test coverage.** This policy is mandatory.

## Exact planned checkpoints — 3 automated gates and 1 final demo
| Gate | When (never on each edit) | What | Runtime budget | Maximum repeats |
|---|---|---|---|---|
| G1 — Core | After dataset parser + contracts + evaluator + decision + curated cases exist | Run only `tests/test_core.py`: JSONL import, valid label scoring, malformed model JSON, critical miss | 60 s | Initial + 1 after a fix |
| G2 — Live model | After LM Studio adapter AND functional UI Run path implemented | Run **ONE** real evaluation of 6 cases, model loaded by user; inspect failures; no cloud/mocks | 4 min | Initial + 1 after a fix; reduce to 3 cases if slow |
| G3 — Passport | After reporting and UI export implemented | Run only `tests/test_passport.py`: valid report JSON, no invented values, correct reasons/hash | 60 s | Initial + 1 after a fix |
| G4 — Manual release check | Once all required modules and README done | Manually launch Streamlit, load bundled dataset, single bounded real model run (max 12), download report and open it | 8 min | One pass; if critical failure fix and do **one targeted recheck only** |

### Formal quantitative ceilings
- **Maximum 3 planned automated gates**, 1 final human walkthrough.
- **Maximum 2 invocations per gate** (first and one post-fix); no re-running every previously passed gate.
- **Maximum 2 focused code-edit attempts per root-cause**. If still broken: mark blocker, prioritize working smaller scope, report operator.
- Individual model call max 25 seconds, **0 automatic retry**; default full evaluation 12 calls maximum, serial, <=8 minutes total; if performance too slow, choose 6.
- Default deterministic test gate must finish in <=60s. Use OS-level process timeout, not just Python client timeout.
- No tests running in background, no watchers (`--watch`), no continuous integration loops, no full benchmark sweeps.
- Debugging by static inspection is allowed; inspection is not an excuse to keep running whole suites.

## What the tests must prove
**G1 (4–6 assertions max, simple fixtures):** 1) imported labels valid, 2) correct prediction passes, 3) incorrect high priority blocks Ready, 4) malformed JSON fails, 5) no denominator division by zero.
**G2:** genuine LM Studio response received; model ID recorded; no hidden remote calls. If LM Studio not available, mark G2 BLOCKED, implement UI with visible connection instructions, do not claim pass.
**G3 (2–4 assertions):** JSON roundtrip, included measured counts, included dataset/model identification and warnings; markdown output not blank.
**G4:** one complete user journey only. No trying 10 themes/browsers/edge configs.

## Failure handling algorithm
1. Log **one concise diagnosis**, not pages of console output.
2. Make a targeted fix with a clear hypothesis.
3. Re-run **only the failed gate** once if warranted.
4. If unresolved, do no more recurring work on the same root cause; mark `BLOCKED` with effect and user action, move to other MVP module or fallback.
5. Under <=8 hours to contest deadline, stop all non-critical debugging and prioritize demo/article.

## Never do
- `while not tests_pass: fix(); run_all_tests()`
- Post-edit auto-testing, aggressive micro-refactoring, dependency version churn.
- Unlimited generated test cases from LLM, full fuzzing or benchmark score chasing.
- Starting dozens of parallel LM Studio inference jobs.
- Replacing stack entirely after one test failure.
- Passing simulated or hardcoded results as live model output.

## Operator override
Only the operator may authorize expanded testing and must explicitly ask. Until then, these caps are hard constraints even if the agent thinks more tests are helpful.
