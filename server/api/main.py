import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

from models.db import init_db, get_db, ScrapedPage, ScrapeJob
from workers.tasks import scrape_url
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

    payload = {
        "sub": body.username,
        "exp": datetime.utcnow() + timedelta(hours=24),
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


class ScrapeRequest(BaseModel):
    url: str
    use_playwright: bool = False


@app.post("/scrape", dependencies=[Depends(require_auth)])
@limiter.limit("10/minute")
def trigger_scrape(request: Request, body: ScrapeRequest, db: Session = Depends(get_db)):
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
def list_data(request: Request, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
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


@app.get("/health")
def health():
    return {"status": "ok"}
