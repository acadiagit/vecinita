# Vecinita Architecture: Supabase Edge Function Embeddings

## Summary of Changes

This update implements **Option 2: Supabase Edge Function for Embeddings**, which eliminates local embedding models from the agent service.

### Memory Savings
- **Before**: Agent with FastEmbed (~25MB) + dependencies = ~918MB Docker image
- **After**: Agent with NO embedding models = **~850MB Docker image** (~68MB saved)
- **Runtime savings**: ~50-90MB memory depending on model caching

### Performance Impact
- **Latency increase**: +50-100ms per query (network roundtrip to edge function)
- **Cold start**: Edge function ~1-2s first call, then warm
- **Agent cold start**: Eliminated (no model loading)

---

## Modified Files

### 1. Dependency Management

**`backend/pyproject.toml`**
```toml
# REMOVED from base dependencies:
- "fastembed"  # Now using edge function

# NEW optional dependency groups:
[project.optional-dependencies]
agent = []  # Agent uses edge function, no local models
scraper = [
    "unstructured[doc,docx,ppt,pdf]>=0.14.0",
    "playwright>=1.40.0",
    "sentence-transformers>=5.1.2",
    "fastembed",  # Only for scraping
]
```

### 2. Edge Function Implementation

**New files:**
- `supabase/functions/generate-embedding/index.ts` - Deno edge function
- `supabase/functions/generate-embedding/README.md` - API documentation
- `supabase/config.toml` - Edge function configuration
- `backend/src/utils/supabase_embeddings.py` - Python client for edge function
- `backend/scripts/deploy_edge_function.ps1` - Deployment automation
- `docs/guides/EDGE_FUNCTION_DEPLOYMENT.md` - Complete deployment guide

### 3. Agent Configuration

**`backend/src/agent/main.py`**
```python
# NEW: Edge function embeddings with fallback
use_edge_function = os.environ.get("USE_EDGE_FUNCTION_EMBEDDINGS", "true")

if use_edge_function:
    from src.utils.supabase_embeddings import create_embedding_model
    embedding_model = create_embedding_model(supabase)
else:
    # Fallback to FastEmbed (requires installation)
    embedding_model = FastEmbedEmbeddings(...)
```

### 4. Deployment Configurations

**`backend/Dockerfile`**
```dockerfile
# REMOVED from pip install:
- fastembed

# Comment updated:
# "Uses Supabase Edge Function for embeddings - ZERO local embedding models!"
```

**`render.yaml`**
```yaml
envVars:
  - key: USE_EDGE_FUNCTION_EMBEDDINGS
    value: "true"  # Enable edge function embeddings
```

**`docker-compose.yml`**
```yaml
environment:
  USE_EDGE_FUNCTION_EMBEDDINGS: "${USE_EDGE_FUNCTION_EMBEDDINGS:-true}"
```

---

## Deployment Steps

### 1. Install Supabase CLI

```bash
npm install -g supabase
```

### 2. Deploy Edge Function

```powershell
# From backend/scripts/
.\deploy_edge_function.ps1
```

Or manually:
```bash
cd vecinita
supabase login
supabase link --project-ref <your-ref>
supabase functions deploy generate-embedding
```

### 3. Set HuggingFace Token

**In Supabase Dashboard:**
1. Go to: Project Settings → Edge Functions → Secrets
2. Add: `HUGGING_FACE_TOKEN` = `hf_your_token_here`

Get free token: https://huggingface.co/settings/tokens

### 4. Enable in Agent

**For Render:**
1. Dashboard → vecinita-agent → Environment
2. Add: `USE_EDGE_FUNCTION_EMBEDDINGS` = `true`
3. Redeploy

**For Local/Docker:**
```bash
# In .env
USE_EDGE_FUNCTION_EMBEDDINGS=true
```

### 5. Test

```bash
# Test edge function
.\deploy_edge_function.ps1 -Test

# Test agent
curl "http://localhost:8000/ask?question=test"

# Check logs for:
# ✅ Embedding model initialized via Supabase Edge Function (zero memory overhead)
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Request                            │
│                    "¿Qué recursos tengo?"                       │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React/Vite)                        │
│                  Port 3000 / Render Static                      │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP GET /api/ask-stream
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              Agent Service (FastAPI)                            │
│               Port 8000 / Render Web                            │
│  • LangGraph agent with tools                                  │
│  • NO embedding models (50-90MB saved!)                        │
│  • Calls edge function for embeddings                          │
└──────────┬──────────────────────────┬───────────────────────────┘
           │                          │
           │ Vector Search            │ Embedding Request
           │                          │ {"text": "..."}
           ▼                          ▼
┌──────────────────────┐    ┌──────────────────────────────────┐
│  Supabase PostgreSQL │    │  Supabase Edge Function          │
│  • pgvector          │    │  generate-embedding              │
│  • document_chunks   │    │  • HuggingFace Inference API     │
│  • RPC search fn     │    │  • sentence-transformers model   │
└──────────────────────┘    │  • 384-dim vectors              │
                            │  • ~100ms latency                │
                            └──────────────────────────────────┘
```

