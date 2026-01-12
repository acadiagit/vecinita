# Frontend Swap Research Summary
**Date**: January 12, 2025  
**Current Frontend**: React 18 + Vite + Tailwind CSS + shadcn/ui (JavaScript)  
**New Frontend**: React 18 + Vite + Tailwind CSS v4 + Figma Design System Components (TypeScript)

---

## 1. Current Frontend Analysis

### Project Structure
```
frontend/
├── src/
│   ├── App.jsx                    # Main app entry point
│   ├── main.jsx                   # Vite entry point (renders App to #root)
│   ├── styles.css                 # Global styles
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatWidget.jsx     # Main chat component (496 lines)
│   │   │   ├── MessageBubble.jsx  # Message display component
│   │   │   └── *.test.jsx         # Component tests
│   │   └── ui/                    # shadcn/ui components
│   ├── lib/
│   │   └── utils.js               # Provider/model config constants
│   └── test/
│       └── setup.js               # Vitest configuration
├── public/                         # Static assets
├── package.json                    # Dependencies & scripts
├── vite.config.js                  # Vite configuration
├── tailwind.config.js              # Tailwind CSS v3.4.0
├── postcss.config.js               # PostCSS configuration
├── Dockerfile                      # Multi-stage Docker build
└── index.html                      # HTML entry point
```

### Key Dependencies
- **React**: 18.2.0
- **UI Framework**: Tailwind CSS 3.4.0 + shadcn/ui components
- **Icons**: lucide-react 0.461.0
- **Markdown**: react-markdown 9.0.0 + remark-gfm 3.0.0
- **Radix UI**: Multiple primitives (@radix-ui/react-dialog, -slider, etc.)
- **Build Tool**: Vite 5.0.0 + @vitejs/plugin-react 4.2.0
- **Testing**: Vitest 1.6.0 + Playwright 1.45.0 + Testing Library
- **CSS Utilities**: class-variance-authority 0.7.0

### Build & Dev Scripts
```json
{
  "dev": "vite",                                    // Dev server on port 5173
  "build": "vite build",                           // Production build
  "preview": "vite preview --host --port 5173",    // Preview production build
  "start": "vite preview --host --port 5173",      // Alias for preview
  "test": "vitest",                                // Run tests in watch mode
  "test:run": "vitest run",                        // Run tests once
  "test:coverage": "vitest run --coverage --coverage.provider=v8",
  "test:e2e": "playwright test"                    // E2E tests
}
```

### Vite Configuration
```javascript
// vite.config.js
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')             // Path alias to src directory
    }
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      // Dev proxy forwards /api/* to backend FastAPI (8000)
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      // Backend config endpoint for provider/model discovery
      '/config': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  preview: {
    port: 5173
  },
  test: {
    environment: 'jsdom',
    setupFiles: [resolve(__dirname, './src/test/setup.js')],
    include: ['src/**/*.test.{js,jsx,ts,tsx}'],
    exclude: ['node_modules/**', 'tests/e2e/**']
  }
})
```

### Dockerfile
- **Build Stage**: Node 20-alpine, npm install, vite build with `VITE_BACKEND_URL` build arg
- **Runtime Stage**: Nginx Alpine with SPA routing, cache busting for `/assets/`, health check endpoint
- **Default Backend URL**: `https://vecinita-agent.onrender.com` (production) or `http://localhost:8000` (dev)
- **Output Port**: 80 (mapped to 3000 in docker-compose)

### Backend Integration Points

#### 1. **Backend URL Configuration**
```javascript
// src/App.jsx
const backendUrl = import.meta.env.VITE_BACKEND_URL || '/api'
```
- Injected via Dockerfile build arg `VITE_BACKEND_URL`
- Falls back to `/api` proxy for local dev
- Passed to `<ChatWidget backendUrl={backendUrl} />`

#### 2. **Configuration Endpoint** (`/config`)
```javascript
// ChatWidget.jsx - Line 122
const res = await fetch(`${base}/config`)
```
- Fetches available providers and models from backend
- Response expected:
  ```json
  {
    "providers": [
      { "key": "deepseek", "label": "DeepSeek" },
      { "key": "llama", "label": "Llama" },
      { "key": "openai", "label": "OpenAI" }
    ],
    "models": {
      "deepseek": ["deepseek-chat", "deepseek-reasoner"],
      "llama": ["llama3.2"],
      "openai": ["gpt-4o-mini"]
    }
  }
  ```
- Auto-selects provider with priority: deepseek > llama > openai

