# WhatToDo? — deploy pack

Files: `docs/index.html` (the whole app), `docs/events.json` (one-off events), `venues.json` (source registry), `probe.py` and `ingest.py` (the content loop). The seed list of London regulars lives inside `index.html`.

## 1. Put it on a domain (GitHub Pages, free)

```
mkdir whattodo && cd whattodo && git init
mkdir docs
cp whattodo.html docs/index.html
cp events.json docs/
cp ingest.py .
git add . && git commit -m "WhatToDo v1"
gh repo create whattodo --public --source=. --push
```

GitHub → repo → Settings → Pages → Source: *Deploy from a branch*, branch `main`, folder `/docs`. You get `https://<you>.github.io/whattodo/`. Add a custom domain there later (CNAME record to `<you>.github.io`).

On a real domain the live lookups come back on: full-postcode geocoding (postcodes.io), the Open-Meteo forecast and TfL journey times all work from the browser. Inside the Claude artifact sandbox they're blocked, which is why the artifact uses the bundled outcode table and the manual Wet/Dry chooser.

## 2. Private usage stats (PostHog, free tier)

1. posthog.com → sign up (EU cloud) → copy the project API key (`phc_...`).
2. In `docs/index.html`, just above the main `<script>`, add:
   ```html
   <script>window.WTD_CONFIG={posthogKey:'phc_XXXX',posthogHost:'https://eu.i.posthog.com'}</script>
   ```
3. Every event the app logs locally (`wtd_session_start`, `wtd_setup_done`, `wtd_deck_built`, `wtd_swipe` with `id/kind/who/car/mins`, `wtd_undo`, `wtd_list_change`, `wtd_wx_manual`) is also sent to PostHog. Build a dashboard there: swipes per session, save rate, most-saved items, who-mix, car vs transport, retention by week. Nobody but you sees it.

The in-app `#stats` page (or seven taps on the logo) stays as the per-device view.

## 3. Refreshing events (source-first)

Three files: `venues.json` (the registry: 111 London venues, councils, parks, farms, theatres, ticketing and aggregator pages, each with coords and default tags), `probe.py` (finds out what each offers) and `ingest.py` (harvests).

```
pip install anthropic
python3 probe.py --discover          # once, and again whenever you add venues
export ANTHROPIC_API_KEY=sk-ant-...
python3 ingest.py --days 14 --out docs/events.json
```

`probe.py` visits every registry URL and records the best feed it finds, in order: schema.org **Event JSON-LD** in the page → **ICS** link → **RSS** → Eventbrite organiser → plain `html`. `--discover` also walks the aggregator pages (IanVisits, Londonist, Time Out, Kidrated, Hoop, Visit London) and writes every outside venue domain they link to into `candidates.csv`; skim it and paste the good ones into `venues.json`.

`ingest.py` then takes the cheapest route per venue: JSON-LD and ICS are parsed directly (exact dates, prices, coords; no model), and Claude only sees (a) `html`/`rss` pages that have no structured data and (b) one short "fill the gaps" call per venue to add indoor/outdoor, age fit, tags and a 30-word own-words blurb. `--no-llm` runs structured sources only. Output is validated (London bounding box, dates in range, link present), merged with the existing file, and past events are dropped.

Social feeds (Instagram, Facebook, Nextdoor) are not in the loop: they block scraping and their APIs don't expose other people's events. Use them by hand to find venues, then add the venue's own site to the registry.

Weekly GitHub Action: `.github/workflows/events.yml`

```yaml
name: events
on:
  schedule: [{cron: "0 6 * * 4"}]   # Thursdays 06:00 UTC
  workflow_dispatch:
jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install anthropic
      - run: python3 ingest.py --days 14 --out docs/events.json
        env: {ANTHROPIC_API_KEY: "${{ secrets.ANTHROPIC_API_KEY }}"}
      - run: |
          git config user.name bot && git config user.email bot@users.noreply.github.com
          git add docs/events.json venues.json && git commit -m "events refresh" || true
          git push
```

Add `ANTHROPIC_API_KEY` under repo Settings → Secrets.

## 3b. Instagram (official API, automatic)

`instagram.py` + `accounts.json` (58 London venue/organiser accounts to start). It uses Meta's Business Discovery API, which returns any professional account's recent posts with captions and images, no scraping. Claude reads captions and poster images and files dated events into `events.json`.

Setup once (about 10 minutes, free): make an Instagram account professional (Creator is fine), create a Meta developer app with the Instagram product, generate a token with `instagram_business_basic`, note your `user_id`. Step-by-step is in the header of `instagram.py`. Then:

```
export IG_TOKEN=... IG_USER_ID=... ANTHROPIC_API_KEY=...
python3 instagram.py --check                 # which handles Meta recognises
python3 instagram.py --days 21 --out docs/events.json
```

Tokens last 60 days; `python3 instagram.py --refresh-token` prints a fresh one.

## 3c. Fully automatic: one daily workflow

Replace the weekly workflow above with `.github/workflows/content.yml`, which runs the web sources and Instagram every morning and commits the result:

```yaml
name: content
on:
  schedule: [{cron: "20 5 * * *"}]   # 05:20 UTC daily
  workflow_dispatch:
jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install anthropic
      - run: python3 ingest.py --days 21 --out docs/events.json
        env: {ANTHROPIC_API_KEY: "${{ secrets.ANTHROPIC_API_KEY }}"}
      - run: python3 instagram.py --days 7 --out docs/events.json
        env:
          ANTHROPIC_API_KEY: "${{ secrets.ANTHROPIC_API_KEY }}"
          IG_TOKEN: "${{ secrets.IG_TOKEN }}"
          IG_USER_ID: "${{ secrets.IG_USER_ID }}"
      - run: |
          git config user.name bot && git config user.email bot@users.noreply.github.com
          git add docs/events.json venues.json ig_seen.json && git commit -m "content $(date +%F)" || true
          git push
```

Secrets to add: `ANTHROPIC_API_KEY`, `IG_TOKEN`, `IG_USER_ID`. Cost: roughly 60 Instagram accounts × 7 days of posts ≈ a few thousand input tokens a day on Haiku, pennies.

To grow the account list: open any venue's Instagram, copy the handle into `accounts.json` with its coordinates. The `--check` run tells you if Meta can't see it (personal accounts are invisible to the API).

## 4. Scoring

In `index.html`, `score(item, mins)`:

| factor | weight |
|---|---|
| travel | −minutes/9 |
| wet day | outdoor −3.2 · both −0.6 · indoor +1.6 |
| fine day (dry, ≥12°, little cloud) | outdoor/both +1.8 |
| dry but not fine | outdoor +0.7 |
| cold (≤6°) | outdoor −0.9 |
| family | age-fit ×1.5 + kid appeal ×0.9 (+0.4 if adults enjoy it too); no age fit → hidden |
| adults / couple / friends | adult appeal ×0.9; kid-only places −1.8; couple-tagged +0.8 for couples; food/market/beer +0.6 for friends |
| free | +0.3 |
| tag affinity from swipes | ±0.35 per tag count, capped ±2 |
| "would go again" | −0.8 |
| one-off event | +1.4 (single day) / +0.6 (run) |
| jitter | +0 to 0.5 |

Tuning is a matter of editing those numbers. Add real swipe data from PostHog before touching them much.

## 5. What's deliberately not here yet

Accounts and cross-device sync, a map view, push nudges on Friday ("this weekend looks dry, three ideas near you"), affiliate links on ticketed events, a venue-submitted listings form. Each is a week or less once the content loop is running.
