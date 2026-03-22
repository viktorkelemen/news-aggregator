import json
import os
import pytest


def test_default_sources_exist():
    from config import DEFAULT_SOURCES
    assert len(DEFAULT_SOURCES) >= 9
    names = [s["name"] for s in DEFAULT_SOURCES]
    assert "The Verge" in names
    assert "Gothamist" in names
    assert "The City" in names
    assert "Brooklyn Paper" in names
    assert "Brooklyn Eagle" in names
    assert "Brownstoner" in names
    assert "amNewYork" in names


def test_default_sources_have_required_fields():
    from config import DEFAULT_SOURCES
    for source in DEFAULT_SOURCES:
        assert "name" in source, f"Source missing 'name': {source}"
        assert "url" in source, f"Source missing 'url': {source}"
        assert source["url"].startswith("http"), f"Invalid URL: {source['url']}"


def test_get_sources_returns_defaults_when_no_env(monkeypatch):
    monkeypatch.delenv("FEED_SOURCES", raising=False)
    from config import get_sources, DEFAULT_SOURCES
    sources = get_sources()
    assert sources == DEFAULT_SOURCES


def test_get_sources_uses_env_override(monkeypatch):
    custom = [{"name": "Test", "url": "https://example.com/feed"}]
    monkeypatch.setenv("FEED_SOURCES", json.dumps(custom))
    from config import get_sources
    assert get_sources() == custom


def test_get_sources_falls_back_on_invalid_json(monkeypatch):
    monkeypatch.setenv("FEED_SOURCES", "not valid json{{{")
    from config import get_sources, DEFAULT_SOURCES
    assert get_sources() == DEFAULT_SOURCES
