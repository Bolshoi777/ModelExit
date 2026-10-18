# ModelExit — Final Integration Experiment

Date: 2026-10-18 (UTC+3)
Run ID: `b2d608e91866`

## 1. Real local model

The UI checked `http://127.0.0.1:1234/v1` and received 18 model IDs. The selected and reported
model was `google/gemma-4-12b-qat`. The response is preserved in `models_response.json`. No paid
or remote API was called.

## 2. Labelled workload

`final_cases.jsonl` contains 12 synthetic support cases with fixed gold labels created before
inference. It includes billing, refund, technical, account, takeover, suspicious activity,
ambiguous wording, negation, order IDs, missing order IDs and prompt-injection text. Four cases
are critical under the existing rule (`priority=high` or `needs_human=true`).

Dataset SHA-256: `3aa79b254bb9f530e7ae387c9dccfdf67970d2d26faef5ee52f9963ef9c091f8`.

## 3. Real Gemma result

- Cases processed: 12/12.
- Successful calls: 11/12; one call error, zero parse errors.
- Exact match: 7/12 (58%).
- Field accuracy: category 9/12, priority 11/12, needs_human 9/12, order_id 11/12.
- High-priority recall: 3/3 (100%).
- needs_human recall: 4/4 (100%).
- Critical cases passed: 4/4; critical misses: none.
- Invalid responses: 1/12; the invalid case was `V05` (`empty_content_reasoning_only`).
- Measured latency: total 158,502 ms, average 13,208.5 ms, maximum 24,427 ms.

## 4. Synthetic Cloud Baseline

`synthetic_cloud_baseline.jsonl` contains 12 saved responses. It is explicitly marked as a
synthetic fixture in the UI and passport. Its `latency_ms` values are controlled test values,
not measurements from a real provider. The baseline contains correct answers, wrong fields,
one invalid response (`V07`), and no real cloud API output.

Baseline SHA-256: `53f1883e573772c9a83b1d375fa6f0b750c79a216ce1118717ef5c0ecb1c5aa0`.

All 12 IDs matched; missing IDs: none; extra IDs: none.

Cloud baseline metrics on the same gold labels:

- Exact match: 7/12 (58%).
- Field accuracy: category 9/12, priority 10/12, needs_human 10/12, order_id 11/12.
- Invalid responses: 1/12.
- Critical misses: `V07`, `V08` (2/4).
- Known latency: 11/12 rows, average 900 ms. These values are synthetic.

Directional differences:

- Local wrong / cloud right: `V05`, `V10`, `V11`.
- Cloud wrong / local right: `V04`, `V07`, `V08`.
- Both wrong: `V02`, `V12`.

## 5. Decision Engine

The local decision was `NEEDS REVIEW`. This is correct: there were enough cases and no local
critical misses, but one invalid response made the results incomplete. The synthetic baseline
did not influence the decision. A cloud result cannot turn a local critical miss into `READY`.

## 6. Exit Passport

The UI downloaded and the verification script opened both exports:

- [`exit_passport.json`](./exit_passport.json)
- [`exit_passport.md`](./exit_passport.md)
- [`gemma_local_outputs.jsonl`](./gemma_local_outputs.jsonl)
- [`comparison_summary.json`](./comparison_summary.json)
- [`models_response.json`](./models_response.json)

The JSON contains the real model ID, dataset and baseline hashes, all 12 per-case local raw
responses, parsed outputs/errors, metrics, decision, synthetic baseline marker and comparison
section. The Markdown contains the same comparison summary and limitations.

## 7. User scenario checked

One UI journey was completed:

`Streamlit start → Check connection → upload labelled dataset → mark synthetic → upload baseline → mark baseline synthetic → Run Local Evaluation → Failures comparison → Passport → download JSON and Markdown`.

The run was one serial 12-call inference with 25-second per-call limits and no automatic retry.

## 8. Limitations and remaining uncertainty

- Both datasets are synthetic and small; this is not evidence of production safety or market
  generalization.
- Baseline latency is synthetic and must not be presented as a provider benchmark.
- The final fixture mostly uses singleton pair IDs, so its Failure Frontier is descriptive rather
  than a balanced paired study; the comparison itself is independent of Frontier labels.
- The full pytest suite was not rerun, per the requested testing policy. Python compilation,
  fixture parsing, passport verification and this one full UI experiment were completed.

## Final status

**GO WITH LIMITATIONS** — the key integration scenario works end-to-end, real Gemma output is
preserved, Cloud vs Local Comparison is visible and exported, and the local Decision Engine
remains authoritative. The result is not a production-safety claim. The repository is published
at https://github.com/Bolshoi777/ModelExit.
