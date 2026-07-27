from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://scraper:scraper@localhost:5432/scraperdb")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_utc_now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class ScrapedPage(Base):
    __tablename__ = "scraped_pages"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String)
    content = Column(Text)
    content_hash = Column(String(64), index=True)   # for deduplication
    status = Column(String, default="pending")       # pending | done | failed
    scraped_at = Column(DateTime, default=get_utc_now)
    last_seen_at = Column(DateTime, default=get_utc_now)


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, index=True)
    celery_task_id = Column(String, unique=True)
    url = Column(String, nullable=False)
    status = Column(String, default="queued")        # queued | running | done | failed
    created_at = Column(DateTime, default=get_utc_now)
    finished_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)


class PeriodicTarget(Base):
    __tablename__ = "periodic_targets"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    interval_minutes = Column(Integer, default=60)
    last_scraped_at = Column(DateTime, nullable=True)
    enabled = Column(Boolean, default=True)


def init_db():
    Base.metadata.create_all(bind=engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
