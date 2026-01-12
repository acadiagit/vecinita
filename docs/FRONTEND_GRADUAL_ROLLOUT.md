# Frontend Gradual Rollout Strategy

## Overview

This document outlines the strategy for gradually rolling out the new TypeScript/Vite 6/Tailwind v4 frontend while maintaining the old JavaScript/Vite 5/Tailwind v3 frontend as a fallback.

## Rollout Methods

### 1. Feature Flag System (Client-Side)

**Implementation:** `src/lib/featureFlags.ts`

**Priority Order:**
1. URL query parameter: `?use_new_frontend=true` (manual override)
2. localStorage cookie: `use_new_frontend=true` (persisted preference)
3. Automatic distribution: Random 10% of users (default)

**Usage:**
```typescript
import { getFeatureFlag, evaluateFeatureFlag } from '@/lib/featureFlags';

const useNewFrontend = evaluateFeatureFlag(
  getFeatureFlag('use_new_frontend', 'percentage'),
  10 // 10% of users
);
```

**Advantages:**
- ✅ No server changes needed
- ✅ Per-user control via query params or cookies
- ✅ A/B testable
- ✅ Easy rollback (just change percentages)

**Disadvantages:**
- ❌ Doesn't work for public URLs (everyone gets old frontend)
- ❌ Requires known users for tracking

### 2. Nginx Upstream Routing (Server-Side)

**Implementation:** `docs/nginx.gradual-rollout.conf`

**How It Works:**
- Nginx routes requests based on weighted upstreams
- Cookie-based routing for per-user control
- Percentage-based split for automatic canary deployment

**Usage:**
```nginx
upstream frontend_split {
  # Week 1-2: 95% old, 5% new
  server old-frontend:3000 weight=95;
  server new-frontend:80 weight=5;
}
```

**Advantages:**
- ✅ Works for all users (no client-side logic)
- ✅ Cookie-based per-user overrides
- ✅ Deterministic routing (same user always gets same version)
- ✅ Weighted split for gradual rollout

**Disadvantages:**
- ❌ Requires Nginx reverse proxy setup
- ❌ Monitoring at reverse proxy level

### 3. Docker Compose Service Selection

**How It Works:**
- Run both frontends as separate services in docker-compose
- Use environment variable to select which frontend to expose on port 80

**Usage:**
```yaml
# docker-compose.yml
services:
  frontend:
    # Comment out to switch between versions
    build: ./frontend  # New TypeScript version
    # build: ./frontend-v1  # Old JavaScript version (if kept)
```

**Advantages:**
- ✅ Simple environment-based switching
- ✅ No proxying overhead
- ✅ Good for staging environments

**Disadvantages:**
- ❌ Binary choice (old vs new, not both running)
- ❌ Downtime during switchover

## Recommended Rollout Timeline

### Timeline

| Phase | Duration | New Frontend | Strategy | Users |
|-------|----------|--------------|----------|-------|
| **Canary** | Week 1-2 | 5-10% | Nginx weighted split | Canary testers |
| **Early Access** | Week 3-4 | 25% | Nginx weighted split | Early adopters |
| **Broad Beta** | Week 5-6 | 50% | Nginx weighted split | 50% of users |
| **Full Rollout** | Week 7+ | 100% | 100% to new frontend | All users |

### Weekly Checklist

**Canary Phase (Week 1-2):**
- ☑️ Deploy new frontend to staging
- ☑️ Run automated tests (vitest + Playwright)
- ☑️ Set Nginx weight: 95% old, 5% new
- ☑️ Monitor error rates, performance, SSE streaming
- ☑️ Gather feedback from canary testers
- ☑️ Fix critical bugs, iterate

**Early Access Phase (Week 3-4):**
- ☑️ Verify canary phase metrics look good
- ☑️ Set Nginx weight: 75% old, 25% new
- ☑️ Announce early access to beta testers
- ☑️ Monitor user-reported issues
- ☑️ Update backend `/config` endpoint if needed
- ☑️ Prepare communication for broader rollout

**Broad Beta Phase (Week 5-6):**
- ☑️ Verify early access metrics acceptable
- ☑️ Set Nginx weight: 50% old, 50% new
- ☑️ Enable feature flag for wider audience
- ☑️ Monitor performance at scale
- ☑️ Conduct load testing
- ☑️ Prepare full rollout messaging

**Full Rollout Phase (Week 7+):**
- ☑️ Set Nginx weight: 0% old, 100% new
- ☑️ Monitor for 24-48 hours
- ☑️ Archive old frontend if stable
- ☑️ Update documentation

