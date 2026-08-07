import os
from celery import Celery
from datetime import datetime
from models.db import SessionLocal, ScrapeJob

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "scraper",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@app.task(bind=True, max_retries=3, default_retry_delay=10)
def scrape_url(
    self,
    url: str,
    job_id: int = None,
    mode: str = "static",
    # scroll-mode options
    feed_selector: str = "body",
    max_scrolls: int = 10,
    # click-through-mode options
    item_selector: str = None,
    detail_wait_selector: str = "h1",
    max_items: int = 10,
):
    """
    mode:
      - "static"        plain requests + BeautifulSoup (fastest, no JS)
      - "playwright"     JS-rendered single page, stealth-aware
      - "scroll"          infinite-scroll feed, scrolls until content stops growing
      - "click_through"   opens each list item and scrapes its detail panel
    """
    from scraper.fetcher import (
        fetch_page,
        fetch_page_static,
        fetch_infinite_scroll,
        fetch_with_click_through,
    )
    from pipeline.store import save_page

    db = SessionLocal()

    try:
        if job_id:
            job = db.query(ScrapeJob).filter_by(id=job_id).first()
            if job:
                job.status = "running"
                db.commit()

        saved_count = 0

        if mode == "playwright":
            data = fetch_page(url)
            page = save_page(data)
            saved_count = 1 if page else 0

        elif mode == "scroll":
            data = fetch_infinite_scroll(url, feed_selector=feed_selector, max_scrolls=max_scrolls)
            page = save_page(data)
            saved_count = 1 if page else 0

        elif mode == "click_through":
            if not item_selector:
                raise ValueError("item_selector is required for click_through mode")
            results = fetch_with_click_through(
                url,
                item_selector=item_selector,
                detail_wait_selector=detail_wait_selector,
                max_items=max_items,
            )
            for data in results:
                page = save_page(data)
                if page:
                    saved_count += 1

        else:  # "static"
            data = fetch_page_static(url)
            page = save_page(data)
            saved_count = 1 if page else 0

        if job_id:
            job = db.query(ScrapeJob).filter_by(id=job_id).first()
            if job:
                job.status = "done"
                job.finished_at = datetime.utcnow()
                db.commit()

        return {"status": "ok", "url": url, "mode": mode, "saved": saved_count}

    except Exception as exc:
        if job_id:
            job = db.query(ScrapeJob).filter_by(id=job_id).first()
            if job:
                job.status = "failed"
                job.error = str(exc)
                job.finished_at = datetime.utcnow()
                db.commit()

        raise self.retry(exc=exc)

    finally:
        db.close()
