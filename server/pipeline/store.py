import redis
import os
from datetime import datetime, timezone
from models.db import SessionLocal, ScrapedPage

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

DEDUP_KEY_PREFIX = "scraper:seen:"
DEDUP_TTL = 60 * 60 * 24 * 7  # 7 days


def is_duplicate(content_hash: str) -> bool:
    """Check Redis for a previously seen content hash."""
    return r.exists(f"{DEDUP_KEY_PREFIX}{content_hash}") == 1


def mark_seen(content_hash: str):
    """Store content hash in Redis with TTL."""
    r.setex(f"{DEDUP_KEY_PREFIX}{content_hash}", DEDUP_TTL, "1")


def save_page(data: dict) -> ScrapedPage | None:
    """
    Save scraped page to PostgreSQL.
    Skips if content hash already seen (deduplication).
    Returns the saved model or None if duplicate.
    """
    if is_duplicate(data["content_hash"]):
        print(f"[pipeline] Duplicate skipped: {data['url']}")
        return None

    db = SessionLocal()
    try:
        existing = db.query(ScrapedPage).filter_by(url=data["url"]).first()

        if existing:
            # Update if content changed
            existing.content = data["content"]
            existing.title = data["title"]
            existing.content_hash = data["content_hash"]
            existing.last_seen_at = datetime.now(timezone.utc)
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
