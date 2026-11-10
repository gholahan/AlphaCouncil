# AlphaCouncil PDF Ingestion Pipeline Plan

## Architecture Overview: URL → PDF → Chunks → Embeddings → pgvector

```
API Endpoint (POST /api/v1/documents/ingest)
    ↓
[1] Download & Validate PDF from URL
    ↓
[2] Extract Text with pdfplumber (PDFExtractorAdapter)
    ↓
[3] Chunk Text (ChunkingService - semantic chunking)
    ↓
[4] Generate Embeddings (Voyage AI - voyage-finance-2)
    ↓
[5] Store in pgvector with metadata (PgVectorStore)
    ↓
[6] Update Company.last_ingestion_date
    ↓
Return: {doc_id, chunks_count, status}
```

---

## Current State (What's Already Built)

### ✅ Database Models ([models.py](backend/src/adapters/storage/models.py))

**CompanyRecord** (line 9-21):
- `ticker`, `name`, `sector`, `ir_page_url`
- `last_ingestion_date` - tracks when PDFs were last processed
- `is_preloaded` - marks top 5 NGX stocks

**FinancialChunkRecord** (line 23-50):
- `ticker`, `company_id`, `filing_type`, `fiscal_year`, `quarter`, `section`
- `chunk_text` - the actual text content
- `embedding` - Vector(384) for pgvector similarity search
- `metadata_json` - flexible JSON field for extra metadata
- **Note: Vector dimension is 384** (for sentence-transformers), but we're using Voyage AI (1024 or 1536 dims)

**DebateTraceRecord** (line 52-71):
- Stores full debate transcripts and verdicts

---

### ✅ Adapters Already Built

**PDFExtractorAdapter** ([pdf_extractor.py](backend/src/adapters/ingestion/pdf_extractor.py)):
- ✅ `extract_text(pdf_path)` - full text extraction
- ✅ `extract_pages(pdf_path)` - page-by-page with tables
- ✅ `extract_tables(pdf_path, page_number)` - structured table data
- ✅ `get_metadata(pdf_path)` - author, title, page_count

**PgVectorStore** ([vector_store.py](backend/src/adapters/storage/vector_store.py)):
- ✅ `upsert(doc_id, text, embedding, metadata)` - insert/update chunks
- ✅ `query(embedding, ticker, top_k=5)` - cosine similarity search
- Uses pgvector's `.cosine_distance()` for retrieval

**Repositories**:
- ✅ `SqlAlchemyCompanyRepository` - track companies and ingestion dates
- ✅ `SqlAlchemyDocumentRepository` - stub for document tracking

---

### ❌ What's Missing

1. **ChunkingService** ([chunking.py](backend/src/domain/services/chunking.py)) - **EMPTY FILE**
2. **Voyage AI Embedding Adapter** - needs implementation for `voyage-finance-2` model
3. **PDF Download Utility** - fetch PDF from URL, validate, save temporarily
4. **Ingestion Use Case** - orchestrate the full pipeline
5. **Celery Task** - async background processing
6. **API Endpoint** - POST `/api/v1/documents/ingest`

---

## Implementation Plan

### Phase 1: Core Pipeline (2-3 hours)

#### Step 1.1: Fix Vector Dimension Mismatch
**Issue**: `FinancialChunkRecord.embedding` is `Vector(384)` but Voyage AI finance model outputs 1024 dims.

**Action**:
```python
# models.py line 44
embedding: list[float] = Field(
    sa_column=Column(Vector(1024))  # voyage-finance-2 dimension
)
```

Create Alembic migration:
```bash
alembic revision --autogenerate -m "Update embedding dimension to 1024 for Voyage AI"
alembic upgrade head
```

---

#### Step 1.2: Build ChunkingService ([chunking.py](backend/src/domain/services/chunking.py))

**Strategy**: Semantic chunking for financial documents

```python
class ChunkingService:
    def chunk_financial_document(
        self,
        text: str,
        doc_type: str,  # "annual_report", "quarterly", "news"
        max_chunk_size: int = 512,
        overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Chunk financial document with metadata preservation.
        
        Returns:
            [
                {
                    "chunk_text": "...",
                    "chunk_index": 0,
                    "section": "Management Discussion & Analysis",
                    "char_start": 0,
                    "char_end": 512
                },
                ...
            ]
        """
```

**Chunking Logic**:
- Detect sections via headers (MD&A, Balance Sheet, Income Statement, Notes)
- Split on sentence boundaries (not mid-sentence)
- Preserve context with 50-token overlap
- Max 512 tokens per chunk (Voyage AI limit)

---

#### Step 1.3: Implement Voyage AI Embedding Adapter

**File**: `backend/src/adapters/embeddings/voyage_ai.py`

```python
class VoyageAIEmbeddingAdapter(EmbeddingService):
    def __init__(self, api_key: str):
        self.client = voyageai.Client(api_key=api_key)
        self.model = "voyage-finance-2"  # 1024 dimensions
    
    async def embed_text(self, text: str) -> List[float]:
        result = self.client.embed([text], model=self.model)
        return result.embeddings[0]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        result = self.client.embed(texts, model=self.model)
        return result.embeddings
```

---

#### Step 1.4: PDF Download Utility

**File**: `backend/src/adapters/ingestion/pdf_downloader.py`

