# Document Chunking & Upload Pipeline

## Overview

The VECINA scraper now has a complete document processing pipeline that:
1. **Loads** raw documents from URLs
2. **Chunks** large documents into semantic pieces  
3. **Uploads** chunks to Supabase with embeddings
4. **Tracks** metadata and sources for attribution

## Architecture

### 1. Document Loading ([src/scraper/loaders.py](src/scraper/loaders.py))
- SmartLoader routes URLs to appropriate loaders
- Handles Playwright, Recursive, Standard (Unstructured), and CSV loaders
- Returns raw LangChain Document objects

### 2. Document Processing ([src/scraper/processors.py](src/scraper/processors.py))
- **DocumentProcessor** cleans and chunks documents
- Cleaning steps:
  - HTML/XML extraction with BeautifulSoup
  - Text cleanup (whitespace, special chars)
- Chunking:
  - RecursiveCharacterTextSplitter with semantic separators
  - Default: 1000 char chunks, 200 char overlap
  - Preserves semantic meaning across chunks

### 3. Database Upload ([src/scraper/uploader.py](src/scraper/uploader.py))
- **DatabaseUploader** manages Supabase connections
- Embeddings:
  - Local: `sentence-transformers/all-MiniLM-L6-v2` (384 dims)
  - Optional: OpenAI embeddings (3072 dims)
- Upload process:
  - Batch processing (50 chunks/batch by default)
  - Individual retry fallback for failed batches
  - Full metadata preservation (source, loader_type, timestamp)

### 4. Scraper Orchestration ([src/scraper/scraper.py](src/scraper/scraper.py))
- **VecinaScraper** coordinates the full pipeline
- Modes:
  - **File Mode**: Chunks written to `data/new_content_chunks.txt` for later batch upload
  - **Streaming Mode**: Chunks uploaded immediately to database during scraping
- Tracks statistics: URLs, chunks, uploads, failures

## Usage

### File-Based Pipeline (Default)
```bash
# Scrape and save chunks to file
uv run python -m src.scraper.cli --debug

# Later: load chunks into database
uv run python src/agent/utils/vector_loader.py data/new_content_chunks.txt
```

### Streaming Pipeline (Real-Time Upload)
```bash
# Scrape with immediate database uploads
uv run python -m src.scraper.cli --stream

# Chunks uploaded immediately - no file staging needed
# Much faster for continuous ingestion
```

### Combined Pipeline
```bash
# Clean database + stream scrape + no local files
uv run python -m src.scraper.cli --clean --stream --debug
```

## Data Flow

```
URL List
  ↓
Load (SmartLoader)
  ├─ Playwright (JS-heavy sites, 10-12s wait)
  ├─ Recursive (crawlers)
  └─ Standard (Unstructured)
  ↓
Process (DocumentProcessor)
  ├─ Clean (HTML extraction, text normalization)
  ├─ Chunk (RecursiveCharacterTextSplitter)
  └─ Extract Metadata
  ↓
Upload (DatabaseUploader)
  ├─ Generate Embeddings (local or OpenAI)
  └─ Batch Insert to Supabase
  ↓
Database + Statistics
```

## Database Schema (Supabase)

Expected `documents` table columns:
- `id` (uuid, pk)
- `content` (text) - chunk text
- `source_url` (text) - original URL
- `chunk_index` (integer) - order within document
- `total_chunks` (integer) - total chunks from source
- `loader_type` (text) - loader used (Playwright, etc)
- `embedding` (vector, 384 dims for local)
- `metadata` (jsonb) - additional data
- `scraped_at` (timestamp)
- `created_at` (timestamp, default now)

## Configuration

### Chunking ([src/scraper/config.py](src/scraper/config.py))
```python
CHUNK_SIZE = 1000          # Characters per chunk
CHUNK_OVERLAP = 200        # Overlapping characters between chunks
RATE_LIMIT_DELAY = 2       # Seconds between requests
```

### Embeddings ([src/scraper/uploader.py](src/scraper/uploader.py))
```python
LOCAL_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# 384-dimensional embeddings, fast on CPU
```

## Error Handling

- **Load failures**: Logged, retried with Playwright in next pass
- **Chunk failures**: Individual chunk retry if batch fails
- **Upload failures**: Logged with source URL for manual intervention
- **Streaming mode unavailable**: Gracefully falls back to file mode

## Performance

- Local embeddings: ~500 chunks/min on modern CPU
- Batch uploads: 50 chunks per request (configurable)
- Memory efficient: Streaming uploads chunks immediately
- Rate limiting: 2s between requests prevents IP blocking

## Monitoring

Check statistics in scraper summary:
```
Total chunks generated: 1,250
Chunks uploaded to database: 1,245
Failed uploads: 5
```

Each chunk preserves source attribution for RAG queries.
