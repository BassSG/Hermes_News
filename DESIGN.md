# Hermes News — Design & Product Spec

## Product understanding
A dark-mode morning news application for Bass: “what I must know every morning.” Primary coverage is Thailand, with only truly major international stories mixed in. The experience must be visual, colorful, fast to scan, and work well on desktop and mobile. It should also be installable on phone as a PWA.

## Information architecture
- **Hero Brief:** top 3 highest-priority stories for the morning.
- **Filters:** All, Breaking, Thailand, Politics, Business, World, Tech, Culture/Sports.
- **Story cards:** impact score, category, source, freshness, compact summary, visual thumbnail/gradient.
- **Detail view:** click any card to open a detail panel with full summary, why it matters, source link, and share/copy actions.
- **Morning Command sidebar:** quick agenda (Market pulse, Government/Policy, Weather/Travel, Global watch) generated from current story mix.
- **Install prompt:** PWA manifest + service worker + PNG icons.

## Visual system
- Theme: premium command-center dark mode.
- Palette: ink surfaces (#06101f, #0b1628), electric cyan, neon violet, amber alert, emerald success.
- Layout: responsive CSS grid, desktop sidebar + cards, mobile stacked cards + sticky top controls.
- Tone: Thai-first, short, direct, “อ่านง่ายกว่า feed ข่าวปกติ”.

## Data strategy
- `scripts/fetch_news.py` collects free RSS feeds (Google News TH and topic searches), deduplicates, scores importance, categorizes, and writes `data/news.json`.
- Static frontend reads `data/news.json`, so the app stays fast and can be hosted on GitHub Pages.
- GitHub Action refreshes every morning and can also be run manually.

## Definition of Done
- Dark-mode responsive web app.
- Clickable detail view for every story.
- PWA manifest, service worker, valid PNG icons.
- Real generated `data/news.json` from RSS sources.
- Local static preview verified.
