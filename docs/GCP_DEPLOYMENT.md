# Vecinita GCP Deployment Guide

Complete guide for deploying Vecinita to Google Cloud Platform with auto-restart, monitoring, and alerting.

## Architecture Overview

Vecinita on GCP consists of:

- **4 Cloud Run Services**:
  - `vecinita-embedding` - Text embeddings service (1GB RAM, min 1 instance)
  - `vecinita-agent` - RAG Q&A orchestration (512MB RAM, scale to zero)
  - `vecinita-frontend` - React UI with Nginx (256MB RAM, scale to zero)
  - `vecinita-scraper` - Web scraping job (2GB RAM, Cloud Run Job)

- **Cloud Scheduler** - Daily cron job triggering scraper at 2 AM UTC
- **Cloud Monitoring** - Dashboard, uptime checks, and alerts
- **Secret Manager** - Secure storage for API keys and credentials
- **Artifact Registry** - Docker image repository

### Service Dependencies

```
User → Frontend (Nginx/React)
        ↓ HTTP
     Agent (FastAPI/LangGraph)
        ↓ HTTP
     Embedding Service (sentence-transformers)
        ↓ Vector Search
     Supabase PostgreSQL (pgvector)
        ↑
     Scraper (Playwright) → Embedding Service
```

## Prerequisites

### Required Tools

1. **Google Cloud SDK (gcloud)**
   ```bash
   # Install from: https://cloud.google.com/sdk/docs/install
   # Verify installation:
   gcloud --version
   ```

2. **Docker**
   ```bash
   # Install from: https://docs.docker.com/get-docker/
   # Verify installation:
   docker --version
   ```

3. **GCP Account & Project**
   - Active GCP account with billing enabled
   - New or existing GCP project
   - Project Owner or Editor role

### Required Secrets

You need the following from your existing Supabase setup:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Supabase anon or service role key
- At least one LLM API key:
  - `GROQ_API_KEY` (recommended) - Free tier available
  - `OPENAI_API_KEY` - For GPT models
  - `DEEPSEEK_API_KEY` - Alternative LLM provider

Optional secrets:
- `DATABASE_URL` - Direct PostgreSQL connection (for advanced use)
- `TAVILY_API_KEY` - Web search functionality
- `LANGSMITH_API_KEY` - Tracing and monitoring

## Quick Start Deployment

### Step 1: Clone and Configure

```bash
# Clone repository
git clone https://github.com/acadiagit/vecinita.git
cd vecinita

# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-east1"  # or your preferred region
export ALERT_EMAIL="your-email@example.com"  # for alerts
```

### Step 2: Setup Secrets

Run the secrets setup script:

```bash
# Linux/Mac
./setup_gcp_secrets.sh

# Windows
.\setup_gcp_secrets.ps1
```

Follow the prompts to enter all required secrets. This creates secrets in GCP Secret Manager.

### Step 3: Deploy All Services

Run the deployment script:

```bash
# Linux/Mac
./deploy_to_gcp.sh

# Windows
.\deploy_to_gcp.ps1
```

This script will:
1. Enable required GCP APIs
2. Create Artifact Registry repository
3. Build and push Docker images
4. Deploy all services to Cloud Run
5. Setup Cloud Scheduler for scraper
6. Configure monitoring and uptime checks

**Deployment time:** ~15-20 minutes for first deployment

### Step 4: Verify Deployment

After deployment completes, you'll see service URLs:

```
Services deployed:
  • Embedding: https://vecinita-embedding-xxxxx-ue.a.run.app
  • Agent: https://vecinita-agent-xxxxx-ue.a.run.app
  • Frontend: https://vecinita-frontend-xxxxx-ue.a.run.app
  • Scraper: Cloud Run Job (scheduled daily at 2 AM UTC)
```

Test each service:

```bash
# Test embedding service
curl https://vecinita-embedding-xxxxx-ue.a.run.app/health

# Test agent service
curl https://vecinita-agent-xxxxx-ue.a.run.app/health

# Test frontend (in browser)
open https://vecinita-frontend-xxxxx-ue.a.run.app
```

## Detailed Configuration

### Service Resource Allocation

