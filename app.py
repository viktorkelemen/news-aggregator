import logging
logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI, Request, Query
from fastapi.responses import Response, HTMLResponse
from fastapi.templating import Jinja2Templates
from feedgen.feed import FeedGenerator
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import timezone

import config
from models import init_db, SessionLocal, Article
from fetcher import fetch_all

app = FastAPI(title=config.SITE_TITLE)
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup():
    init_db()
    # Initial fetch
    try:
        fetch_all()
    except Exception as e:
        logging.error(f"Initial fetch failed: {e}")
    # Schedule periodic fetches
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_all, "interval", minutes=config.FETCH_INTERVAL_MINUTES)
    scheduler.start()

@app.get("/", response_class=HTMLResponse)
def index(request: Request, source: str = Query(None), page: int = Query(1, ge=1)):
    db = SessionLocal()
    try:
        q = db.query(Article).order_by(Article.published.desc())
        if source:
            q = q.filter(Article.source == source)
        total = q.count()
        per_page = 50
        articles = q.offset((page - 1) * per_page).limit(per_page).all()
        sources = [r[0] for r in db.query(Article.source).distinct().order_by(Article.source).all()]
        return templates.TemplateResponse("index.html", {
            "request": request,
            "articles": articles,
            "sources": sources,
            "current_source": source,
            "page": page,
            "has_next": total > page * per_page,
            "title": config.SITE_TITLE,
        })
    finally:
        db.close()

@app.get("/feed.xml")
def feed_xml():
    fg = FeedGenerator()
    fg.title(config.FEED_TITLE)
    fg.description(config.FEED_DESCRIPTION)
    fg.link(href=config.FEED_LINK, rel="alternate")
    fg.language("en")

    db = SessionLocal()
    try:
        articles = db.query(Article).order_by(Article.published.desc()).limit(100).all()
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
    finally:
        db.close()

    return Response(content=fg.rss_str(pretty=True), media_type="application/rss+xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)
