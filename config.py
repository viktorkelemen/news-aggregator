import os
import json
import logging

log = logging.getLogger(__name__)

_db_dir = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(_db_dir, 'news.db')}")
# Fix Railway's postgres:// -> postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

PORT = int(os.environ.get("PORT", 8000))
FETCH_INTERVAL_MINUTES = int(os.environ.get("FETCH_INTERVAL_MINUTES", "360"))

SITE_TITLE = os.environ.get("SITE_TITLE", "News Aggregator")
FEED_TITLE = os.environ.get("FEED_TITLE", "Curated News Feed")
FEED_DESCRIPTION = os.environ.get("FEED_DESCRIPTION", "Aggregated news from multiple sources")
FEED_LINK = os.environ.get("FEED_LINK", "https://example.com")

DEFAULT_SOURCES = [
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml"},
    {"name": "CNN", "url": "http://rss.cnn.com/rss/edition.rss"},
    {"name": "Telex.hu", "url": "https://telex.hu/rss"},
    {"name": "Gothamist", "url": "https://gothamist.com/feed"},
    {"name": "The City", "url": "https://www.thecity.nyc/feed/"},
    {"name": "Brooklyn Paper", "url": "https://www.brooklynpaper.com/feed/"},
    {"name": "Brooklyn Eagle", "url": "https://brooklyneagle.com/feed"},
    {"name": "Brownstoner", "url": "https://www.brownstoner.com/feed/"},
    {"name": "amNewYork", "url": "https://www.amny.com/feed/"},
]

def get_sources():
    env_sources = os.environ.get("FEED_SOURCES")
    if env_sources:
        try:
            return json.loads(env_sources)
        except json.JSONDecodeError as e:
            log.error(f"Invalid FEED_SOURCES JSON: {e}, falling back to defaults")
    return DEFAULT_SOURCES
