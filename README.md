# TransactIQ

AI-powered transaction processing pipeline built with FastAPI, PostgreSQL, Redis,
Celery, SQLAlchemy, Alembic, and Docker Compose.

This repository is currently at Phase 2: job management and Celery lifecycle.

## Run

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

## Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "TransactIQ",
  "environment": "development"
}
```

## Job API

Upload a CSV and enqueue a placeholder processing task:

```bash
curl -X POST http://localhost:8000/jobs/upload \
  -F "file=@transactions.csv"
```

List all jobs:

```bash
curl http://localhost:8000/jobs
```

Filter jobs by status:

```bash
curl "http://localhost:8000/jobs?status=completed"
```

Poll a job:

```bash
curl http://localhost:8000/jobs/{job_id}/status
```

## Services

- `api`: FastAPI application. Runs Alembic migrations on startup, then starts Uvicorn.
- `worker`: Celery worker process using the same application image.
- `postgres`: PostgreSQL database with a persistent Docker volume.
- `redis`: Redis broker/result backend for Celery.

## Current Scope

Implemented:

- FastAPI bootstrap application
- `/health` endpoint
- Pydantic Settings configuration
- SQLAlchemy 2.x database setup
- Approved ORM models
- Alembic configuration and initial migration
- Celery application configuration
- Redis broker/result backend wiring
- Dockerfile
- Docker Compose with API, worker, PostgreSQL, and Redis
- Shared uploads volume
- Structured JSON logging
- `POST /jobs/upload`
- `GET /jobs`
- `GET /jobs/{job_id}/status`
- CSV extension and empty file validation
- Uploaded file storage as `storage/uploads/{job_id}.csv`
- Job repository and summary repository
- Job service orchestration
- Celery placeholder task for `pending -> processing -> completed`

Not implemented yet:

- Transaction cleaning
- Anomaly detection
- Gemini classification
- Gemini narrative summary
- Real Celery processing pipeline

## Future Submission Links

- High-level visual diagram: TBD
- Technical video walkthrough: TBD
