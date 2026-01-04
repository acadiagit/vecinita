# 📚 Documentation Index - Microservice Architecture

**Last Updated:** January 3, 2026  
**Status:** ✅ Implementation Complete

---

## Quick Links by Use Case

### 🚀 "I want to deploy to Render right now"
→ Start here: **[docs/RENDER_DEPLOYMENT_THREE_SERVICES.md](docs/RENDER_DEPLOYMENT_THREE_SERVICES.md)**
- Step-by-step deployment guide
- Checklist format
- Screenshots and examples

### 🏗️ "I want to understand the architecture"
→ Read: **[ARCHITECTURE_MICROSERVICE.md](ARCHITECTURE_MICROSERVICE.md)**
- Detailed architecture explanation
- Before/after comparison
- Diagrams and comparisons

### ⚡ "I need the quick version"
→ Check: **[QUICK_REFERENCE_MICROSERVICE.md](QUICK_REFERENCE_MICROSERVICE.md)**
- TL;DR format
- Common commands
- Quick troubleshooting

### 🎯 "What changed and why?"
→ See: **[IMPLEMENTATION_MICROSERVICE_COMPLETE.md](IMPLEMENTATION_MICROSERVICE_COMPLETE.md)**
- Complete summary of changes
- File-by-file breakdown
- Deployment checklist

### ✅ "Am I ready to deploy?"
→ Check: **[DEPLOYMENT_READY.md](DEPLOYMENT_READY.md)**
- Pre-deployment checklist
- What's new summary
- Next steps

---

## Documentation Files

### 📖 Core Guides

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[docs/RENDER_DEPLOYMENT_THREE_SERVICES.md](docs/RENDER_DEPLOYMENT_THREE_SERVICES.md)** | Complete step-by-step deployment guide with screenshots | 15 min |
| **[ARCHITECTURE_MICROSERVICE.md](ARCHITECTURE_MICROSERVICE.md)** | Detailed architecture documentation with diagrams | 20 min |
| **[QUICK_REFERENCE_MICROSERVICE.md](QUICK_REFERENCE_MICROSERVICE.md)** | Quick reference for common tasks and commands | 5 min |
| **[IMPLEMENTATION_MICROSERVICE_COMPLETE.md](IMPLEMENTATION_MICROSERVICE_COMPLETE.md)** | What was implemented and why | 15 min |
| **[DEPLOYMENT_READY.md](DEPLOYMENT_READY.md)** | Status check and next steps | 5 min |

### 📝 Code Documentation

| File | Purpose |
|------|---------|
| **[backend/src/embedding_service/README.md](backend/src/embedding_service/README.md)** | API documentation for embedding service |
| **[backend/src/embedding_service/main.py](backend/src/embedding_service/main.py)** | Source code with inline documentation |
| **[backend/src/embedding_service/client.py](backend/src/embedding_service/client.py)** | Python client for using embedding service |

---

## File Locations Quick Reference

### Configuration Files
- `render.yaml` - Render deployment config (all services)
- `docker-compose.yml` - Local Docker orchestration
- `backend/pyproject.toml` - Python dependencies

### New Service Files
- `backend/src/embedding_service/main.py` - Embedding service code
- `backend/src/embedding_service/client.py` - HTTP client for agent
- `backend/Dockerfile.embedding` - Docker build for embedding service

### Documentation
- `docs/RENDER_DEPLOYMENT_THREE_SERVICES.md` - Full deployment guide
- `ARCHITECTURE_MICROSERVICE.md` - Architecture deep-dive
- `QUICK_REFERENCE_MICROSERVICE.md` - Quick reference
- `IMPLEMENTATION_MICROSERVICE_COMPLETE.md` - Implementation details
- `DEPLOYMENT_READY.md` - Status summary

---

## Architecture Overview

```
Frontend (React)
    ↓ HTTP
Agent (FastAPI)
    ↓ HTTP
Embedding Service (FastAPI)
    ↓
HuggingFace Model Cache
    ↓ (persisted)
Supabase (PostgreSQL + pgvector)
```

