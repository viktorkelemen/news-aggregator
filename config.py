import os
import json

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/news_aggregator")
# Fix Railway's postgres:// -> postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

PORT = int(os.environ.get("PORT", 8000))
FETCH_INTERVAL_MINUTES = int(os.environ.get("FETCH_INTERVAL_MINUTES", "30"))

SITE_TITLE = os.environ.get("SITE_TITLE", "News Aggregator")
FEED_TITLE = os.environ.get("FEED_TITLE", "Curated News Feed")
FEED_DESCRIPTION = os.environ.get("FEED_DESCRIPTION", "Aggregated news from multiple sources")
FEED_LINK = os.environ.get("FEED_LINK", "https://example.com")

DEFAULT_SOURCES = [
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
    {"name": "CNN", "url": "http://rss.cnn.com/rss/edition.rss"},
    {"name": "Telex.hu", "url": "https://telex.hu/rss"},
]

def get_sources():
    env_sources = os.environ.get("FEED_SOURCES")
    if env_sources:
        return json.loads(env_sources)
    return DEFAULT_SOURCES
