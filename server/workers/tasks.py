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
def scrape_url(self, url: str, job_id: int = None, use_playwright: bool = False):
    from scraper.fetcher import fetch_page, fetch_page_static
    from pipeline.store import save_page

    db = SessionLocal()

    try:
        if job_id:
            job = db.query(ScrapeJob).filter_by(id=job_id).first()
            if job:
                job.status = "running"
                db.commit()

        if use_playwright:
            data = fetch_page(url)
        else:
            data = fetch_page_static(url)

        page = save_page(data)

        if job_id:
            job = db.query(ScrapeJob).filter_by(id=job_id).first()
            if job:
                job.status = "done"
                job.finished_at = datetime.utcnow()
                db.commit()

        return {"status": "ok", "url": url, "duplicate": page is None}

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
