# PRD: News Aggregator

## Introduction

A personalized, self-hosted news aggregator that collects articles from RSS feeds, filters them based on configurable criteria, and serves a curated selection through both a web UI and a standard RSS feed. The core value is filtering out noise — topics you don't care about (e.g., politics, celebrity news) never reach your feed. Designed for single-user, personal use with minimal operational overhead. Deployed on Railway.

## Goals

- Aggregate RSS feeds from multiple configurable sources on a schedule
- Store all articles in PostgreSQL, deduplicated by link
- Filter articles at read time using configurable keyword-based rules (with LLM classification planned for later)
- Serve filtered articles through a clean web UI with source filtering and pagination
- Re-publish filtered articles as a standard RSS feed at `/feed.xml` compatible with feed readers like NetNewsWire
- Filter rules defined in a JSON config file checked into the repo
- Deploy to Railway with zero manual setup beyond connecting the repo

## User Stories

### US-001: Fix deprecated APIs and code quality issues
**Description:** As a developer, I want the codebase to use current FastAPI patterns and follow best practices so it's maintainable and doesn't produce deprecation warnings.

**Acceptance Criteria:**
- [ ] Replace `@app.on_event("startup")` with FastAPI lifespan context manager
- [ ] Use FastAPI `Depends` for DB session lifecycle instead of manual try/finally
- [ ] Batch dedup check in fetcher — query all existing links for a feed in one query instead of one per entry
- [ ] Store scheduler reference and shut it down on app shutdown
- [ ] Add `index=True` on `Article.published` column
- [ ] URL-encode source filter parameter in template
- [ ] Add try/except with fallback for `FEED_SOURCES` JSON parsing
- [ ] Defer initial feed fetch to scheduler instead of blocking startup
- [ ] Add `/health` endpoint
- [ ] Fix README: document correct default for `FETCH_INTERVAL_MINUTES` (360)

### US-002: Store article categories from RSS metadata
**Description:** As the filtering system, I need article categories stored in the database so keyword and topic filters can use them.

**Acceptance Criteria:**
- [ ] Add `categories` column to `Article` model (e.g., comma-separated string or JSON array)
- [ ] Parse `<category>` tags from RSS/Atom feed entries during ingestion
- [ ] The Verge category tags (e.g., "Tech", "Policy", "Science") are stored
- [ ] Telex.hu category tags (e.g., "Belfold", "Sport", "Techtud") are stored
- [ ] Existing articles without categories are not broken by the migration

### US-003: Define filter rules in a JSON config file
**Description:** As a user, I want to define my article filter rules in a JSON file so I can version-control my preferences and edit them easily.

**Acceptance Criteria:**
- [ ] App reads filter config from `filters.json` in the project root
- [ ] Config supports keyword blocklist (exclude articles matching these words in title/summary)
- [ ] Config supports keyword allowlist (only show articles matching these words)
- [ ] Config supports topic exclusion by category tag
- [ ] Config supports per-source overrides (e.g., different rules for The Verge vs Telex)
- [ ] Missing or empty `filters.json` means no filtering (show all articles)
- [ ] Invalid JSON in config file logs an error and falls back to no filtering
- [ ] A documented example `filters.example.json` is provided

### US-004: Apply keyword filters at read time
**Description:** As a user, I want articles filtered by my keyword rules so I only see news that's relevant to me in both the web UI and RSS feed.

**Acceptance Criteria:**
- [ ] Web UI index page applies filters from `filters.json` before rendering
- [ ] `/feed.xml` applies the same filters before generating RSS output
- [ ] Keyword blocklist: articles with blocked words in title or summary are hidden
- [ ] Keyword allowlist: when set, only articles matching at least one allowed word are shown
- [ ] Topic exclusion: articles with excluded category tags are hidden
- [ ] Per-source rules override global rules for that source
- [ ] Filters are case-insensitive
- [ ] All raw articles remain in the database regardless of filter status
- [ ] Pagination counts reflect filtered totals, not raw totals

### US-005: Show filter status in web UI
**Description:** As a user, I want to see which filters are active so I know why certain articles may not be showing.

**Acceptance Criteria:**
- [ ] Web UI displays active filter summary (e.g., "Hiding: politics, celebrity | Showing: tech, science")
- [ ] When no filters are active, no filter status is shown
- [ ] Filter status does not interfere with existing source tabs and pagination
- [ ] Verify in browser using dev-browser skill

### US-006: Serve curated RSS feed
**Description:** As a feed reader user, I want `/feed.xml` to serve only my filtered articles so I get a personalized feed in NetNewsWire.

**Acceptance Criteria:**
- [ ] `/feed.xml` returns valid RSS with only articles passing the active filters
- [ ] Feed metadata (title, description, link) still configurable via env vars
- [ ] Feed serves up to 100 filtered articles, newest first
- [ ] Feed is compatible with NetNewsWire (valid RSS 2.0)

## Functional Requirements

- FR-1: Fetch RSS feeds from configurable sources on a scheduled interval (default: 360 minutes)
- FR-2: Deduplicate articles by link URL — do not store the same article twice
- FR-3: Store article title, link, source, published date, summary, content, and categories
- FR-4: Read filter rules from `filters.json` at the project root
- FR-5: Support keyword blocklist — hide articles whose title or summary contains any blocked keyword (case-insensitive)
- FR-6: Support keyword allowlist — when non-empty, only show articles matching at least one keyword
- FR-7: Support topic exclusion by category tag
- FR-8: Support per-source filter overrides
- FR-9: Apply filters at read time to both the web UI and `/feed.xml`
- FR-10: Serve paginated article list (50/page) on the web UI with source tab filtering
- FR-11: Serve RSS feed at `/feed.xml` with up to 100 filtered articles
- FR-12: Provide `/health` endpoint for deployment health checks
- FR-13: All configuration via environment variables (DB, port, sources, feed metadata) except filter rules which use `filters.json`

## Non-Goals

- User accounts or multi-tenancy
- Full-text search
- Article content scraping beyond what RSS provides
- Mobile app
- Social features (comments, sharing, likes)
- LLM-based classification (planned for future, not this version)
- Editing filter rules from the web UI (edit the JSON file directly)
- Replacing the CNN source (not a priority right now)

## Technical Considerations

- **Python 3** with FastAPI + Uvicorn
- **PostgreSQL** via SQLAlchemy ORM
- **feedparser** for RSS parsing, **feedgen** for RSS output
- **APScheduler** for background fetch scheduling, running in-process
- **Jinja2** for HTML templating
- Deployed on **Railway** via Nixpacks — single-process, PostgreSQL auto-provisioned
- Filters applied via SQLAlchemy query conditions, not in-memory post-filtering, where possible
- `filters.json` is read on each request (or cached with short TTL) so changes take effect without restart

## Success Metrics

- Filtered feed contains zero articles matching blocklisted keywords
- Web UI and RSS feed show identical filtered results
- App starts and serves requests within 5 seconds (no blocking fetch on startup)
- Filter config changes take effect without redeploying

## Open Questions

- What is the exact JSON schema for `filters.json`? (To be finalized during implementation of US-003)
- Should keyword matching support regex or just substring matching?
- When LLM classification is added later, should it tag articles at ingest time or at read time?
