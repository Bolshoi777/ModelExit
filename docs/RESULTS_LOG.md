# Verified experiment results (measured; no invented figures)

All numbers below come from real local runs executed on the operator's machine on 2026-10-18 (UTC+3).
Evidence artifacts were exported by ModelExit itself and are committed under `docs/evidence/`.

## Measurement conditions
- Date/time and timezone: 2026-10-18, 02:07–02:18 UTC+3 (UTC timestamps inside the passports: 2026-10-17T23:07:54Z and 2026-10-17T23:14:40Z)
- OS / CPU / GPU / RAM: Windows 11 Pro; Intel i5-12600KF; NVIDIA GeForce RTX 3060 (VRAM variant not captured); 31.9 GB RAM
- LM Studio version: not recorded (server reachable at http://127.0.0.1:1234/v1; version not captured)
- Exact local model ID: `google/gemma-4-12b-qat` (read from `GET /v1/models` before the runs; LM Studio label "QAT", 7.15 GB — exact quantization format not captured)
- Dataset (synthetic): bundled sample `samples/support_cases.jsonl` — 12 synthetic cases / 6 curated pairs; not real customer data
- Dataset SHA-256: `a6d7b70d57b92d4f2868838af2de0f47684894dcc6919b4dc857a5a48faf369a`
- Number of cases actually evaluated: 12 (reference run `3521c8420411`); 6 (G2 gate run `e95819ad13e7`)
- Total elapsed time: 177.7 s (12-case reference run); 65.9 s (6-case gate run)

## Metrics — reference run `3521c8420411` (Streamlit UI, 12 cases)
- Successful calls / total: 11 / 12 (one call abandoned at the 25 s cap — S10; no automatic retries)
- Exact full-field matches / total: 6 / 12 (50%)
- Accuracy per field (denominator 12): category 9/12; priority 11/12; needs_human 8/12; order_id 11/12
- Gold-high recall: 2/2 (100%)
- needs_human recall: 2/3 (67%)
- Critical misses (IDs and reason): `S10` — gold needs_human=true; the call timed out, so priority/needs_human could not be satisfied
- Malformed responses / total: 1 / 12 (1 call error — timeout; 0 parse errors)
- Paired frontier (actual outputs in the passport): P01 stable_pass; P02 stable_pass (urgency removal handled); P03 both_fail (S05/S06 predicted needs_human=true vs gold false — over-escalation); P04 stable_pass (security case correct); P05 both_fail (S09 wrong fields + S10 timeout); P06 both_fail (S11/S12 predicted category=billing vs gold other; the S12 instruction-injection variant produced the same structured prediction — no hijack)
- Model errors / timeouts: 1 timeout (S10, exceeded 25 s, abandoned once, counted as a failure)
- Latency (12 evaluated cases, passport figures): total 152,515 ms / average 12,710 ms / max 21,828 ms
- Migration recommendation and decision reasons: **NOT READY** — "Critical miss on 1 of 3 critical cases: S10 (priority/needs_human). A critical miss always blocks a READY recommendation."

## Metrics — G2 gate run `e95819ad13e7` (CLI, 6 cases)
- Successful calls: 6/6; exact 4/6 (67%); category 6/6; priority 6/6; needs_human 4/6; order_id 6/6
- Gold-high recall 1/1; needs_human recall 1/1; invalid 0/6; no critical misses; elapsed 65.9 s
- Decision: INSUFFICIENT EVIDENCE (6 evaluated < 10 required) — correct rule behavior

## Evidence
- Actual evidence paths: `docs/evidence/g4_ui_run_passport.json` + `.md` (downloaded through the UI download buttons during G4 and opened for verification); `docs/evidence/g2_gate_passport.json` + `.md` (CLI artifacts)
- Note: the frozen G2/G4 passports were exported before commit "fix: export per-case raw responses in the passport"; their JSON has no `cases[]` section. Later exports include per-case records with truncated raw outputs (≤600 chars).
- Post-review fix pass (2026-10-18 UTC+3, operator-authorized; see PROGRESS_LOG gate log): failed model calls now record their measured time-to-failure as latency (the earlier build recorded 0 ms, which excluded the 25 s S10 timeout from the latency aggregates above). New exports also state this latency definition in the Markdown passport. The frozen figures above remain the truthful output of the build that produced them.
- Public demo link: pending (video to be recorded by the operator)
- Public GitHub link: pending publication
- Tests executed (G1–G4), status and durations: G1 PASS (6/6, 0.13 s; 1 fix + rerun); G2 PASS (initial FAIL — reasoning-model max_tokens issue; 1 fix; rerun 6/6 calls, 65.9 s); G3 PASS (3/3, 0.16 s first run; rerun after the raw-export fix 3/3, 0.33 s); G4 PASS as a release journey (12-case run 177.7 s; measured outcome NOT READY, not an app failure). No test loops — see `TEST_POLICY.md`.

## Honest commercial hypothesis
- Buyer profile: small SaaS / indie teams paying per-ticket cloud inference who want measured evidence before moving support triage to a local model — **hypothesis only, NOT validated**.
- Paid product or consulting service being considered: none yet; this is a contest MVP.
- Pricing hypothesis (NOT confirmed revenue): none published.
- Actual customer feedback: NONE — no real user or customer has tried it; all demo data is synthetic.
- Cloud baseline availability: NONE — no provider invoice or measured cloud comparison is included; any such comparison in the product would be a user-provided estimate.
