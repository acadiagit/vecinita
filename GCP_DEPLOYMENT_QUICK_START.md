# GCP Cloud Run Deployment Quick Start

## Current Status
✅ Local stack running and verified  
✅ Frontend configuration fixed (Nginx proxies)  
✅ Frontend submodule updated to dev branch  
✅ All services healthy (Agent, Embedding, PostgreSQL, PostgREST)  

## Quick Start: Deploy to GCP in 5 Steps

### Step 1: Install gcloud CLI (if not already installed)
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud --version  # Verify installation
```

### Step 2: Authenticate to GCP
```bash
gcloud auth login
# Browser will open for Google account authentication

# Set your GCP project ID (replace with actual project)
gcloud config set project vecinita-project-id
gcloud config list  # Verify configuration
```

### Step 3: Create GCP Secrets (required for deployment)
```bash
# Create secrets in Google Secret Manager
# You'll be prompted to enter values for each

gcloud secrets create SUPABASE_URL --data-file=- << 'EOF'
https://your-project.supabase.co
EOF

gcloud secrets create SUPABASE_KEY --data-file=- << 'EOF'
your-supabase-anon-key
EOF

gcloud secrets create GROQ_API_KEY --data-file=- << 'EOF'
your-groq-api-key
EOF

gcloud secrets create HUGGINGFACE_TOKEN --data-file=- << 'EOF'
your-huggingface-token
EOF

# Verify secrets created
gcloud secrets list
```

### Step 4: Run Deployment Script
```bash
cd /workspaces/vecinita

# Make script executable
chmod +x backend/scripts/deploy_gcp.sh

# Deploy all services (embedding + scraper)
./backend/scripts/deploy_gcp.sh --all

# Or deploy individually:
# ./backend/scripts/deploy_gcp.sh --embedding  # Just embedding service
# ./backend/scripts/deploy_gcp.sh --scraper    # Just scraper job
```

**Script will:**
- ✅ Build container images in Cloud Build
- ✅ Deploy Embedding Service to Cloud Run
- ✅ Deploy Scraper as Cloud Run Job
- ✅ Create Cloud Scheduler for daily execution (2 AM UTC)
- ✅ Validate all deployments with health checks
- ✅ Output EMBEDDING_SERVICE_URL for use in production agent

### Step 5: Verify Deployment
```bash
# Check Cloud Run services
gcloud run services list --region=us-central1

# Check Cloud Run jobs
gcloud run jobs list --region=us-central1

# View recent deployments
gcloud builds log --limit=100

# Monitor Cloud Scheduler
gcloud scheduler jobs list --location=us-central1
```

## Configuration Files Used

- `backend/scripts/deploy_gcp.sh` - Main deployment orchestration
- `backend/Dockerfile.embedding` - Embedding service container image
- `backend/Dockerfile` - Agent service container image (for scraper reference)
- `backend/Dockerfile.scraper` - Scraper service container image
- `.env.prod` - Production environment variables template

## Expected Output

After successful `deploy_gcp.sh --all`:

```
✅ Cloud Build completed
✅ Embedding Service deployed: https://embedding-xxx.run.app
✅ Scraper Job created: vecinita-scraper
✅ Cloud Scheduler configured: Daily at 02:00 UTC
✅ EMBEDDING_SERVICE_URL: https://embedding-xxx.run.app

Production Agent Configuration:
EMBEDDING_SERVICE_URL=https://embedding-xxx.run.app
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
GROQ_API_KEY=your-key
```

## Troubleshooting

**Error: "gcloud: command not found"**
→ Install gcloud SDK from https://cloud.google.com/sdk/docs/install

**Error: "No GCP project configured"**
→ Run `gcloud config set project <PROJECT_ID>`

**Error: "Permission denied"**
→ Ensure service account has Cloud Run Editor and Secret Manager roles

**Error: "Secret not found"**
→ Verify secrets were created: `gcloud secrets list`

**Building timeout**
→ Increase timeout in Cloud Build settings or split deployment into phases

## Monitoring After Deployment

```bash
# Stream service logs
gcloud run services describe embedding-service --region=us-central1
gcloud run jobs describe vecinita-scraper --region=us-central1

# View execution history
gcloud scheduler jobs run vecinita-scraper-trigger --region=us-central1

# Check scheduler logs
gcloud functions logs read --limit=50
```

## Next Steps After Deployment

1. **Update Agent Configuration**:
   - Set `EMBEDDING_SERVICE_URL` to Cloud Run URL
   - Deploy agent backend to Cloud Run or managed platform

2. **Update Frontend** (if applicable):
   - Update API endpoints to point to production agent
   - Configure CORS if needed

3. **Monitor and Scale**:
   - Use Cloud Monitoring for metrics
   - Adjust Cloud Run min/max instances as needed
   - Monitor Cloud Scheduler execution

## Documentation

- Full guide: `docs/GCP_CLOUD_RUN_DEPLOYMENT.md`
- Architecture: `docs/FULL_STACK_RESTORATION_COMPLETE.md`
- Migration details: `MIGRATION_MODAL_TO_CLOUD_RUN.md`

---

**Ready to deploy? Run Step 2 above to begin!**
