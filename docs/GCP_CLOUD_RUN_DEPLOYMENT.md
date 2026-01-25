# Google Cloud Run Deployment Guide

**Migrated from Modal Labs to Google Cloud Run**

This guide walks you through deploying Vecinita services to Google Cloud Run for production use.

## Architecture

- **Embedding Service**: Cloud Run service (always-on or auto-scaling)
- **Scraper**: Cloud Run Job (on-demand batch execution)
- **Scheduler**: Cloud Scheduler triggers the scraper daily
- **Secrets**: Google Secret Manager stores credentials
- **Monitoring**: Cloud Logging and Cloud Monitoring

## Prerequisites

### 1. Install and Configure gcloud CLI

```bash
# Install gcloud (https://cloud.google.com/sdk/docs/install)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Or on macOS with Homebrew:
brew install --cask google-cloud-sdk

# Authenticate
gcloud auth login
gcloud auth application-default login
```

### 2. Set Default Project and Region

```bash
# List projects
gcloud projects list

# Set default project
gcloud config set project <PROJECT_ID>

# Set default region (e.g., us-central1, us-west1, europe-west1)
gcloud config set run/region us-central1
gcloud config set compute/region us-central1
```

### 3. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com \
  monitoring.googleapis.com
```

## Step 1: Create Secrets in Secret Manager

Store sensitive environment variables securely:

```bash
# Read from stdin interactively
gcloud secrets create SUPABASE_URL --replication-policy="automatic" --data-file=- << EOF
<paste-your-supabase-url-here>
EOF

gcloud secrets create SUPABASE_KEY --replication-policy="automatic" --data-file=- << EOF
<paste-your-supabase-anon-key-here>
EOF

gcloud secrets create GROQ_API_KEY --replication-policy="automatic" --data-file=- << EOF
<paste-your-groq-api-key-here>
EOF

# Optional: Store HuggingFace token if using local embeddings
gcloud secrets create HUGGINGFACE_TOKEN --replication-policy="automatic" --data-file=- << EOF
<paste-your-hf-token-here>
EOF

# Verify created secrets
gcloud secrets list
```

## Step 2: Create Service Account for Cloud Run

```bash
# Create service account
gcloud iam service-accounts create vecinita-cloud-run \
  --display-name="Vecinita Cloud Run Services"

# Get the service account email
SA_EMAIL=$(gcloud iam service-accounts list --filter="email~vecinita-cloud-run" --format="value(email)")
echo "Service Account: $SA_EMAIL"

# Grant Secret Manager access
gcloud secrets add-iam-policy-binding SUPABASE_URL \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding SUPABASE_KEY \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding GROQ_API_KEY \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding HUGGINGFACE_TOKEN \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor" 2>/dev/null || true
```

## Step 3: Deploy Embedding Service

The embedding service runs as a Cloud Run service, handling HTTP requests.

```bash
# Navigate to repo root
cd /path/to/vecinita

# Deploy using the GCP script (recommended)
./backend/scripts/deploy_gcp.sh --embedding

# Or deploy manually with detailed control
PROJECT_ID=$(gcloud config get-value project)
REGION=$(gcloud config get-value run/region)
SA_EMAIL=$(gcloud iam service-accounts list --filter="email~vecinita-cloud-run" --format="value(email)")

gcloud builds submit backend \
  --dockerfile=Dockerfile.embedding \
  --tag=gcr.io/$PROJECT_ID/vecinita-embedding \
  --project=$PROJECT_ID

gcloud run deploy vecinita-embedding \
  --image=gcr.io/$PROJECT_ID/vecinita-embedding \
  --region=$REGION \
  --project=$PROJECT_ID \
  --platform=managed \
  --allow-unauthenticated \
  --cpu=1 \
  --memory=1Gi \
  --port=8001 \
  --min-instances=1 \
  --max-instances=5 \
  --timeout=300 \
  --service-account=$SA_EMAIL \
  --set-env-vars=PYTHONUNBUFFERED=1 \
  --set-secrets=SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_KEY=SUPABASE_KEY:latest,GROQ_API_KEY=GROQ_API_KEY:latest
```

**After deployment:**

```bash
# Get the service URL
EMBEDDING_URL=$(gcloud run services describe vecinita-embedding --region=$REGION --format="value(status.url)")
echo "Embedding Service URL: $EMBEDDING_URL"

# Test the service
curl "$EMBEDDING_URL/health"

# View logs
gcloud run services logs read vecinita-embedding --limit=50
```

## Step 4: Deploy Scraper as Cloud Run Job

The scraper runs as a job, invoked on-demand or via scheduler.

```bash
# Deploy using the GCP script (recommended)
./backend/scripts/deploy_gcp.sh --scraper

# Or deploy manually
gcloud builds submit backend \
  --dockerfile=Dockerfile.scraper \
  --tag=gcr.io/$PROJECT_ID/vecinita-scraper \
  --project=$PROJECT_ID

gcloud run jobs create vecinita-scraper \
  --image=gcr.io/$PROJECT_ID/vecinita-scraper \
  --region=$REGION \
  --project=$PROJECT_ID \
  --cpu=2 \
  --memory=2Gi \
  --timeout=1800 \
  --service-account=$SA_EMAIL \
  --set-env-vars=PYTHONUNBUFFERED=1,EMBEDDING_SERVICE_URL=$EMBEDDING_URL \
  --set-secrets=SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_KEY=SUPABASE_KEY:latest
