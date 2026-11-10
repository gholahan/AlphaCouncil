"""
AlphaCouncil - PDF Ingestion API Documentation
==============================================

Base URL: http://localhost:8000
API Version: v1

## Endpoints

### 1. Ingest Document (Async)
POST /api/v1/documents/ingest

Start background ingestion of a company financial document.

**Request Body:**
```json
{
  "ticker": "DANGCEM",
  "pdf_url": "https://example.com/annual_report_2024.pdf",
  "filing_type": "annual_report",
  "fiscal_year": 2024,
  "quarter": null
}
```

**Parameters:**
- `ticker` (string, required): Company ticker symbol (e.g., "DANGCEM")
- `pdf_url` (string, required): URL to download PDF from
- `filing_type` (string, required): One of: "annual_report", "quarterly", "news"
- `fiscal_year` (integer, required): Fiscal year (2000-2050)
- `quarter` (string, optional): "Q1", "Q2", "Q3", or "Q4" (required for quarterly reports)

**Response (202 Accepted):**
```json
{
  "task_id": "abc123-def456-ghi789",
  "ticker": "DANGCEM",
  "filing_type": "annual_report",
  "fiscal_year": 2024,
  "quarter": null,
  "status": "PENDING",
  "message": "Document ingestion started for DANGCEM - annual_report FY2024"
}
```

---

### 2. Check Task Status
GET /api/v1/documents/ingest/status/{task_id}

Check the status of a document ingestion task.

**Path Parameters:**
- `task_id` (string, required): Task ID from ingestion request

**Response (200 OK):**

**Pending/Running:**
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "PENDING"
}
```

**Success:**
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "SUCCESS",
  "result": {
    "ticker": "DANGCEM",
    "filing_type": "annual_report",
    "fiscal_year": 2024,
    "quarter": null,
    "chunks_stored": 285,
    "embedding_dimensions": 1024,
    "pdf_name": "DANGCEM_2024_abc123.pdf",
    "page_count": 120,
    "processing_time_seconds": 45.2
  }
}
```

**Failure:**
```json
{
  "task_id": "abc123-def456-ghi789",
  "status": "FAILURE",
  "error": "Failed to download PDF: Connection timeout"
}
```

**Status Values:**
- `PENDING`: Task is waiting to start
- `STARTED`: Task is currently running
- `SUCCESS`: Task completed successfully
- `FAILURE`: Task failed with error
- `RETRY`: Task is being retried after failure

---

### 3. Health Check
GET /health

Check if the API is running.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "app": "AlphaCouncil",
  "environment": "development"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid filing_type. Must be one of: ['annual_report', 'quarterly', 'news']"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to start ingestion task: Database connection error"
}
```

---

## Example Usage

### Using curl:

```bash
# Start ingestion
curl -X POST http://localhost:8000/api/v1/documents/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "DANGCEM",
    "pdf_url": "https://example.com/report.pdf",
    "filing_type": "annual_report",
    "fiscal_year": 2024
  }'

# Response: {"task_id": "abc123...", ...}

# Check status
curl http://localhost:8000/api/v1/documents/ingest/status/abc123...
```

### Using Python requests:

```python
import requests
import time

# Start ingestion
response = requests.post(
    "http://localhost:8000/api/v1/documents/ingest",
    json={
        "ticker": "DANGCEM",
        "pdf_url": "https://example.com/report.pdf",
        "filing_type": "annual_report",
        "fiscal_year": 2024
    }
)
task_id = response.json()["task_id"]

# Poll for completion
while True:
    status = requests.get(
        f"http://localhost:8000/api/v1/documents/ingest/status/{task_id}"
    ).json()
    
    if status["status"] in ["SUCCESS", "FAILURE"]:
        print(status)
        break
    
    time.sleep(5)
```

---

## Pipeline Details

When you call POST /api/v1/documents/ingest, the following happens:

1. **Validation**: Request is validated (ticker, filing_type, fiscal_year)
2. **Task Creation**: Celery background task is started
3. **Immediate Response**: 202 Accepted with task_id

The background task then executes:

1. **Download PDF**: Fetch from URL, validate PDF magic bytes
2. **Extract Metadata**: Get page count, author, title
3. **Extract Text**: Page-by-page text extraction with pdfplumber
4. **Chunk Text**: LangChain RecursiveCharacterTextSplitter (2000 chars, 200 overlap)
5. **Map Pages**: Track which pages each chunk spans
6. **Generate Embeddings**: Voyage AI voyage-finance-2 (1024 dimensions)
7. **Store in pgvector**: Save chunks with embeddings and metadata
8. **Update Company**: Set last_ingestion_date
9. **Cleanup**: Delete temporary PDF file

**Metadata stored per chunk:**
- `page_number`: Starting page number
- `page_range`: e.g., "5-7" for multi-page chunks
- `pdf_name`: Original PDF filename
- `ticker`, `filing_type`, `fiscal_year`, `quarter`
- `char_start`, `char_end`: Position in document

---

## Running the API

### 1. Start Redis (Celery broker)
```bash
# Aiven Redis is configured in .env
# No local Redis needed if using Aiven
```

### 2. Start Celery Worker
```bash
cd backend
celery -A src.adapters.celery.app worker --loglevel=info
```

### 3. Start FastAPI Server
```bash
cd backend
python run.py
# Or with hot reload:
python run.py --reload
```

### 4. Access API
- API: http://localhost:8000
- Docs: http://localhost:8000/docs (Swagger UI)
- ReDoc: http://localhost:8000/redoc

---

## Environment Variables Required

```bash
# Database
DATABASE_URL=postgresql://user:pass@db.supabase.co:5432/postgres

# Redis/Celery
REDIS_URL=rediss://default:pass@redis.aivencloud.com:12345
CELERY_BROKER_URL=rediss://default:pass@redis.aivencloud.com:12345  # Optional, falls back to REDIS_URL
CELERY_RESULT_BACKEND=rediss://default:pass@redis.aivencloud.com:12345  # Optional, falls back to REDIS_URL

# AI Services
VOYAGE_API_KEY=your_voyage_api_key
GROQ_API_KEY=your_groq_key  # For MAD system
TAVILY_API_KEY=your_tavily_key  # For web search tools

# App Config
APP_NAME=AlphaCouncil
ENVIRONMENT=development
```

---

## Next Steps

1. ✅ Run Alembic migration to create database tables
2. ✅ Test with real Nigerian stock PDF
3. ✅ Build RAG retrieval endpoint (POST /api/v1/analysis/query)
4. ✅ Wire up MAD debate system with ingested chunks
