# Submission Playbook — reserve time for writing (priority 1 for judging)

## Internal target
- 2026-10-18 20:00 UTC+3: code frozen enough; article **published**.
- Contest official end: 2026-10-19 09:59 UTC+3 (Oct 18 23:59 PDT). Do not wait for last minute.

## Deliverables before publication
1. Public GitHub repository with clear README, license (only if chosen by operator), install instructions for Windows and system requirements.
2. At least one measured run on a **real open-weight local model**, screenshots with actual results. All synthetic test cases explicitly marked synthetic.
3. A **video demo** or reachable deployed URL. Local app is okay if video supplied. A 2–3 minute screen recording is enough (contest rules don't impose 3-min limit; ours is a clarity target).
4. Exports: Exit Passport with failure cases + decision, model ID and hardware if known.
5. English article using official template linked on challenge page, with `devchallenge`, `hf26challenge` tags.
6. If truly used Gemma, `Best Use of Gemma` clearly identified under Prize Categories. Avoid other categories unless meaningfully integrated.

## 2:30 demo storyboard
- 00:00–00:20 Buyer/problem: small SaaS support workflow; no universal model benchmark.
- 00:20–00:40 Show LM Studio running loaded open-weight model; model ID visible.
- 00:40–01:10 Import bundled **synthetic** labelled dataset; press Run; show finite progress.
- 01:10–01:45 Show 1–2 real errors or successful paired differences. If no error occurs, show clean outcomes honestly; don't fabricate failures.
- 01:45–02:10 Explain conservative readiness recommendation with denominator.
- 02:10–02:30 Export passport, show GitHub and run instructions.

## Technical article angle
Suggested title: **I Built a Local AI Migration Test Bench — Here's What My Model Actually Passed**.
Only change to 'Here's Where It Broke' if results show real failure.

### Narrative, not corporate marketing
- What was the workload and who might buy a migration audit?
- Why an open-weight local model is central, not decorative.
- Short architecture diagram (dataset → inference → deterministic scoring → paired cases → passport).
- Test method and honest findings: dataset sizes, synthesized source, cases, invalid JSON, model ID, hardware.
- At least 1 actual screenshot and link to repo/video.
- The most instructive surprise or failure, measured not guessed.
- The economics paragraph should state either grounded scenario assumptions or **not yet calculated**.
- Limitations, what's next, and any genuine user feedback.

## User research in remaining time (optional)
Contact one QA engineer/indie SaaS developer and ask: 'Would you pay for a local migration-readiness report that shows specific failure cases? What proof would you need?' Document response only if it actually happened. Do not fabricate a first user.

## Final checklist
- [ ] Source built during contest period, repo public.
- [ ] App executes open-weight inference; not mocked in video.
- [ ] Post uses actual template and correct tags.
- [ ] Working video link or deployed app.
- [ ] GitHub link and README Windows steps.
- [ ] Explains open innovation and target paying buyer.
- [ ] Labels all demo data synthetic and cost scenarios estimated.
- [ ] States what is incomplete and model-specific limitations.
- [ ] Link opens in incognito/browser without private sign-in.
- [ ] Only one contest entry this week; publish on time.
