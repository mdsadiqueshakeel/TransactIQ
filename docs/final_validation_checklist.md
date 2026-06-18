# Final Validation Checklist

1. Start stack.

```bash
docker compose up --build
```

Confirm Gemini config is loaded:

```bash
docker compose exec worker env | grep GEMINI_API_KEY
docker compose logs worker | grep "Gemini SDK initialized"
```

2. Verify health.

```bash
curl http://localhost:8000/health
```

3. Upload CSV.

```bash
curl -X POST http://localhost:8000/jobs/upload -F "file=@transactions.csv"
```

4. Verify job completion.

```bash
curl http://localhost:8000/jobs
curl http://localhost:8000/jobs/{job_id}/status
```

Expected:

```text
status=completed
row_count_raw=95
row_count_clean=85
```

5. Verify anomalies.

```bash
curl http://localhost:8000/jobs/{job_id}/results
```

Expected:

```text
anomalies array is not empty
transactions with anomalies have is_anomaly=true
anomaly_reason is HIGH_AMOUNT_ACCOUNT_MEDIAN or USD_DOMESTIC_MERCHANT
```

6. Verify Gemini categories.

Expected:

```text
rows with original_category=null have final_category set to an allowed category
llm_failed=false when Gemini succeeds
```

Allowed categories:

```text
Food, Shopping, Travel, Transport, Utilities, Cash Withdrawal, Entertainment, Other
```

7. Verify summary.

Expected:

```text
summary exists
summary.narrative is generated
summary.risk_level is low, medium, or high
category_breakdown exists
top_merchants exists
```

8. Verify results endpoint.

Expected response shape:

```json
{
  "job": {},
  "summary": {},
  "anomalies": [],
  "category_breakdown": {},
  "transactions": []
}
```
