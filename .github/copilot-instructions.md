# Vecinita Copilot Instructions

Vecinita is a **RAG (Retrieval-Augmented Generation) Q&A Assistant** using LangChain, LangGraph, and Supabase. It scrapes web content, stores embeddings in a vector database, and answers user questions with source attribution.

## Architecture Overview

### Data Flow
1. **Web Scraping** ([backend/src/scraper/](backend/src/scraper/)): Downloads content from configured URLs using multiple loaders (PyPDF, Unstructured, Playwright for JS-heavy sites)
2. **Vector Storage** ([backend/src/utils/](backend/src/utils/)): Chunks content, generates embeddings (HuggingFace local), stores in Supabase with source attribution
3. **Q&A Engine** ([backend/src/agent/main.py](backend/src/agent/main.py)): FastAPI app detects query language, retrieves similar docs via vector search, prompts LLM with source context, returns answers with citations

### Key Components
- **FastAPI Server** ([backend/src/agent/main.py](backend/src/agent/main.py)): Main endpoints—`GET /config`, `GET /ask`, `GET /ask-stream` (streaming Q&A)
- **Agent Tools** ([backend/src/agent/tools/](backend/src/agent/tools/)):
  - `db_search_tool` - Vector similarity search on Supabase documents
  - `static_response_tool` - Bilingual FAQ lookup (EN/ES)
  - `web_search_tool` - Tavily API + DuckDuckGo fallback
- **Embedding Service** ([backend/src/embedding_service/](backend/src/embedding_service/)): Separate FastAPI service on port 8001
- **Frontend** ([frontend/src/](frontend/src/)): React + Vite UI with Tailwind CSS
- **Supabase PostgreSQL**: Stores document chunks with embeddings; RPC function `search_similar_documents` performs vector similarity search
- **LLM**: Groq's Llama 3.1 8B (configured via `GROQ_API_KEY`)

## Data Pipeline & Configuration

### Orchestration Script
[backend/scripts/data_scrape_load.sh](backend/scripts/data_scrape_load.sh) automates the full pipeline:
- Accepts `--clean` flag to truncate database (additive mode is default)
- Runs scraper in two passes: standard loaders first, then Playwright for failures
- Loads chunks into Supabase with deduplication via `unique_content_source` constraint
- Restarts Docker container on completion

### Configuration Files (data/config/)
- **recursive_sites.txt**: Format `<url> <depth>` for crawling (e.g., `https://example.com 2`)
- **playwright_sites.txt**: Domains requiring Playwright (JS-heavy content)
- **skip_sites.txt**: Domains to skip entirely

### URL Input
[data/urls.txt](data/urls.txt): List of URLs to scrape (one per line, ignoring comments starting with `#`)

## Development Workflows

### UV Package Manager
This project uses **uv** for fast, reliable dependency management and script execution. Install it first:
```bash
# Install UV (https://docs.astral.sh/uv/getting-started/)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Local Development (Recommended)

**Backend** (FastAPI + LangGraph Agent):
```bash
cd backend
uv sync
uv run -m uvicorn src.agent.main:app --reload
```
Runs on `http://localhost:8000` with auto-reload on code changes.

**Frontend** (React + Vite):
```bash
cd frontend
npm install
npm run dev
```
Runs on `http://localhost:5173` (or next available port) with HMR.

### Full System Testing (Docker Compose)

For complete end-to-end testing with all services (database, embedding service, etc.):
```bash
docker-compose up --build      # Run with services
docker-compose up -d           # Background
docker-compose down            # Stop & remove containers
```

**Use Docker Compose for:**
- Testing complete data pipeline (scraper → database → search)
- Verifying multi-service integration
- Pre-production environment testing
- CI/CD pipeline validation

**Use local development (`uv`/`npm`) for:**
- Feature development with fast feedback loops
- Debugging specific tools or components
- Unit and integration tests
- Quick iterations on frontend UI

### Testing

**For local development tests** (fast, mocked services):
```bash
cd backend
uv run pytest                    # Run all 108 backend tests
uv run pytest -v                 # Verbose output
uv run pytest --cov              # With coverage report
uv run pytest tests/test_agent_langgraph.py -v  # Specific test file
```

**For frontend tests**:
```bash
cd frontend
npm run test                     # Unit tests (Vitest)
npm run test:coverage            # Coverage report
npm run test:e2e                 # E2E tests (requires backend running)
```

**For full integration tests** (requires Docker Compose + real services):
```bash
docker-compose up
cd backend
uv run pytest -m integration     # Tests marked with @pytest.mark.integration
```

