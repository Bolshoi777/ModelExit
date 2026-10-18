# AGENTS.md — SYSTEM POLICY FOR OPENCODE (ModelExit only)

READ THIS FIRST. Apply these instructions whenever you work in this repository. Source of truth hierarchy: `AGENTS.md` > `TEST_POLICY.md` > `SPEC.md` > `IMPLEMENTATION_PLAN.md` > other docs. Preserve user's explicit later instructions when not conflicting with contest legality and product integrity.

## Mission / time
- Build a **genuinely functional** Windows-first ModelExit MVP within **48 wall-clock hours** of first coding session, targeting publication by **2026-10-18 20:00 UTC+3**, ahead of the official 2026-10-18 23:59 PDT deadline.
- Work in **this repo only**, never modify PortalGuard or import PortalGuard code.
- New code is produced within contest's Oct 12–18 entry window. Keep normal Git commits at major milestones; do not manufacture history.
- Speak to operator in Russian; public UI, README and competition article in clear English.
- Software should run locally, with zero paid API requirement. Model inference only to LM Studio at a configurable localhost address.

## Non-negotiable development priorities
1. Actually connect to LM Studio, enumerate models, select a loaded/available one, call it for support case classifications and save outputs.
2. Deterministic, reviewable scoring and disclosure of failures; no model self-judging its own answers.
3. Show Failure Frontier (curated original/edge-case pairs), recommendation grounded in measured outcomes.
4. Export a useful Exit Passport, reproducible README and short truthful demo.
5. Small understandable Streamlit UI, no complicated infrastructure.

## TEST CEILING — strict, must not quietly violate
**Never run tests, builds, lint, model batch evaluations or manual clicking after each small edit.** Finish coherent modules, then run only pre-specified milestone gates. Read `TEST_POLICY.md` before starting work.
- Exactly **3 planned automated gates** (Import/Evaluator, LM Studio Inference, Passport/Export) and **1 final manual smoke walkthrough**, not ongoing test loops.
- Each planned gate: **one initial run + at most ONE rerun after a fix**. No broad re-running previously passed suites.
- Automated deterministic gate default timeout 60 s; live model gate maximum 8 min TOTAL, max 12 cases, max 25 s per case, zero automatic retries.
- A failure allows **at most two focused code-fix attempts on the same root cause** (the one rerun still applies). If not resolved, document BLOCKER and proceed to next viable task or request operator guidance. Do not repeatedly reinstall packages, regenerate code, or replace framework.
- Never run stress tests, continuous watchers, full property-based fuzzing, `pytest` in watch loops, full lint every commit, benchmark hundreds of examples, repeated model downloads, or agent self-improvement loops.
- A final release can have **one** short smoke walkthrough; if critical failure, fix directly and make a single targeted verification only, then ship/mark blocker.

## Development workflow
- Before coding: inspect docs, check existing files, select simplest implementation, output short plan. Do not spend more than 20–30 minutes on planning/investigations.
- Implementation is in 3 broad, working batches. In one batch, create **several coherent modules before testing**.
- Prioritize shipping. At ~70% of time budget freeze feature additions, at ~85% stop coding except critical fixes, reserve final time for video/article.
- Maintain `PROGRESS_LOG.md` after milestones: completed, blockers, actual command/run, results, time left. Do not falsely mark tests as passed.
- Do not auto-publish DEV post or represent synthetic cases as real customers/user tests.

## Product truthfulness and privacy
- Distinguish synthetic input fixtures, measured LM Studio outputs, and hypothetical cloud-provider costs.
- Never claim quality of an untested closed model, real migration completed, a paid customer acquired, guaranteed cost savings or a universal accuracy score.
- Local/private data stays local; remove emails/tokens/secrets in exported/public demo artifacts. Do not print full private prompts in logs by default.
- If model unavailable, show meaningful local model-connection error, **not fake success**. A simulator/mocked backend may exist strictly for unit tests and must be labelled as a simulator, and must NOT be used in prize demo.
- Safety: no arbitrary input-driven shell execution, dynamic code eval, unknown remote endpoints, or unsandboxed untrusted plugins.
- Include model name, settings, timestamp, sample size, run status, and source labels in every exported assessment.

## Definition of Done (contest MVP)
- New user can start UI using README instructions, choose LM Studio model, run 8–12 bundled cases end-to-end, view pass/fail and failed edge pairs, see transparent readiness rule, export a valid JSON and Markdown passport.
- Repo contains source and basic tests; at least a short credible video and published DEV submission using official template with repo/demo links.
- If some stretch functionality omitted, document honest limitations rather than working forever to add it.

## Handling uncertainty
- Use the actual `GET /v1/models` response to select model, do not hardcode a fictitious Gemma model ID.
- Start with `/v1/chat/completions` using an OpenAI-compatible client, explicit timeout, temperature 0 if supported, ask for a single JSON object. Validate and parse responses; malformed JSON is a recorded failure, not a reason for unbounded reprompting.
- OpenCode's *own* model used to write code need not be the same as the Gemma model powering ModelExit. No remote AI connection is required at runtime.

## Do not build
No authentication, subscriptions, billing, SaaS backend, live cloud LLM integrations, LoRA, generalized agent, true automated source-code migration, huge dashboard, complex Docker orchestration, multi-model leaderboards, uncontrolled test-case generation.

## Final agent report format
`Done:` features and paths. `Actually verified:` exact one-line commands and results. `Not verified/blockers:` uncertainties. `Operator next steps:` no more than 3 actionable items. `Timing:` what remains before the internal cutoff. No inflated claims.
