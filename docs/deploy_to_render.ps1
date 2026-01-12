#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Deploy Vecinita to Render (3 free-tier services)
    
.DESCRIPTION
    Interactive PowerShell script to deploy embedding, agent, scraper, and frontend services to Render
    
.EXAMPLE
    .\deploy_to_render.ps1
#>

param(
    [string]$RenderApiKey
)

# Colors for output
$ErrorColor = "Red"
$SuccessColor = "Green"
$InfoColor = "Cyan"
$WarningColor = "Yellow"

function Write-Success {
    Write-Host "✅ $args" -ForegroundColor $SuccessColor
}

function Write-Error-Custom {
    Write-Host "❌ $args" -ForegroundColor $ErrorColor
}

function Write-Info {
    Write-Host "ℹ️  $args" -ForegroundColor $InfoColor
}

function Write-Warning-Custom {
    Write-Host "⚠️  $args" -ForegroundColor $WarningColor
}

# Banner
Write-Host "
╔════════════════════════════════════════════════════════════════╗
║                 Vecinita Render Deployment                    ║
║              3 Free-Tier Services Architecture                 ║
╚════════════════════════════════════════════════════════════════╝
" -ForegroundColor $InfoColor

# Prerequisites check
Write-Info "Checking prerequisites..."

$prereqs = @(
    @{ Name = "Git"; Command = "git --version" },
    @{ Name = "Docker"; Command = "docker --version" }
)

$missing = @()
foreach ($prereq in $prereqs) {
    try {
        Invoke-Expression $prereq.Command | Out-Null
        Write-Success "$($prereq.Name) installed"
    }
    catch {
        $missing += $prereq.Name
        Write-Error-Custom "$($prereq.Name) not found"
    }
}

if ($missing.Count -gt 0) {
    Write-Error-Custom "Missing prerequisites: $($missing -join ', ')"
    Write-Info "Please install missing tools and try again"
    exit 1
}

# Configuration section
Write-Host "`n📋 Configuration" -ForegroundColor $InfoColor
Write-Host "═" * 50

Write-Info "Services to be deployed:"
Write-Host "  1. vecinita-embedding  (Free, 512MB) - Sentence embeddings"
Write-Host "  2. vecinita-agent      (Free, 512MB) - FastAPI agent"
Write-Host "  3. vecinita-scraper    (Free cron)   - Background scraper"
Write-Host "  4. vecinita-frontend   (Free, 512MB) - React frontend"

Write-Host "`nRegion: Virginia"
Write-Host "Plan: Free tier (512MB RAM, shared CPU)"

# Get Render API key
if (-not $RenderApiKey) {
    Write-Info "Visit https://dashboard.render.com/account/api-tokens to get your API key"
    $RenderApiKey = Read-Host "Enter your Render API key"
}

if (-not $RenderApiKey) {
    Write-Error-Custom "API key required"
    exit 1
}

# Get GitHub repo
$RepoUrl = (git config --get remote.origin.url) -replace "\.git$"
Write-Success "Using repository: $RepoUrl"

# Supabase credentials
Write-Host "`n🔑 Supabase Credentials" -ForegroundColor $InfoColor
Write-Host "═" * 50

$SupabaseUrl = Read-Host "Enter SUPABASE_URL (from https://app.supabase.com/project/_/settings/general)"
$SupabaseKey = Read-Host "Enter SUPABASE_KEY (anon key)" -AsSecureString

if (-not $SupabaseUrl -or -not $SupabaseKey) {
    Write-Error-Custom "Supabase credentials required"
    exit 1
}

Write-Success "Supabase credentials configured"

# LLM API key
Write-Host "`n🤖 LLM Configuration" -ForegroundColor $InfoColor
Write-Host "═" * 50

Write-Host "Choose LLM provider:"
Write-Host "  1. Groq (Recommended - free tier)"
Write-Host "  2. OpenAI"
Write-Host "  3. DeepSeek"
Write-Host "  4. Skip (use local Ollama)"

$llmChoice = Read-Host "Select (1-4)"

switch ($llmChoice) {
    "1" {
        $GroqKey = Read-Host "Enter GROQ_API_KEY (from https://console.groq.com)" -AsSecureString
        if ($GroqKey) {
            Write-Success "Groq API key configured"
        }
    }
    "2" {
        $OpenaiKey = Read-Host "Enter OPENAI_API_KEY" -AsSecureString
        if ($OpenaiKey) {
            Write-Success "OpenAI API key configured"
        }
    }
    "3" {
        $DeepseekKey = Read-Host "Enter DEEPSEEK_API_KEY" -AsSecureString
        if ($DeepseekKey) {
            Write-Success "DeepSeek API key configured"
        }
    }
    default {
        Write-Info "Skipping LLM configuration (will use local Ollama if available)"
    }
}

# Summary
Write-Host "`n📦 Deployment Summary" -ForegroundColor $InfoColor
Write-Host "═" * 50

Write-Host "Services to deploy:"
Write-Host "  • Embedding Service  → https://vecinita-embedding.onrender.com"
Write-Host "  • Agent Service      → https://vecinita-agent.onrender.com"
Write-Host "  • Scraper Cron       → Daily at 2 AM UTC"
Write-Host "  • Frontend           → https://vecinita-frontend.onrender.com"

Write-Host "`nEstimated deployment time: 5-10 minutes"
Write-Host "Cost: $0 (free tier)"

$confirm = Read-Host "`nProceed with deployment? (yes/no)"

if ($confirm -ne "yes") {
    Write-Warning-Custom "Deployment cancelled"
    exit 0
}

# Deployment
Write-Host "`n🚀 Deploying to Render..." -ForegroundColor $InfoColor
Write-Host "═" * 50

Write-Info "Note: Full deployment requires manual steps in Render Dashboard"
Write-Info "See docs/RENDER_DEPLOYMENT_THREE_SERVICES.md for detailed instructions"

Write-Host "`n📝 Next Steps:" -ForegroundColor $InfoColor
Write-Host "═" * 50

Write-Host @"
1. Go to https://dashboard.render.com

2. Deploy Embedding Service:
   - New → Web Service
   - Name: vecinita-embedding
   - Dockerfile: backend/Dockerfile.embedding
   - Plan: Free
   - Add env: PORT=8001, PYTHONUNBUFFERED=1

3. Deploy Agent Service:
   - New → Web Service
   - Name: vecinita-agent
   - Dockerfile: backend/Dockerfile
   - Plan: Free
   - Add env: EMBEDDING_SERVICE_URL=https://vecinita-embedding.onrender.com
   - Add secrets: SUPABASE_URL, SUPABASE_KEY, GROQ_API_KEY

4. Deploy Scraper (optional):
   - New → Background Worker
   - Name: vecinita-scraper
   - Dockerfile: backend/Dockerfile.scraper
   - Schedule: 0 2 * * * (daily 2 AM UTC)

5. Deploy Frontend:
   - New → Web Service
   - Name: vecinita-frontend
   - Dockerfile: frontend/Dockerfile
   - Add env: VITE_BACKEND_URL=https://vecinita-agent.onrender.com

6. After all services are deployed:
   ✓ Test embedding service: https://vecinita-embedding.onrender.com/health
   ✓ Test agent: https://vecinita-agent.onrender.com/health
   ✓ Visit frontend: https://vecinita-frontend.onrender.com

For detailed instructions, see: docs/RENDER_DEPLOYMENT_THREE_SERVICES.md
"@

Write-Success "Setup complete! Visit Render Dashboard to complete deployment"
Write-Success "Deployment guide: docs/RENDER_DEPLOYMENT_THREE_SERVICES.md"
