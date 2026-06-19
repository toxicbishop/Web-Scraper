# Web Scraper

A production-grade web scraper with a FastAPI REST API, Celery task queue, Redis deduplication, and PostgreSQL storage.

## Stack

| Layer | Tech |
|---|---|
| Scraping | Playwright + BeautifulSoup + lxml |
| Queue | Celery + Redis |
| Deduplication | Redis (SHA-256 content hash, 7-day TTL) |
| Storage | PostgreSQL via SQLAlchemy |
| API | FastAPI + JWT auth + slowapi rate limiting |
| Infra | Docker Compose |

## Quick Start

```bash
cp .env.example .env
docker-compose up --build
```

API will be live at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

## API Endpoints

### Auth
```
POST /token
  body: { "username": "admin", "password": "admin" }
  returns: { "access_token": "..." }
```

### Scraping
```
POST /scrape                   # queue a scrape job
  body: { "url": "https://example.com", "use_playwright": false }
  returns: { "job_id": 1, "task_id": "...", "status": "queued" }

GET  /status/{job_id}          # poll job status
GET  /data                     # list scraped pages (paginated)
GET  /data/{page_id}           # full content of a page
GET  /health                   # health check
```

All endpoints except `/token` and `/health` require `Authorization: Bearer <token>`.

## Architecture

```
POST /scrape
    └─► ScrapeJob created (DB)
    └─► scrape_url.delay() → Celery worker
            └─► fetch_page() / fetch_page_static()
            └─► parse_html() → { url, title, content, hash }
            └─► is_duplicate()? → Redis hash check
            └─► save_page() → PostgreSQL
            └─► mark_seen() → Redis TTL
    └─► GET /status/{id} to poll
```

## Key Portfolio Features

- **Deduplication** — SHA-256 hash stored in Redis; duplicate content never hits Postgres
- **Retry logic** — Celery retries failed tasks 3x with 10s delay
- **Rate limiting** — per-domain configurable delay + slowapi on API endpoints
- **JWT auth** — stateless token auth on all data endpoints
- **Incremental scraping** — `last_seen_at` tracks re-visits; content updates in place
- **Playwright support** — `use_playwright: true` for JS-heavy sites
- **One-command deploy** — `docker-compose up --build`
