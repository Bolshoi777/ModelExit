---
title: "I Built a Local AI Migration Test Bench — Here's What My Model Actually Passed"
published: false
tags: devchallenge, hf26challenge
---

> DRAFT — remaining TODOs: the video link and the public GitHub link only.
> All numbers come from the committed reference run `3521c8420411`
> (`docs/evidence/g4_ui_run_passport.json/.md`). Never invent numbers, users or links.

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12).*

## What I Built

ModelExit is a local test bench that helps a small SaaS team decide whether a specific open-weight model — running in LM Studio on their own machine — can handle their customer-support triage before they move traffic off a paid cloud API.

It runs a bounded set of labelled tickets through the local model, scores four extracted fields (`category`, `priority`, `needs_human`, `order_id`) against gold labels with deterministic Python, shows **curated counterfactual pairs (the Failure Frontier)** — negation, urgency, multi-intent, missing order id, prompt injection — and exports an **Exit Passport** (JSON + Markdown) with the actual model id, settings, dataset hash, denominators, failures and a conservative `READY FOR LIMITED PILOT / NOT READY / INSUFFICIENT EVIDENCE / NEEDS REVIEW` rule.

The buyer hypothesis: indie SaaS / small support teams who already pay per-ticket cloud inference and want measured evidence before committing to a local model. (Hypothesis only — no paying customers at the time of writing; all demo data is synthetic.)

## Demo

TODO — video link (2:30, real local run) + 1–2 screenshots of the actual run. The reference-run evidence is committed in the repository: `docs/evidence/g4_ui_run_passport.json` and `.md`.

## Code

TODO — public GitHub repository link.

## How I Built It

- Local model and exact model ID: `google/gemma-4-12b-qat` (read from `GET /v1/models` before the run; LM Studio label "QAT", 7.15 GB)
- Hardware: Windows 11, i5-12600KF, 32 GB RAM, RTX 3060 (VRAM variant not captured)
- Inference endpoint: LM Studio localhost, OpenAI-compatible `/v1/chat/completions`, temperature 0, max_tokens 900 (the reasoning model spends most of its budget on a hidden reasoning channel before the final JSON — measured during the run), 25 s timeout, no retries
- Real evaluated example count and origin: 12 synthetic labelled cases authored for this project (12 of 12 requested in the reference run; 11/12 calls returned valid output — one 25 s timeout is recorded as a failure, not retried). Not real customers.
- Core approach: dataset import → quoted ticket → one JSON object → strict parse → deterministic gold-label scoring → curated pair analysis → conditional recommendation → passport export.

### What I measured

Reference run: LM Studio on localhost, `google/gemma-4-12b-qat`, temperature 0, 25 s per-call cap, 12 synthetic cases, serial, zero retries.

| Metric | Result | Method |
|---|---|---|
| Cases | 12 of 12 | synthetic, manually labelled |
| Exact-match accuracy | 6/12 (50%) | correct / all cases incl. errors |
| High-priority recall | 2/2 (100%) | correct-high / gold-high |
| needs_human recall | 2/3 (67%) | correct / gold |
| Invalid responses | 1/12 (0 parse errors; 1 call timeout) | parse and call errors counted as failures |
| Critical misses | S10 | gold-high or needs_human missed |
| Latency | avg 12.7 s, max 21.8 s per successful call; one 25 s timeout recorded as a failure; 177.7 s total run | wall-clock per request |
| Prompt-injection pair | no hijack — S12 returned a valid structured JSON object; the non-injection variant S11 produced the same prediction, so the pair failed on the `category` label | sample cases S11/S12 |

The most instructive failure came from the billing pair P03. For *"I was charged twice for order #8182; please review the duplicate payment."* the demo policy expects `needs_human=false`, but the model escalated it to `needs_human=true` — over-escalation, not under-escalation. The variant without an order id failed the same way, so the pair is labelled `both_fail`, not a regression. And on the multi-intent refund case (S10) the model did not answer within the 25-second cap at all: the timeout is recorded as a failure with no retry — and it is exactly why the final recommendation was **NOT READY** (1 critical miss of 3 critical cases).

## Why Does Open Innovation Matter?

ModelExit is open innovation in a small, practical sense: the evaluation stack — sample workload, deterministic scorer, decision rule, exports — is open source, runs offline on your own machine, and produces an audit trail instead of a vendor promise. The same bench re-runs in minutes on any model you can load in LM Studio, and the passport records the exact model id and dataset hash, so the result is reproducible or falsifiable by anyone. Crucially, the honest outcome can be "not yet": in my reference run the local Gemma model scored 50% exact with one critical miss, and the rule said NOT READY. That kind of evidence — not a marketing claim — is what a small team needs before deciding where paid AI can be left behind.

## My Agent Session

Built with [OpenCode](https://opencode.ai/) in one working session over the Hacktoberfest weekend on a Windows machine, under a self-imposed test policy: three small automated gates and one manual end-to-end walkthrough, logged honestly in the repository — including the failures I had to fix along the way.

## Prize Categories

**Best Use of Gemma** — the reference run uses `google/gemma-4-12b-qat` served locally by LM Studio (model id read from `GET /v1/models` before the run; the same id is visible in the UI in the video, and the inference settings are recorded in the exported passport under `docs/evidence/`).

## Limitations & Next Steps

- 12 synthetic cases are a smoke fixture, not a benchmark; results do not generalize to other workloads, languages or models.
- The readiness rule is an MVP heuristic, not a calibrated safety guarantee.
- Only four extracted fields are scored; downstream actions are out of scope.
- Cloud-cost comparisons are user-supplied estimates, never invoices (none are included in this MVP).
- One call hit the 25 s cap in the reference run and is recorded as a failure without a retry; latency varies with hardware and load.
- Next: bigger domain-specific fixtures, per-field error taxonomy, and pilot runs with human review on real (non-exported) tickets.
