# TransactIQ

TransactIQ is a production-style backend assignment for an AI-powered transaction processing pipeline. It accepts a dirty financial transaction CSV, processes it asynchronously, cleans and stores transaction data, detects anomalies, uses Gemini for missing category classification and narrative summary generation, and exposes polling APIs through FastAPI.

The intended reviewer workflow is through Swagger UI:

```text
http://localhost:8000/docs
```

## Problem Statement

Financial exports often contain inconsistent dates, mixed casing, duplicate rows, missing categories, currency symbols in amount fields, and suspicious transactions. A synchronous upload endpoint would block while processing and would be fragile under larger files or LLM latency.

TransactIQ solves this by creating a job immediately, queueing processing work in Celery, and allowing reviewers to poll for status and results.

## Solution Overview

1. A reviewer uploads `transactions.csv` from Swagger UI.
2. FastAPI validates the upload, creates a `pending` job, saves the CSV, and pushes a task to Redis.
3. Celery reads the CSV, cleans rows, bulk inserts transactions, detects anomalies, calls Gemini, creates a summary, and marks the job `completed`.
4. Swagger UI is used to inspect job status and full results.

## Key Features

- CSV upload with file validation.
- Asynchronous job processing with Celery and Redis.
- PostgreSQL persistence using SQLAlchemy models and Alembic migrations.
- Data cleaning for dates, amounts, currency, status, duplicates, and missing categories.
- Rule-based anomaly detection.
- Gemini 1.5 Flash category classification for missing categories.
- Gemini narrative summary and risk level generation.
- Results endpoint with cleaned transactions, anomalies, category breakdown, and summary.
- Swagger/OpenAPI documentation for reviewer-friendly testing.
- Graceful LLM failure handling with structured logs.

## Architecture Overview

```text
User
 |
Swagger UI
 |
FastAPI
 |
Redis Queue
 |
Celery Worker
 |--------> PostgreSQL
 |
Gemini 1.5 Flash
 |
Results API
```

Detailed draw.io compatible architecture diagram:

```text
docs/architecture.drawio
```

Request lifecycle:

```text
CSV Upload
 -> Job Creation
 -> Redis Queue
 -> Celery Worker
 -> Cleaning
 -> Persistence
 -> Anomaly Detection
 -> Gemini Classification
 -> Summary Generation
 -> Results
```

## Component Responsibilities

- `FastAPI`: exposes health, upload, job listing, status, and results APIs.
- `Redis`: stores Celery queue messages and worker coordination state.
- `Celery Worker`: performs CSV processing outside the request-response path.
- `PostgreSQL`: stores jobs, cleaned transactions, anomaly flags, LLM metadata, and summaries.
- `Gemini`: classifies missing categories and generates narrative/risk summary text.

## Technology Stack

- Python 3.12
- FastAPI
- PostgreSQL
- Redis
- Celery
- SQLAlchemy 2.x
- Alembic
- Pydantic Settings
- Gemini 1.5 Flash
- Docker Compose

## Local Setup

Create a local environment file:

```bash
cp .env.example .env
```

Set a real Gemini key in `.env`:

```text
GEMINI_API_KEY=your_real_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
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
GEMINI_MODEL=gemini-2.5-flash
```

## Docker Setup

Start the complete system:

```bash
docker compose up --build
```

Docker Compose starts:

- `api`: FastAPI app and Alembic startup migration.
- `worker`: Celery worker for transaction processing.
- `postgres`: PostgreSQL database with persistent volume.
- `redis`: Celery broker/result backend.

## Running Migrations

Migrations run automatically when the API container starts.

Manual migration command:

```bash
docker compose run --rm api alembic upgrade head
```

## Running the System

1. Run `docker compose up --build`.
2. Open Swagger UI at `http://localhost:8000/docs`.
3. Use `POST /jobs/upload` to upload `transactions.csv`.
4. Copy the returned `job_id`.
5. Use `GET /jobs/{job_id}/status` until the job is `completed`.
6. Use `GET /jobs/{job_id}/results` to inspect cleaned transactions, anomalies, categories, and summary.

## Swagger UI Usage

Swagger UI is the official testing interface for this submission.

Open:

```text
http://localhost:8000/docs
```

Recommended demo flow:

1. Expand `GET /health` and execute it.
2. Expand `POST /jobs/upload`, choose `transactions.csv`, and execute.
3. Copy the returned `job_id`.
4. Expand `GET /jobs` and execute.
5. Expand `GET /jobs/{job_id}/status`, paste the UUID, and execute.
6. Expand `GET /jobs/{job_id}/results`, paste the UUID, and execute.

## API Documentation

### Upload CSV

Swagger operation:

```text
POST /jobs/upload
```

Purpose:

```text
Uploads transactions.csv, creates a pending job, stores the file, and queues Celery processing.
```

Swagger screenshot placeholder:

```text
docs/screenshots/swagger-upload-placeholder.png
```

### Get Jobs

Swagger operation:

```text
GET /jobs
```

Purpose:

```text
Lists jobs with filename, status, raw row count, clean row count, and created timestamp.
```

### Get Job Status

Swagger operation:

```text
GET /jobs/{job_id}/status
```

Purpose:

```text
Returns pending, processing, completed, or failed. Includes summary when available.
```

### Get Results

Swagger operation:

```text
GET /jobs/{job_id}/results
```

Purpose:

```text
Returns job metadata, summary, anomalies, category breakdown, and cleaned transactions.
```

## Gemini Integration

Gemini 1.5 Flash is used for:

- Missing category classification.
- Narrative summary and risk level generation.

Category classification only runs for transactions where `original_category IS NULL`.

Allowed categories:

```text
Food
Shopping
Travel
Transport
Utilities
Cash Withdrawal
Entertainment
Other
```

If Gemini is missing, unavailable, or returns invalid JSON, the job still completes and records `llm_failed=true`. Worker logs include the exact Gemini exception type and message.

## Error Handling

- Invalid file type: rejected with `400`.
- Empty upload: rejected with `400`.
- Missing CSV columns: job is marked `failed`.
- CSV parsing/cleaning failure: job is marked `failed`.
- Database failure during upload: returns `500`.
- Gemini failure: job continues with graceful fallback and `llm_failed=true`.
- Missing `GEMINI_API_KEY`: startup logs an error and LLM steps use fallback behavior.

## Scalability Considerations

- Pandas currently loads the whole CSV in memory.
- Redis queue depth grows if workers cannot keep up.
- Gemini rate limits can slow category classification and summaries.
- Polling APIs read directly from PostgreSQL.
- Local upload volume is assignment-friendly but not production-grade object storage.

## Future Improvements

- Store uploads in S3 or GCS.
- Replace Redis queue with Kafka for high-throughput event streaming.
- Run API and worker deployments on Kubernetes.
- Horizontally scale Celery workers by workload type.
- Add PostgreSQL read replicas for heavy results traffic.
- Add metrics, tracing, and dashboarding.
- Add authentication and per-user job ownership.
- Add integration tests with a mocked Gemini client.

## Supporting Review Docs

- `docs/final_validation_checklist.md`
- `docs/review_prep.md`
- `docs/demo_video_script.md`
- `docs/final_repository_audit.md`
