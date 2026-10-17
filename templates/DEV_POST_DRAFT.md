---
title: "I Built a Local AI Migration Test Bench — Here's What My Model Actually Passed"
published: false
tags: devchallenge, hf26challenge
---

> DRAFT — fill every `TODO` from `docs/RESULTS_LOG.md` and the recorded run before publishing.
> Never invent numbers, users or links. Keep the official Submission Template structure.

*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12).*

## What I Built

ModelExit is a local test bench that helps a small SaaS team decide whether a specific open-weight model — running in LM Studio on their own machine — can handle their customer-support triage before they move traffic off a paid cloud API.

It runs a bounded set of labelled tickets through the local model, scores four extracted fields (`category`, `priority`, `needs_human`, `order_id`) against gold labels with deterministic Python, shows **curated counterfactual pairs (the Failure Frontier)** — negation, urgency, multi-intent, missing order id, prompt injection — and exports an **Exit Passport** (JSON + Markdown) with the actual model id, settings, dataset hash, denominators, failures and a conservative `READY FOR LIMITED PILOT / NOT READY / INSUFFICIENT EVIDENCE / NEEDS REVIEW` rule.

The buyer hypothesis: indie SaaS / small support teams who already pay per-ticket cloud inference and want measured evidence before committing to a local model. (Hypothesis — not validated with paying customers at the time of writing: TODO confirm/remove.)

## Demo

TODO — video link (2:30, real local run) + 1–2 screenshots of the actual run.

## Code

TODO — public GitHub repository link.

## How I Built It

- Local model and exact model ID: TODO (from the recorded run; read from `GET /v1/models`)
- Hardware: Windows 11, i5-12600KF, 32 GB RAM, RTX 3060 (TODO confirm VRAM)
- Inference endpoint: LM Studio localhost, OpenAI-compatible `/v1/chat/completions`, temperature 0, max_tokens 900 (the reasoning model spends most of its budget on a hidden reasoning channel before the final JSON — measured during the run), 25 s timeout, no retries
- Real evaluated example count and origin: TODO — 12 synthetic labelled cases authored for this project (visibly labelled synthetic; not real customers)
- Core approach: dataset import → quoted ticket → one JSON object → strict parse → deterministic gold-label scoring → curated pair analysis → conditional recommendation → passport export.

### What I measured

| Metric | Result | Method |
|---|---|---|
| Cases | TODO | synthetic, manually labelled |
| Exact-match accuracy | TODO (x/12) | correct / all cases incl. errors |
| High-priority recall | TODO or N/A | correct-high / gold-high |
| needs_human recall | TODO or N/A | correct / gold |
| Invalid JSON responses | TODO (x/12) | parse failures counted as failures |
| Critical misses | TODO (IDs) | gold-high or needs_human missed |
| Latency | TODO | wall-clock per request |
| Prompt-injection pair | TODO | sample case S12 behavior |

TODO — one genuinely surprising or difficult case with the actual raw output (quote it exactly).

## Why Does Open Innovation Matter?

TODO — grounded in what actually happened: local ownership of the data path, no per-ticket cost, the ability to swap models (the same bench reruns in minutes), and reproducibility — the exported passport contains the exact model id and dataset hash, so anyone can re-run the same evaluation. Do not claim cloud APIs are universally insecure or more expensive.

## My Agent Session

TODO — optional. [OpenCode](https://opencode.ai/) built the project in one working session over a weekend; link to the session transcript only if it is actually public.

## My First User

TODO — omit this whole section if no real user tried it. Do not fabricate.

## Prize Categories

TODO — add **Best Use of Gemma** only if the recorded run actually uses a Gemma model; include the exact id and the inference proof in the video. Otherwise delete this section.

## Limitations & Next Steps

- 12 synthetic cases are a smoke fixture, not a benchmark; results do not generalize to other workloads, languages or models.
- The readiness rule is an MVP heuristic, not a calibrated safety guarantee.
- Only four extracted fields are scored; downstream actions are out of scope.
- Cloud-cost comparisons are user-supplied estimates, never invoices (none are included in this MVP).
- Next: bigger domain-specific fixtures, per-field error taxonomy, and pilot runs with human review on real (non-exported) tickets.