| Service | CPU | Memory | Min Instances | Max Instances | Cold Start |
|---------|-----|--------|---------------|---------------|------------|
| Embedding | 1 vCPU | 1GB | 1 | 10 | N/A (always on) |
| Agent | 1 vCPU | 512MB | 0 | 10 | ~5-10s |
| Frontend | 1 vCPU | 256MB | 0 | 10 | ~2-3s |
| Scraper (Job) | 2 vCPU | 2GB | - | - | Runs on schedule |

**Why min instances for embedding?**
- Model loading takes 20-40s on cold start
- Keeping 1 instance warm ensures fast response times
- Cost: ~$10-15/month for always-on instance

### Health Checks Configuration

All services have comprehensive health checks:

- **Liveness Probe** - Restarts container if unhealthy
  - Check interval: 30s
  - Timeout: 10s
  - Failure threshold: 3 failures = restart

- **Readiness Probe** - Controls traffic routing
  - Check interval: 10s
  - Timeout: 5s
  - Failure threshold: 3 failures = remove from load balancer

- **Startup Probe** - Allows longer startup time
  - Embedding: 2 minutes (model loading)
  - Agent: 1 minute
  - Frontend: 30 seconds

### Auto-Restart Policy

All Cloud Run services have `restart-policy: always`:
- Container crashes → Automatic restart
- Failed health checks → Automatic restart
- OOM (Out of Memory) → Automatic restart with logging
- Platform updates → Zero-downtime rolling restart

## Monitoring & Alerting

### Cloud Monitoring Dashboard

Access at: https://console.cloud.google.com/monitoring/dashboards

Dashboard includes:
- Request count per service
- Response latency (p95)
- CPU utilization with thresholds (80%, 90%)
- Memory utilization with thresholds (80%, 90%)
- Error rate (5xx responses)
- Active instance count
- Scraper job execution status
- Service health scorecards

### Uptime Checks

Automated health monitoring for all services:
- Check frequency: Every 60 seconds
- Timeout: 10 seconds
- Locations: Multi-region (automatic)
- Endpoint: `/health` on each service

### Alert Policies

Create alerts via Console or Terraform (`gcp/monitoring-alerts.tf`):

1. **High Error Rate** - >5% 5xx responses for 5 minutes
2. **High Memory** - >85% memory usage for 3 minutes
3. **High CPU** - >85% CPU usage for 5 minutes
4. **Service Down** - Failed health checks for 5 minutes
5. **High Latency** - p95 latency >5 seconds for 5 minutes
6. **Scraper Failure** - Job execution failed

Setup alerts:
```bash
# Using Terraform
cd gcp
terraform init
terraform apply

# Or manually in Console
# https://console.cloud.google.com/monitoring/alerting
```

### Viewing Logs

**Real-time logs:**
```bash
# View agent logs
gcloud run logs tail vecinita-agent --region=us-east1

# View scraper job logs
gcloud run jobs logs tail vecinita-scraper --region=us-east1

# Filter for errors only
gcloud run logs tail vecinita-agent --region=us-east1 --filter='severity>=ERROR'
```

**Logs Explorer (Console):**
https://console.cloud.google.com/logs/query

Advanced queries:
```
# Find all 5xx errors
resource.type="cloud_run_revision"
httpRequest.status>=500

# Find slow requests (>2s)
resource.type="cloud_run_revision"
httpRequest.latency>"2s"

# Scraper errors
resource.type="cloud_run_job"
resource.labels.job_name="vecinita-scraper"
severity>=ERROR
```

## Manual Operations

### Triggering Scraper Manually

```bash
# Trigger scraper job immediately
gcloud run jobs execute vecinita-scraper --region=us-east1

# View execution status
gcloud run jobs executions list --job=vecinita-scraper --region=us-east1
```

### Updating Services

**Update single service:**
```bash
# Rebuild and deploy agent
docker build -f backend/Dockerfile -t us-east1-docker.pkg.dev/$PROJECT_ID/vecinita/vecinita-agent:latest backend
docker push us-east1-docker.pkg.dev/$PROJECT_ID/vecinita/vecinita-agent:latest
gcloud run deploy vecinita-agent --image=us-east1-docker.pkg.dev/$PROJECT_ID/vecinita/vecinita-agent:latest --region=us-east1
```

