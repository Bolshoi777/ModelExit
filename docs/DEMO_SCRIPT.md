# Demo video script — ModelExit (target 2:30, one bounded take)

Record in English for the DEV audience (Russian notes for the operator in brackets).
Show the real model, real run, real numbers. Never fake a failure or a pass.

## Pre-recording checklist (5 minutes)

- [ ] LM Studio open, target model loaded, **Developer → Start Server** running on port 1234. Write down the exact model id.
- [ ] `Invoke-RestMethod http://localhost:1234/v1/models` returns the id (know it before recording).
- [ ] App running: `.\.venv\Scripts\Activate.ps1` then `streamlit run app.py`.
- [ ] Browser window clean (no personal tabs/bookmarks visible), readable zoom, 1920×1080 or 1366×768.
- [ ] In the app: connection checked, model selected, bundled sample loaded.
- [ ] `docs/RESULTS_LOG.md` open in another tab (final numbers must match the video).

## Storyboard

**00:00–00:20 — Problem (slide or direct camera).**
Narration: “Small SaaS teams pay a cloud AI provider per support ticket. Before they move that traffic to a local open-weight model, they need one honest question answered: where will it fail? I built ModelExit — a local migration test bench that answers exactly that, with measured evidence instead of vibes.”

**00:20–00:40 — Show the real local model.**
[Alt-Tab в LM Studio: видно название загруженной модели и запущенный сервер на порту 1234.]
Narration: “Everything runs locally in LM Studio. The model id you see here is the model that will actually power the evaluation. No cloud, no API keys.”

**00:40–01:10 — Run tab.**
- Click *Check connection* → show the real model id in the dropdown.
- *Load bundled sample* → open the preview: point at the “synthetic” label and a paired case.
- Choose 12 cases → **Run Local Evaluation** → show the bounded progress (“6/12…”).
Narration: “Twelve labelled tickets, one serial call at a time, 25-second timeout, zero retries. The run is deliberately bounded so the whole evaluation is reproducible in one sitting.”

**01:10–01:45 — Failures tab.**
- Exact match as `x/12` with denominator; invalid responses; critical misses.
- Open one failing case: gold label vs parsed prediction vs raw response. [Если все прошли — честно скажите об этом и покажите frontier со stable pairs.]
- Failure Frontier: show one pair (original vs changed, e.g. urgency removed) and read its real verdict.
Narration: “The scoring is deterministic Python against gold labels — the model never grades itself. The Failure Frontier shows curated original/edge pairs, so you see *where* the meaning change broke the model, not just an average.”

**01:45–02:10 — Passport tab.**
- Decision badge + reasons with counts (e.g. “exact-match 10/12, critical misses: none / S03”).
- Metadata block: model id(s), dataset SHA-256, timestamp, settings.
Narration: “The recommendation is a transparent rule: it only says READY FOR LIMITED PILOT with at least ten cases, zero critical misses, at least 85% exact match and zero invalid responses — otherwise it refuses or asks for review.”

**02:10–02:30 — Export and close.**
- Download JSON and Markdown passports; briefly open the JSON (show schema_version, model id, metrics).
- Show GitHub repo README in a tab (Windows run steps visible).
Narration: “Both passports come out of the same run — model, settings, denominators, failures and limitations. The repo has the Windows setup in the README. This is an honest small-scale test bench: twelve synthetic cases decide nothing about your production traffic, but they show exactly where this model already stumbles.”

## Post-recording

- [ ] Verify every number in the video matches `docs/RESULTS_LOG.md` (same run).
- [ ] Upload (YouTube unlisted/public). Put the link into README “Demo” and the DEV post.
- [ ] Confirm no tokens/emails/private data visible anywhere.
