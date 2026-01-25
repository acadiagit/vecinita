#!/bin/bash
# Deploy Vecinita services to Google Cloud Run
# Usage: ./backend/scripts/deploy_gcp.sh [--embedding] [--scraper] [--all]
# Requires: gcloud CLI installed and authenticated (gcloud auth login)
#           Project and region configured (gcloud config set project PROJECT_ID)

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================"
echo "Vecinita Google Cloud Run Deployment Script"
echo "======================================${NC}\n"

# Check prerequisites
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# Get current project and region
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
REGION=${REGION:-us-central1}

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No GCP project configured.${NC}"
    echo -e "  Run: ${BLUE}gcloud config set project <PROJECT_ID>${NC}"
    exit 1
fi

echo -e "${YELLOW}Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Image Registry: gcr.io/$PROJECT_ID"
echo ""

# Parse arguments
DEPLOY_EMBEDDING=false
DEPLOY_SCRAPER=false

if [ $# -eq 0 ]; then
    DEPLOY_EMBEDDING=true
    DEPLOY_SCRAPER=true
else
    for arg in "$@"; do
        case $arg in
            --embedding) DEPLOY_EMBEDDING=true ;;
            --scraper) DEPLOY_SCRAPER=true ;;
            --all) DEPLOY_EMBEDDING=true; DEPLOY_SCRAPER=true ;;
            *) echo "Unknown option: $arg"; exit 1 ;;
        esac
    done
fi

# Navigate to repo root
cd "$(dirname "$0")/../.."

# ============================================================================
# Deploy Embedding Service
# ============================================================================
if [ "$DEPLOY_EMBEDDING" = true ]; then
    echo -e "${BLUE}→ Building and deploying Embedding Service to Cloud Run...${NC}\n"
    
    if [ ! -f "backend/Dockerfile.embedding" ]; then
        echo -e "${RED}❌ Dockerfile.embedding not found${NC}"
        exit 1
    fi
    
    SERVICE_NAME="vecinita-embedding"
    IMAGE_URL="gcr.io/$PROJECT_ID/$SERVICE_NAME"
    
    echo "  Building Docker image: $IMAGE_URL..."
    gcloud builds submit backend \
        --dockerfile=Dockerfile.embedding \
        --tag=$IMAGE_URL \
        --project=$PROJECT_ID \
        --quiet
    
    echo -e "${GREEN}✓ Image built: $IMAGE_URL${NC}\n"
    
    echo "  Deploying to Cloud Run..."
    EMBEDDING_URL=$(gcloud run deploy $SERVICE_NAME \
        --image=$IMAGE_URL \
        --region=$REGION \
        --project=$PROJECT_ID \
        --platform=managed \
        --allow-unauthenticated \
        --cpu=1 \
        --memory=1Gi \
        --port=8001 \
        --min-instances=0 \
        --max-instances=5 \
        --timeout=300 \
        --set-env-vars=PYTHONUNBUFFERED=1 \
        --set-secrets=SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_KEY=SUPABASE_KEY:latest,GROQ_API_KEY=GROQ_API_KEY:latest \
        --format='value(status.url)' \
        --quiet)
    
    echo -e "${GREEN}✓ Embedding Service Deployed${NC}"
    echo -e "  URL: ${BLUE}$EMBEDDING_URL${NC}\n"
    
    # Test the service
    echo "  Testing health endpoint..."
    if curl -sSf "$EMBEDDING_URL/health" > /dev/null; then
        echo -e "${GREEN}  ✓ Health check passed${NC}\n"
    else
        echo -e "${YELLOW}  ⚠ Health check timed out (service may still be starting)${NC}\n"
    fi
    
    # Save URL for next steps
    export EMBEDDING_SERVICE_URL="$EMBEDDING_URL"
fi