#### 3. **Streaming Ask Endpoint** (`/ask-stream`)
```javascript
// ChatWidget.jsx - Line 184
const streamUrl = `${urlBase}/ask-stream?query=${encodeURIComponent(q)}${langParam}&provider=${encodeURIComponent(provider)}&model=${encodeURIComponent(model)}&thread_id=${encodeURIComponent(thread)}`
```

**Query Parameters**:
- `query`: User question (URL-encoded, max 2000 chars)
- `lang`: Language ('en', 'es', or omitted for auto-detect)
- `provider`: LLM provider ('openai', 'llama', 'deepseek')
- `model`: Model name (e.g., 'gpt-4o-mini')
- `thread_id`: Session ID for context persistence (UUID or fallback format)

**Response Format** (Server-Sent Events):
```
data: {"type":"thinking","message":"Looking for..."}
data: {"type":"thinking","message":"Analyzing..."}
data: {"type":"complete","answer":"...","sources":[...],"plan":""}
```

**Message Types**:
- `thinking`: Agent's reasoning process (can occur multiple times)
- `complete`: Final answer with `answer`, `sources`, and optional `plan`
- `clarification`: Asks user clarifying questions (type, context, questions)
- `error`: Error message

#### 4. **Session Management**
- Thread ID stored in localStorage (`vecinita_thread_id`)
- Enables multi-turn conversations with context
- Fallback: UUID or `thread-{timestamp}-{random}`

#### 5. **Provider/Model Selection**
```javascript
// lib/utils.js - Default fallback options
export const PROVIDERS = [
  { key: 'openai', label: 'OpenAI' },
  { key: 'llama', label: 'Llama' },
  { key: 'deepseek', label: 'DeepSeek' }
]

export const MODELS = {
  openai: ['gpt-4o-mini'],
  llama: ['llama3.2'],
  deepseek: ['deepseek-chat', 'deepseek-reasoner']
}
```

### Docker Integration
```yaml
# docker-compose.yml excerpt
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
    args:
      VITE_BACKEND_URL: ${VITE_BACKEND_URL:-http://localhost:8000}
  image: vecinita-frontend:latest
  container_name: vecinita-frontend
  depends_on:
    vecinita-agent:
      condition: service_healthy
  ports:
    - "3000:80"  # Frontend exposed on port 3000
```

**Environment Variables**:
- `VITE_BACKEND_URL`: Injected during build (default: `http://localhost:8000`)

---

## 2. New Frontend Analysis

### Project Structure
```
Vecinitafrontend/
├── src/
│   ├── main.tsx                   # Vite entry point (TypeScript)
│   ├── app/
│   │   ├── App.tsx                # Main app component (TypeScript)
│   │   ├── components/            # UI Components
│   │   │   ├── ChatMessage.tsx    # Chat message display
│   │   │   ├── LanguageSelector.tsx
│   │   │   ├── ThemeToggle.tsx
│   │   │   ├── AccessibilityPanel.tsx
│   │   │   ├── SourceCard.tsx
│   │   │   └── [other UI components]
│   │   └── context/               # Context providers
│   │       ├── LanguageContext.tsx
│   │       └── AccessibilityContext.tsx
│   └── styles/
│       ├── index.css              # Global styles
│       ├── tailwind.css           # Tailwind directives
│       ├── theme.css              # Theme variables
│       └── fonts.css              # Font definitions
├── package.json                    # Dependencies (significantly different)
├── vite.config.ts                  # TypeScript Vite config
├── postcss.config.mjs              # PostCSS (empty, Tailwind v4 handles it)
├── index.html                      # HTML entry point
├── Dockerfile                      # [NOT FOUND - needs to be created]
├── README.md                        # Basic setup instructions
├── ATTRIBUTIONS.md                 # Component attributions
└── guidelines/
    └── Guidelines.md               # Design guidelines (mostly template)
```

### Key Dependencies (MAJOR DIFFERENCES)
- **React**: 18.3.1 (peer dependency, optional)
- **React DOM**: 18.3.1 (peer dependency, optional)
- **Tailwind CSS**: v4.1.12 (NEW - using @tailwindcss/vite plugin instead of postcss)
- **Build Tool**: Vite 6.3.5 (newer than current 5.0.0)
- **UI Components**: Massive Radix UI component library (50+ components)
- **Material UI**: @mui/material 7.3.5 + @mui/icons-material 7.3.5
- **Emotion**: @emotion/react 11.14.0 + @emotion/styled 11.14.1
- **Advanced UI**: 
  - cmdk 1.1.1 (command palette)
  - embla-carousel-react 8.6.0 (carousel)
  - react-dnd 16.0.1 + react-dnd-html5-backend 16.0.1 (drag & drop)
  - react-hook-form 7.55.0 (form management)
  - recharts 2.15.2 (charts/visualizations)
  - sonner 2.0.3 (toast notifications)
  - vaul 1.1.2 (drawer component)