```

**Test the job manually:**

```bash
# Run the job once
gcloud run jobs execute vecinita-scraper --region=$REGION

# Monitor job execution
gcloud run jobs logs read vecinita-scraper --limit=100

# View job status
gcloud run jobs describe vecinita-scraper --region=$REGION
```

## Step 5: Set Up Cloud Scheduler (Optional)

Automatically trigger the scraper on a schedule.

```bash
# Create a daily schedule (2 AM UTC)
gcloud scheduler jobs create http vecinita-scraper-daily \
  --location=$REGION \
  --schedule="0 2 * * *" \
  --http-method=POST \
  --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/vecinita-scraper:run" \
  --oidc-service-account-email=$SA_EMAIL \
  --oidc-token-audience="https://$REGION-run.googleapis.com/"

# Verify the scheduler job
gcloud scheduler jobs list --location=$REGION

# Manually trigger (for testing)
gcloud scheduler jobs run vecinita-scraper-daily --location=$REGION

# View scheduler job logs
gcloud scheduler jobs describe vecinita-scraper-daily --location=$REGION
```

## Step 6: Update Agent to Use Cloud Run Embedding Service

Point your agent to the deployed embedding service.

### Option A: Environment Variable (for docker-compose)

```bash
# Export the embedding URL
export EMBEDDING_SERVICE_URL=$(gcloud run services describe vecinita-embedding --region=$REGION --format="value(status.url)")

# Restart the local agent with the Cloud Run embedding service
docker compose up -d vecinita-agent
```

### Option B: Update `.env.prod` Permanently

```bash
EMBEDDING_SERVICE_URL=$(gcloud run services describe vecinita-embedding --region=$REGION --format="value(status.url)")
sed -i "s|EMBEDDING_SERVICE_URL=.*|EMBEDDING_SERVICE_URL=$EMBEDDING_SERVICE_URL|" .env.prod
```

## Monitoring and Logs

### View Logs

```bash
# Embedding service logs
gcloud run services logs read vecinita-embedding --limit=100 --region=$REGION

# Scraper job logs
gcloud run jobs logs read vecinita-scraper --limit=100 --region=$REGION

# Real-time streaming
gcloud run services logs read vecinita-embedding --follow --region=$REGION
```

### Set Up Cloud Monitoring Alerts

```bash
# View metrics
gcloud monitoring metrics-descriptors list --filter="resource.type=cloud_run_revision"

# Create alerts via Cloud Console (more user-friendly)
# https://console.cloud.google.com/monitoring/alerting/policies
```

## Troubleshooting

### Service won't start

```bash
# Check build errors
gcloud builds log <BUILD_ID>

# Check deployment errors
gcloud run services describe vecinita-embedding --region=$REGION

# View detailed logs
gcloud run services logs read vecinita-embedding --limit=200 --region=$REGION
```

### Secret access denied

```bash
# Verify service account has secret accessor role
SA_EMAIL=$(gcloud iam service-accounts list --filter="email~vecinita-cloud-run" --format="value(email)")
gcloud secrets get-iam-policy SUPABASE_URL

# Re-grant access if needed
gcloud secrets add-iam-policy-binding SUPABASE_URL \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

### Cold starts taking too long

```bash
# Increase minimum instances for embedding service
gcloud run services update vecinita-embedding \
  --region=$REGION \
  --min-instances=1
```

### Scraper job timing out

```bash
# Increase timeout (max 3600 seconds = 1 hour)
gcloud run jobs update vecinita-scraper \
  --region=$REGION \
  --timeout=3600
```

## Cleanup and Teardown

```bash
# Delete the embedding service
gcloud run services delete vecinita-embedding --region=$REGION

# Delete the scraper job
gcloud run jobs delete vecinita-scraper --region=$REGION

# Delete the scheduler (if created)
gcloud scheduler jobs delete vecinita-scraper-daily --location=$REGION

# Delete images from container registry
gcloud container images delete gcr.io/$PROJECT_ID/vecinita-embedding --quiet
gcloud container images delete gcr.io/$PROJECT_ID/vecinita-scraper --quiet

# Delete service account
gcloud iam service-accounts delete vecinita-cloud-run@$PROJECT_ID.iam.gserviceaccount.com
```

## Cost Optimization

- **Embedding Service**: Use `--min-instances=0` for auto-scaling from zero (no cost when idle)
  - Trade-off: Cold starts (~5-15s) on first request
  - Alternative: Use `--min-instances=1` to keep service warm (~$7/month)

- **Scraper Job**: Runs on-demand; only charges for execution time

- **Cloud Scheduler**: Free tier includes 3 jobs; paid jobs at ~$0.40 per 1M executions

- **Secret Manager**: First 6 secrets free; $0.06 per secret per month after

## Next Steps

1. **Test the deployment:**
   ```bash
   curl "$(gcloud run services describe vecinita-embedding --region=$REGION --format='value(status.url)')/health"
   ```

2. **Monitor in Cloud Console:**
   - https://console.cloud.google.com/run

3. **Set up continuous deployment:**
   - Use Cloud Build triggers to auto-deploy on git commits

4. **Review IAM and security:**
   - Ensure `--allow-unauthenticated` is appropriate for your use case
   - Consider adding API authentication (API keys, OAuth 2.0) if public

5. **Plan for production:**
   - Add custom domains and SSL/TLS
   - Enable VPC connectors for private database access (if using private Supabase)
   - Set up backup and disaster recovery

## References

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Run Jobs Documentation](https://cloud.google.com/run/docs/create-jobs/quickstart)
- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
