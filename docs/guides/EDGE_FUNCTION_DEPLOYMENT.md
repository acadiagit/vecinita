# Supabase Edge Function Deployment Guide

This guide shows you how to deploy the `generate-embedding` edge function to eliminate embedding models from the agent service.

## Why Use Edge Functions for Embeddings?

**Benefits:**
- ✅ **Zero agent memory overhead** - saves ~50-90MB
- ✅ **Centralized model management** - same model for queries and documents
- ✅ **No version drift** - update model without redeploying agent
- ✅ **Auto-scaling** - Supabase handles traffic spikes
- ✅ **No cold starts in agent** - model always warm in edge function

**Tradeoffs:**
- ⚠️ Adds **~50-100ms latency** per query (network roundtrip)
- ⚠️ Requires HuggingFace API token (free tier: 30k requests/month)

## Prerequisites

### 1. Install Supabase CLI

**Windows (Recommended - Scoop):**
```powershell
# First install Scoop (one-time setup)
powershell -ExecutionPolicy Bypass -Command "irm get.scoop.sh | iex"

# Add Supabase bucket and install
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase

# Verify
supabase --version
```

**Alternative (Direct Binary Download):**
Download from: https://github.com/supabase/cli/releases

**Note:** Installing via `npm install -g supabase` is no longer supported. Use Scoop or download binary instead.

### 2. Get HuggingFace Token

1. Go to: https://huggingface.co/settings/tokens
2. Create a new token (Read access is sufficient)
3. Copy the token (starts with `hf_...`)

### 3. Login to Supabase

```bash
supabase login
```

## Deployment

### Option 1: PowerShell Script (Recommended for Windows)

```powershell
# Deploy to production
cd backend/scripts
.\deploy_edge_function.ps1

# Test locally
.\deploy_edge_function.ps1 -Local

# Test production deployment
.\deploy_edge_function.ps1 -Test
```

### Option 2: Manual Deployment

```bash
# From repository root
cd c:\Users\bigme\OneDrive\Documents\GitHub\VECINA\vecinita

# Link to your Supabase project (first time only)
supabase link --project-ref <your-project-ref>

# Deploy the function
supabase functions deploy generate-embedding
```

**Get your project ref from:**
https://app.supabase.com/project/_/settings/general

## Configuration

### 1. Set HuggingFace Token in Supabase

**Dashboard Method:**
1. Go to: https://app.supabase.com/project/_/settings/functions
2. Click "Edge Function Secrets"
3. Add secret:
   - Name: `HUGGING_FACE_TOKEN`
   - Value: `hf_your_token_here`

**CLI Method:**
```bash
supabase secrets set HUGGING_FACE_TOKEN=hf_your_token_here
```

### 2. Enable Edge Function in Agent Service

**For Render Deployment:**
1. Go to Render Dashboard → vecinita-agent → Environment
2. Add environment variable:
   - Key: `USE_EDGE_FUNCTION_EMBEDDINGS`
   - Value: `true`
3. Save and redeploy

**For Docker/Local:**
Add to `.env`:
```bash
USE_EDGE_FUNCTION_EMBEDDINGS=true
```

## Testing

### Test Edge Function Directly

```bash
# Using curl (with your actual URL and key)
curl -i https://your-project.supabase.co/functions/v1/generate-embedding \
  -H "Authorization: Bearer YOUR_SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world"}'
```

### Test via Agent

```bash
# Start agent locally
cd backend
uv run uvicorn src.agent.main:app --reload

# Test endpoint
curl "http://localhost:8000/ask?question=community+resources"
```

Check logs for:
```
✅ Embedding model initialized via Supabase Edge Function (zero memory overhead)
```

## Monitoring

### View Edge Function Logs

**Dashboard:**
https://app.supabase.com/project/_/functions/generate-embedding/logs

**CLI:**
```bash
supabase functions logs generate-embedding
```

### Performance Metrics

Expected latencies:
- **Cold start**: 1-2 seconds (first call after inactivity)
- **Warm**: 100-200ms per embedding
- **Batch**: ~50-100ms per text (parallelized)

## Rollback / Fallback

The agent automatically falls back to local FastEmbed if edge function fails:

1. Set `USE_EDGE_FUNCTION_EMBEDDINGS=false` in environment
2. Redeploy agent service
3. Agent will use local FastEmbed (~25MB memory)

Or disable temporarily:
```bash
# In .env or Render dashboard
USE_EDGE_FUNCTION_EMBEDDINGS=false
```

## Troubleshooting

### Error: "supabase: command not found"
- Install Supabase CLI: `npm install -g supabase`
- Or download from: https://github.com/supabase/cli/releases

### Error: "HuggingFace API error: 401"
- Check HUGGING_FACE_TOKEN is set correctly in Supabase secrets
- Get new token: https://huggingface.co/settings/tokens

### Error: "Edge function returned 500"
- View logs: `supabase functions logs generate-embedding`
- Check HuggingFace API status: https://status.huggingface.co/

### Slow responses (>2 seconds)
- First call has cold start (~1-2s) - this is normal
- Subsequent calls should be ~100-200ms
- Consider HuggingFace Pro for faster inference

### Agent falls back to FastEmbed
- Check Supabase project URL is correct
- Verify edge function is deployed: `supabase functions list`
- Test edge function directly (see Testing section)

## Cost Estimation

**HuggingFace Inference API:**
- Free tier: 30,000 requests/month
- Pro tier: $9/month for 1M requests

**Supabase Edge Functions:**
- Free tier: 500k invocations/month
- Pro tier: $25/month for 2M invocations

For Vecinita usage (~100 queries/day):
- **Monthly requests**: ~3,000
- **Cost**: $0 (well within free tier)

## Next Steps

1. ✅ Deploy edge function
2. ✅ Set HUGGING_FACE_TOKEN in Supabase
3. ✅ Enable USE_EDGE_FUNCTION_EMBEDDINGS in agent
4. ✅ Test with sample queries
5. ✅ Monitor performance and adjust as needed
6. 🚀 Enjoy ~50-90MB memory savings!
