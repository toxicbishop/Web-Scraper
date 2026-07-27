import os
from celery import Celery
from datetime import datetime, timezone
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
    task_acks_late=True,                    # only ack after task completes
    worker_prefetch_multiplier=1,           # one task at a time per worker
)

app.conf.beat_schedule = {
    "check-periodic-scrapes-every-minute": {
        "task": "workers.tasks.check_periodic_scrapes",
        "schedule": 60.0,
    }
}


@app.task(bind=True, max_retries=3, default_retry_delay=10)
def scrape_url(self, url: str, job_id: int = None, use_playwright: bool = False):
    """
    Main scrape task. Fetches a URL, parses it, and stores to DB.
    Retries up to 3 times on failure with 10s delay.
    """
    from scraper.fetcher import fetch_page, fetch_page_static
    from pipeline.store import save_page

    db = SessionLocal()

    try:
        # Mark job as running
        if job_id:
            job = db.query(ScrapeJob).filter_by(id=job_id).first()
            if job:
                job.status = "running"
                db.commit()

        # Fetch
        if use_playwright:
            data = fetch_page(url)
        else:
            data = fetch_page_static(url)

        # Store
        page = save_page(data)

        # Mark job done
        if job_id:
            job = db.query(ScrapeJob).filter_by(id=job_id).first()
            if job:
                job.status = "done"
                job.finished_at = datetime.now(timezone.utc)
                db.commit()

        return {"status": "ok", "url": url, "duplicate": page is None}

    except Exception as exc:
        if job_id:
            job = db.query(ScrapeJob).filter_by(id=job_id).first()
            if job:
                job.status = "failed"
                job.error = str(exc)
                job.finished_at = datetime.now(timezone.utc)
                db.commit()

        raise self.retry(exc=exc)

    finally:
        db.close()


@app.task
def check_periodic_scrapes():
    """
    Periodic task triggered by Celery Beat to check if any enabled targets
    are due for a fresh scrape based on their configured interval.
    """
    from models.db import PeriodicTarget, ScrapeJob
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        targets = db.query(PeriodicTarget).filter_by(enabled=True).all()
        for target in targets:
            should_scrape = False
            if not target.last_scraped_at:
                should_scrape = True
            else:
                elapsed = now - target.last_scraped_at.replace(tzinfo=timezone.utc)
                if elapsed.total_seconds() >= target.interval_minutes * 60:
                    should_scrape = True

            if should_scrape:
                job = ScrapeJob(url=target.url, status="queued")
                db.add(job)
                db.commit()
                db.refresh(job)

                task = scrape_url.delay(target.url, job_id=job.id)
                job.celery_task_id = task.id
                target.last_scraped_at = now
                db.commit()
    except Exception as e:
        print(f"[scheduler] Error running periodic check: {e}")
    finally:
        db.close()


@app.task
def export_to_s3_task(bucket_name: str = None, s3_key: str = None):
    """
    Task to generate a CSV export of all scraped pages and upload it to AWS S3.
    """
    import io
    import csv
    import boto3
    from models.db import ScrapedPage

    db = SessionLocal()
    try:
        pages = db.query(ScrapedPage).filter_by(status="done").all()
        
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["id", "url", "title", "scraped_at", "last_seen_at", "content"])
        for p in pages:
            writer.writerow([p.id, p.url, p.title, p.scraped_at, p.last_seen_at, p.content])
        
        csv_data = csv_buffer.getvalue()
        
        bucket = bucket_name or os.getenv("AWS_S3_BUCKET")
        if not bucket:
            raise ValueError("No S3 bucket specified or configured via AWS_S3_BUCKET env variable.")
            
        key = s3_key or f"exports/scraped_pages_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        
        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        )
        
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=csv_data.encode("utf-8"),
            ContentType="text/csv",
        )
        
        return {"status": "ok", "bucket": bucket, "key": key, "rows_exported": len(pages)}
        
    except Exception as e:
        print(f"[exporter] S3 Export failed: {e}")
        raise e
    finally:
        db.close()

