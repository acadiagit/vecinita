# Generate Embedding Edge Function

This Supabase Edge Function generates text embeddings using HuggingFace's Inference API with the `sentence-transformers/all-MiniLM-L6-v2` model.

## Benefits

- **Zero agent memory overhead**: No embedding models loaded in agent service
- **Centralized embeddings**: Same model for queries and document scraping
- **No version drift**: Update model without redeploying agent
- **Scales independently**: Edge function auto-scales with usage

## Setup

### 1. Install Supabase CLI

**Windows (Recommended - Scoop):**
```powershell
# First install Scoop (one-time setup)
powershell -ExecutionPolicy Bypass -Command "irm get.scoop.sh | iex"

# Add Supabase bucket and install
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase
```

**Alternative (Download Binary):**
Download from: https://github.com/supabase/cli/releases

**macOS (Brew):**
```bash
brew install supabase/tap/supabase
```

**Verify installation:**
```bash
supabase --version
```

### 2. Login to Supabase

```bash
supabase login
```

### 3. Link to your project

```bash
# From repository root
cd c:\Users\bigme\OneDrive\Documents\GitHub\VECINA\vecinita
supabase link --project-ref <your-project-ref>
```

Get your project ref from: https://app.supabase.com/project/_/settings/general

### 4. Set HuggingFace Token

Get a free token from: https://huggingface.co/settings/tokens

**In Supabase Dashboard:**
1. Go to Project Settings → Edge Functions
2. Add secret: `HUGGING_FACE_TOKEN` = `hf_...`

**For local testing:**
```bash
# Create .env file in supabase/functions/generate-embedding/
echo "HUGGING_FACE_TOKEN=hf_your_token_here" > supabase/functions/generate-embedding/.env
```

### 5. Deploy the function

```bash
# From repository root
supabase functions deploy generate-embedding

# Or deploy all functions
supabase functions deploy
```

### 6. Test the function

```bash
# Test locally (starts local Supabase)
supabase start
supabase functions serve generate-embedding

# Then in another terminal:
curl -i http://127.0.0.1:54321/functions/v1/generate-embedding \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world"}'

# Test production deployment
curl -i https://<project-ref>.supabase.co/functions/v1/generate-embedding \
  -H "Authorization: Bearer <anon-or-service-key>" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world"}'
```

## API Usage

### Single text embedding

**Request:**
```json
{
  "text": "What community resources are available?"
}
```

**Response:**
```json
{
  "embedding": [0.123, -0.456, ...],  // 384-dimensional vector
  "dimension": 384,
  "model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

### Batch embeddings

**Request:**
```json
{
  "texts": [
    "First document",
    "Second document",
    "Third document"
  ]
}
```

**Response:**
```json
{
  "embeddings": [
    [0.123, -0.456, ...],
    [0.789, -0.012, ...],
    [0.345, -0.678, ...]
  ],
  "count": 3,
  "dimension": 384,
  "model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

## Performance

- **Cold start**: ~1-2 seconds (first call or after inactivity)
- **Warm**: ~100-200ms per embedding
- **HuggingFace API limits**: 
  - Free tier: ~30,000 requests/month
  - Pro tier: Higher limits with better performance

## Monitoring

View logs in Supabase Dashboard:
1. Go to Edge Functions → generate-embedding
2. Click "Logs" tab

Or via CLI:
```bash
supabase functions logs generate-embedding
```

## Troubleshooting

### Function returns 500
- Check HUGGING_FACE_TOKEN is set correctly
- View logs: `supabase functions logs generate-embedding`
- Test HF API directly: https://api-inference.huggingface.co/

### Slow first response
- HuggingFace models have cold start time
- Use `wait_for_model: true` (already configured)
- Consider upgrading to HF Pro for faster inference

### Authentication errors
- For internal use (agent → edge function): Use service role key
- For external use: Enable JWT verification in config.toml
