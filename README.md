<div align="center">

# Vecinita

🧭 Visualizing Environmental & Community Information for Neighborhood Advocacy (VECINA / "Vecinita")

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)](#roadmap)
[![RAG](https://img.shields.io/badge/RAG-LangGraph-purple.svg)](RAG_AGENT_README.md)

</div>

Vecinita is a community-focused, retrieval‑augmented assistant supporting Spanish (primary) and English. It uses **LangGraph**, **LangChain**, and a **Supabase** vectorstore to deliver grounded answers sourced from your curated content.

---

## 🆕 LangGraph RAG Agent

The repository includes a **LangGraph-based RAG agent** that can:

- Decide whether to retrieve documents vs. answer directly
- Grade retrieved documents for relevance (binary yes/no)
- Rewrite poorly performing questions automatically
- Generate concise, cited answers (English & Spanish)

### Architecture

```
User Question
  ↓
[Generate Query or Respond] ← model decides direct answer vs retrieval
  ↓                    ↓
[Retrieve Docs]      [Direct Response]
  ↓
[Grade Documents] ← relevance? (yes/no)
  ↓           ↓
[Generate Answer]  [Rewrite Question] → (loops back to retrieval)
```

### Quick Start

```powershell
# (1) Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate   # macOS/Linux

# (2) Install dependencies
pip install -r requirements.txt

# (3) Verify environment & dependencies
python src/setup_check.py

# (4) Run the RAG example (interactive at end)
python -m scripts.example_rag_usage
```

### Documentation

- **[QUICKSTART.md](QUICKSTART.md)** – 3-step intro
- **[RAG_AGENT_README.md](RAG_AGENT_README.md)** – Deep dive & troubleshooting
- **[IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md)** – What was built
- **Workflow Diagram** – See `src/workflow_diagram.py`

### Key Features

✅ Intelligent retrieval decision logic  
✅ Document relevance grading (structured)  
✅ Automatic question rewriting loop  
✅ Multi-language prompts (EN/ES)  
✅ Supabase vectorstore integration  
✅ Works with Groq (free) or OpenAI models  
✅ Modular configuration in `src/agent_config.py`

---

## ⚙️ Prerequisites

- Python **3.10+** (verified with 3.12 as well)
- Supabase project (with `document_chunks` table and RPC `search_similar_documents` function)
- API key for at least one LLM provider:
 	- Groq: `llama-3.1-8b-instant` (default example)
 	- OpenAI: `gpt-4o` (configure in `agent_config.py`)
- (Optional) GPU / optimized BLAS increases embedding/model speed

---

## 🔐 Environment Variables (`.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Your Supabase project URL (starts with https://) |
| `SUPABASE_KEY` | ✅ | Service Role key (store securely, do NOT expose publicly) |
| `OPEN_API_KEY` | ⚠️ | OpenAI key (optional if using Groq) |
| `GROQ_API_KEY` | ⚠️ | Groq key (optional if using OpenAI) |
| `DATABASE_URL` | ⚠️ | Direct Postgres connection for loaders (postgresql://...) |
| `EMBEDDING_MODEL` | Optional | Defaults: `text-embedding-3-small` or local model |
| `USE_LOCAL_EMBEDDINGS` | Optional | `true`/`false` to switch to HuggingFace local embeddings |

> Important: Keys currently committed in `.env` should be **revoked and rotated**. Never commit real production credentials. Add `.env` to version control ignore (already in `.gitignore`).

---

## 🚀 Running Components

### 1. RAG Agent Example

```powershell
python -m scripts.example_rag_usage
```

Shows retrieval vs direct answer, rewriting loop, interactive mode.

### 2. FastAPI Integration

See `scripts/fastapi_integration_example.py` for an example. After adding an endpoint (e.g. `/ask_agent`) to your FastAPI app:

```powershell
uvicorn src.main:app --reload
# Query:
curl "http://localhost:8000/ask_agent?question=Hola"
```

### 3. Setup Check

```powershell
python src/setup_check.py
```

Validates env vars, Supabase connectivity, embedding model.

### 4. Supabase Connection Test

```powershell
python src/utils/supabase_db_test.py
```

### 5. Loading Data

Use the chunk loader after generating a chunk file from scraper:

```powershell
python src/utils/vector_loader.py --file path/to/chunks.txt
```

Scraping flow (customize paths):

1. Prepare URL list: `data/urls.txt`
2. Run scraper: `scraper_to_text.py --input data/urls.txt --output-file data/chunks.txt`
3. Load vectors: run `vector_loader.py`

---

## 🧠 Model Selection

| Provider | Model | Pros | Notes |
|----------|-------|------|-------|
| Groq | `llama-3.1-8b-instant` | Fast, free tier | Good for experimentation |
| OpenAI | `gpt-4o` | Strong reasoning | Paid usage; set `CHAT_MODEL_NAME` |
| Local Embeddings | `all-MiniLM-L6-v2` | No external calls | Must align with indexing |

Configure in `src/agent_config.py`. Use consistent embedding model for both indexing (`vector_loader.py`) and querying.

---

## 🛠 Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: langchain.tools.retriever` | API moved | Updated to `langchain_core.tools` (already applied) |
| Supabase import error (`supabase_auth.http_clients`) | Partial install / old cache | Reinstall: `pip install --upgrade supabase` |
| Corrupted virtualenv / permission errors (Windows) | Locked files | Deactivate, delete `.venv`, recreate: `python -m venv .venv` |
| Missing embeddings dimension mismatch | Wrong model used | Ensure same embedding model for load & query |
| No documents retrieved | Empty/low-quality index | Load chunks via loader & lower `SIMILARITY_THRESHOLD` |
| Long install times (Torch) | Large dependency | Use `pip install --no-cache-dir -r requirements.txt` or pre-built wheels |

Use verbose mode in the agent (`agent.query(q, verbose=True)`) to trace decision-making.

---

## 📁 Project Layout

```
vecinita/
 src/
  rag_agent.py            # Core LangGraph agent
  supabase_retriever.py   # Custom Supabase retriever
  agent_config.py         # Centralized prompts & params
  utils/                  # Scraping, loading, DB tests
 scripts/
  example_rag_usage.py    # End-to-end demonstration
  fastapi_integration_example.py
 docs/                     # Summary, deep dive & quickstart
 requirements.txt          # Runtime dependencies
 pyproject.toml            # Project metadata & extras
```

---

## 🤝 Contributing

1. Fork & branch: `git checkout -b feat/my-change`
2. Create/update tests (if adding logic)
3. Run lint/format (optional extras: `pip install .[dev]`)
4. Submit PR with clear description / screenshots (if UI)

Please avoid committing real credentials or large data dumps. Public examples should be anonymized.

---

## 🗺 Roadmap

- [ ] Expand document grading to multi-label relevance reasoning
- [ ] Add streaming responses endpoint in FastAPI
- [ ] Add batch question evaluation harness
- [ ] Integrate lightweight caching layer for repeated queries
- [ ] Optional vector re-ranking (e.g., ColBERT / LLM-based) layer
- [ ] Interactive web UI (Static Web App / simple React)

---

## 📄 License

MIT – see `LICENSE`.

---

## ✅ Quick Commands (Reference)

```powershell
# Environment setup
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Verify
python src/setup_check.py

# Run agent example
python -m scripts.example_rag_usage

# FastAPI (after integrating endpoint)
uvicorn src.main:app --reload

# Supabase test
python src/utils/supabase_db_test.py

# Load vectors
python src/utils/vector_loader.py --file data/chunks.txt
```

---

## ⚠️ Security Note

Rotate any committed keys immediately. Prefer using environment injection (`Azure / GitHub Actions / local secrets managers`). Never expose service role keys in client-side code.

---

Enjoy building with Vecinita! Reach out via Issues for enhancements or problems.