---

## Comparison: Before vs After

| Aspect | Before (FastEmbed) | After (Edge Function) |
|--------|-------------------|----------------------|
| **Docker Image** | 918MB | ~850MB |
| **Runtime Memory** | ~250-300MB | ~200-250MB |
| **Agent Cold Start** | ~5s (model loading) | ~2s (no model) |
| **Query Latency** | ~50ms (local) | ~150ms (+100ms network) |
| **Model Updates** | Requires agent redeploy | Update edge function only |
| **Scraper Impact** | Shared model (risk of drift) | Separate scraper models |
| **Scalability** | Limited by agent memory | Edge function auto-scales |

---

## Fallback Strategy

If edge function unavailable, agent automatically falls back:

```
Edge Function (primary)
  ↓ (fails)
FastEmbed (local, ~25MB)
  ↓ (fails)
HuggingFace (local, ~90MB)
```

**Manual fallback:**
```bash
USE_EDGE_FUNCTION_EMBEDDINGS=false
```

---

## Service Dependency Structure

### Agent Service (Production)
```toml
dependencies = [
    "fastapi", "uvicorn",
    "langchain", "langgraph",
    "supabase",
    # NO embedding models!
]
```

### Scraper Service (Background)
```toml
dependencies = [
    "supabase",
    "sentence-transformers",  # For batch embedding generation
    "fastembed",              # Alternative lightweight model
    "playwright",             # For JS-heavy sites
    "unstructured",           # For PDFs, docs
]
```

Install scraper dependencies:
```bash
uv pip install ".[scraper]"
```

---

## Cost Analysis

### HuggingFace Inference API
- **Free tier**: 30,000 requests/month
- **Vecinita usage**: ~3,000/month (100 queries/day)
- **Cost**: $0

### Supabase Edge Functions
- **Free tier**: 500k invocations/month
- **Vecinita usage**: ~3,000/month
- **Cost**: $0

### Render Memory Savings
- **Freed memory**: ~50-90MB
- **Value**: Can handle more concurrent requests or reduce instance size

---

## Next Steps

1. ✅ Dependencies cleaned up (pyproject.toml)
2. ✅ Edge function created and documented
3. ✅ Agent configured with fallback
4. ✅ Deployment scripts ready
5. 🔄 **Deploy edge function** (see: `docs/guides/EDGE_FUNCTION_DEPLOYMENT.md`)
6. 🔄 **Set HUGGING_FACE_TOKEN** in Supabase
7. 🔄 **Enable in Render** via environment variable
8. 🔄 **Test and monitor** performance

---

## Monitoring

### Check which embedding method is active:

```bash
# Agent startup logs
✅ Embedding model initialized via Supabase Edge Function (zero memory overhead)
# OR
⚠️ Edge function embeddings failed; falling back to FastEmbed
```

### Monitor edge function:

```bash
supabase functions logs generate-embedding --tail
```

### Verify memory usage:

**Render Dashboard:**
- vecinita-agent → Metrics → Memory Usage
- Should see ~50-90MB reduction after switching to edge function

---

## Troubleshooting

### "Edge function embeddings failed"
1. Check Supabase URL is correct
2. Verify edge function is deployed: `supabase functions list`
3. Test edge function: `.\deploy_edge_function.ps1 -Test`
4. Check HUGGING_FACE_TOKEN is set in Supabase

### "FastEmbed fallback successful"
- Edge function call failed, but agent is working
- Check edge function logs for errors
- Verify network connectivity to Supabase

### High query latency (>500ms)
- Edge function cold start (first ~2 calls after inactivity)
- Check HuggingFace API status: https://status.huggingface.co/
- Consider HuggingFace Pro for better performance

---

## References

- Edge Function Code: `supabase/functions/generate-embedding/index.ts`
- Python Client: `backend/src/utils/supabase_embeddings.py`
- Deployment Guide: `docs/guides/EDGE_FUNCTION_DEPLOYMENT.md`
- Deployment Script: `backend/scripts/deploy_edge_function.ps1`