- **Utilities**:
  - clsx 2.1.1 (className merging)
  - tailwind-merge 3.2.0 (Tailwind class merging)
  - motion 12.23.24 (animations)
  - date-fns 3.6.0 (date utilities)

### Build & Dev Scripts
```json
{
  "dev": "vite",                    // Dev server (no port specified, defaults to 5173)
  "build": "vite build"             // Production build
}
```
**Note**: No preview, preview, test, or e2e scripts - must be added if testing/preview needed

### Vite Configuration
```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),  // NEW: Tailwind v4 via Vite plugin
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

**Key Differences**:
- **No explicit server proxy configuration** - would need to be added for backend integration
- **No test configuration** - vitest setup needed
- **Tailwind v4 via Vite plugin** - no separate PostCSS setup required
- **No preview configuration** - port 5173 implicit

### PostCSS Configuration
```javascript
// postcss.config.mjs
export default {}  // EMPTY - Tailwind v4 with Vite plugin handles all PostCSS automatically
```

### App Structure (App.tsx)
- **State**: Messages, input, loading state, theme, language, accessibility panel
- **Components Used**:
  - ChatMessage (displays messages with sources)
  - LanguageSelector (i18n)
  - ThemeToggle (dark/light mode)
  - AccessibilityPanel (settings)
  - SourceCard (source attribution)
- **No Backend Integration**: Currently uses **mock responses** with keyword-based detection
- **Language Context**: Provides `t()` translation function and `language` state
- **Accessibility Context**: Manages accessibility settings

### Mock Response Examples
```javascript
// Current implementation uses hard-coded mock responses
// Examples for "water", "air", "climate" queries with bilingual support
// Includes mock sources with EPA, WHO, CDC links
// NO REAL API CALLS - just setTimeout(1000) simulation
```

### Styling Approach
- Tailwind v4 with CSS variables for theming
- Dark mode support via `document.documentElement.classList`
- Responsive design (sm:, md: breakpoints)
- Accessible components with ARIA labels and semantic HTML

---

## 3. Specific Differences Summary

### Architecture
| Aspect | Current | New |
|--------|---------|-----|
| **Language** | JavaScript | TypeScript |
| **Vite Version** | 5.0.0 | 6.3.5 |
| **Tailwind CSS** | v3.4.0 (PostCSS) | v4.1.12 (Vite plugin) |
| **UI Components** | shadcn/ui (Radix primitives) | Extensive Radix UI + Material UI |
| **Backend Integration** | ✅ Real API calls to `/ask-stream` | ❌ Mock responses only |
| **Form Handling** | Manual state management | react-hook-form 7.55.0 |
| **Drag & Drop** | Not present | react-dnd included |
| **Charts/Visualization** | Not present | recharts 2.15.2 |
| **Testing** | Vitest + Playwright | ❌ No test setup |
| **Docker** | ✅ Nginx-based production build | ❌ No Dockerfile |

### Dependencies Count
- **Current**: ~15-20 core dependencies
- **New**: ~50+ dependencies (significantly larger bundle)

### Environment Variables
- **Current**: `VITE_BACKEND_URL` (passed as build arg)
- **New**: No environment variables found or documented

### Dev Server Configuration
- **Current**: Explicit port 5173, `/api` proxy, `/config` proxy
- **New**: No explicit proxy configuration (needs to be added)

---

## 4. Critical Integration Points to Maintain/Update

### Must Be Preserved
1. **Backend URL Configuration**
   - New frontend NEEDS environment variable setup for backend URL
   - Should support `VITE_BACKEND_URL` pattern or similar
   - Must work in both dev (with proxy) and production

2. **API Endpoints**
   - `/config` endpoint (provider/model discovery)
   - `/ask-stream` endpoint (streaming responses)
   - Both need to be available in new frontend

3. **Request Parameters**
   - `query`: User question
   - `lang`: Language code ('en', 'es')
   - `provider`: LLM provider
   - `model`: Model name
   - `thread_id`: Session ID
   - **Verify new frontend passes all these correctly**

4. **Response Parsing**
   - Server-Sent Events (SSE) format with `data: {JSON}` lines
   - Message types: `thinking`, `complete`, `clarification`, `error`
   - Sources format: `[{title, url, snippet}]`
   - **New frontend currently expects mock format - needs alignment**

5. **Session Management**
   - localStorage for `vecinita_thread_id`
   - Thread ID generation (UUID or fallback)
   - **Verify new frontend maintains this pattern**

6. **Language Support**
   - Spanish (es) and English (en)
   - Language detection and user selection
   - **New frontend has LanguageContext - check implementation**

### Configuration Changes Needed
1. **Vite Config**: Add dev server proxy for `/api` and `/config` endpoints
2. **Dockerfile**: Create production-ready Docker image for new frontend
3. **Environment Variables**: Document and implement `VITE_BACKEND_URL`
4. **Test Setup**: Add vitest configuration if testing needed
5. **Build Scripts**: Add preview and test scripts to package.json

---

## 5. Docker & Containerization

### Current Frontend Dockerfile
```dockerfile
# Build stage (Node 20-alpine)
RUN VITE_BACKEND_URL=${VITE_BACKEND_URL} npm run build

