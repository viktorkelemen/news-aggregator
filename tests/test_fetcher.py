import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from time import mktime


@pytest.fixture
def db_session():
    """Create a fresh in-memory SQLite database for each test."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _make_feed_entry(title="Test Article", link="https://example.com/1", tags=None):
    entry = MagicMock()
    entry.get = lambda k, d="": {"title": title, "link": link}.get(k, d)
    entry.published_parsed = datetime(2026, 3, 20, tzinfo=timezone.utc).timetuple()
    entry.content = []
    entry.tags = tags or []
    # feedparser uses hasattr checks
    type(entry).published_parsed = property(lambda self: datetime(2026, 3, 20, tzinfo=timezone.utc).timetuple())
    type(entry).content = property(lambda self: [])
    type(entry).tags = property(lambda self: tags or [])
    return entry


def _make_feed(entries):
    feed = MagicMock()
    feed.entries = entries
    return feed


class TestFetchSource:
    @patch("fetcher.SessionLocal")
    @patch("fetcher.feedparser")
    def test_fetches_and_stores_articles(self, mock_fp, mock_session_cls, db_session):
        mock_session_cls.return_value = db_session
        entries = [
            _make_feed_entry(title="Article 1", link="https://example.com/1"),
            _make_feed_entry(title="Article 2", link="https://example.com/2"),
        ]
        mock_fp.parse.return_value = _make_feed(entries)

        from fetcher import fetch_source
        count = fetch_source("TestSource", "https://example.com/feed")

        assert count == 2
        from models import Article
        articles = db_session.query(Article).all()
        assert len(articles) == 2
        assert articles[0].source == "TestSource"

    @patch("fetcher.SessionLocal")
    @patch("fetcher.feedparser")
    def test_deduplicates_by_link(self, mock_fp, mock_session_cls, db_session):
        mock_session_cls.return_value = db_session
        entries = [
            _make_feed_entry(title="Article 1", link="https://example.com/same"),
            _make_feed_entry(title="Article 1 Dupe", link="https://example.com/same"),
        ]
        mock_fp.parse.return_value = _make_feed(entries)

        from fetcher import fetch_source
        count = fetch_source("TestSource", "https://example.com/feed")
        assert count == 1

    @patch("fetcher.SessionLocal")
    @patch("fetcher.feedparser")
    def test_skips_entries_without_link(self, mock_fp, mock_session_cls, db_session):
        mock_session_cls.return_value = db_session
        entry = _make_feed_entry(title="No Link", link="")
        mock_fp.parse.return_value = _make_feed([entry])

        from fetcher import fetch_source
        count = fetch_source("TestSource", "https://example.com/feed")
        assert count == 0

    @patch("fetcher.SessionLocal")
    @patch("fetcher.feedparser")
    def test_skips_already_stored_articles(self, mock_fp, mock_session_cls, db_session):
        """Articles already in the DB should not be re-inserted."""
        from models import Article
        existing = Article(
            title="Existing",
            link="https://example.com/existing",
            source="TestSource",
            published=datetime.now(timezone.utc),
        )
        db_session.add(existing)
        db_session.commit()

        mock_session_cls.return_value = db_session
        entries = [
            _make_feed_entry(title="Existing", link="https://example.com/existing"),
            _make_feed_entry(title="New One", link="https://example.com/new"),
        ]
        mock_fp.parse.return_value = _make_feed(entries)

        from fetcher import fetch_source
        count = fetch_source("TestSource", "https://example.com/feed")
        assert count == 1


class TestFetchAll:
    @patch("fetcher.fetch_source")
    def test_fetch_all_calls_each_source(self, mock_fetch_source):
        mock_fetch_source.return_value = 5
        from fetcher import fetch_all
        from config import get_sources
        total = fetch_all()
        sources = get_sources()
        assert mock_fetch_source.call_count == len(sources)
        assert total == 5 * len(sources)

    @patch("fetcher.fetch_source")
    def test_fetch_all_handles_source_errors(self, mock_fetch_source):
        """If one source fails, others should still be fetched."""
        def side_effect(name, url):
            if name == "The Verge":
                raise Exception("Network error")
            return 3

        mock_fetch_source.side_effect = side_effect
        from fetcher import fetch_all
        from config import get_sources
        total = fetch_all()
        # All sources called despite The Verge failing
        assert mock_fetch_source.call_count == len(get_sources())
        # Total should exclude the failed source
        assert total == 3 * (len(get_sources()) - 1)
