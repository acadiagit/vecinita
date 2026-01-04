#!/usr/bin/env pwsh
# Deploy Supabase Edge Function for Embeddings
# This script deploys the generate-embedding edge function to Supabase

param(
    [switch]$Local = $false,
    [switch]$Test = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying Supabase Edge Function: generate-embedding" -ForegroundColor Cyan

# Check if Supabase CLI is installed
if (-not (Get-Command supabase -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Supabase CLI not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install Supabase CLI:" -ForegroundColor Yellow
    Write-Host "  npm install -g supabase"
    Write-Host "  OR download from: https://github.com/supabase/cli/releases"
    Write-Host ""
    exit 1
}

Write-Host "✅ Supabase CLI found: $(supabase --version)" -ForegroundColor Green

# Change to repository root
$repoRoot = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $repoRoot
Set-Location $repoRoot

Write-Host "📁 Repository root: $repoRoot" -ForegroundColor Gray

# Check if .env exists for HuggingFace token
$envFile = Join-Path $repoRoot ".env"
if (Test-Path $envFile) {
    Write-Host "✅ Found .env file" -ForegroundColor Green
    
    # Check for HuggingFace token
    $envContent = Get-Content $envFile -Raw
    if ($envContent -match "HUGGING_FACE_TOKEN=(.+)") {
        Write-Host "✅ HUGGING_FACE_TOKEN found in .env" -ForegroundColor Green
    } else {
        Write-Host "⚠️  HUGGING_FACE_TOKEN not found in .env" -ForegroundColor Yellow
        Write-Host "   Get a free token from: https://huggingface.co/settings/tokens" -ForegroundColor Yellow
        Write-Host "   Add to .env: HUGGING_FACE_TOKEN=hf_your_token_here" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "   Create .env and add: HUGGING_FACE_TOKEN=hf_your_token_here" -ForegroundColor Yellow
    Write-Host "   Get token from: https://huggingface.co/settings/tokens" -ForegroundColor Yellow
}

if ($Local) {
    # Start local Supabase
    Write-Host ""
    Write-Host "🏠 Starting local Supabase..." -ForegroundColor Cyan
    supabase start
    
    Write-Host ""
    Write-Host "🔧 Serving edge function locally..." -ForegroundColor Cyan
    Write-Host "   Access at: http://127.0.0.1:54321/functions/v1/generate-embedding" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    supabase functions serve generate-embedding
    
} elseif ($Test) {
    # Test the deployed function
    Write-Host ""
    Write-Host "🧪 Testing edge function..." -ForegroundColor Cyan
    
    $testPayload = @{
        text = "Hello, this is a test embedding!"
    } | ConvertTo-Json
    
    Write-Host "   Payload: $testPayload" -ForegroundColor Gray
    
    # Get Supabase URL from .env
    if (Test-Path $envFile) {
        $envContent = Get-Content $envFile -Raw
        if ($envContent -match "SUPABASE_URL=(.+)") {
            $supabaseUrl = $matches[1].Trim()
            if ($envContent -match "SUPABASE_KEY=(.+)") {
                $supabaseKey = $matches[1].Trim()
                
                $functionUrl = "$supabaseUrl/functions/v1/generate-embedding"
                Write-Host "   Calling: $functionUrl" -ForegroundColor Gray
                
                try {
                    $response = Invoke-RestMethod -Uri $functionUrl `
                        -Method Post `
                        -Headers @{
                            "Authorization" = "Bearer $supabaseKey"
                            "Content-Type" = "application/json"
                        } `
                        -Body $testPayload
                    
                    Write-Host ""
                    Write-Host "✅ Success! Response:" -ForegroundColor Green
                    Write-Host "   Dimension: $($response.dimension)" -ForegroundColor Gray
                    Write-Host "   Model: $($response.model)" -ForegroundColor Gray
                    Write-Host "   First 5 values: $($response.embedding[0..4] -join ', ')" -ForegroundColor Gray
                    
                } catch {
                    Write-Host ""
                    Write-Host "❌ Test failed: $_" -ForegroundColor Red
                    Write-Host $_.Exception.Message -ForegroundColor Red
                    exit 1
                }
            } else {
                Write-Host "❌ SUPABASE_KEY not found in .env" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "❌ SUPABASE_URL not found in .env" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ .env file not found" -ForegroundColor Red
        exit 1
    }
    
} else {
    # Deploy to production
    Write-Host ""
    Write-Host "🚢 Deploying to production Supabase..." -ForegroundColor Cyan
    Write-Host ""
    
    # Check if logged in
    try {
        supabase projects list 2>&1 | Out-Null
    } catch {
        Write-Host "❌ Not logged in to Supabase!" -ForegroundColor Red
        Write-Host "   Run: supabase login" -ForegroundColor Yellow
        exit 1
    }
    
    # Deploy
    Write-Host "📤 Deploying function..." -ForegroundColor Cyan
    supabase functions deploy generate-embedding
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Deployment successful!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Set HUGGING_FACE_TOKEN in Supabase Dashboard:" -ForegroundColor White
        Write-Host "   → Project Settings → Edge Functions → Secrets" -ForegroundColor Gray
        Write-Host "   → Add: HUGGING_FACE_TOKEN=hf_your_token_here" -ForegroundColor Gray
        Write-Host ""
        Write-Host "2. Set USE_EDGE_FUNCTION_EMBEDDINGS=true in Render:" -ForegroundColor White
        Write-Host "   → Dashboard → vecinita-agent → Environment" -ForegroundColor Gray
        Write-Host ""
        Write-Host "3. Test the function:" -ForegroundColor White
        Write-Host "   .\backend\scripts\deploy_edge_function.ps1 -Test" -ForegroundColor Gray
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "❌ Deployment failed!" -ForegroundColor Red
        exit 1
    }
}