# ============================================================================
# Deploy Scraper Service as Cloud Run Job
# ============================================================================
if [ "$DEPLOY_SCRAPER" = true ]; then
    echo -e "${BLUE}→ Building and deploying Scraper to Cloud Run Jobs...${NC}\n"
    
    if [ ! -f "backend/Dockerfile.scraper" ]; then
        echo -e "${RED}❌ Dockerfile.scraper not found${NC}"
        exit 1
    fi
    
    JOB_NAME="vecinita-scraper"
    IMAGE_URL="gcr.io/$PROJECT_ID/$JOB_NAME"
    
    echo "  Building Docker image: $IMAGE_URL..."
    gcloud builds submit backend \
        --dockerfile=Dockerfile.scraper \
        --tag=$IMAGE_URL \
        --project=$PROJECT_ID \
        --quiet
    
    echo -e "${GREEN}✓ Image built: $IMAGE_URL${NC}\n"
    
    echo "  Creating Cloud Run Job..."
    # Check if job already exists
    if gcloud run jobs describe $JOB_NAME --region=$REGION --project=$PROJECT_ID &>/dev/null; then
        echo "  Updating existing job..."
        gcloud run jobs update $JOB_NAME \
            --image=$IMAGE_URL \
            --region=$REGION \
            --project=$PROJECT_ID \
            --cpu=2 \
            --memory=2Gi \
            --timeout=1800 \
            --set-env-vars=PYTHONUNBUFFERED=1,EMBEDDING_SERVICE_URL=${EMBEDDING_SERVICE_URL:-http://embedding-service:8001} \
            --set-secrets=SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_KEY=SUPABASE_KEY:latest \
            --quiet
    else
        echo "  Creating new job..."
        gcloud run jobs create $JOB_NAME \
            --image=$IMAGE_URL \
            --region=$REGION \
            --project=$PROJECT_ID \
            --cpu=2 \
            --memory=2Gi \
            --timeout=1800 \
            --set-env-vars=PYTHONUNBUFFERED=1,EMBEDDING_SERVICE_URL=${EMBEDDING_SERVICE_URL:-http://embedding-service:8001} \
            --set-secrets=SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_KEY=SUPABASE_KEY:latest \
            --quiet
    fi
    
    echo -e "${GREEN}✓ Scraper Job Created/Updated${NC}\n"
    
    # Optional: Create Cloud Scheduler trigger
    SCHEDULER_NAME="vecinita-scraper-daily"
    SCHEDULE="0 2 * * *"  # 2 AM UTC daily
    
    echo "  Setting up Cloud Scheduler trigger..."
    if gcloud scheduler jobs describe $SCHEDULER_NAME --location=$REGION --project=$PROJECT_ID &>/dev/null; then
        echo "  Updating existing scheduler job..."
        gcloud scheduler jobs update http $SCHEDULER_NAME \
            --location=$REGION \
            --project=$PROJECT_ID \
            --schedule="$SCHEDULE" \
            --http-method=POST \
            --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run" \
            --quiet
    else
        echo "  Creating new scheduler job..."
        gcloud scheduler jobs create http $SCHEDULER_NAME \
            --location=$REGION \
            --project=$PROJECT_ID \
            --schedule="$SCHEDULE" \
            --http-method=POST \
            --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run" \
            --oidc-service-account-email=$(gcloud iam service-accounts list --filter="email~^cloud-scheduler" --format="value(email)" | head -1 || echo "Scheduler SA not found") \
            --quiet 2>/dev/null || echo -e "${YELLOW}  ⚠ Scheduler setup skipped (SA may not exist)${NC}"
    fi
    
    echo -e "${GREEN}✓ Scraper scheduled (daily at 2 AM UTC)${NC}\n"
fi

# ============================================================================
# Summary
# ============================================================================
echo -e "${GREEN}======================================"
echo "✓ Deployment Complete"
echo "======================================${NC}\n"

echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Create/verify Secret Manager secrets (one-time):"
echo "   ${BLUE}gcloud secrets create SUPABASE_URL --data-file=- < /dev/stdin${NC}"
echo "   ${BLUE}gcloud secrets create SUPABASE_KEY --data-file=- < /dev/stdin${NC}"
echo "   ${BLUE}gcloud secrets create GROQ_API_KEY --data-file=- < /dev/stdin${NC}"
echo ""
echo "2. Grant service account access to secrets:"
echo "   ${BLUE}gcloud secrets add-iam-policy-binding SUPABASE_URL --member=serviceAccount:SA@PROJECT.iam.gserviceaccount.com --role=roles/secretmanager.secretAccessor${NC}"
echo ""
echo "3. Update your .env or CI/CD with Cloud Run URLs:"
if [ -n "$EMBEDDING_SERVICE_URL" ]; then
    echo "   ${BLUE}export EMBEDDING_SERVICE_URL=$EMBEDDING_SERVICE_URL${NC}"
fi
echo ""
echo "4. Monitor logs:"
echo "   ${BLUE}gcloud run services logs read vecinita-embedding --limit 100 --region=$REGION${NC}"
echo "   ${BLUE}gcloud run jobs log read vecinita-scraper --limit 100 --region=$REGION${NC}"
echo ""
echo "5. Test embedding service:"
if [ -n "$EMBEDDING_SERVICE_URL" ]; then
    echo "   ${BLUE}curl $EMBEDDING_SERVICE_URL/health${NC}"
fi
echo ""
echo "6. Run scraper manually (if needed):"
echo "   ${BLUE}gcloud run jobs execute $JOB_NAME --region=$REGION${NC}"
echo ""
echo "7. To undeploy:"
echo "   ${BLUE}gcloud run services delete vecinita-embedding --region=$REGION${NC}"
echo "   ${BLUE}gcloud run jobs delete vecinita-scraper --region=$REGION${NC}"
echo "   ${BLUE}gcloud scheduler jobs delete vecinita-scraper-daily --location=$REGION${NC}"
echo ""
