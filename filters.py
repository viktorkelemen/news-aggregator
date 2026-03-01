import json
import os
import logging
from models import Article

log = logging.getLogger(__name__)

FILTERS_PATH = os.path.join(os.path.dirname(__file__), "filters.json")

def load_filters() -> dict:
    """Load filter config from filters.json. Returns empty config on error."""
    try:
        with open(FILTERS_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        log.error(f"Invalid filters.json: {e}, filtering disabled")
        return {}

def _get_rules_for_source(config: dict, source_name: str) -> dict:
    """Merge global rules with source-specific overrides."""
    global_rules = config.get("global", {})
    source_rules = config.get("sources", {}).get(source_name)
    if source_rules is not None:
        return source_rules
    return global_rules

def article_passes_filter(article: Article, config: dict) -> bool:
    """Check if a single article passes the filter criteria."""
    rules = _get_rules_for_source(config, article.source)

    keyword_blocklist = [kw.lower() for kw in rules.get("keyword_blocklist", [])]
    keyword_allowlist = [kw.lower() for kw in rules.get("keyword_allowlist", [])]
    category_blocklist = [cat.lower() for cat in rules.get("category_blocklist", [])]

    text = f"{article.title or ''} {article.summary or ''}".lower()

    # Category blocklist
    if category_blocklist and article.categories:
        article_cats = [c.strip().lower() for c in article.categories.split(",")]
        if any(blocked in article_cats for blocked in category_blocklist):
            return False

    # Keyword blocklist
    if keyword_blocklist:
        if any(kw in text for kw in keyword_blocklist):
            return False

    # Keyword allowlist (when non-empty, article must match at least one)
    if keyword_allowlist:
        if not any(kw in text for kw in keyword_allowlist):
            return False

    return True

def _has_any_rules(config: dict) -> bool:
    """Check if there are any active filter rules."""
    if not config:
        return False
    global_rules = config.get("global", {})
    if any(global_rules.get(k) for k in ("keyword_blocklist", "keyword_allowlist", "category_blocklist")):
        return True
    for rules in config.get("sources", {}).values():
        if any(rules.get(k) for k in ("keyword_blocklist", "keyword_allowlist", "category_blocklist")):
            return True
    return False

def apply_filters(articles: list[Article], config: dict) -> list[Article]:
    """Filter a list of articles using the loaded config."""
    if not _has_any_rules(config):
        return articles
    return [a for a in articles if article_passes_filter(a, config)]

def get_filter_summary(config: dict) -> str | None:
    """Return a human-readable summary of active filters, or None if no filters active."""
    if not config:
        return None
    global_rules = config.get("global", {})
    parts = []
    blocklist = global_rules.get("keyword_blocklist", [])
    allowlist = global_rules.get("keyword_allowlist", [])
    cat_blocklist = global_rules.get("category_blocklist", [])
    if blocklist:
        parts.append(f"Hiding keywords: {', '.join(blocklist)}")
    if cat_blocklist:
        parts.append(f"Hiding categories: {', '.join(cat_blocklist)}")
    if allowlist:
        parts.append(f"Only showing: {', '.join(allowlist)}")
    source_rules = config.get("sources", {})
    if source_rules:
        for name, rules in source_rules.items():
            src_parts = []
            if rules.get("keyword_blocklist"):
                src_parts.append(f"hiding: {', '.join(rules['keyword_blocklist'])}")
            if rules.get("category_blocklist"):
                src_parts.append(f"hiding categories: {', '.join(rules['category_blocklist'])}")
            if rules.get("keyword_allowlist"):
                src_parts.append(f"only: {', '.join(rules['keyword_allowlist'])}")
            if src_parts:
                parts.append(f"{name}: {'; '.join(src_parts)}")
    return " | ".join(parts) if parts else None
