# Technical Review Prep

Target total time: 3 minutes.

## A. 60-Second Architecture Explanation

TransactIQ is an asynchronous backend pipeline for processing dirty transaction CSV files. FastAPI handles the reviewer-facing APIs and Swagger UI. PostgreSQL stores jobs, cleaned transactions, anomaly flags, Gemini metadata, and summaries. Redis is the Celery broker, and Celery workers execute the processing pipeline outside the request path. Gemini 1.5 Flash is used only for LLM-specific enrichment: missing category classification and narrative summary generation. Docker Compose runs the entire system with API, worker, Redis, and PostgreSQL.

## B. 60-Second Request Lifecycle

A reviewer opens Swagger UI, uploads `transactions.csv`, and receives a `job_id` immediately. FastAPI stores the file, creates a pending job, and queues work in Redis. A Celery worker picks up the job, marks it processing, loads the CSV with pandas, validates required columns, cleans the data, removes duplicates, and bulk inserts transactions. It then detects anomalies, classifies missing categories with Gemini, creates a structured summary, stores everything in PostgreSQL, and marks the job completed. The reviewer polls status and retrieves results through Swagger.

## C. Bottlenecks at 100x Traffic

- CSV files are loaded fully in memory with pandas.
- Local upload volume can become an I/O bottleneck.
- Redis queue depth can grow if workers cannot keep up.
- Gemini API latency and rate limits can slow processing.
- PostgreSQL connection pools and write throughput can saturate.
- Polling can create repeated database reads.

## D. Enterprise-Scale Redesign

- Store uploads in S3 or GCS instead of a local shared volume.
- Use Kafka for high-throughput event streaming and replayable processing.
- Deploy API and workers on Kubernetes with autoscaling.
- Split worker pools by task type: cleaning, anomaly detection, Gemini, summary.
- Horizontally scale Celery workers based on queue depth.
- Add PostgreSQL read replicas for read-heavy results traffic.
- Add Redis caching for job status polling.
- Add dead-letter queues, idempotency keys, tracing, and metrics.