```python
class PDFDownloader:
    async def download_pdf(self, url: str, save_dir: str) -> str:
        """
        Download PDF from URL, validate, return local path.
        
        Args:
            url: PDF URL (company IR page, SEC filing link, etc.)
            save_dir: Temporary directory to save PDF
        
        Returns:
            str: Local file path to downloaded PDF
        
        Raises:
            ValueError: If URL is invalid or not a PDF
            HTTPError: If download fails
        """
        # 1. Validate URL
        # 2. Download with requests/httpx
        # 3. Validate PDF header (magic bytes: %PDF)
        # 4. Save to temp directory
        # 5. Return path
```

---

#### Step 1.5: Ingestion Use Case

**File**: `backend/src/application/use_cases/ingest_company.py`

```python
class IngestCompanyDocumentUseCase:
    def __init__(
        self,
        pdf_downloader: PDFDownloader,
        pdf_extractor: PDFExtractor,
        chunking_service: ChunkingService,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        company_repo: CompanyRepository,
    ):
        ...
    
    async def execute(
        self,
        ticker: str,
        pdf_url: str,
        filing_type: str,
        fiscal_year: int,
        quarter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full ingestion pipeline.
        
        Steps:
        1. Download PDF from URL
        2. Extract text with pdfplumber
        3. Chunk text semantically
        4. Batch embed chunks with Voyage AI
        5. Upsert to pgvector with metadata
        6. Update company.last_ingestion_date
        
        Returns:
            {
                "doc_id": str,
                "chunks_stored": int,
                "embedding_dimensions": int,
                "processing_time_seconds": float
            }
        """
```

---

### Phase 2: API & Background Tasks (1-2 hours)

#### Step 2.1: Celery Task

**File**: `backend/src/adapters/celery/tasks.py`

```python
from src.adapters.celery.app import celery_app

@celery_app.task(bind=True, name="ingest_pdf_document")
def ingest_pdf_document(
    self,
    ticker: str,
    pdf_url: str,
    filing_type: str,
    fiscal_year: int,
    quarter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Background task for PDF ingestion.
    
    Returns task result with doc_id and chunks_stored.
    """
    # Initialize dependencies
    # Call IngestCompanyDocumentUseCase.execute()
    # Return result
```

---

#### Step 2.2: API Endpoint

**File**: `backend/src/entrypoints/api/v1/endpoints/documents.py`

```python
@router.post("/ingest")
async def ingest_document(
    ticker: str,
    pdf_url: str,
    filing_type: str,
    fiscal_year: int,
    quarter: Optional[str] = None,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Ingest PDF document for RAG retrieval.
    
    Request body:
    {
        "ticker": "DANGCEM",
        "pdf_url": "https://example.com/annual_report_2025.pdf",
        "filing_type": "annual_report",
        "fiscal_year": 2025,
        "quarter": null
    }
    
    Returns:
    {
        "task_id": "celery-task-uuid",
        "status": "queued",
        "message": "PDF ingestion started in background"
    }
    """
    task = ingest_pdf_document.delay(ticker, pdf_url, filing_type, fiscal_year, quarter)
    return {
        "task_id": task.id,
        "status": "queued",
        "message": f"PDF ingestion started for {ticker}"
    }

@router.get("/ingest/status/{task_id}")
async def get_ingestion_status(task_id: str):
    """Check ingestion task status."""
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.state,
        "result": task.result if task.ready() else None
    }
```

---

### Phase 3: Testing & Validation (1 hour)

#### End-to-End Test

```python
# Test flow:
# 1. POST /api/v1/documents/ingest with Dangote Cement annual report URL
# 2. Wait for Celery task completion
# 3. Query pgvector with test embedding
# 4. Verify chunks are retrieved with correct metadata
```

---

## Data Flow Example

### Input:
```json
POST /api/v1/documents/ingest
{
  "ticker": "DANGCEM",
  "pdf_url": "https://dangotecement.com/wp-content/uploads/2025/04/annual-report-2024.pdf",
  "filing_type": "annual_report",
  "fiscal_year": 2024
}
```

### Processing:
1. **Download**: PDF saved to `/tmp/dangcem_2024_annual.pdf`
2. **Extract**: 120 pages → 150,000 characters of text
3. **Chunk**: 150,000 chars → 285 chunks (512 tokens each, 50 overlap)
4. **Embed**: 285 chunks → 285 x 1024-dim vectors (Voyage AI batch API)
5. **Store**: 285 `FinancialChunkRecord` rows inserted into Supabase pgvector

### Database State:
```sql
SELECT COUNT(*) FROM financial_chunks WHERE ticker = 'DANGCEM' AND fiscal_year = 2024;
-- Result: 285

SELECT chunk_text, section, chunk_index 
FROM financial_chunks 
WHERE ticker = 'DANGCEM' 
ORDER BY embedding <=> '[query_embedding_vector]' 
LIMIT 5;
-- Returns top 5 semantically similar chunks
```

---

## Next Steps

1. **Fix vector dimension** (384 → 1024)
2. **Build ChunkingService** (semantic chunking with section detection)
3. **Implement Voyage AI adapter** (voyage-finance-2 embeddings)
4. **Create PDF downloader utility**
5. **Wire up IngestCompanyDocumentUseCase**
6. **Add Celery task + API endpoint**
7. **Test end-to-end with real NGX company PDF**

---

## Questions to Resolve

1. **Vector dimension**: Confirm Voyage AI `voyage-finance-2` outputs 1024 dims (or 1536)?
2. **Chunking strategy**: Should we detect sections via regex or use fixed-size chunking?
3. **Metadata fields**: What additional metadata should we store in `metadata_json`?
4. **Rate limits**: Voyage AI batch embedding limits per request?
5. **Error handling**: Retry logic for failed embeddings or PDF downloads?

Would you like me to start implementing Phase 1 (ChunkingService, Voyage AI adapter, vector dimension fix)?
