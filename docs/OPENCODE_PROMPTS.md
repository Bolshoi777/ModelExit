# Copy-paste prompts for OpenCode

## Prompt A — START NOW

```text
You are the lead ModelExit developer on Windows. FIRST read AGENTS.md, TEST_POLICY.md, SPEC.md, ARCHITECTURE.md, DATA_CONTRACTS.md, IMPLEMENTATION_PLAN.md, DEV_CHALLENGE_RULES.md and START_HERE.md. Then begin implementation immediately rather than stopping at a plan. We have a 48-hour window and an internal publication target of 2026-10-18 20:00 UTC+3.

IMPORTANT: DO NOT run endless tests. Finish several coherent modules for a milestone, then run only the gate specified by TEST_POLICY.md, with at most one rerun after a fix. For a problem, make no more than two focused attempts and then move on. Do not spend time on broad market research or an architecture rewrite.

Implement in this order: JSONL/CSV dataset, schemas, deterministic evaluator, decision engine, LM Studio API, simple Streamlit UI, curated Failure Frontier and Exit Passport export. Use real local inference; simulators are allowed only in clearly labelled unit tests. I need a working application, not a mock UI or paperwork.

Stack: Python 3.11/3.12, Streamlit, Pydantic and the LM Studio OpenAI-compatible localhost endpoint. ModelExit must remain separate from PortalGuard. Do not use paid APIs or automatically download large models.

After each major milestone, provide a short English report with files/functions, the actual gate result and the next stage. Start Stage A now and continue sequentially unless blocked.
```

## Prompt B — CONTINUE AFTER THE FIRST MILESTONE

```text
Continue ModelExit from the current repository state. First read PROGRESS_LOG.md and do not repeat completed modules or checks. Follow AGENTS.md and TEST_POLICY.md. Complete the next coherent stage and test only at the specified gates. Do not start a new design or create a plan from scratch. Priorities are real LM Studio calls, measured results and exports, followed by contest publication. Report briefly after the milestone.
```

## Prompt C — QUALITY FREEZE / PREPARE DEMO

```text
ModelExit is in release-preparation mode. Do not add features, rebuild the architecture or start regression loops. Verify only the critical path once under TEST_POLICY.md: real LM Studio inference on a bounded case set, correct pass/fail scoring, Failure Frontier and passport export. Record truthful measured results in RESULTS_LOG.md, update the Windows README, prepare the demo script and complete the English article draft from the official template. Never invent results, customers or costs.
```

## Prompt D — CONTEST ARTICLE

```text
Using the factual RESULTS_LOG.md and the finished application, prepare a detailed but lively English post in templates/DEV_POST_DRAFT.md for DEV Challenge Week 2 Side Hustle. Follow the official template. Explain who could pay and why, why open-weight AI matters, how Failure Frontier works, what actually passed or failed with exact denominators and model ID, and the limitations. Add placeholders for missing links. Do not invent users, tests, prices or links, and do not publish automatically.
```
