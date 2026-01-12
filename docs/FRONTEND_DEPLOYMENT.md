# Frontend Deployment Guide

Complete guide for deploying the new Vecinita frontend (TypeScript/Vite 6/Tailwind v4) to production.

## Prerequisites

- Docker & Docker Compose installed
- Node.js 18+ (for local builds)
- `VITE_BACKEND_URL` environment variable set
- Backend service (vecinita-agent) running or accessible

## Local Development

### 1. Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
```

### 2. Configure Backend URL

Edit `.env.local`:
```env
# For local development
VITE_BACKEND_URL=http://localhost:8000

# For Docker Compose
# VITE_BACKEND_URL=http://vecinita-agent:8000
```

### 3. Start Dev Server

```bash
npm run dev
```

Dev server will run at `http://localhost:5173` with hot reload and dev proxy to backend.

### 4. Test Backend Integration

1. Open browser console (F12)
2. Should see config loading from `/config` endpoint
3. Should see provider/model dropdowns populated
4. Try asking a question

## Docker Build & Deployment

### Local Docker Build

```bash
# From root vecinita directory
docker build -f frontend/Dockerfile -t vecinita-frontend:latest \
  --build-arg VITE_BACKEND_URL=http://localhost:8000 \
  frontend/

# For production build
docker build -f frontend/Dockerfile -t vecinita-frontend:prod \
  --build-arg VITE_BACKEND_URL=https://api.vecinita.example.com \
  frontend/

# Run container
docker run -p 3000:80 vecinita-frontend:latest
```

### Docker Compose Deployment

```bash
# From root directory
docker-compose up frontend

# Or background
docker-compose up -d frontend

# View logs
docker-compose logs -f frontend

# Stop
docker-compose down
```

### Environment Variables for Docker Build

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_BACKEND_URL` | `http://localhost:8000` | Backend API endpoint |

**Important:** Set `VITE_BACKEND_URL` at **build time**, not runtime.

```bash
# Correct
docker build --build-arg VITE_BACKEND_URL=https://api.prod.example.com ...

# Incorrect (won't work)
docker run -e VITE_BACKEND_URL=https://api.prod.example.com vecinita-frontend
```

## Staging Deployment

### 1. Build for Staging

```bash
docker build -f frontend/Dockerfile -t vecinita-frontend:staging \
  --build-arg VITE_BACKEND_URL=https://api-staging.vecinita.example.com \
  frontend/

docker tag vecinita-frontend:staging YOUR_REGISTRY/vecinita-frontend:staging
docker push YOUR_REGISTRY/vecinita-frontend:staging
```

### 2. Deploy to Staging

Update staging docker-compose.yml:
```yaml
services:
  frontend:
    image: YOUR_REGISTRY/vecinita-frontend:staging
    ports:
      - "3000:80"
    depends_on:
      vecinita-agent:
        condition: service_healthy
```

Then:
```bash
docker-compose -f docker-compose.staging.yml up -d
```

### 3. Test Staging Deployment

1. Visit `http://staging.vecinita.example.com`
2. Open browser console, verify no errors
3. Test provider/model selection
4. Send test questions
5. Verify sources appear with links
6. Test language switching
7. Test dark mode toggle
8. Test accessibility panel

## Production Deployment

### 1. Checklist Before Production

- ☑️ Frontend builds successfully
- ☑️ All tests pass (`npm run test:e2e`)
- ☑️ No console errors
- ☑️ Bundle size acceptable (~200KB)
- ☑️ Backend API responding to requests
- ☑️ SSE streaming working
- ☑️ Staging deployment verified

### 2. Build for Production

```bash
# Build with production backend URL
docker build -f frontend/Dockerfile -t vecinita-frontend:1.0.0 \
  --build-arg VITE_BACKEND_URL=https://api.vecinita.example.com \
  frontend/

# Tag and push to registry
docker tag vecinita-frontend:1.0.0 YOUR_REGISTRY/vecinita-frontend:1.0.0
docker tag vecinita-frontend:1.0.0 YOUR_REGISTRY/vecinita-frontend:latest
docker push YOUR_REGISTRY/vecinita-frontend:1.0.0
docker push YOUR_REGISTRY/vecinita-frontend:latest
```

### 3. Deploy to Production

Option A: Docker Compose
```bash
# Update docker-compose.yml
docker-compose pull frontend
docker-compose up -d frontend

# Verify
docker-compose ps
docker-compose logs -f frontend
```

Option B: Kubernetes
```bash
kubectl set image deployment/vecinita-frontend \
  frontend=YOUR_REGISTRY/vecinita-frontend:1.0.0 \
  --record
```

Option C: Cloud Platform (Render, Vercel, etc.)
- Set environment variables in platform UI
- Trigger deployment from Git or manual deploy
- Configure build command: `npm run build`
- Configure start command: `npm run preview` (or `nginx -g "daemon off;"` for Docker)

### 4. Post-Deployment Verification

1. **Health Check**
   ```bash
   curl https://vecinita.example.com/health
   # Should return 200 OK
   ```

2. **Smoke Tests**
   ```bash
   # Ask test question
   curl "https://api.vecinita.example.com/config"
   curl "https://api.vecinita.example.com/ask-stream?query=test&lang=en&provider=groq&model=llama3.1-8b"
   ```

3. **Browser Tests**
   - Load homepage
   - Check console for errors (F12)
   - Select provider/model
   - Ask a question
   - Verify response appears
   - Check sources render correctly

