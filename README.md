# ModelExit

> **Know where your app can safely leave paid AI behind.**
> A local, failure-aware migration-readiness test bench for open-weight models — run on your own Windows machine with LM Studio. **Not a guarantee of model safety or cloud-model equivalence.**

ModelExit answers one narrow question for a small SaaS or indie developer paying a cloud AI provider per support ticket:

**Is *this specific local open-weight model* reliable enough for a limited pilot on *this specific* support-triage workload — and where will human review still be required?**

Instead of a generic benchmark score, it runs a bounded set of your labelled tickets through a locally served model, scores every field against your gold labels with deterministic code, shows the curated **Failure Frontier** (paired original/edge cases), and exports an auditable **Exit Passport** (JSON + Markdown) with all denominators, the actual model id, settings and honest limitations.

This is a contest MVP (DEV Hacktoberfest 2026, Week 2: Side Hustle), not production SaaS.

---

## Features (implemented)

- **Dataset import** — bundled synthetic JSONL sample (12 curated cases, including 6 paired edge cases; an equivalent CSV is provided in `samples/`) or your own CSV/JSONL upload with trusted labels; strict validation with line/row numbers; hard caps (24 cases accepted, 12 evaluated by default).
- **Real local inference** — LM Studio via its OpenAI-compatible API (`/v1/models`, `/v1/chat/completions`), loopback-only, temperature 0, one serial request at a time, 25 s timeout per call, **no automatic retries**.
- **Deterministic scoring** — exact field comparison against gold labels (`category`, `priority`, `needs_human`, `order_id`); malformed JSON is a recorded failure, never a silent pass; every metric reports its denominator; recall shows `N/A` when the gold denominator is zero.
- **Failure Frontier** — curated counterfactual pairs (negation, urgency, multi-intent, missing order id, instruction injection) with per-pair labels: `regression`, `stable_pass`, `both_fail`, `improvement`.
- **Transparent readiness rule** — `READY FOR LIMITED PILOT` only with ≥ 10 evaluated cases, zero critical-case misses (critical = gold `priority=high` or `needs_human=true`), exact-match ≥ 85% and zero invalid responses; any critical miss returns `NOT READY`. The rule text ships inside every export.
- **Exit Passport** — downloadable JSON + Markdown containing run status, dataset name + SHA-256, actual model id(s), settings, timestamp, measured counts, per-case failures and limitations.
- **Headless CLI** (`run_cli.py`) — same core as the UI for reproducible logs.

## Requirements

