# 3-Minute Technical Review Script

## 1-Minute Architecture Explanation

TransactIQ is an asynchronous transaction-processing backend. FastAPI handles uploads and polling APIs, PostgreSQL stores jobs, cleaned transactions, and summaries, Redis acts as the Celery broker, and a Celery worker performs the heavy processing outside the request path. Uploaded CSVs are saved to a shared Docker volume so the API can accept the file quickly and the worker can process it later. Gemini 1.5 Flash is used only for LLM-specific work: missing category classification and narrative/risk summary generation.

## 1-Minute Request Lifecycle

A reviewer uploads `transactions.csv` to `POST /jobs/upload`. FastAPI validates that it is a non-empty CSV, creates a `pending` job, saves the file as `storage/uploads/{job_id}.csv`, and enqueues a Celery task. The worker marks the job `processing`, loads the CSV with pandas, validates columns, cleans dates, amounts, currency, status, and categories, removes duplicate rows, and bulk inserts transactions. It then detects anomalies, classifies missing categories in Gemini batches, generates a summary, stores everything in PostgreSQL, and marks the job `completed`. The reviewer polls `/jobs/{job_id}/status` and fetches full output from `/jobs/{job_id}/results`.

## Bottlenecks at 100x Traffic

The first pressure points are file I/O on the shared local upload volume, PostgreSQL connection pool limits, Redis queue depth, worker concurrency, and Gemini rate limits. Large CSVs may also become memory-heavy because pandas loads the full file at once. Polling can add database read pressure if many clients repeatedly call status/results endpoints.

## Enterprise Redesign Plan

For enterprise scale, I would move uploads to object storage such as S3 or GCS, split Celery queues by task type, use dedicated worker pools for CSV processing and LLM calls, stream or chunk large CSVs, add Redis caching for job status, and add observability with metrics, tracing, and structured log aggregation. I would also add idempotency keys, per-job retry policies, rate-limit handling for Gemini, dead-letter queues, and database read replicas for heavy results reads. The trade-off is more infrastructure complexity, but each component can scale independently.
