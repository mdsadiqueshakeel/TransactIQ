# TransactIQ

AI-powered transaction processing pipeline for dirty financial CSV exports.

TransactIQ accepts a transaction CSV, creates an asynchronous processing job, cleans and persists transactions, detects anomalies, uses Gemini 1.5 Flash for missing category classification and narrative summary generation, and exposes polling APIs for status and results.

## Architecture

```text
Client
  -> FastAPI API
      -> PostgreSQL: jobs, transactions, summaries
      -> Redis: Celery broker/result backend
      -> storage/uploads/{job_id}.csv
  -> Celery Worker
      -> PostgreSQL
      -> Redis
      -> Gemini 1.5 Flash
```

Draw.io compatible diagram:

```text
docs/architecture.drawio
```

## Stack

- FastAPI
- PostgreSQL
- Redis
- Celery
- SQLAlchemy 2.x
- Alembic
- Pydantic Settings
- Gemini 1.5 Flash
- Docker Compose

## Setup

Create `.env` from `.env.example` and set your Gemini API key:

```bash
cp .env.example .env
```

Required Gemini variable:

```text
GEMINI_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-1.5-flash
```

Start everything:

```bash
docker compose up --build
```

The API runs at:

```text
http://localhost:8000
```

OpenAPI docs:

```text
http://localhost:8000/docs
```

## Docker Setup

Docker Compose starts four services:

- `api`: FastAPI application. Runs Alembic migrations on startup.
- `worker`: Celery worker. Processes uploaded CSV jobs.
- `postgres`: PostgreSQL database with persistent volume.
- `redis`: Celery broker and result backend.

## Running Migrations

Migrations run automatically when the API container starts:

```bash
docker compose up --build
```

Run migrations manually:

```bash
docker compose run --rm api alembic upgrade head
```

## Environment Variables

```text
APP_ENV=development
DEBUG=false
LOG_LEVEL=INFO
POSTGRES_DB=transactiq
POSTGRES_USER=transactiq
POSTGRES_PASSWORD=transactiq
DATABASE_URL=postgresql+psycopg://transactiq:transactiq@postgres:5432/transactiq
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
UPLOAD_DIR=/app/storage/uploads
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash
```

## API Endpoints

- `GET /health`
- `POST /jobs/upload`
- `GET /jobs`
- `GET /jobs?status=pending`
- `GET /jobs/{job_id}/status`
- `GET /jobs/{job_id}/results`

## Example Curl Commands

Health:

```bash
curl http://localhost:8000/health
```

Upload CSV:

```bash
curl -X POST http://localhost:8000/jobs/upload \
  -F "file=@transactions.csv"
```

List jobs:

```bash
curl http://localhost:8000/jobs
```

Filter jobs:

```bash
curl "http://localhost:8000/jobs?status=completed"
```

Poll status:

```bash
curl http://localhost:8000/jobs/{job_id}/status
```

Fetch results:

```bash
curl http://localhost:8000/jobs/{job_id}/results
```

## Processing Pipeline

```text
Upload CSV
  -> Create pending Job
  -> Queue Celery task
  -> Load CSV with pandas
  -> Validate required columns
  -> Clean data
  -> Bulk insert transactions
  -> Detect anomalies
  -> Classify missing categories with Gemini
  -> Generate summary with Gemini
  -> Store job summary
  -> Mark job completed
```

## Gemini Setup

1. Create a Gemini API key from Google AI Studio.
2. Put the key in `.env` as `GEMINI_API_KEY`.
3. Restart Docker Compose after changing `.env`.
4. Check logs for `Gemini configuration detected`.

If `GEMINI_API_KEY` is missing, the job still completes, but:

- `jobs.llm_failed` becomes `true`
- category rows that needed Gemini stay gracefully handled
- summary narrative falls back to deterministic text

## Troubleshooting

`llm_failed=true`:

- Confirm `.env` exists, not only `.env.example`.
- Confirm `GEMINI_API_KEY` is set in `.env`.
- Confirm the worker container sees the key with `docker compose exec worker env`.
- Restart containers with `docker compose up --build`.
- Check worker logs for `Gemini SDK initialized`.
- Check worker logs for exact Gemini API exception type and message.

`row_count_clean=0`:

- Check worker logs.
- Confirm the CSV has all required columns.
- Confirm the worker container is running.

`GET /jobs/{job_id}/results` returns empty transactions:

- Confirm the job status is `completed`.
- Confirm the worker processed the queue.
- Confirm PostgreSQL migrations ran.

`GeminiUnavailableError`:

- The worker is running without `GEMINI_API_KEY`.
- Add the key to `.env`.
- Recreate containers with `docker compose up --build`.

## Final Validation

Use:

```text
docs/final_validation_checklist.md
```

## Technical Review

Use:

```text
docs/technical_review.md
```
