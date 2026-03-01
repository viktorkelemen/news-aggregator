import feedparser
from datetime import datetime, timezone
from time import mktime
from models import SessionLocal, Article
from config import get_sources
import logging

log = logging.getLogger(__name__)

def fetch_all():
    sources = get_sources()
    total = 0
    for source in sources:
        try:
            count = fetch_source(source["name"], source["url"])
            total += count
            log.info(f"Fetched {count} new articles from {source['name']}")
        except Exception as e:
            log.error(f"Error fetching {source['name']}: {e}")
    log.info(f"Total new articles: {total}")
    return total

def fetch_source(name: str, url: str) -> int:
    feed = feedparser.parse(url)
    db = SessionLocal()
    count = 0
    try:
        # Batch dedup: collect all links, query existing ones in one shot
        all_links = [entry.get("link", "") for entry in feed.entries if entry.get("link")]
        existing_links = set()
        if all_links:
            rows = db.query(Article.link).filter(Article.link.in_(all_links)).all()
            existing_links = {row[0] for row in rows}

        seen_links = set(existing_links)
        for entry in feed.entries:
            link = entry.get("link", "")
            if not link or link in seen_links:
                continue
            seen_links.add(link)

            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)

            summary = entry.get("summary", "")
            content = ""
            if hasattr(entry, "content") and entry.content:
                content = entry.content[0].get("value", "")

            # Parse category tags
            categories = ""
            if hasattr(entry, "tags") and entry.tags:
                categories = ",".join(t.get("term", "") for t in entry.tags if t.get("term"))

            article = Article(
                title=entry.get("title", "Untitled"),
                link=link,
                source=name,
                published=published or datetime.now(timezone.utc),
                summary=summary[:5000] if summary else None,
                content=content[:50000] if content else None,
                categories=categories or None,
            )
            db.add(article)
            count += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return count
