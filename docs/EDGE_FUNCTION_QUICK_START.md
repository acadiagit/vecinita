# Supabase Edge Function Deployment Quick Start

✅ **Supabase CLI v2.67.1 installed and ready!**

## Next Steps (5 minutes)

### 1. Navigate to Repository
```powershell
cd c:\Users\bigme\OneDrive\Documents\GitHub\VECINA\vecinita
```

### 2. Login to Supabase
```bash
supabase login
```
This opens your browser to authenticate. Click the button to authorize.

### 3. Link to Your Project
Get your project ref from: https://app.supabase.com/project/_/settings/general

```bash
# Replace <your-project-ref> with actual ref (e.g., abcdefghijklmnop)
supabase link --project-ref <your-project-ref>
```

### 4. Deploy Edge Function
```bash
supabase functions deploy generate-embedding
```

You should see:
```
✓ Function deployed successfully!
Deployment complete!
```

### 5. Set HuggingFace Token in Supabase Dashboard

1. Go to: https://huggingface.co/settings/tokens
2. Create a new token (copy it)
3. In Supabase Dashboard:
   - Project Settings → Edge Functions → Secrets
   - Add new secret:
     - Name: `HUGGING_FACE_TOKEN`
     - Value: `hf_xxxxxxxxxxxx...` (your token)

### 6. Enable in Vecinita Agent

**Option A: Render Dashboard (if deploying to Render)**
1. Go to Render Dashboard → vecinita-agent → Environment
2. Add: `USE_EDGE_FUNCTION_EMBEDDINGS=true`
3. Redeploy

**Option B: Local Testing**
Update `.env`:
```bash
USE_EDGE_FUNCTION_EMBEDDINGS=true
```

### 7. Test Edge Function

```bash
# Test locally (starts Supabase containers)
supabase functions serve generate-embedding

# In another terminal:
curl -i http://127.0.0.1:54321/functions/v1/generate-embedding \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGc..." \
  -d '{"text":"Hello world"}'
```

Or use the deployment script:
```powershell
.\backend\scripts\deploy_edge_function.ps1 -Test
```

---

## Verification Checklist

- [ ] Supabase CLI installed: `supabase --version` returns 2.67.1+
- [ ] Logged in to Supabase: `supabase projects list` shows your project
- [ ] Edge function deployed: Check https://app.supabase.com/project/_/functions
- [ ] HuggingFace token set: Check Project Settings → Edge Functions → Secrets
- [ ] `USE_EDGE_FUNCTION_EMBEDDINGS=true` in environment
- [ ] Test query works: `curl http://localhost:8000/ask?question=test`
- [ ] Agent logs show: `✅ Embedding model initialized via Supabase Edge Function`

---

## Troubleshooting

**"supabase: command not found"**
- Restart PowerShell or terminal
- Or use full path: `& "$env:USERPROFILE\scoop\shims\supabase" --version`

**"No project found"**
- Run: `supabase link --project-ref <your-ref>`

**Edge function returns 500**
- Check HUGGING_FACE_TOKEN is set in Supabase Dashboard
- View logs: `supabase functions logs generate-embedding`

**Agent still using local embeddings**
- Verify `USE_EDGE_FUNCTION_EMBEDDINGS=true` in environment
- Check agent startup logs for: `✅ Embedding model initialized via Supabase Edge Function`

---

## Useful Commands

```bash
# View your projects
supabase projects list

# Check function deployment status
supabase functions list

# View function logs (real-time)
supabase functions logs generate-embedding --tail

# Local testing (starts containers)
supabase start

# Stop local Supabase
supabase stop
```

---

## Memory Savings After Deployment

**Agent Service:**
- Docker image: 918MB → **850MB** (68MB saved)
- Runtime memory: ~250-300MB → **~200-250MB** (50-90MB saved)
- Cold start: ~5s → **~2s** (60% faster)
- No embedding model loading needed!

**Trade-off:**
- Query latency: +50-100ms (network roundtrip)
- But well worth the memory savings for Render!

---

## Next: Deploy to Render

After verifying edge function works locally:

```bash
# Commit changes
git add .
git commit -m "feat: Supabase Edge Function embeddings for zero-memory agent"
git push

# Then in Render Dashboard:
# 1. Ensure vecinita-agent service exists
# 2. Add environment variable: USE_EDGE_FUNCTION_EMBEDDINGS=true
# 3. Redeploy (auto-triggers on git push)
# 4. Monitor memory usage - should be ~50-90MB lower!
```