**Redeploy all services:**
```bash
./deploy_to_gcp.sh
```

### Scaling Services

```bash
# Increase max instances for agent during high traffic
gcloud run services update vecinita-agent \
  --region=us-east1 \
  --max-instances=20

# Add min instances to frontend (prevent cold starts)
gcloud run services update vecinita-frontend \
  --region=us-east1 \
  --min-instances=1

# Increase memory for embedding service
gcloud run services update vecinita-embedding \
  --region=us-east1 \
  --memory=2Gi
```

### Managing Secrets

```bash
# Update a secret
echo "new-api-key" | gcloud secrets versions add groq-api-key --data-file=-

# View secret value (requires permissions)
gcloud secrets versions access latest --secret=groq-api-key

# List all secrets
gcloud secrets list

# Delete old secret versions (keep only latest 3)
gcloud secrets versions destroy VERSION_NUMBER --secret=SECRET_NAME
```

### Pausing/Resuming Scraper

```bash
# Pause scraper (skip scheduled runs)
gcloud scheduler jobs pause vecinita-daily-scraper --location=us-east1

# Resume scraper
gcloud scheduler jobs resume vecinita-daily-scraper --location=us-east1
```

## Cost Optimization

### Expected Monthly Costs

**With current configuration:**
- Cloud Run (embedding always-on): ~$10-15/month
- Cloud Run (agent/frontend scale-to-zero): ~$0-5/month (depends on traffic)
- Cloud Scheduler: $0.10/month (1 job)
- Secret Manager: $0.06/month (6 secrets)
- Artifact Registry: ~$0.10/month (storage)
- Cloud Monitoring: Free tier sufficient
- **Total: ~$10-20/month**

**Free tier allowances (per month):**
- Cloud Run: 2M requests, 360k GB-seconds, 180k vCPU-seconds
- Cloud Monitoring: 150 MB logs ingestion
- Secret Manager: 6 active secrets
- Artifact Registry: 0.5 GB storage

### Cost Reduction Strategies

1. **Scale embedding to zero** (increases cold start latency by 20-40s):
   ```bash
   gcloud run services update vecinita-embedding --min-instances=0 --region=us-east1
   ```
   Savings: ~$10-15/month

2. **Reduce scraper frequency** (weekly instead of daily):
   ```bash
   gcloud scheduler jobs update http vecinita-daily-scraper --schedule="0 2 * * 0" --location=us-east1
   ```
   Savings: Minimal, but reduces data processing

3. **Use Cloud Storage CDN for frontend** (serve static assets from bucket):
   - Deploy frontend to Cloud Storage + CDN
   - Savings: ~$1-2/month
   - Trade-off: More complex deployment

