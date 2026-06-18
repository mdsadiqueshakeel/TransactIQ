# 3-Minute Demo Video Script

Use Swagger UI as the main interface:

```text
http://localhost:8000/docs
```

## 0:00-0:20 Open Swagger

"This is TransactIQ, an asynchronous AI-powered transaction processing backend. The full system runs with Docker Compose and exposes reviewer-friendly Swagger documentation at localhost port 8000."

Show:

```text
GET /health
POST /jobs/upload
GET /jobs
GET /jobs/{job_id}/status
GET /jobs/{job_id}/results
```

## 0:20-0:45 Upload CSV

"I will upload the provided transactions.csv file. The API validates the file, stores it, creates a pending job, and immediately returns a job_id."

Show:

```text
POST /jobs/upload
```

Copy:

```text
job_id
```

## 0:45-1:05 Show Job Creation

"Now I can list jobs and see the uploaded file, raw row count, clean row count, and current status."

Show:

```text
GET /jobs
```

## 1:05-1:25 Show Worker Logs

"The actual processing happens asynchronously in Celery. The worker loads the CSV, removes duplicates, persists transactions, detects anomalies, calls Gemini, and creates the summary."

Show terminal logs:

```text
CSV loaded
Rows persisted
Anomalies stored
Rows sent to Gemini
Category rows updated
Summary created
```

## 1:25-1:45 Show Database Results

"The cleaned records are stored in PostgreSQL. The original raw count is 95, and exact duplicate removal produces 85 cleaned transactions."

Show:

```text
GET /jobs/{job_id}/status
```

## 1:45-2:05 Show Anomalies

"The system flags anomalies directly on transactions. It supports high amount versus account median and USD transactions at domestic merchants like Swiggy, Ola, and IRCTC."

Show:

```text
GET /jobs/{job_id}/results
anomalies
```

## 2:05-2:25 Show Gemini Categories

"Rows with missing original categories are sent to Gemini in batches. The returned category is validated against the allowed category list and persisted as final_category."

Show:

```text
transactions with original_category=null
final_category updated
llm_failed=false
```

## 2:25-2:40 Show Summary

"The summary combines deterministic aggregates with Gemini narrative output. The backend computes spend totals, top merchants, category breakdown, and anomaly count locally, then asks Gemini only for the narrative and risk level."

Show:

```text
summary.narrative
summary.risk_level
```

## 2:40-3:00 Explain Architecture

"Architecturally, FastAPI owns the API layer, Redis queues work, Celery processes asynchronously, PostgreSQL stores durable results, and Gemini provides AI enrichment. At scale, uploads would move to S3, events to Kafka, API and workers to Kubernetes, workers would scale horizontally, and PostgreSQL read replicas would support heavy results traffic."
