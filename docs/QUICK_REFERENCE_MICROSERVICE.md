# Quick Reference - Three Service Deployment

## TL;DR: What Changed

❌ **Old:** Supabase Edge Function for embeddings  
✅ **New:** Dedicated embedding microservice (separate free-tier Render service)

---

## Architecture (30-second version)

```
Frontend (React)
    ↓
Agent (FastAPI) 
    ↓
Embedding Service (FastAPI + sentence-transformers)
    ↓
Supabase (PostgreSQL + pgvector)
```

**All 3 services run on Render free tier. Total cost: $0.**

---

## Files You Need to Know About

| File | Purpose |
|------|---------|
| `backend/src/embedding_service/main.py` | **NEW** - Embedding service code |
| `backend/Dockerfile.embedding` | **NEW** - Build embedding service |
| `backend/src/embedding_service/client.py` | **NEW** - HTTP client for agent |
| `docker-compose.yml` | UPDATED - Now has 3 services |
| `render.yaml` | UPDATED - All free tier, new config |
| `backend/src/agent/main.py` | UPDATED - Uses HTTP instead of edge function |
| `docs/RENDER_DEPLOYMENT_THREE_SERVICES.md` | **NEW** - Full deployment guide |

---

## Quick Start

### Local Testing
```bash
# Start all 3 services locally
docker-compose up

# Wait ~40 seconds for services to be healthy
# Then test:
curl http://localhost:8001/health     # Embedding
curl http://localhost:8000/health     # Agent
open http://localhost:3000            # Frontend
```

### Production Deployment

1. Go to https://dashboard.render.com
2. Create 4 new web services:
   - **vecinita-embedding** (Dockerfile: `backend/Dockerfile.embedding`, Plan: Free)
   - **vecinita-agent** (Dockerfile: `backend/Dockerfile`, Plan: Free)
   - **vecinita-frontend** (Dockerfile: `frontend/Dockerfile`, Plan: Free)
   - **vecinita-scraper** (optional, Dockerfile: `backend/Dockerfile.scraper`, Background Worker)

3. Set environment variables:
   - Agent: `EMBEDDING_SERVICE_URL=https://vecinita-embedding.onrender.com`
   - Agent secrets: `SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY`
   - Frontend: `VITE_BACKEND_URL=https://vecinita-agent.onrender.com`

4. Deploy each service

See `docs/RENDER_DEPLOYMENT_THREE_SERVICES.md` for detailed steps.

---

## Key Config Changes

### docker-compose.yml
**Added:** embedding service dependency
```yaml
embedding-service:
  build: ./backend/Dockerfile.embedding
  ports: ["8001:8001"]

vecinita-agent:
  environment:
    EMBEDDING_SERVICE_URL: "http://embedding-service:8001"
  depends_on: [embedding-service]
```

### render.yaml
**Changed:** All services to free tier, added embedding service
```yaml
- name: vecinita-embedding
  plan: free
  dockerfilePath: ./backend/Dockerfile.embedding
  
- name: vecinita-agent
  plan: free
  envVars:
    EMBEDDING_SERVICE_URL: "https://vecinita-embedding.onrender.com"
```

### backend/src/agent/main.py
**Changed:** Embedding initialization (lines ~111-130)
```python
# OLD: Uses edge function
# NEW: Uses HTTP client
from src.embedding_service.client import create_embedding_client
embedding_model = create_embedding_client(
    "http://embedding-service:8001"  # or EMBEDDING_SERVICE_URL env
)
```

---

## Memory Usage

| Service | RAM | Fits Free Tier? |
|---------|-----|-----------------|
| Embedding | ~350-400MB | ✅ Yes (512MB available) |
| Agent | ~200-250MB | ✅ Yes (512MB available) |
| Frontend | ~50-100MB | ✅ Yes (512MB available) |
| Scraper | ~150-200MB | ✅ Yes (runs as cron, terminates) |

**All services fit on free tier!** ✅

---

## Deployment Checklist

- [ ] `docker-compose up` works locally
- [ ] Both services show "health: ok" in logs
- [ ] curl tests pass
- [ ] Render account created & GitHub connected
- [ ] Deploy embedding service first
- [ ] Deploy agent service (point to embedding service URL)
- [ ] Deploy frontend service (point to agent URL)
- [ ] Test all endpoints return 200 OK
- [ ] Visit frontend URL, verify it loads

---

## Environment Variables Needed

### For Embedding Service
```
PORT=8001
PYTHONUNBUFFERED=1
```

### For Agent Service
```
PORT=10000
PYTHONUNBUFFERED=1
TF_ENABLE_ONEDNN_OPTS=0
EMBEDDING_SERVICE_URL=https://vecinita-embedding.onrender.com

# Secrets (set in Render Dashboard)
SUPABASE_URL=...
SUPABASE_KEY=...
GROQ_API_KEY=...
```

### For Frontend
```
VITE_BACKEND_URL=https://vecinita-agent.onrender.com
```

---

## Expected Performance

| Metric | Value |
|--------|-------|
| Cold start (first request) | ~20-30s (embedding model loads) |
| Warm requests | ~300-500ms |
| Embedding latency | ~150-300ms |
| Memory footprint | ~600-750MB total (across 3 services) |

---

## Cost

```
✅ Embedding service: $0
✅ Agent service: $0  
✅ Frontend service: $0
✅ Scraper service: $0
✅ Supabase: $0
─────────────────────
  TOTAL: $0/month
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection refused" | Embedding service not running or URL incorrect |
| "504 Gateway" | Embedding service is starting (wait 30s) |
| "Out of memory" | Service restarting. Normal on first deploy. |
| Agent can't find embedding service | Check `EMBEDDING_SERVICE_URL` environment variable |
| Frontend won't load | Check `VITE_BACKEND_URL` environment variable |

---

## Testing Endpoints

```bash
# Embedding service
curl https://vecinita-embedding.onrender.com/health
curl -X POST https://vecinita-embedding.onrender.com/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world"}'

# Agent service
curl https://vecinita-agent.onrender.com/health
curl "https://vecinita-agent.onrender.com/ask?question=test"

# Frontend
open https://vecinita-frontend.onrender.com
```

---

## Documentation

- **Full deployment guide:** `docs/RENDER_DEPLOYMENT_THREE_SERVICES.md`
- **Architecture details:** `ARCHITECTURE_MICROSERVICE.md`
- **API reference:** `backend/src/embedding_service/main.py` (docstrings)

---

## Support

Need help? Check:
1. Render logs: https://dashboard.render.com → Service → Logs
2. Architecture docs: `ARCHITECTURE_MICROSERVICE.md`
3. Deployment guide: `docs/RENDER_DEPLOYMENT_THREE_SERVICES.md`