4. **Migrate to local embeddings in agent** (remove embedding service):
   - Combine embedding logic into agent service
   - Savings: ~$10-15/month
   - Trade-off: Agent uses more memory (1GB vs 512MB)

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
gcloud run logs tail SERVICE_NAME --region=us-east1
```

**Common issues:**
- Missing secrets → Verify secrets exist and have correct IAM permissions
- Memory OOM → Increase memory allocation
- Health check failures → Check `/health` endpoint returns 200
- Port mismatch → Ensure container listens on `PORT` env var

**Verify secrets access:**
```bash
# Check service account has secretAccessor role
gcloud secrets get-iam-policy supabase-url
```

### High Latency

**Check dashboard:**
- CPU/Memory utilization →If >80%, increase resources
- Request count → May need to increase max instances
- Cold starts → Consider increasing min instances

**Enable request tracing:**
Add `LANGSMITH_API_KEY` to track request flow through services.

### Scraper Job Fails

**View job logs:**
```bash
gcloud run jobs executions logs EXECUTION_ID --job=vecinita-scraper --region=us-east1
```

**Common issues:**
- Timeout (2 hour limit) → Split URLs into multiple jobs
- Memory OOM → Increase memory to 4GB
- Playwright browser crashes → Add `--no-sandbox` flag (already configured)
- Rate limiting → Adjust `RATE_LIMIT_DELAY` in scraper code

### Service Repeatedly Restarting

**Check restart history:**
```bash
gcloud run revisions list --service=SERVICE_NAME --region=us-east1
```

**Common causes:**
- Failed health checks → Check `/health` endpoint
- Memory leaks → Monitor memory over time, look for gradual increase
- Unhandled exceptions → Check logs for Python tracebacks
- Database connection issues → Verify Supabase credentials

**Temporarily disable health checks for debugging:**
```bash
gcloud run services update SERVICE_NAME --no-use-http2 --region=us-east1
```

### High Costs

**Analyze costs:**
```bash
# View cost breakdown
gcloud billing accounts list
# Then view in Console: https://console.cloud.google.com/billing
```

**Top cost drivers:**
1. Embedding service always-on instances
2. Excessive request volume
3. Large Docker images (slow builds, high storage)

**Quick fixes:**
- Scale embedding to zero (see Cost Optimization)
- Enable Cloud CDN for frontend
- Clean up old container images in Artifact Registry

## Advanced Topics

### Custom Domain Setup

1. **Verify domain ownership:**
   ```bash
   gcloud domains verify DOMAIN_NAME
   ```

2. **Map domain to service:**
   ```bash
   gcloud run services update vecinita-frontend \
     --region=us-east1 \
     --add-domain-mapping=app.yourdomain.com
   ```

3. **Add DNS records** (provided by GCP after mapping)

4. **Enable Cloud CDN:**
   ```bash
   gcloud compute backend-services update vecinita-frontend-backend \
     --enable-cdn
   ```

### CI/CD with GitHub Actions

Create `.github/workflows/deploy-gcp.yml`:

```yaml
name: Deploy to GCP

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
      
      - name: Deploy to Cloud Run
        run: ./deploy_to_gcp.sh
```

### VPC Connector (Private Networking)

For private database connections:

```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create vecinita-connector \
  --region=us-east1 \
  --range=10.8.0.0/28

# Update service to use connector
gcloud run services update vecinita-agent \
  --region=us-east1 \
  --vpc-connector=vecinita-connector
```

### Multi-Region Deployment

Deploy to multiple regions for high availability:

```bash
# Deploy to us-central1
export GCP_REGION=us-central1
./deploy_to_gcp.sh

# Setup global load balancer
gcloud compute url-maps create vecinita-lb \
  --default-service=vecinita-frontend
```

## Migration from Render

### Data Migration

Your Supabase database doesn't need migration - it's already in the cloud!

### Environment Variables Mapping

| Render | GCP Secret Manager |
|--------|-------------------|
| SUPABASE_URL | supabase-url |
| SUPABASE_KEY | supabase-key |
| GROQ_API_KEY | groq-api-key |
| TAVILY_API_KEY | tavily-api-key |
| LANGSMITH_API_KEY | langsmith-api-key |

### URL Updates

After deployment, update:
1. Frontend build with new agent URL
2. Agent environment with new embedding URL
3. Any external integrations pointing to Render URLs

### DNS Cutover

1. Deploy to GCP (services get `*.run.app` URLs)
2. Test thoroughly with new URLs
3. Update DNS records to point to GCP
4. Monitor both platforms during transition
5. Decommission Render services after 24 hours

## Support & Resources

- **GCP Documentation:** https://cloud.google.com/run/docs
- **Cloud Monitoring:** https://cloud.google.com/monitoring/docs
- **Cost Calculator:** https://cloud.google.com/products/calculator
- **GCP Free Tier:** https://cloud.google.com/free

- **Vecinita Issues:** https://github.com/acadiagit/vecinita/issues
- **Architecture Docs:** See [docs/ARCHITECTURE_MICROSERVICE.md](ARCHITECTURE_MICROSERVICE.md)

## Security Best Practices

1. **Use service accounts with minimal permissions**
2. **Rotate secrets regularly** (every 90 days)
3. **Enable audit logging** for compliance
4. **Use VPC connectors** for private database access
5. **Set up binary authorization** for signed containers
6. **Enable Cloud Armor** for DDoS protection (if using load balancer)
7. **Regular security scanning** of container images

---

**Next Steps:**
1. Run `./setup_gcp_secrets.sh` to configure secrets
2. Run `./deploy_to_gcp.sh` to deploy services
3. Setup alerts in Cloud Monitoring Console
4. Configure custom domain (optional)
5. Monitor costs in first week and optimize