**General test commands**:
```bash
# Recommended: Use uv to run tests with isolated dependencies
uv run pytest

# Run specific test file
uv run pytest tests/test_main.py

# Run with coverage
uv run pytest --cov

# Run marked tests (unit, integration, db, api, ui)
uv run pytest -m unit

# Install Playwright browsers (required for UI tests)
uv run playwright install
```

Fixtures in [tests/conftest.py](tests/conftest.py) provide mocked Supabase, embedding models, and LLM clients. See [tests/README.md](tests/README.md) for full test strategy.

## Language-Aware Prompting

The `/ask` endpoint uses `langdetect` to detect query language and selects the appropriate prompt template:
- **Spanish** (es): System prompt in Spanish with Spanish instructions
- **English** (default): System prompt in English

Both enforce:
1. Answer only from provided context
2. Cite sources with `(Fuente: URL)` or `(Source: URL)`
3. Return fallback message if no relevant docs found

See [src/main.py](src/main.py) lines 102–138 for prompt templates.

## Key Patterns & Conventions

### Dependency Pinning (pyproject.toml)
- **onnxruntime & tokenizers**: Windows-specific versions (dev/RC releases lack wheels)
- **sentence-transformers & fastembed**: Pinned to avoid NumPy 2.x conflicts
- **LangSmith ≥0.4.56**: Compatible with NumPy 2.x for tracing

### Scraper Design
- **Rate limiting**: 2-second delays between requests (RATE_LIMIT_DELAY in [backend/src/scraper/scraper.py](backend/src/scraper/scraper.py))
- **Loader selection**: Standard (Unstructured) first, fallback to Playwright for JS-heavy sites
- **Chunking**: RecursiveCharacterTextSplitter with configurable size (default 1000 chars, 200 overlap)
- **Failure recovery**: Failed URLs logged and re-run with Playwright in second pass
- **Configuration**: Managed in [data/config/](data/config/) (recursive_sites.txt, playwright_sites.txt, skip_sites.txt)

### Database Constraints
- **unique_content_source**: Prevents duplicate content; enables safe re-scraping
- **Vector search RPC**: `search_similar_documents(query_embedding, match_threshold, match_count)`—default threshold 0.3, return top 5

### Static File Mounting
FastAPI mounts `src/static/` directory; ensure `index.html` and `favicon.ico` exist for `/` and `/favicon.ico` endpoints.

## Environment Variables

Required in `.env`:
```
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=<anon-or-service-key>
GROQ_API_KEY=<your-groq-api-key>
```

Optional: `DATABASE_URL` (for direct PostgreSQL operations)

## Error Handling & Debugging

- **Missing UI**: Check static path in error message; ensure `src/static/index.html` exists
- **Embedding failures**: Verify HuggingFace model download; model auto-caches on first use
- **Vector search failures**: Check Supabase RPC function exists and embedding dimensions match (384 for all-MiniLM-L6-v2)
- **Scraper timeouts**: Increase RATE_LIMIT_DELAY or configure Playwright in config
- **Duplicate detection**: Database constraint `unique_content_source` silently rejects duplicates; check logs for details

## Testing Guidance

- **Unit tests** (fast): Test utility functions without external services
- **Integration tests**: Mock Supabase; test vector search logic
- **DB tests** (skipped in CI): Require real Supabase credentials
- **UI tests** (Playwright): Require running FastAPI server; mark with `@pytest.mark.ui`

Use `env_vars` fixture to inject test credentials; mock `supabase_client`, `embedding_model`, `llm` for isolated testing.

## Temporary Documentation

Reference and implementation guides are organized in the [tmp/](../tmp/) folder:

- **[tmp/QUICKSTART.md](../tmp/QUICKSTART.md)** - Quick start guide for local development
- **[tmp/IMPLEMENTATION_STATUS.md](../tmp/IMPLEMENTATION_STATUS.md)** - Current implementation status and phase completion
- **[tmp/IMPLEMENTATION_COMPLETE.md](../tmp/IMPLEMENTATION_COMPLETE.md)** - Phase 1-2 completion summary
- **[tmp/FRONTEND_FETCH_FIX.md](../tmp/FRONTEND_FETCH_FIX.md)** - Frontend API connectivity fix details
- **[tmp/GCP_DEPLOYMENT_QUICK_START.md](../tmp/GCP_DEPLOYMENT_QUICK_START.md)** - Quick GCP deployment 5-step guide
- **[tmp/MIGRATION_MODAL_TO_CLOUD_RUN.md](../tmp/MIGRATION_MODAL_TO_CLOUD_RUN.md)** - Migration guide from Modal to Cloud Run

For production deployment details, see [docs/GCP_CLOUD_RUN_DEPLOYMENT.md](../docs/GCP_CLOUD_RUN_DEPLOYMENT.md).
