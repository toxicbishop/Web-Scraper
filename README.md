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
![Platform](https://img.shields.io/badge/platform-Docker%20%7C%20Linux%20%7C%20Windows-blue.svg)

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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.