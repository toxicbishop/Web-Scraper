import redis
import os
from datetime import datetime
from models.db import SessionLocal, ScrapedPage

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

DEDUP_KEY_PREFIX = "scraper:seen:"
DEDUP_TTL = 60 * 60 * 24 * 7


def is_duplicate(content_hash: str) -> bool:
    return r.exists(f"{DEDUP_KEY_PREFIX}{content_hash}") == 1


def mark_seen(content_hash: str):
    r.setex(f"{DEDUP_KEY_PREFIX}{content_hash}", DEDUP_TTL, "1")


def save_page(data: dict):
    if is_duplicate(data["content_hash"]):
        print(f"[pipeline] Duplicate skipped: {data['url']}")
        return None

    db = SessionLocal()
    try:
        existing = db.query(ScrapedPage).filter_by(url=data["url"]).first()

        if existing:
            existing.content = data["content"]
            existing.title = data["title"]
            existing.content_hash = data["content_hash"]
            existing.last_seen_at = datetime.utcnow()
            existing.status = "done"
            db.commit()
            db.refresh(existing)
            page = existing
        else:
            page = ScrapedPage(
                url=data["url"],
                title=data["title"],
                content=data["content"],
                content_hash=data["content_hash"],
                status="done",
            )
            db.add(page)
            db.commit()
            db.refresh(page)

        mark_seen(data["content_hash"])
        return page

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