## Monitoring & Rollback

### Key Metrics to Monitor

```
Error Rates
├── 5xx errors (backend)
├── 4xx errors (client-side)
├── JavaScript console errors
└── SSE streaming failures

Performance
├── Page load time (CLS, LCP, FID)
├── Time to first question
├── Time to first response
└── Bundle size

Functionality
├── Questions sent successfully
├── Responses received
├── Sources displayed correctly
├── Provider/model selection working
└── Language switching working

User Experience
├── Session duration
├── Questions per session
├── Provider/model usage distribution
└── Error recovery attempts
```

### Rollback Triggers

Automatically rollback if:
- ❌ Error rate >1% (vs baseline <0.1%)
- ❌ Page load time +50% slower than baseline
- ❌ SSE streaming failures >5%
- ❌ Provider/model selection broken
- ❌ Critical security issue found

**Rollback Steps:**
```nginx
# docker/nginx.conf - revert weight
upstream frontend_split {
  server old-frontend:3000 weight=100;
  server new-frontend:80 weight=0;
}

# Restart Nginx
docker-compose restart nginx
```

## Implementation Checklist

- [ ] **Phase 1: Setup**
  - [ ] Deploy new frontend to staging
  - [ ] Set up monitoring dashboards
  - [ ] Configure Nginx routing
  - [ ] Brief canary testers
  
- [ ] **Phase 2: Canary Deployment**
  - [ ] Deploy new frontend to production
  - [ ] Set Nginx weight: 95% old, 5% new
  - [ ] Monitor metrics for 48+ hours
  - [ ] Gather canary tester feedback
  
- [ ] **Phase 3: Gradual Rollout**
  - [ ] Increase weight incrementally (25% → 50% → 75% → 100%)
  - [ ] Wait 48 hours between weight changes
  - [ ] Monitor metrics at each stage
  - [ ] Document issues and resolutions
  
- [ ] **Phase 4: Full Migration**
  - [ ] Achieve 100% new frontend traffic
  - [ ] Monitor for 72+ hours
  - [ ] Archive old frontend code (keep in Git history)
  - [ ] Update documentation and runbooks

## Feature Flag Strategy

Use client-side feature flags to decouple frontend deployment from feature availability:

```typescript
// src/lib/featureFlags.ts
export const DEFAULT_FEATURE_FLAGS = {
  NEW_FRONTEND: true,           // Fully rolled out
  STREAMING_RESPONSES: true,    // All users
  PROVIDER_SELECTION: true,     // All users
  EXPERIMENTAL_FEATURES: 'canary', // Canary only
};
```

**Benefits:**
- Feature releases independent of deployment
- A/B testing capabilities
- Quick feature toggles without redeployment
- Per-user control

## Communication Plan

### Week 0 (Announcement)
- 📧 Email: "Exciting UI improvements coming!"
- 💬 Forum post: Explain TypeScript/Vite upgrade benefits
- 📝 Release notes draft

### Week 2 (Early Access)
- 📧 Email: "You've been selected as an early tester!"
- 🐛 Bug report form
- 💬 Feedback channel

### Week 4 (Broader Access)
- 📧 Email: "New UI now available"
- 📣 Public announcement
- ✨ Release highlights

### Week 7+ (Full Rollout)
- 📣 "New UI is now default for all users"
- 📖 Documentation updated
- 🎉 Thank you message to beta testers

## Troubleshooting

### Issue: Users seeing old frontend even with flag set to new

**Cause:** Browser caching, CDN cache, or session affinity

**Solution:**
```javascript
// Force cache bust
window.location.reload(true);

// Or clear localStorage
localStorage.clear();

// Then retry
```

### Issue: New frontend failing for small percentage of users

**Cause:** Browser compatibility (very old browsers)

**Solution:**
1. Check error logs in browser console
2. Add browser compatibility polyfills if needed
3. Consider excluding users with old browsers

### Issue: Backend returning different responses to old vs new frontend

**Cause:** API endpoint differences or response format changes

**Solution:**
1. Update frontend API client to match backend spec
2. Version API endpoints: `/api/v1/ask-stream` vs `/api/v2/ask-stream`
3. Test both frontends against same backend

## References

- Feature Flags: `src/lib/featureFlags.ts`
- Nginx Config: `docs/nginx.gradual-rollout.conf`
- API Integration: `src/api/client.ts`
- Docker Compose: `docker-compose.yml`
- Frontend README: `frontend/README_INTEGRATION.md`
