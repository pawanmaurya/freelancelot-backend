# Freelancelot Scraper & Alerts (FastAPI)

A FastAPI-based backend that fetches Upwork jobs via Apify, stores them in Postgres, exposes a powerful filtered search API, and sends real‑time Telegram alerts to users based on their saved filters in Supabase.

### Key Features
- Fetch Upwork jobs from Apify and persist to Postgres
- Rich job schema with client stats, budgets, skills, and timestamps
- Filtered search API over the last 24 hours of jobs
- Telegram alerting pipeline with rate and duplicate suppression
- Supabase integration for user profiles and filters
- Dockerized stack with Nginx reverse proxy and optional TLS via Let’s Encrypt

## Architecture

- `FastAPI app` (`main.py`)
  - Wires CORS, routers, startup hooks, and a test `/ping` endpoint.
  - On startup: initializes logging, database tables, and the scheduler.
- `Scheduler` (`background_tasks/scheduler.py`)
  - Defines async jobs to crawl from Apify and to notify users of new jobs.
  - Uses `services.postgres` for persistence and alert bookkeeping.
- `Scraper` (`services/apify_scrapper.py`)
  - Calls Apify Actor Task endpoint using `httpx` (async) and maps items to a normalized job dict.
- `Persistence` (`services/postgres.py`, `model/job.py`, `model/job_alert.py`)
  - SQLAlchemy models and session management
  - `save_jobs` dedupes by Upwork `id` and persists normalized jobs
  - `get_latest_jobs` returns jobs published in the last N minutes for alerting
  - `job_alerts` table records user/job alert emissions to avoid duplicates
- `Supabase` (`services/supabase.py`)
  - Loads eligible users (paid/active trial and Telegram linked) and their filters
  - Updates profile with Telegram chat id during linking
- `Notification` (`services/notification.py`)
  - `match_jobs_to_filter` performs keyword/category/price/type/location/rating checks
  - `send_telegram_alert` formats rich HTML messages and posts via Telegram Bot API
- `HTTP API` (`routers/jobs.py`, `routers/telegram.py`)
  - `/api/fetch_filtered_jobs` returns filtered jobs (24h window)
  - `/api/link-telegram` links Telegram chat id to a user profile
- `Proxy & TLS` (`nginx.*.conf`, `docker-compose.yml`, `init_ssl.sh`)
  - Nginx -> FastAPI reverse proxy, with Certbot for Let’s Encrypt certificates

### High-Level Data Flow
1. Scheduler (or `/ping`) triggers Apify crawl → normalized job dicts
2. Jobs are persisted to Postgres (deduped by `id`)
3. Alert loop fetches recent jobs → loads eligible users and filters from Supabase
4. Jobs matched per filter → Telegram messages sent → alerts recorded to avoid duplicates
5. Clients query `/api/fetch_filtered_jobs` for on-demand filtered lists

## Project Layout

- `main.py` — App bootstrap, CORS, routers, startup hooks
- `background_tasks/scheduler.py` — Crawling and alert scheduling
- `routers/jobs.py` — Filtered job search API
- `routers/telegram.py` — Telegram linking endpoint
- `services/apify_scrapper.py` — Apify Actor Task integration
- `services/postgres.py` — DB engine, sessions, queries, alert bookkeeping
- `services/notification.py` — Matching and Telegram sending
- `services/supabase.py` — Supabase client and queries
- `model/job.py` — SQLAlchemy `Job` model (rich schema)
- `model/job_alert.py` — `JobAlert` model to record sent alerts
- `model/filter.py` — ORM models mirroring Supabase filter structure
- `utils/logger.py` — Basic logging setup
- `utils/telegram_link_bot.py` — Standalone Telegram bot to link accounts
- `docker-compose.yml`, `Dockerfile` — Containerization and orchestration
- `nginx.*.conf`, `init_ssl.sh` — Reverse proxy and TLS bootstrap

## API

### Health / Test
- `GET /ping`
  - Triggers a fetch from Apify, saves jobs, and returns the raw jobs payload.

### Jobs
- `GET /api/fetch_filtered_jobs`
  - Auth: API key via dependency (`utils.authcheck.verify_api_key`) if configured.
  - Query params (selected):
    - `categories` (List[str], required)
    - `keywords` (List[str]) — AND logic across provided keywords
    - `client_locations`, `exclude_locations` (List[str])
    - `min_client_rating` (float)
    - `job_types` (List[str]) — `HOURLY`, `FIXED`
    - Hourly: `min_hourly_rate`, `max_hourly_rate`
    - Fixed: `min_fixed_budget`, `max_fixed_budget`
    - Client metrics: `min_reviews_count`, `min_total_jobs_posted`, `min_total_hires`, `min_total_spent`, `max_total_spent`, `min_hire_rate`, `min_avg_hourly_rate`, `payment_method_verified`
  - Returns: `{ matches: JobDTO[], total_matches: number }`
  - Window: Only jobs from the last 24 hours (`published_at >= now() - 1 day`).