4. **Performance Check**
   ```bash
   # Lighthouse
   lighthouse https://vecinita.example.com

   # Response times
   time curl https://vecinita.example.com
   ```

## Gradual Rollout

See [FRONTEND_GRADUAL_ROLLOUT.md](./FRONTEND_GRADUAL_ROLLOUT.md) for detailed rollout strategy.

Quick version:

### Week 1-2: Canary (5% of users)
```nginx
upstream frontend_split {
  server old-frontend:3000 weight=95;
  server new-frontend:80 weight=5;
}
```

### Week 3-4: Early Access (25% of users)
```nginx
upstream frontend_split {
  server old-frontend:3000 weight=75;
  server new-frontend:80 weight=25;
}
```

### Week 5-6: Broad Beta (50% of users)
```nginx
upstream frontend_split {
  server old-frontend:3000 weight=50;
  server new-frontend:80 weight=50;
}
```

### Week 7+: Full Rollout (100% of users)
```nginx
upstream frontend_split {
  server old-frontend:3000 weight=0;
  server new-frontend:80 weight=100;
}
```

## Monitoring

### Key Metrics

Track these in your monitoring system:

```
Error Rates
- HTTP 5xx errors
- HTTP 4xx errors (especially 404, 500)
- JavaScript console errors
- SSE connection failures

Performance
- Page load time (First Contentful Paint)
- Time to Interactive
- Largest Contentful Paint
- Cumulative Layout Shift
- Response time for /ask-stream

Functionality
- % questions answered successfully
- Average response time
- SSE streaming success rate
- Provider/model selection usage
- Language selection distribution

Availability
- Uptime % (99.9% target)
- Error rate % (target <0.1%)
```

### Nginx Access Logs

```bash
# View real-time logs
docker-compose logs -f frontend

# Parse upstream routing
docker exec vecinita-frontend nginx -V

# Check config
docker exec vecinita-frontend cat /etc/nginx/conf.d/default.conf
```

## Troubleshooting

### Issue: Frontend shows "Backend connection error"

**Causes:**
1. Backend not running
2. `VITE_BACKEND_URL` incorrect
3. CORS issues

**Fix:**
```bash
# Check backend is running
curl $VITE_BACKEND_URL/health

# Check frontend config
docker exec vecinita-frontend printenv | grep VITE

# Check browser console for exact error
```

### Issue: Provider/model dropdown is empty

**Cause:** `/config` endpoint not responding

**Fix:**
```bash
# Test /config endpoint
curl "$VITE_BACKEND_URL/config"

# Should return JSON with providers and models
```

### Issue: Streaming responses don't work

**Cause:** SSE or proxy buffering issue

**Fix:**
```nginx
# Ensure proxy_buffering is off
proxy_buffering off;
proxy_cache off;

# And in docker-compose health check
proxy_read_timeout 3600s;
```

### Issue: Build fails with "out of memory"

**Cause:** Node running out of memory

**Fix:**
```bash
# Increase Node memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

### Issue: Docker image too large

**Cause:** Node modules or build artifacts in image

**Fix:**
- Add to `.dockerignore`:
  ```
  node_modules
  .git
  .gitignore
  dist
  build
  .venv
  __pycache__
  .pytest_cache
  ```
- Use multi-stage build (already in Dockerfile)

## Rollback Procedure

If production issues occur:

### Immediate Rollback

```bash
# Revert to previous image tag
docker-compose down frontend
docker-compose up -d frontend  # Uses 'latest' tag, update to previous version

# Or specify version explicitly
docker pull YOUR_REGISTRY/vecinita-frontend:previous-version
docker run -p 3000:80 YOUR_REGISTRY/vecinita-frontend:previous-version
```

### Gradual Rollback

If using Nginx with weighted routing:

```nginx
# Reduce new frontend weight
upstream frontend_split {
  server old-frontend:3000 weight=75;  # Increased from 50
  server new-frontend:80 weight=25;    # Decreased from 50
}
```

Then `docker-compose restart nginx`.

## Maintenance

### Regular Updates

```bash
# Check for vulnerabilities
npm audit

# Update dependencies
npm update

# Rebuild and test
npm run build
npm run test

# Commit changes
git commit -am "chore: update dependencies"
```

### Log Rotation

Configure Docker daemon for log rotation:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Backup

Frontend is stateless, but preserve:
- Environment variables
- Custom CSS/themes
- Deployment configuration files

```bash
# Backup docker-compose
git commit docker-compose.yml

# Backup environment
git commit .env.production (if in repo)
```

## Support & Debugging

### Access frontend container shell

```bash
docker-compose exec frontend sh
```

### View Nginx configuration inside container

```bash
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

### Check network connectivity from frontend to backend

```bash
docker-compose exec frontend wget http://vecinita-agent:8000/health
```

### Clear browser cache (for end users)

Instruct users:
1. Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Open DevTools > Settings > Network > Check "Disable cache"
3. Close and reopen DevTools, refresh page

## References

- Frontend README: [frontend/README_INTEGRATION.md](../frontend/README_INTEGRATION.md)
- Gradual Rollout: [FRONTEND_GRADUAL_ROLLOUT.md](./FRONTEND_GRADUAL_ROLLOUT.md)
- Dockerfile: [frontend/Dockerfile](../frontend/Dockerfile)
- Docker Compose: [docker-compose.yml](../docker-compose.yml)

---

**Last Updated:** January 2026  
**Version:** 1.0 (TypeScript/Vite 6/Tailwind v4)