# Runtime stage (Nginx alpine)
# - Serves static build on port 80
# - SPA routing (try_files $uri $uri/ /index.html)
# - Cache busting for /assets/
# - Health check endpoint /health
```

### New Frontend - MISSING
- **No Dockerfile exists** in new repository
- **Must create** for Docker Compose integration
- **Must handle** TypeScript compilation (npm run build)
- **Should follow** same pattern as current (Nginx runtime)

### Docker Compose Configuration
```yaml
# Current integration
frontend:
  build:
    context: ./frontend
    args:
      VITE_BACKEND_URL: ${VITE_BACKEND_URL:-http://localhost:8000}
  ports:
    - "3000:80"
  depends_on:
    vecinita-agent:
      condition: service_healthy
```

**New frontend will need**:
- Dockerfile created
- Same build args pattern
- Same port mapping (3000:80)
- Same health dependency chain

---

## 6. Port & URL Configuration

### Development
| Service | Current Port | New Frontend Port | Notes |
|---------|-------------|-------------------|-------|
| Frontend Dev | 5173 | 5173 | Same (implicit in Vite) |
| Backend FastAPI | 8000 | 8000 | Unchanged |
| Frontend (Docker) | 3000 | 3000 | Maps to internal 80 |

### Proxy Configuration Required
**Current**: Configured in vite.config.js
- `/api/*` → `http://localhost:8000`
- `/config` → `http://localhost:8000`

**New**: MISSING - Must add to vite.config.ts
```typescript
server: {
  proxy: {
    '/api': { target: 'http://localhost:8000', changeOrigin: true, rewrite: ... },
    '/config': { target: 'http://localhost:8000', changeOrigin: true }
  }
}
```

### Production Backend URL
- **Current**: `https://vecinita-agent.onrender.com` (in Dockerfile)
- **New**: Not configured - must add build arg support

---

## 7. Deployment & Environment

### Environment Variables Required
1. `VITE_BACKEND_URL`: Backend service URL
   - Dev: `http://localhost:8000`
   - Prod: `https://vecinita-agent.onrender.com` (or cloud URL)
   - Injected during build time (Vite requirement)

### CI/CD Considerations
- **Current**: Docker build accepts VITE_BACKEND_URL as build arg
- **New**: Needs same pattern (create Dockerfile first)

### Configuration Management
- **Current**: Single backend URL (dev proxy vs production)
- **New**: Must implement same approach

---

## 8. Component & Feature Comparison

### Current Frontend Features
1. ✅ Chat widget (standalone or embedded)
2. ✅ Language selection (Spanish/English)
3. ✅ Provider/model selection (OpenAI, Llama, DeepSeek)
4. ✅ Streaming responses with thinking messages
5. ✅ Source attribution with links
6. ✅ Thread-based conversation history
7. ✅ Input validation (max 2000 chars)
8. ✅ Loading states and error handling
9. ✅ Responsive design
10. ✅ Full test coverage (unit + e2e)

### New Frontend Features
1. ✅ Chat interface (full-page only, not standalone widget)
2. ✅ Language selection (Spanish/English)
3. ✅ Theme toggle (light/dark)
4. ✅ Accessibility panel
5. ✅ Message display with sources
6. ✅ Mock responses only (no real API yet)
7. ❌ No streaming implementation
8. ❌ No provider/model selection UI
9. ❌ No test coverage
10. ✅ Responsive design with Tailwind v4

### Missing in New Frontend
- Backend integration (critical)
- Provider/model selection interface
- Streaming response handling
- Thread ID management
- Input validation
- Loading/error states (minimal)
- Test setup
- Docker configuration

---

## 9. Migration Path Recommendations

### Phase 1: Foundation (High Priority)
1. **Create Dockerfile**
   - Multi-stage build (node:20-alpine → nginx:alpine)
   - Support VITE_BACKEND_URL build arg
   - SPA routing with health check

2. **Add Backend Integration**
   - Implement /api and /config proxies in vite.config.ts
   - Update App.tsx to fetch real backend responses
   - Remove mock response logic
   - Implement streaming SSE parsing

3. **API Contract Implementation**
   - Provider/model selection from `/config`
   - /ask-stream endpoint with correct parameter passing
   - Thread ID management via localStorage
   - Error handling for API failures

4. **Environment Configuration**
   - Document VITE_BACKEND_URL variable
   - Update docker-compose.yml for new frontend
   - Test local dev with proxy
   - Test production build

### Phase 2: Feature Parity (Medium Priority)
1. **Convert to TypeScript** (optional - already in new frontend)
2. **Chat Widget Functionality**
   - Streaming response handling
   - Thinking messages display
   - Source attribution UI
3. **Testing**
   - Add vitest configuration
   - Implement unit tests
   - Add e2e tests with Playwright

### Phase 3: Enhancement (Lower Priority)
1. **New Features** (make use of new dependencies)
   - Form validation with react-hook-form
   - Charts/visualizations with recharts
   - Drag & drop capabilities
   - Advanced UI components

---

## 10. Key Technical Decisions to Make

### 1. TypeScript vs JavaScript
- **Current**: JavaScript
- **New**: TypeScript (stricter, better IDE support)
- **Decision**: Keep TypeScript or convert back to JavaScript?

### 2. Tailwind CSS Version
- **Current**: v3.4.0
- **New**: v4.1.12 (major version, breaking changes)
- **Decision**: Upgrade for new builds or maintain v3 compatibility?

### 3. UI Component Library
- **Current**: shadcn/ui (lightweight, copy-paste based)
- **New**: Full Radix UI + Material UI (heavier, feature-rich)
- **Decision**: Keep current minimalist approach or embrace new components?

### 4. Testing Framework
- **Current**: Vitest + Playwright
- **New**: No testing setup
- **Decision**: Add testing to new frontend or accept reduced test coverage?

### 5. Bundle Size Impact
- **Current**: ~100KB gzipped (estimate)
- **New**: ~200KB+ gzipped (significantly larger)
- **Decision**: Optimize/tree-shake unused dependencies or accept larger bundle?

---

## Summary Table

| Category | Current Frontend | New Frontend | Gap |
|----------|-----------------|--------------|-----|
| **Language** | JavaScript (ESM) | TypeScript | ✓ Upgrade |
| **Build Tool** | Vite 5.0.0 | Vite 6.3.5 | ✓ Newer |
| **Tailwind CSS** | v3.4.0 | v4.1.12 | ⚠️ Major version |
| **React** | 18.2.0 | 18.3.1 | ✓ Patch |
| **Testing** | ✓ Vitest + Playwright | ❌ None | ⚠️ Missing |
| **Docker** | ✓ Nginx build | ❌ Missing | ⚠️ Critical |
| **Backend Integration** | ✓ Real API | ❌ Mock only | ⚠️ Critical |
| **Streaming SSE** | ✓ Implemented | ❌ Not implemented | ⚠️ Critical |
| **Dev Proxy** | ✓ Configured | ❌ Missing | ⚠️ Important |
| **Env Variables** | ✓ VITE_BACKEND_URL | ❌ Not configured | ⚠️ Important |
| **Provider Selection** | ✓ UI + API | ❌ UI missing | ⚠️ Feature gap |
| **Bundle Size** | ~100KB | ~200KB+ | ⚠️ 2x larger |
| **Dependencies** | ~20 core | ~50+ | ⚠️ Complexity |

---

## Conclusion

The new frontend is a **significant redesign** with:
- ✅ Modern TypeScript implementation
- ✅ Enhanced UI component ecosystem
- ✅ Better accessibility features
- ⚠️ **NOT READY FOR PRODUCTION** - missing critical backend integration, Docker, and testing
- ⚠️ **2x larger bundle** - may impact performance
- ⚠️ **Breaking changes** - Tailwind v4, different component structure

### Recommended Action
1. **Keep current frontend** for immediate production use
2. **Complete backend integration** in new frontend before swap
3. **Add Docker support** to new frontend
4. **Implement testing** in new frontend
5. **Performance test** before deploying (bundle size analysis)
6. **Gradual migration** with parallel deployments if possible