**All services run on Render free tier. Cost: $0/month.**

---

## Services Summary

### 1. Embedding Service (`vecinita-embedding`)

**What it does:** Generates text embeddings  
**Port:** 8001  
**Memory:** ~350-400MB  
**Endpoints:**
- `GET /health` - Health check
- `POST /embed` - Single embedding
- `POST /embed-batch` - Batch embeddings
- `POST /similarity` - Find similar texts

**Code:** [backend/src/embedding_service/main.py](backend/src/embedding_service/main.py)  
**Docs:** [backend/src/embedding_service/README.md](backend/src/embedding_service/README.md)

### 2. Agent Service (`vecinita-agent`)

**What it does:** RAG Q&A with LangGraph  
**Port:** 10000 (Render) / 8000 (local)  
**Memory:** ~200-250MB  
**Depends on:** Embedding service  

**Endpoints:**
- `GET /health` - Health check
- `GET /ask` - Ask a question

**Code:** [backend/src/agent/main.py](backend/src/agent/main.py)

### 3. Scraper Service (`vecinita-scraper`)

**What it does:** Background content scraping  
**Schedule:** Daily at 2 AM UTC (optional)  
**Depends on:** Embedding service  

**Code:** [backend/scripts/data_scrape_load.py](backend/scripts/data_scrape_load.py)

### 4. Frontend Service (`vecinita-frontend`)

**What it does:** React web UI  
**Port:** 80 (Render) / 3000 (local)  
**Depends on:** Agent service  

**Code:** [frontend/src/](frontend/src/)

---

## Deployment Workflow

### Step 1: Understand (5 minutes)
- Read: [QUICK_REFERENCE_MICROSERVICE.md](QUICK_REFERENCE_MICROSERVICE.md)
- Understand: 3 services, all free tier, $0 cost

### Step 2: Prepare (10 minutes)
- Get Supabase credentials
- Get GROQ API key
- Have GitHub repo connected to Render

### Step 3: Deploy (15 minutes)
- Follow: [docs/RENDER_DEPLOYMENT_THREE_SERVICES.md](docs/RENDER_DEPLOYMENT_THREE_SERVICES.md)
- Deploy in order: embedding → agent → frontend → scraper (optional)

### Step 4: Verify (5 minutes)
- Check health endpoints
- Test with sample question
- Monitor logs

**Total time:** ~35 minutes

---

## Common Commands

### Local Development

```bash
# Start all services
docker-compose up

# Run embedding service alone
docker build -f backend/Dockerfile.embedding -t embedding .
docker run -p 8001:8001 embedding

# Test embedding service
curl http://localhost:8001/health
curl -X POST http://localhost:8001/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "hello"}'

# Test agent
curl "http://localhost:8000/ask?question=test"
```

### Render Deployment

```bash
# View deployment guide
cat docs/RENDER_DEPLOYMENT_THREE_SERVICES.md

# Test deployed services
curl https://vecinita-embedding.onrender.com/health
curl https://vecinita-agent.onrender.com/health
curl https://vecinita-frontend.onrender.com
```

---

## FAQ

### Q: Why did you switch from edge functions?
A: Microservice approach is more flexible, easier to debug, and gives you full control over the model. Cost is the same ($0).

