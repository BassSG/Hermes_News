# Hermes News

Dark-mode morning briefing web app for Thailand-first breaking and trending news, with major international stories mixed in.

## What it does
- Builds a colorful morning dashboard from free RSS sources.
- Prioritizes Thailand news first and scores stories by urgency/impact.
- Lets you click every story to open a readable detail panel.
- Works on desktop and mobile.
- Installable on phone as a PWA.

## Local preview
```bash
python3 scripts/fetch_news.py
python3 -m http.server 8080
# open http://localhost:8080
```

## Update data
```bash
python3 scripts/fetch_news.py
```

## Deployment
This repo is static and ready for GitHub Pages. The workflow in `.github/workflows/update-news.yml` refreshes `data/news.json` every morning Thailand time and commits the update.

## Files
- `index.html` — app shell
- `styles.css` — dark responsive UI
- `app.js` — rendering, filters, details, install prompt
- `manifest.json` — PWA metadata
- `service-worker.js` — offline/cache behavior
- `scripts/fetch_news.py` — RSS collector/scorer
- `data/news.json` — generated news payload
