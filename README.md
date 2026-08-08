# Web Scraper

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=next.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=flat&logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A production-grade web scraper with a FastAPI backend, async Celery task queue, Redis-backed deduplication and dynamic scheduling, PostgreSQL storage, and a Next.js dashboard.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16 + TypeScript + Tailwind CSS v4 |
| Scraping | Playwright (stealth) + BeautifulSoup + lxml + requests |
| Queue | Celery + Redis |
| Scheduling | celery-redbeat — dynamic cron schedules, no Beat restart needed |
| Deduplication | Redis (SHA-256 content hash, 7-day TTL) |
| Storage | PostgreSQL via SQLAlchemy |
| Export | CSV stream download + S3 upload via boto3 |
| API | FastAPI + JWT auth + slowapi rate limiting |
| Infra | Docker Compose (postgres, redis, api, worker, beat, frontend) |

## Quick Start

### Full stack (Docker)

```bash
cp server/.env.example server/.env
docker-compose up --build
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |

### Local (without Docker)

```bash
# Backend — terminal 1
cd server
python -m uvicorn api.main:app --reload

# Celery worker — terminal 2
cd server
celery -A workers.tasks worker --loglevel=info

# Celery Beat (scheduling) — terminal 3
cd server
celery -A workers.tasks beat -S redbeat.RedBeatScheduler --loglevel=info

# Frontend — terminal 4
pnpm install
pnpm dev
```

## API Reference

All endpoints except `POST /token` and `GET /health` require `Authorization: Bearer <token>`.

### Auth

```
POST /token
  body:    { "username": "admin", "password": "admin" }
  returns: { "access_token": "..." }
```

### Scraping

Four modes are supported. `mode` defaults to `static` if omitted.

```
POST /scrape
  body: {
    "url": "https://example.com",
    "mode": "static" | "playwright" | "scroll" | "click_through",

    // scroll mode
    "feed_selector": "body",   // CSS selector of the scrollable container
    "max_scrolls": 10,

    // click_through mode
    "item_selector": "a.result",   // required for click_through
    "detail_wait_selector": "h1",
    "max_items": 10
  }
  returns: { "job_id": 1, "task_id": "...", "status": "queued", "mode": "static" }

GET  /status/{job_id}     poll job status
GET  /data                list scraped pages  (?skip=0&limit=20)
GET  /data/{page_id}      full content of a page
```

| Mode | When to use |
|---|---|
| `static` | Plain HTML pages — fastest, no browser overhead |
| `playwright` | JS-rendered pages; uses stealth args and randomised UA |
| `scroll` | Infinite-scroll feeds; scrolls until height stops growing |
| `click_through` | List views where each item must be opened for full data |

### Scheduling

Schedules use standard crontab syntax and take effect immediately without restarting the Beat process.

```
POST   /schedules           create a recurring scrape
  body: {
    "url": "https://example.com",
    "mode": "static",
    "minute": "*/15",   // every 15 minutes
    "hour": "*",
    "day_of_week": "*",
    "day_of_month": "*",
    "month_of_year": "*"
  }
  returns: { "id": 1, "status": "scheduled" }

GET    /schedules           list all schedules
PATCH  /schedules/{id}      enable or disable  (?enabled=true|false)
DELETE /schedules/{id}      remove schedule and cancel the Beat entry
```

### Export

```
GET  /export          stream all scraped pages as a CSV download
POST /export/s3       upload CSV to S3
  body: { "bucket": "my-bucket", "key_prefix": "scraper-exports" }
  returns: { "bucket": "...", "key": "...", "url": "..." }
```

S3 export requires `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `S3_BUCKET` set in the environment (or passed in the request body). Without them the endpoint returns a 400 with a clear error.

### Health

```
GET /health   returns: { "status": "ok" }
```

## Architecture

```
POST /scrape
    └── ScrapeJob created (PostgreSQL)
    └── scrape_url.delay() --> Celery worker
            └── fetch_page_static()          mode=static
                fetch_page()                 mode=playwright  (stealth UA, jitter)
                fetch_infinite_scroll()      mode=scroll      (scroll loop)
                fetch_with_click_through()   mode=click_through
            └── parse_html() --> { url, title, content, hash }
            └── is_low_quality()? --> reject if no title and <40 chars content
            └── is_duplicate()? --> Redis SHA-256 check
            └── save_page() --> PostgreSQL
            └── mark_seen() --> Redis TTL

POST /schedules
    └── ScheduledScrape row created (PostgreSQL)
    └── upsert_beat_entry() --> RedBeat entry saved to Redis
            └── RedBeat fires run_scheduled_scrape on cron
                    └── creates ScrapeJob --> scrape_url.delay()

GET /export
    └── pages_to_csv() --> StreamingResponse (text/csv)

POST /export/s3
    └── pages_to_csv() --> boto3 s3.put_object()
```

## Features

- **Four scrape modes** — static, Playwright, infinite-scroll, and click-through extraction
- **Anti-detection layer** — `--disable-blink-features=AutomationControlled`, rotating User-Agent pool, randomised jitter between page actions, randomised viewport per session
- **Data-quality gate** — results with no title and under 40 characters of content are rejected before dedup or storage; catches silent blocks, captcha redirects, and failed renders
- **Deduplication** — SHA-256 hash checked in Redis before any Postgres write; 7-day TTL
- **Dynamic scheduling** — celery-redbeat stores schedules in Redis; add, enable, disable, or delete without restarting the Beat process
- **CSV and S3 export** — one endpoint streams a CSV directly; another uploads it to any S3-compatible bucket
- **Retry logic** — Celery retries failed tasks 3 times with a 10-second backoff
- **JWT auth** — stateless token auth on all data and schedule endpoints
- **Rate limiting** — per-domain configurable delay in the fetcher; slowapi on the API (10 req/min on `/scrape`, 30 req/min on `/data`)
- **Incremental scraping** — `last_seen_at` updated on re-visits; content updated in place, not duplicated
- **One-command deploy** — `docker-compose up --build` starts all six services

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | yes | PostgreSQL connection string |
| `REDIS_URL` | yes | Redis connection string |
| `SECRET_KEY` | yes | JWT signing secret |
| `FRONTEND_ORIGIN` | no | CORS allowed origin (default: http://localhost:3000) |
| `RATE_LIMIT_DELAY` | no | Seconds between requests (default: 1.5) |
| `AWS_ACCESS_KEY_ID` | S3 only | AWS credentials for S3 export |
| `AWS_SECRET_ACCESS_KEY` | S3 only | AWS credentials for S3 export |
| `AWS_REGION` | S3 only | AWS region (default: us-east-1) |
| `S3_BUCKET` | S3 only | Default bucket for `/export/s3` |

## License

MIT — see [LICENSE](LICENSE).