See: [ARCHITECTURE_MICROSERVICE.md](ARCHITECTURE_MICROSERVICE.md#comparison-edge-function-vs-microservice)

### Q: Will the embedding service fit in free tier?
A: Yes! It uses ~350-400MB, which fits in the 512MB free tier limit.

See: [QUICK_REFERENCE_MICROSERVICE.md#memory-usage](QUICK_REFERENCE_MICROSERVICE.md#memory-usage)

### Q: How much will this cost?
A: $0/month. All services run on Render's free tier.

See: [DEPLOYMENT_READY.md#environment-configuration](DEPLOYMENT_READY.md#environment-configuration)

### Q: What if the embedding service goes down?
A: Agent automatically falls back to local FastEmbed, so no downtime.

See: [DEPLOYMENT_READY.md#fallback-chain](DEPLOYMENT_READY.md#fallback-chain)

### Q: How long does first request take?
A: ~20-30 seconds (embedding model downloads). Subsequent requests: ~300-500ms.

See: [QUICK_REFERENCE_MICROSERVICE.md#expected-performance](QUICK_REFERENCE_MICROSERVICE.md#expected-performance)

---

## Performance Expectations

| Metric | Value |
|--------|-------|
| Cold start | ~20-30s (first request, model loads) |
| Warm requests | ~300-500ms |
| Embedding latency | ~150-300ms |
| Memory usage | ~600-750MB (across 3 services) |
| Cost | **$0/month** |

---

## What's New

### Services
- ✅ Embedding microservice created
- ✅ Agent updated to call embedding service
- ✅ Docker Compose updated with 3 services
- ✅ Render config updated to free tier

### Documentation
- ✅ Complete deployment guide
- ✅ Architecture documentation
- ✅ Quick reference
- ✅ API documentation
- ✅ Python client library

### Code
- ✅ `embedding_service/main.py` (260 lines)
- ✅ `embedding_service/client.py` (95 lines)
- ✅ `Dockerfile.embedding` (58 lines)

---

## Support Resources

- **Render Docs:** https://render.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **sentence-transformers:** https://www.sbert.net
- **LangChain:** https://python.langchain.com

---

## Next Actions

### Immediate (Today)
1. ✅ Read [QUICK_REFERENCE_MICROSERVICE.md](QUICK_REFERENCE_MICROSERVICE.md) (5 min)
2. ✅ Test locally: `docker-compose up` (2 min)
3. ✅ Verify health checks (1 min)

### Short-term (This Week)
1. ✅ Deploy to Render using guide (20 min)
2. ✅ Test endpoints (5 min)
3. ✅ Monitor logs (5 min)

### Long-term
1. ✅ Monitor memory usage
2. ✅ Optimize if needed
3. ✅ Scale if usage increases

---

## Document Map

```
📚 Documentation Index (YOU ARE HERE)
├── 🚀 QUICK START
│   └── QUICK_REFERENCE_MICROSERVICE.md (5 min)
├── 📖 DETAILED GUIDES
│   ├── docs/RENDER_DEPLOYMENT_THREE_SERVICES.md (15 min)
│   ├── ARCHITECTURE_MICROSERVICE.md (20 min)
│   └── IMPLEMENTATION_MICROSERVICE_COMPLETE.md (15 min)
├── ✅ STATUS CHECKS
│   ├── DEPLOYMENT_READY.md (5 min)
│   └── This file (index)
├── 💻 CODE DOCUMENTATION
│   ├── backend/src/embedding_service/README.md
│   ├── backend/src/embedding_service/main.py
│   └── backend/src/embedding_service/client.py
└── ⚙️ CONFIGURATION
    ├── render.yaml
    ├── docker-compose.yml
    └── backend/pyproject.toml
```

---

## Ready to Deploy?

1. **Read:** [QUICK_REFERENCE_MICROSERVICE.md](QUICK_REFERENCE_MICROSERVICE.md) (5 min)
2. **Deploy:** [docs/RENDER_DEPLOYMENT_THREE_SERVICES.md](docs/RENDER_DEPLOYMENT_THREE_SERVICES.md) (20 min)
3. **Verify:** Check all endpoints return 200 OK

**Questions?** See [QUICK_REFERENCE_MICROSERVICE.md#troubleshooting](QUICK_REFERENCE_MICROSERVICE.md#troubleshooting)

---

**Status:** ✅ Ready for deployment  
**Cost:** $0/month  
**Complexity:** Low  
**Benefits:** Full control, independent scaling, easy debugging

🚀 **Let's go!**
