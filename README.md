# News Aggregator

A lightweight news aggregator that pulls RSS feeds, stores articles in PostgreSQL, and serves a curated RSS feed + web UI.

## Features

- Fetches RSS feeds from configured sources on a schedule
- Stores articles in PostgreSQL (deduped by link)
- Serves a clean RSS feed at `/feed.xml` (compatible with NetNewsWire, etc.)
- Simple web UI with source filtering and pagination

## Quick Start (Local)

```bash
pip install -r requirements.txt
export DATABASE_URL="postgresql://localhost/news_aggregator"
python app.py
```

Open http://localhost:8000

## Deploy to Railway

1. Create a new Railway project
2. Add a PostgreSQL service
3. Connect this repo
4. Railway auto-detects the `Procfile` — no config needed
5. The `DATABASE_URL` is set automatically by Railway's PostgreSQL plugin

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://localhost/news_aggregator` | PostgreSQL connection string |
| `PORT` | `8000` | Server port |
| `FETCH_INTERVAL_MINUTES` | `30` | Minutes between feed fetches |
| `SITE_TITLE` | `News Aggregator` | Page title |
| `FEED_TITLE` | `Curated News Feed` | RSS feed title |
| `FEED_DESCRIPTION` | `Aggregated news from multiple sources` | RSS feed description |
| `FEED_LINK` | `https://example.com` | RSS feed link |
| `FEED_SOURCES` | *(built-in defaults)* | JSON array of `{"name": "...", "url": "..."}` |

## Default Sources

- The Verge
- CNN
- Telex.hu

Override with `FEED_SOURCES`:
```bash
export FEED_SOURCES='[{"name":"Ars Technica","url":"https://feeds.arstechnica.com/arstechnica/index"}]'
```
