# ModelExit — Start Here

## Goal

ModelExit is a 48-hour contest MVP for DEV Hacktoberfest 2026 Week 2 (Side Hustle). It is a standalone project, separate from PortalGuard, and runs a local open-weight model through LM Studio without paid APIs.

## Install

- Python 3.11 or 3.12 and Git.
- LM Studio with a local open-weight model.
- An active model server at the default port 1234.

## Before running

1. Work in a separate project folder; do not place ModelExit inside another application repository.
2. Load a local model in LM Studio and select **Developer → Start Server** on port 1234.
3. Check the server in PowerShell:

   ```powershell
   Invoke-RestMethod http://localhost:1234/v1/models
   ```

4. Confirm that the response contains the model ID you intend to evaluate.

## First run

1. Start the app with `streamlit run app.py`.
2. In the Run tab, click **Check connection** and select the real model ID.
3. Load `samples/support_cases.jsonl` or upload your own labelled CSV/JSONL.
4. Run no more than 12 cases.
5. Inspect pass/fail results, Failure Frontier pairs, the readiness decision and both Exit Passport formats.

The optional `samples/support_cases_extended.jsonl` fixture and the comparison feature are documented in the main README.

## Navigation

- `docs/SPEC.md` — scope and acceptance criteria.
- `docs/ARCHITECTURE.md` — module design.
- `docs/DATA_CONTRACTS.md` — CSV/JSONL and scoring rules.
- `docs/RESULTS_LOG.md` — measured local-run evidence.
- `docs/evidence/` — exported JSON and Markdown passports.
- `samples/` — synthetic fixtures, never real customer data.

## Official sources

- https://dev.to/challenges/hacktoberfest-week2-2026-10-12
- https://dev.to/page/hacktoberfest-week2-2026-10-12-contest-rules
- https://lmstudio.ai/docs/developer/openai-compat
- https://lmstudio.ai/docs/developer/core/server