Example:
```bash
curl -G "http://localhost:8000/api/fetch_filtered_jobs" \
  --data-urlencode "categories=Web,Mobile" \
  --data-urlencode "keywords=python" \
  --data-urlencode "job_types=HOURLY" \
  --data-urlencode "min_hourly_rate=20"
```

### Telegram
- `POST /api/link-telegram`
  - Body: `{ "user_token": "<profile_id>", "chat_id": 123456 }`
  - Associates Telegram chat id with the given Supabase user profile id.

## Environment Variables

Required for core services:
- `DATABASE_URL` — Postgres SQLAlchemy URL, e.g. `postgresql://user:pass@host:5432/db`
- `APIFY_API_TOKEN` — Token for Apify Actor Task
- `ALLOWED_ORIGINS` — CSV list for CORS, e.g. `http://localhost:3000,https://freelancelot.app`

Telegram & Supabase:
- `TELEGRAM_BOT_TOKEN` — Telegram bot token
- `BACKEND_LINK_ENDPOINT` — e.g., `http://localhost:8000/api/link-telegram` (bot -> backend)
- `SUPABASE_URL` — Supabase URL
- `SUPABASE_SERVICE_KEY` — Service role key for backend access

Optional/Deployment:
- `UVICORN_*` settings if you customize the run command

## Local Development

### Prerequisites
- Python 3.11+
- Postgres 15+ (or use Docker Compose)

### Setup
```bash
# 1) Create and populate .env
cp .env.example .env   # create one with the vars above

# 2) (Optional) Start Postgres via Docker
docker compose up -d db

# 3) Install deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 4) Run the API
uvicorn main:app --reload
```

Open http://localhost:8000/ping to test a crawl-and-save run.

## Docker & Deployment

### Compose (API, DB, Nginx, Telegram bot)
```bash
docker compose up --build
```
- FastAPI is available on container port 8000 (proxied by Nginx if configured)
- Telegram bot container runs `utils/telegram_link_bot.py`

### TLS with Let’s Encrypt
The helper script boots Nginx with HTTP-only config, acquires certs, then switches to HTTPS.
```bash
bash init_ssl.sh
```
- Ensure your domain `api.freelancelot.app` points to the server’s IP beforehand
- Nginx configs: `nginx.http.conf` (challenges), `nginx.https.conf` (proxy + TLS)

## Scheduler

- Defined in `background_tasks/scheduler.py` and started on app startup.
- Contains two async jobs you can enable by uncommenting the `add_job` calls:
  - Crawl: fetch from Apify at intervals and persist jobs
  - Alerts: evaluate filters and send Telegram messages

## Database Schema (key tables)

- `jobs` (`model/job.py`):
  - Core: `id`, `title`, `url`, `description`, `type`, `status`
  - Taxonomy: `category`, `category_group`, `occupation`
  - Requirements: `skills`, `tags`, `questions`
  - Payment: `budget`, `currency`, `hourly_min`, `hourly_max`
  - Details: `contractor_tier`, `level`, `is_contract_to_hire`, `is_payment_method_verified`, `premium`, `number_of_positions`, `duration_label`, `duration_weeks`, `hourly_type`
  - Client: `client_company_*`, `client_*` stats, computed `hire_rate`
  - Timestamps: `published_at`, `created_at`, `sourced_at`
- `job_alerts` (`model/job_alert.py`): `id`, `user_id` (UUID), `job_id`, `sent_at`

Supabase (external):
- `profiles`: `id` (UUID), `telegram_id`, plan/trial gating
- `filters`, `filter_keywords`, `filter_categories` used to build in-memory filters

## Security Notes
- CORS configured via `ALLOWED_ORIGINS`
- API key dependency exists in `utils/authcheck.verify_api_key` (wire as needed)
- No PII stored besides Telegram chat id in Supabase

## Troubleshooting
- Apify returns empty list: verify `APIFY_API_TOKEN`
- DB connection errors: confirm `DATABASE_URL` and Postgres reachability
- Telegram alerts not sending: check `TELEGRAM_BOT_TOKEN`, ensure chat linked via `/start <token>`
- No matches from `/api/fetch_filtered_jobs`: ensure `categories` provided and data exists within 24h window
- TLS issues: ensure DNS points to server, run `init_ssl.sh`, inspect `nginx` container logs

## License
MIT 