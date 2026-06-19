import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from contextlib import asynccontextmanager

import jwt
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

from models.db import init_db, get_db, ScrapedPage, ScrapeJob, PeriodicTarget
from workers.tasks import scrape_url, export_to_s3_task
from sqlalchemy.orm import Session

SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
ALGORITHM = "HS256"

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Portfolio Scraper API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Auth ──────────────────────────────────────────────────────────────────────

class TokenRequest(BaseModel):
    username: str
    password: str


@app.post("/token")
def get_token(body: TokenRequest):
    """Issue a JWT. In production, verify against a real user store."""
    if body.username != "admin" or body.password != "admin":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    payload = {
        "sub": body.username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
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


# ── Scrape endpoints ──────────────────────────────────────────────────────────

class ScrapeRequest(BaseModel):
    url: str
    use_playwright: bool = False


@app.post("/scrape", dependencies=[Depends(require_auth)])
@limiter.limit("10/minute")
def trigger_scrape(request: Request, body: ScrapeRequest, db: Session = Depends(get_db)):
    """Queue a scrape job. Returns job ID for status polling."""
    job = ScrapeJob(url=body.url, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)

    task = scrape_url.delay(body.url, job_id=job.id, use_playwright=body.use_playwright)

    job.celery_task_id = task.id
    db.commit()

    return {"job_id": job.id, "task_id": task.id, "status": "queued"}


@app.get("/status/{job_id}", dependencies=[Depends(require_auth)])
def job_status(job_id: int, db: Session = Depends(get_db)):
    """Poll the status of a scrape job."""
    job = db.query(ScrapeJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.id,
        "url": job.url,
        "status": job.status,
        "created_at": job.created_at,
        "finished_at": job.finished_at,
        "error": job.error,
    }


@app.get("/data", dependencies=[Depends(require_auth)])
@limiter.limit("30/minute")
def list_data(
    request: Request,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List all successfully scraped pages."""
    pages = db.query(ScrapedPage).filter_by(status="done").offset(skip).limit(limit).all()
    return [
        {
            "id": p.id,
            "url": p.url,
            "title": p.title,
            "scraped_at": p.scraped_at,
            "content_preview": p.content[:300] if p.content else "",
        }
        for p in pages
    ]


@app.get("/data/{page_id}", dependencies=[Depends(require_auth)])
def get_page(page_id: int, db: Session = Depends(get_db)):
    """Fetch full content of a scraped page."""
    page = db.query(ScrapedPage).filter_by(id=page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return {
        "id": page.id,
        "url": page.url,
        "title": page.title,
        "content": page.content,
        "content_hash": page.content_hash,
        "scraped_at": page.scraped_at,
        "last_seen_at": page.last_seen_at,
    }


# ── Schedule & Export Endpoints ───────────────────────────────────────────────

class ScheduleRequest(BaseModel):
    url: str
    interval_minutes: int = 60
    enabled: bool = True


class S3ExportRequest(BaseModel):
    bucket_name: Optional[str] = None
    s3_key: Optional[str] = None


@app.post("/schedule", dependencies=[Depends(require_auth)])
def add_schedule(body: ScheduleRequest, db: Session = Depends(get_db)):
    """Add or update a periodic scraping schedule for a URL."""
    existing = db.query(PeriodicTarget).filter_by(url=body.url).first()
    if existing:
        existing.interval_minutes = body.interval_minutes
        existing.enabled = body.enabled
        db.commit()
        db.refresh(existing)
        return {"status": "updated", "target_id": existing.id}
    
    target = PeriodicTarget(url=body.url, interval_minutes=body.interval_minutes, enabled=body.enabled)
    db.add(target)
    db.commit()
    db.refresh(target)
    return {"status": "created", "target_id": target.id}


@app.get("/schedule", dependencies=[Depends(require_auth)])
def list_schedule(db: Session = Depends(get_db)):
    """List all scheduled periodic scraping targets."""
    targets = db.query(PeriodicTarget).all()
    return [
        {
            "id": t.id,
            "url": t.url,
            "interval_minutes": t.interval_minutes,
            "last_scraped_at": t.last_scraped_at,
            "enabled": t.enabled,
        }
        for t in targets
    ]


@app.delete("/schedule/{target_id}", dependencies=[Depends(require_auth)])
def delete_schedule(target_id: int, db: Session = Depends(get_db)):
    """Remove a periodic scraping schedule."""
    target = db.query(PeriodicTarget).filter_by(id=target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    db.delete(target)
    db.commit()
    return {"status": "deleted"}


@app.get("/export/csv", dependencies=[Depends(require_auth)])
def export_csv(db: Session = Depends(get_db)):
    """Stream all scraped done pages as a CSV file download."""
    import io
    import csv
    pages = db.query(ScrapedPage).filter_by(status="done").all()
    
    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "url", "title", "scraped_at", "last_seen_at", "content"])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)
        
        for p in pages:
            writer.writerow([p.id, p.url, p.title, p.scraped_at, p.last_seen_at, p.content])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    headers = {
        "Content-Disposition": 'attachment; filename="scraped_pages.csv"',
        "Content-Type": "text/csv",
    }
    return StreamingResponse(generate(), headers=headers)


@app.post("/export/s3", dependencies=[Depends(require_auth)])
def trigger_s3_export(body: S3ExportRequest):
    """Trigger a background task to export scraped pages to AWS S3 in CSV format."""
    task = export_to_s3_task.delay(body.bucket_name, body.s3_key)
    return {"status": "queued", "task_id": task.id}


@app.get("/health")
def health():
    return {"status": "ok"}
