import pytest
from unittest.mock import MagicMock
from filters import article_passes_filter, apply_filters, _get_rules_for_source, load_filters, get_filter_summary


def _make_article(title="Test", summary="", source="TestSource", categories=None):
    a = MagicMock()
    a.title = title
    a.summary = summary
    a.source = source
    a.categories = categories
    return a


class TestArticlePassesFilter:
    def test_passes_with_empty_config(self):
        a = _make_article(title="Anything goes")
        assert article_passes_filter(a, {}) is True

    def test_blocked_by_keyword(self):
        config = {"global": {"keyword_blocklist": ["politics"]}}
        a = _make_article(title="NYC politics today")
        assert article_passes_filter(a, config) is False

    def test_keyword_blocklist_case_insensitive(self):
        config = {"global": {"keyword_blocklist": ["POLITICS"]}}
        a = _make_article(title="nyc politics")
        assert article_passes_filter(a, config) is False

    def test_passes_keyword_blocklist(self):
        config = {"global": {"keyword_blocklist": ["politics"]}}
        a = _make_article(title="Brooklyn park reopens")
        assert article_passes_filter(a, config) is True

    def test_blocked_by_category(self):
        config = {"global": {"category_blocklist": ["Politics"]}}
        a = _make_article(title="News", categories="Politics,Local")
        assert article_passes_filter(a, config) is False

    def test_passes_category_blocklist(self):
        config = {"global": {"category_blocklist": ["Politics"]}}
        a = _make_article(title="News", categories="Local,Brooklyn")
        assert article_passes_filter(a, config) is True

    def test_keyword_allowlist_passes(self):
        config = {"global": {"keyword_allowlist": ["brooklyn"]}}
        a = _make_article(title="Brooklyn bridge repair")
        assert article_passes_filter(a, config) is True

    def test_keyword_allowlist_blocks(self):
        config = {"global": {"keyword_allowlist": ["brooklyn"]}}
        a = _make_article(title="Manhattan traffic update")
        assert article_passes_filter(a, config) is False

    def test_summary_checked_for_keywords(self):
        config = {"global": {"keyword_blocklist": ["spam"]}}
        a = _make_article(title="Good title", summary="This is spam content")
        assert article_passes_filter(a, config) is False


class TestSourceSpecificRules:
    def test_source_rules_override_global(self):
        config = {
            "global": {"keyword_blocklist": ["politics"]},
            "sources": {"Gothamist": {"keyword_blocklist": ["crypto"]}},
        }
        # Gothamist uses its own rules, so "politics" is not blocked
        a = _make_article(title="NYC politics", source="Gothamist")
        assert article_passes_filter(a, config) is True

        # But "crypto" is blocked for Gothamist
        a2 = _make_article(title="Crypto news", source="Gothamist")
        assert article_passes_filter(a2, config) is False

    def test_global_rules_apply_to_unconfigured_source(self):
        config = {
            "global": {"keyword_blocklist": ["politics"]},
            "sources": {"Gothamist": {"keyword_blocklist": ["crypto"]}},
        }
        a = _make_article(title="NYC politics", source="Brooklyn Paper")
        assert article_passes_filter(a, config) is False


class TestApplyFilters:
    def test_no_rules_returns_all(self):
        articles = [_make_article(title=f"Article {i}") for i in range(5)]
        assert apply_filters(articles, {}) == articles

    def test_filters_out_blocked_articles(self):
        config = {"global": {"keyword_blocklist": ["bad"]}}
        articles = [
            _make_article(title="Good article"),
            _make_article(title="Bad article"),
            _make_article(title="Another good one"),
        ]
        result = apply_filters(articles, config)
        assert len(result) == 2
        assert all("bad" not in a.title.lower() for a in result)


class TestGetFilterSummary:
    def test_empty_config(self):
        assert get_filter_summary({}) is None

    def test_shows_blocklist(self):
        config = {"global": {"keyword_blocklist": ["politics", "war"]}}
        summary = get_filter_summary(config)
        assert "politics" in summary
        assert "war" in summary

    def test_shows_source_rules(self):
        config = {
            "global": {},
            "sources": {"Gothamist": {"keyword_blocklist": ["crypto"]}},
        }
        summary = get_filter_summary(config)
        assert "Gothamist" in summary
        assert "crypto" in summary
