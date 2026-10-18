# ModelExit — Release Checklist Before Submission

**Status:** completed from the final reviews on 2026-10-18 (UTC+3). `[x]` means confirmed by code, logs or a live run; `[ ]` means not confirmed; `BLOCKED` means operator-owned.

**Scope:** honest contest MVP and reproducible publication. This checklist does not authorize extra test runs; use the recorded gate evidence and static review.

## 0. Stop rule

- [x] No test loops after each edit; only the planned G1, G2, G3 and one G4 walkthrough.
- [x] G1/G3 runs stayed within 60 seconds; G2 and G4 stayed within their live-run budgets.
- [x] Each automated gate used at most one initial run and one post-fix rerun.
- [x] Each root cause received no more than two focused fix attempts.
- [x] Each model request was capped at 25 seconds, with no automatic retries and no more than 12 cases.
- [x] Feature work stopped before publication preparation.

Evidence is recorded in `docs/PROGRESS_LOG.md`; no completed gate was rerun merely to update a checkbox.

## 1. Critical product path

- [x] Windows installation and Streamlit launch steps are documented in `README.md`.
- [x] The application opens locally with a non-empty interface.
- [x] The UI obtains real model IDs from `GET /v1/models`.
- [x] The selected model ID is reported by the local server, not hardcoded.
- [x] A stopped LM Studio server produces a clear connection error and never fake success.
- [x] The bundled labelled dataset contains 12 clearly synthetic cases.
- [x] The Run button makes real local model calls, serially and without retries.
- [x] Each case stores expected fields, parsed output or error, raw response and latency.
- [x] Malformed or empty model output is recorded as invalid.
- [x] Metrics show denominators, field accuracy, exact match, invalid responses and critical misses.
- [x] Failure Frontier shows evaluated curated pairs without claiming complete discovery.
- [x] The Decision Engine applies transparent local-only readiness rules.
- [x] Exit Passport exports JSON and Markdown with model ID, dataset hash, timestamp, settings, results and limitations.
- [x] Optional Cloud vs Local Comparison imports saved CSV/JSONL responses, never calls a provider, and is included in the passport.

## 2. Planned gates

| Gate | Result | Command or action | Evidence |
|---|---|---|---|
| G1 Core | PASS | `.venv\Scripts\python.exe -m pytest tests/test_core.py -q` | 6/6; 0.13 s; one fix and rerun |
| G2 Live model | PASS | `run_cli.py --model "google/gemma-4-12b-qat" --cases 6 --out results/g2_run` | 6/6 real calls; exact 4/6; 65.9 s |
| G3 Passport | PASS | `.venv\Scripts\python.exe -m pytest tests/test_passport.py -q` | 3/3; one post-fix rerun; 0.33 s |
| G4 Release walkthrough | PASS | UI connection → dataset → 12-case run → Failures → Passport → downloads | Run `3521c8420411`; 177.7 s; measured decision NOT READY |

Additional operator-requested live evidence is recorded in `docs/evidence/` and `validation/final_experiment/`.

## 3. Truthfulness and privacy

- [x] Synthetic fixtures, measured local outputs and hypothetical economics are clearly separated.
- [x] No claims are made about untested closed models, real migrations, customers, guaranteed savings or universal accuracy.
- [x] No real customer messages, emails, tokens or private prompts are included in public artifacts.
- [x] User input is not executed as shell code; network access is limited to loopback LM Studio.
- [x] Passport limitations state that small synthetic samples do not prove production safety.
- [x] Machine-specific hardware and account paths are omitted from public documents.

## 4. GitHub and reproducibility

- [x] The public repository is `https://github.com/Bolshoi777/ModelExit`.
- [x] `README.md` explains purpose, requirements, Windows setup, LM Studio usage, datasets, comparison mode and limitations.
- [x] `README.md` contains the centered `ModelExit.png` overview image.
- [x] Relative setup commands are used; no personal absolute paths are published.
- [x] Evidence includes real local model runs and a final integration experiment.
- [x] The English DEV draft contains measured results and no invented users or links.

## 5. Video

**BLOCKED — operator-owned:** the recording is not part of this repository task.

- [ ] The video shows LM Studio with the real model ID.
- [ ] The video shows a synthetic dataset and real inference.
- [ ] The video shows denominators, a Failure Frontier result, the recommendation and passport export.
- [ ] The video is available at a public link.

## 6. DEV Challenge

- [x] The official submission structure is represented by `templates/DEV_POST_DRAFT.md`.
- [x] The draft is in English and labels the buyer as a hypothesis.
- [x] The open-weight model is central and the limitations are explicit.
- [x] Tags `hf26challenge` and `devchallenge` are present.
- [x] Gemma is named only because the recorded runs actually used Gemma.
- [ ] The final video and DEV article links are still operator-owned.

## 7. Decision

**GO WITH LIMITATIONS** for the technical MVP. G1–G4 and the final integration experiment confirm the critical path, real local inference, deterministic scoring, comparison logic and passport export. The small synthetic workload and model-specific failures remain explicit limitations.

Publication is technically unblocked in GitHub. Video and DEV publication remain operator actions.

## Current final integration experiment

Run `b2d608e91866` used `google/gemma-4-12b-qat` on 12 synthetic cases and a 12-row synthetic baseline. Local exact match was 7/12, critical cases passed 4/4, one response was invalid, and the local decision was `NEEDS REVIEW`. The baseline matched all IDs, had exact match 7/12, and did not affect the local decision. Evidence is in `validation/final_experiment/`.
