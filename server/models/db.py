from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://scraper:scraper@localhost:5432/scraperdb")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class ScrapedPage(Base):
    __tablename__ = "scraped_pages"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String)
    content = Column(Text)
    content_hash = Column(String(64), index=True)
    status = Column(String, default="pending")
    scraped_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, index=True)
    celery_task_id = Column(String, unique=True)
    url = Column(String, nullable=False)
    status = Column(String, default="queued")
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)


class ScheduledScrape(Base):
    """
    A recurring scrape job. Mirrors a RedBeat entry (same id used as the
    RedBeat entry name: 'schedule:{id}') so the DB row and the live Beat
    schedule stay in sync — DB is the source of truth for display,
    RedBeat is the source of truth for actually firing.
    """
    __tablename__ = "scheduled_scrapes"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    mode = Column(String, default="static")

    # cron fields, celery.schedules.crontab syntax (e.g. "*/15" for every 15 min)
    minute = Column(String, default="*")
    hour = Column(String, default="*")
    day_of_week = Column(String, default="*")
    day_of_month = Column(String, default="*")
    month_of_year = Column(String, default="*")

    feed_selector = Column(String, default="body")
    item_selector = Column(String, nullable=True)
    detail_wait_selector = Column(String, default="h1")
    max_scrolls = Column(Integer, default=10)
    max_items = Column(Integer, default=10)

    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_triggered_at = Column(DateTime, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
