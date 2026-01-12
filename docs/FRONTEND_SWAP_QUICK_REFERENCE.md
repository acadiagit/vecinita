# Frontend Swap - Quick Reference Guide

## Current Frontend Details
- **Location**: `frontend/` 
- **Language**: JavaScript
- **Framework**: React 18.2 + Vite 5.0 + Tailwind v3.4
- **UI Library**: shadcn/ui (Radix primitives)
- **Status**: ✅ Production-ready, fully integrated
- **Dev Port**: 5173 | **Docker Port**: 3000 (→ 80)

## New Frontend Details
- **Repository**: https://github.com/joseph-c-mcguire/Vecinitafrontend.git
- **Language**: TypeScript
- **Framework**: React 18.3 + Vite 6.3 + Tailwind v4.1
- **UI Library**: Radix UI (50+ components) + Material UI
- **Status**: ⚠️ **NOT PRODUCTION-READY** - lacks backend integration, Docker, tests
- **Dev Port**: 5173 (same) | **Docker Port**: ❌ No Dockerfile

## Critical API Endpoints (MUST BE MAINTAINED)

### /config
**Purpose**: Discover available LLM providers and models  
**Method**: GET  
**Expected Response**:
```json
{
  "providers": [
    {"key": "deepseek", "label": "DeepSeek"},
    {"key": "llama", "label": "Llama"},
    {"key": "openai", "label": "OpenAI"}
  ],
  "models": {
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "llama": ["llama3.2"],
    "openai": ["gpt-4o-mini"]
  }
}
```

### /ask-stream
**Purpose**: Stream responses from RAG Q&A system  
**Method**: GET  
**Query Parameters**:
- `query` (string): User question (URL-encoded, max 2000 chars)
- `lang` (string, optional): 'en' or 'es' (auto-detect if omitted)
- `provider` (string): 'openai', 'llama', 'deepseek'
- `model` (string): Model name
- `thread_id` (string): Session UUID for context persistence

**Response Format** (Server-Sent Events):
```
data: {"type":"thinking","message":"Analyzing..."}
data: {"type":"complete","answer":"...","sources":[...],"plan":""}
```

## Environment Variables

### Current (Working)
```
VITE_BACKEND_URL=http://localhost:8000  # Dev
VITE_BACKEND_URL=https://vecinita-agent.onrender.com  # Prod
```
- Injected as Docker build arg during `npm run build`
- Falls back to `/api` proxy in dev
- Hardcoded in bundled app for production

### New Frontend (Missing)
- No environment variable configuration found
- **MUST ADD** VITE_BACKEND_URL support
- **MUST ADD** dev proxy configuration

## Must-Have Features for New Frontend

### Before Swap Can Happen
- [ ] Remove mock response logic
- [ ] Implement real `/ask-stream` API calls with SSE parsing
- [ ] Add provider/model selection UI
- [ ] Implement `/config` endpoint integration
- [ ] Add localStorage session management (thread_id)
- [ ] Set up Dockerfile (multi-stage, Nginx runtime)
- [ ] Configure vite.config.ts with dev proxy
- [ ] Document VITE_BACKEND_URL setup
- [ ] Implement error handling for API failures
- [ ] Test with actual backend responses

### Testing & Validation
- [ ] Unit tests for API integration
- [ ] E2E tests with real backend
- [ ] Dark mode functionality (already in new frontend)
- [ ] Language switching (already in new frontend)
- [ ] Streaming response display
- [ ] Source attribution accuracy
- [ ] Thread persistence across sessions
- [ ] Bundle size analysis
- [ ] Performance testing (lighthouse scores)

## File Checklist for Migration

### From New Frontend Repository
```
✓ package.json - Dependencies (very different)
✓ vite.config.ts - Needs proxy config added
✓ src/app/App.tsx - Remove mock responses, add real API
✓ src/app/context/LanguageContext.tsx - Keep
✓ src/app/context/AccessibilityContext.tsx - Keep
✓ src/app/components/* - Most can be kept
✓ src/styles/* - Tailwind v4 compatibility check
✓ index.html - Already set up correctly
✗ Dockerfile - MUST CREATE
✗ .env example - SHOULD CREATE
✗ vitest.config.ts - ADD IF TESTING NEEDED
```

