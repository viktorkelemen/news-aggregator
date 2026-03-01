# News Aggregator — Product Requirements Document

## Overview

A personalized, self-hosted news aggregator that collects articles from RSS feeds, filters them based on configurable criteria, and serves a curated selection through both a web UI and a standard RSS feed. Designed for personal use — the goal is to read news that matters to you, not everything.

## Problem

News feeds are noisy. Following multiple sources means wading through topics you don't care about (or actively want to avoid) to find what's relevant. Existing aggregators give you everything or nothing — they don't let you define simple rules like "no politics" or "only tech and science." This project provides a personalized feed where you control what gets through.

## Goals

- Aggregate RSS feeds from multiple configurable sources
- **Filter and curate articles based on configurable criteria** (e.g., exclude politics, prioritize certain topics)
- Serve a clean web UI for browsing the curated article list
- Re-publish the curated selection as a single RSS feed for use in feed readers (e.g., NetNewsWire)
- Deploy with minimal configuration on Railway (or similar PaaS)

## Non-Goals

- User accounts or multi-tenancy
- Full-text search
- Article content scraping beyond what RSS provides
- Mobile app
- Social features (comments, sharing, likes)

## Architecture

```
[RSS Sources] → [Fetcher] → [PostgreSQL] → [Filter/Criteria] → [FastAPI] → [Web UI / RSS Feed]
```

- **Fetcher**: Background job running on a configurable interval. Parses RSS feeds with `feedparser`, deduplicates by article link, and stores all articles.
- **Filter**: Applies configurable criteria to decide which articles appear in the web UI and RSS output. Articles are stored regardless of filter status (filters are applied at read time, not ingest time) so criteria can be changed without re-fetching.
- **Database**: PostgreSQL with an `articles` table. Articles are keyed by unique link.
- **Web Server**: FastAPI serving two endpoints — an HTML index page and an RSS feed at `/feed.xml`. Both respect the active filter criteria.
- **Scheduler**: APScheduler running in-process alongside the web server.

## Article Filtering

The core differentiator. Filtering criteria are applied when serving articles (not during ingestion), so all raw articles are preserved and criteria can be adjusted without data loss.

### Planned Criteria Types

- **Topic exclusion** — hide articles matching certain topics (e.g., "no politics", "no celebrity news")
- **Topic inclusion** — only show articles matching certain topics (e.g., "only tech and science")
- **Keyword blocklist** — exclude articles whose title or summary contains specific words
- **Keyword allowlist** — boost or require articles containing specific words
- **Source-level rules** — apply different criteria per source

### Implementation (TBD)

The filtering mechanism is intentionally left open for now. Possible approaches:

- **Keyword matching** — simple, fast, no dependencies; prone to false positives
- **LLM-based classification** — send title + summary to an LLM for topic tagging; more accurate but adds latency and cost
- **Hybrid** — keyword pre-filter with LLM refinement for ambiguous cases

Criteria configuration will likely be stored in the database or as a structured config (JSON/YAML) rather than just environment variables, since filter rules are more complex than simple key-value settings.

## Features

### Feed Fetching
- Pulls from a configurable list of RSS sources
- Runs on a scheduled interval (default: every 360 minutes)
- Deduplicates articles by link URL
- Stores title, link, source name, published date, summary, and content

### Web UI
- Paginated article list (50 per page), newest first
- Source filter tabs to view articles from a single source
- Displays headline, source, publish date, and truncated summary
- RSS feed autodiscovery link in `<head>`

### RSS Output
- Standard RSS feed at `/feed.xml`
- Serves the latest 100 articles
- Compatible with standard feed readers

### Configuration
All settings via environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://localhost/news_aggregator` | PostgreSQL connection |
| `PORT` | `8000` | Server port |
| `FETCH_INTERVAL_MINUTES` | `360` | Minutes between fetches |
| `SITE_TITLE` | `News Aggregator` | Page title |
| `FEED_TITLE` | `Curated News Feed` | RSS feed title |
| `FEED_DESCRIPTION` | `Aggregated news from multiple sources` | RSS feed description |
| `FEED_LINK` | `https://example.com` | RSS feed link |
| `FEED_SOURCES` | Built-in defaults | JSON array of `{"name", "url"}` objects |

### Default Sources
- The Verge
- CNN
- Telex.hu

## Tech Stack

- **Python 3** with FastAPI + Uvicorn
- **PostgreSQL** via SQLAlchemy ORM
- **feedparser** for RSS parsing, **feedgen** for RSS output
- **APScheduler** for background fetch scheduling
- **Jinja2** for HTML templating
- Deployed on **Railway** via Nixpacks

## Deployment

Single-process deployment: the web server and scheduler run in the same process. Railway auto-provisions PostgreSQL and injects `DATABASE_URL`. No build step beyond `pip install`.
