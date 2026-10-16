# IMPLEMENTATION_PLAN — 48 HOURS MAX

## Working assumptions
- Start: **2026-10-16**, user begins when opening OpenCode. Budget **48 elapsed hours from start**, target published DEV submission by **2026-10-18 20:00 UTC+3**. Official absolute deadline is Oct 18 23:59 PDT (= Oct 19 09:59 UTC+3).
- Operator has Windows PC, local LM Studio, OpenCode. Exact GPU/RAM unknown, so adaptive small-model strategy. Code and docs should be written quickly, without endless testing.
- This is a two-day contest MVP, not production SaaS.

## Stage A — Foundation (hours 0–5)
- Confirm Python, env, LM Studio `/v1/models`; **do not spend >45 minutes on installation**. If model setup delayed, implement deterministic core first.
- Create public Git repo (operator can connect remotely later), `requirements.txt`, README starter.
- Implement `contracts.py`, `dataset.py`, `evaluator.py`, `decision.py` plus bounded curated JSONL fixtures.
- **G1 once** after all four modules exist; fix/re-run only if necessary.
- Git commit: `feat: add labelled workload and deterministic evaluation`.

## Stage B — Live product core (hours 5–14)
- Implement LM Studio client, selection UI, complete serial bounded inference and handling for invalid JSON/timeouts.
- Streamlit Run tab, progress, datasets, results table and error details.
- **G2 once** on 6 cases after all these work (must be real LM Studio).
- Git commit: `feat: run local open-weight workload evaluation`.

## Stage C — Unique value (hours 14–23)
- Failure Frontier view with `pair_id` and `dimension`, compare original and changed case, highlight regression and critical misses.
- Selective Exit transparent recommendation; reasons with counts.
- JSON + Markdown Passport export; metadata and limitations.
- **G3 once** after exports implemented; fix only critical failures.
- Git commit: `feat: report failure frontier and migration passport`.

## Stage D — Polish & evidence (hours 23–31)
- Make UI coherent and readable; no overdesign. Include sensible empty, loading, and error states.
- Documentation for Windows. Add one commercial use case with *hypothetical* pricing; if economics is P1, skip when tight.
- **G4 one manual smoke walkthrough**; capture screenshots + real model ID/result logs.
- Git commit: `docs: reproducible local demo and limitations`.

## Stage E — Publication (hours 31–40)
- Record one 2–3 min video showing model connection, live evaluation, failure case, recommendation, export.
- Write thoughtful English article using `templates/DEV_POST_TEMPLATE.md` and real results. Strong focus on observed problems and why local/open-weight matters.
- Confirm links, public repo, actual model name, no fake user feedback, tags from official template.
- Publish DEV entry **before internal cutoff**.

## Stage F — Buffer (hours 40–48)
- Buffer only for video upload/post corrections and critical blocker fixes.
- If already published, improve README and optionally seek honest feedback from a developer. Do NOT add new app features.

## Stop rules
- At hour 24: if core works, freeze features except report/export. If core does not work, narrow MVP to bundled dataset and 6 cases.
- At hour 32: freeze implementation; prioritize reliable demo and documentation.
- At hour 40: draft/publish article; do not delay waiting for an optional feature.
- At hour 48: stop development, produce status report. Never continue loops indefinitely.

## Fallback ladder, maintaining honesty
- Full feature: 12 cases, Failure Frontier, Passport.
- If slow model: 6 cases, real requests, smaller supported model.
- If UI issues: single-page Streamlit with table and download buttons.
- If report issues: one JSON export and Markdown summary in README.
- If LM Studio never works: do not fabricate product demo; clearly report blocker and seek operator fix quickly; contest submission cannot honestly claim working open-weight core.

## Daily operator updates (compact)
After milestone, print: completed components / Git commit / G gate pass or blocked / remaining known work / exact next task. Do not spam status for each small code edit.