### To Create/Update
```
1. Dockerfile - Production build with VITE_BACKEND_URL support
2. vite.config.ts - Add dev proxy for /api and /config
3. docker-compose.yml - Update frontend service definition
4. .env.example - Document VITE_BACKEND_URL requirement
5. App.tsx - Replace mock responses with real API calls
6. package.json - Add preview and test scripts
```

## Bundle Size Comparison
- **Current**: ~100 KB gzipped (lean, optimized)
- **New**: ~200+ KB gzipped (2x larger)
  - Additional dependencies: Material UI, Radix UI full suite, recharts, react-dnd
  - **Action**: Consider tree-shaking unused components

## Tailwind CSS Version Migration

### v3.4.0 (Current) → v4.1.12 (New)
**Breaking Changes**:
- Vite plugin instead of PostCSS
- New CSS variable syntax for theme tokens
- postcss.config.js becomes empty (handled by Vite)
- Improved performance and smaller output

**Migration Steps**:
1. Remove `tailwindcss` and `postcss` from devDependencies
2. Add `@tailwindcss/vite` plugin
3. Update vite.config
4. Verify all utility classes still work
5. Test dark mode transitions
6. Update custom CSS variable usage (if any)

## Backend Service Dependency Chain

```yaml
# docker-compose.yml dependency order
embedding-service (port 8001)
    ↓
vecinita-agent (port 8000) - depends on embedding-service healthy
    ↓
vecinita-frontend (port 3000) - depends on vecinita-agent healthy
```

New frontend MUST maintain this dependency order in docker-compose.

## Local Development Workflow

### With Current Frontend
```bash
# Terminal 1: Backend
cd backend
uvicorn src.main:app --reload

# Terminal 2: Frontend
cd frontend
npm install
npm run dev
# Proxy forwards /api/* to http://localhost:8000
```

### With New Frontend (After Updates)
```bash
# Same backend as above
# Terminal 2: New Frontend
cd new-frontend-repo
npm install
npm run dev
# Must have vite.config.ts proxy configured
```

## Docker Build & Run

### Current Frontend
```bash
docker build frontend \
  --build-arg VITE_BACKEND_URL=https://vecinita-agent.onrender.com \
  -t vecinita-frontend:latest

docker run -p 3000:80 vecinita-frontend:latest
```

### New Frontend (Template - TO BE CREATED)
```bash
# Dockerfile must support same pattern
docker build frontend \
  --build-arg VITE_BACKEND_URL=https://vecinita-agent.onrender.com \
  -t vecinita-frontend-new:latest

docker run -p 3000:80 vecinita-frontend-new:latest
```

## Decision Matrix

| Decision | Option A | Option B | Recommendation |
|----------|----------|----------|-----------------|
| **Keep Current or Swap?** | Keep v5 + v3 | Swap to v6 + v4 | Complete new frontend first, then swap |
| **TypeScript or JS?** | JavaScript | TypeScript (new) | Keep TypeScript for new frontend |
| **Testing?** | Add to new | Keep current | Add vitest to new frontend before swap |
| **Bundle Size?** | Optimize now | Accept 2x | Optimize via tree-shaking |
| **Component Library** | Keep minimal | Use Material UI | Use what's imported, optimize unused |
| **Migration Timeline** | Immediate | Phased | 2-4 weeks (complete integration first) |

## Next Steps

1. **Immediate (Week 1)**
   - Clone and set up new frontend for development
   - Create Dockerfile
   - Add backend integration scaffolding
   - Set up dev proxy in vite.config.ts

2. **Short-term (Week 2)**
   - Implement /config endpoint integration
   - Implement /ask-stream with SSE parsing
   - Add provider/model selection
   - Test with real backend

3. **Medium-term (Week 3-4)**
   - Add testing framework
   - Implement error handling
   - Performance optimization
   - Docker build validation

4. **Before Swap**
   - Full regression testing
   - Production deployment validation
   - Rollback plan ready
   - Team training on new stack

---

**Last Updated**: January 12, 2025  
**Status**: Research Complete - Ready for Implementation Planning
