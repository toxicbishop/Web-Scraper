import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

from models.db import init_db, get_db, ScrapedPage, ScrapeJob, ScheduledScrape
from workers.tasks import scrape_url
from scheduler.manager import upsert_beat_entry, remove_beat_entry
from pipeline.export import pages_to_csv, upload_csv_to_s3
from sqlalchemy.orm import Session

SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
ALGORITHM = "HS256"
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Portfolio Scraper API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


class TokenRequest(BaseModel):
    username: str
    password: str


@app.post("/token")
def get_token(body: TokenRequest):
    if body.username != "admin" or body.password != "admin":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    payload = {"sub": body.username, "exp": datetime.utcnow() + timedelta(hours=24)}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


def require_auth(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ")[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


class ScrapeRequest(BaseModel):
    url: str
    mode: str = "static"
    feed_selector: str = "body"
    max_scrolls: int = 10
    item_selector: Optional[str] = None
    detail_wait_selector: str = "h1"
    max_items: int = 10


@app.post("/scrape", dependencies=[Depends(require_auth)])
@limiter.limit("10/minute")
def trigger_scrape(request: Request, body: ScrapeRequest, db: Session = Depends(get_db)):
    if body.mode not in ("static", "playwright", "scroll", "click_through"):
        raise HTTPException(status_code=400, detail="Invalid mode")
    if body.mode == "click_through" and not body.item_selector:
        raise HTTPException(status_code=400, detail="item_selector is required for click_through mode")

    job = ScrapeJob(url=body.url, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)

    task = scrape_url.delay(
        body.url, job_id=job.id, mode=body.mode, feed_selector=body.feed_selector,
        max_scrolls=body.max_scrolls, item_selector=body.item_selector,
        detail_wait_selector=body.detail_wait_selector, max_items=body.max_items,
    )
    job.celery_task_id = task.id
    db.commit()

    return {"job_id": job.id, "task_id": task.id, "status": "queued", "mode": body.mode}


@app.get("/status/{job_id}", dependencies=[Depends(require_auth)])
def job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(ScrapeJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id, "url": job.url, "status": job.status,
        "created_at": job.created_at, "finished_at": job.finished_at, "error": job.error,
    }


@app.get("/data", dependencies=[Depends(require_auth)])
@limiter.limit("30/minute")
def list_data(request: Request, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    pages = db.query(ScrapedPage).filter_by(status="done").offset(skip).limit(limit).all()
    return [
        {"id": p.id, "url": p.url, "title": p.title, "scraped_at": p.scraped_at,
         "content_preview": p.content[:300] if p.content else ""}
        for p in pages
    ]


@app.get("/data/{page_id}", dependencies=[Depends(require_auth)])
def get_page(page_id: int, db: Session = Depends(get_db)):
    page = db.query(ScrapedPage).filter_by(id=page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return {
        "id": page.id, "url": page.url, "title": page.title, "content": page.content,
        "content_hash": page.content_hash, "scraped_at": page.scraped_at, "last_seen_at": page.last_seen_at,
    }


# ── Scheduling ──────────────────────────────────────────────────────────────────

class ScheduleRequest(BaseModel):
    url: str
    mode: str = "static"
    minute: str = "*"
    hour: str = "*"
    day_of_week: str = "*"
    day_of_month: str = "*"
    month_of_year: str = "*"
    feed_selector: str = "body"
    item_selector: Optional[str] = None
    detail_wait_selector: str = "h1"
    max_scrolls: int = 10
    max_items: int = 10


@app.post("/schedules", dependencies=[Depends(require_auth)])
def create_schedule(body: ScheduleRequest, db: Session = Depends(get_db)):
    if body.mode not in ("static", "playwright", "scroll", "click_through"):
        raise HTTPException(status_code=400, detail="Invalid mode")

    schedule = ScheduledScrape(**body.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    upsert_beat_entry(schedule)  # registers with live RedBeat scheduler

    return {"id": schedule.id, "status": "scheduled"}


@app.get("/schedules", dependencies=[Depends(require_auth)])
def list_schedules(db: Session = Depends(get_db)):
    schedules = db.query(ScheduledScrape).all()
    return [
        {
            "id": s.id, "url": s.url, "mode": s.mode,
            "cron": f"{s.minute} {s.hour} {s.day_of_month} {s.month_of_year} {s.day_of_week}",
            "enabled": s.enabled, "created_at": s.created_at, "last_triggered_at": s.last_triggered_at,
        }
        for s in schedules
    ]


@app.patch("/schedules/{schedule_id}", dependencies=[Depends(require_auth)])
def toggle_schedule(schedule_id: int, enabled: bool, db: Session = Depends(get_db)):
    schedule = db.query(ScheduledScrape).filter_by(id=schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    schedule.enabled = enabled
    db.commit()

    if enabled:
        upsert_beat_entry(schedule)
    else:
        remove_beat_entry(schedule_id)  # disabling removes the live entry so it stops firing

    return {"id": schedule_id, "enabled": enabled}


@app.delete("/schedules/{schedule_id}", dependencies=[Depends(require_auth)])
def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(ScheduledScrape).filter_by(id=schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    remove_beat_entry(schedule_id)
    db.delete(schedule)
    db.commit()
    return {"id": schedule_id, "status": "deleted"}


# ── Export ────────────────────────────────────────────────────────────────────

@app.get("/export", dependencies=[Depends(require_auth)])
def export_csv():
    buffer = pages_to_csv()
    filename = f"scraped_pages_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


class S3ExportRequest(BaseModel):
    bucket: Optional[str] = None
    key_prefix: str = "scraper-exports"


@app.post("/export/s3", dependencies=[Depends(require_auth)])
def export_to_s3(body: S3ExportRequest):
    try:
        result = upload_csv_to_s3(bucket=body.bucket, key_prefix=body.key_prefix)
        return result
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
