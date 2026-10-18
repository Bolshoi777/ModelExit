# ModelExit Publication Steps

Run these steps once, in order. The internal target was 2026-10-18 20:00 UTC+3; the official deadline was 2026-10-19 09:59 UTC+3.

## 1. GitHub repository

The ModelExit repository is now public at https://github.com/Bolshoi777/ModelExit.

For future updates from PowerShell:

```powershell
git add -A
git commit -m "describe the change"
git push origin main
```

Open the repository in a private browser window and confirm that the README and setup instructions are visible without signing in.

## 2. Real demo video

1. Start LM Studio with the target model loaded and record the exact model ID.
2. Start the app: `.\.venv\Scripts\Activate.ps1`, then `streamlit run app.py`.
3. Follow [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md): connection → model → 12-case run → failures/frontier → recommendation → passport export.
4. Show the actual values from the screen. Do not invent results.
5. If the fresh run differs from the reference run, keep the fresh passport and make the article match it.
6. Upload the video and add its public link to the README and DEV post.

## 3. DEV article

1. Open the official challenge submission template.
2. Use [`../templates/DEV_POST_DRAFT.md`](../templates/DEV_POST_DRAFT.md). Replace only the remaining TODO links with the public video and repository links.
3. Keep the tags `devchallenge` and `hf26challenge`.
4. Use **Best Use of Gemma** only when the measured run actually used Gemma and the exact model ID is shown.
5. Check [`SUBMISSION.md`](SUBMISSION.md), then publish before the deadline.

## 4. After publication

- Add the video and article links to the README and `PROGRESS_LOG.md`.
- Open every public link without signing in.
- Confirm that screenshots and video contain no tokens, emails or private data.
- Confirm that article numbers match the screenshots, logs and exported passport.