- Windows 10/11, Python 3.11 or 3.12.
- [LM Studio](https://lmstudio.ai/) with **any open-weight instruct model loaded** that fits your hardware (4–12B works well on 8–12 GB VRAM; we tested with a small Gemma-class model — see `RESULTS_LOG.md` for the exact id used in the recorded run). No paid API, no keys, no cloud.

## Run on Windows

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

In LM Studio: load a model → **Developer → Start Server** (default port 1234). Quick check:

```powershell
Invoke-RestMethod http://localhost:1234/v1/models
```

Then in the browser (Streamlit opens automatically):

1. **Run tab** — click `Check connection`, pick the model id that `GET /v1/models` actually reported, load the bundled sample or upload your CSV/JSONL, choose 6 or 12 cases, press **Run Local Evaluation**.
2. **Failures tab** — metrics with denominators, per-case pass/fail, single-case detail (gold vs parsed prediction vs raw response), and the curated Failure Frontier pairs.
3. **Passport tab** — the readiness decision with measured reasons, run metadata, and **Download Exit Passport** as JSON and Markdown.

Every run is bounded: ≤ 12 model calls, ≤ 25 s per call, serial, zero retries. Inference only happens when you press the button; widget changes never re-run the model. All data stays in the local process — nothing is uploaded anywhere except your own LM Studio on loopback.

## Headless CLI (reproducible runs)

```powershell
.\.venv\Scripts\python.exe run_cli.py --list-models
.\.venv\Scripts\python.exe run_cli.py --model "<exact id from the server>" --cases 6
.\.venv\Scripts\python.exe run_cli.py --model "<exact id>" --cases 12 --out results/run1
```

`--out` writes `results/run1.json` and `results/run1.md` — the same Exit Passport the UI produces. Uploaded datasets can be declared synthetic with `--synthetic`; the bundled sample is always labelled synthetic.

## What it evaluates

A short customer-support message must be classified into:

- `category`: `billing` | `technical` | `account` | `other`
- `priority`: `low` | `medium` | `high`
- `needs_human`: boolean (urgent / security-sensitive / mixed-intent requests require review)
- `order_id`: explicit order number from the text, or `null`

The model must return **exactly one JSON object** with those four fields; expected labels are never included in the prompt, and the ticket text is quoted/delimited as untrusted data (prompt-injection pairs are part of the sample). The model never grades itself: all comparisons are deterministic code against provided gold labels.

The bundled dataset is **synthetic** (written for this project, not real customers) and the rubric is a demo policy, not universal support-triage guidance.

## Readiness rule (transparent, conservative)

| Status | When |
|---|---|
| `NOT READY` | Any critical-case miss on `priority` or `needs_human` (critical = gold high/needs_human), or no successful model calls |
| `READY FOR LIMITED PILOT` | ≥ 10 evaluated cases **and** zero critical misses **and** exact-match ≥ 85% **and** zero invalid responses |
| `INSUFFICIENT EVIDENCE` | Fewer than 10 evaluated cases without critical misses |
| `NEEDS REVIEW` | Everything else (e.g. accurate enough but invalid responses present) |

This is an MVP heuristic on a small fixture — not a scientifically calibrated safety guarantee, and never a claim that a class of traffic is globally safe.

## Exit Passport

Every export includes, with no invented values: run status and id, UTC timestamp, dataset name + SHA-256 + case counts, synthetic-fixture flag, provider and endpoint, requested/reported model id(s), temperature / max_tokens / timeout, calls succeeded vs total, exact-match and per-field accuracy with denominators, gold-high and needs_human recall (or `N/A`), critical-case pass counts and miss ids, latency stats, the evaluated frontier pairs, the decision with reasons, and shipped limitations/warnings.

## Tests

Two small deterministic suites (no model, no network):

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_core.py tests/test_passport.py -q
```

They cover dataset validation, correct/incorrect scoring, malformed JSON handling, critical-miss blocking, zero-denominator safety, passport JSON round-trip and export contents. The fake client in `tests/test_passport.py` is a **test-only simulator** and is never used by the app or the demo.

## Privacy and safety

- Loopback endpoints only (`127.0.0.1` / `localhost`); non-loopback URLs are refused.
- No cloud LLM integrations, no API keys, no telemetry, no auto-downloads.
- Ticket bodies are treated as untrusted input; prompt-injection attempts are data, not instructions.
- Raw model responses are stored truncated (600 chars) for audit; nothing leaves your machine unless you download/export it yourself.

## Limitations (honest list)

- 12 synthetic cases are a smoke fixture, not a statistically representative benchmark; results do not generalize to other workloads or other models.
- Only four extracted fields are scored; tone, policy text and downstream actions are out of scope.
- The Failure Frontier shows curated pairs that were actually evaluated — it does not claim to discover every failure mode.
- Any cloud-cost comparison would be a user-provided estimate, never an invoice or a measured commercial benchmark.
- Small local models can fail arbitrarily on inputs like these; that is exactly what the bench is for.

## Demo

- Video: _TODO — to be recorded and linked before publication._
- Recorded results with the exact model id, hardware and denominators: see [`docs/RESULTS_LOG.md`](docs/RESULTS_LOG.md).

## License and credits

- License: MIT (see [`LICENSE`](LICENSE)).
- Built with [Streamlit](https://streamlit.io/), [Pydantic](https://docs.pydantic.dev/), [httpx](https://www.python-httpx.org/); local inference served by [LM Studio](https://lmstudio.ai/). The open-weight model used in any run is chosen and loaded by the operator in LM Studio; model licences belong to their respective authors.
- Project/process documents (spec, architecture, data contracts, test policy, milestone log, demo script) live in [`docs/`](docs/).
