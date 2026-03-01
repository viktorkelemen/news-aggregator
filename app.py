import logging
logging.basicConfig(level=logging.INFO)

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Query, Depends
from fastapi.responses import Response, HTMLResponse
from fastapi.templating import Jinja2Templates
from feedgen.feed import FeedGenerator
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from datetime import timezone

import config
from models import init_db, SessionLocal, Article
from fetcher import fetch_all
from filters import load_filters, apply_filters, get_filter_summary

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app):
    init_db()
    scheduler.add_job(fetch_all, "interval", minutes=config.FETCH_INTERVAL_MINUTES)
    scheduler.add_job(fetch_all)  # run once immediately, non-blocking
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title=config.SITE_TITLE, lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def index(request: Request, source: str = Query(None), page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    filter_config = load_filters()

    q = db.query(Article).order_by(Article.published.desc())
    if source:
        q = q.filter(Article.source == source)

    # Filter in Python since keyword matching is substring-based.
    # Load all matching articles, filter, then paginate.
    per_page = 50
    raw_articles = q.all()
    filtered = apply_filters(raw_articles, filter_config)

    total = len(filtered)
    start = (page - 1) * per_page
    articles = filtered[start:start + per_page]

    sources = [r[0] for r in db.query(Article.source).distinct().order_by(Article.source).all()]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "articles": articles,
        "sources": sources,
        "current_source": source,
        "page": page,
        "has_next": total > start + per_page,
        "title": config.SITE_TITLE,
        "filter_summary": get_filter_summary(filter_config),
    })

@app.get("/feed.xml")
def feed_xml(db: Session = Depends(get_db)):
    fg = FeedGenerator()
    fg.title(config.FEED_TITLE)
    fg.description(config.FEED_DESCRIPTION)
    fg.link(href=config.FEED_LINK, rel="alternate")
    fg.language("en")

    filter_config = load_filters()
    raw_articles = db.query(Article).order_by(Article.published.desc()).all()
    articles = apply_filters(raw_articles, filter_config)[:100]
    for a in articles:
        fe = fg.add_entry()
        fe.id(a.link)
        fe.title(a.title)
        fe.link(href=a.link)
        fe.published(a.published.replace(tzinfo=timezone.utc) if a.published.tzinfo is None else a.published)
        if a.summary:
            fe.summary(a.summary)
        if a.content:
            fe.content(a.content, type="html")

    return Response(content=fg.rss_str(pretty=True), media_type="application/rss+xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)
