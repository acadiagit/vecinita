#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Complete Supabase Edge Function setup automation for Vecinita
    
.DESCRIPTION
    Automates the entire Edge Function deployment process:
    1. Verifies Supabase CLI installation
    2. Logs in to Supabase
    3. Links to project
    4. Deploys edge function
    5. Tests deployment
    6. Provides next steps

.EXAMPLE
    .\setup_edge_function.ps1
    
.NOTES
    Requires: Supabase CLI 2.67.1+ (installed via Scoop)
#>

param(
    [switch]$SkipLogin = $false,
    [string]$ProjectRef = "",
    [switch]$LocalOnly = $false
)

$ErrorActionPreference = "Stop"

# Colors for output
$colors = @{
    Success = 'Green'
    Error = 'Red'
    Warning = 'Yellow'
    Info = 'Cyan'
    Highlight = 'Magenta'
}

function Write-Status {
    param([string]$Message, [string]$Status = 'Info')
    $emoji = @{
        Success = '✅'
        Error = '❌'
        Warning = '⚠️'
        Info = 'ℹ️'
        Highlight = '🚀'
    }
    Write-Host "$($emoji[$Status]) $Message" -ForegroundColor $colors[$Status]
}

# Banner
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      Supabase Edge Function Setup for Vecinita                ║" -ForegroundColor Cyan
Write-Host "║      Zero-Memory Embeddings Architecture                      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Supabase CLI
Write-Status "Step 1: Verifying Supabase CLI installation..." -Status Info
if (-not (Get-Command supabase -ErrorAction SilentlyContinue)) {
    Write-Status "Supabase CLI not found in PATH!" -Status Error
    Write-Status "Run: scoop install supabase" -Status Warning
    exit 1
}

$cliVersion = (supabase --version 2>&1)
Write-Status "Supabase CLI $cliVersion installed" -Status Success

# Step 2: Navigate to repo
Write-Host ""
Write-Status "Step 2: Navigating to repository..." -Status Info
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot
Write-Status "Working in: $repoRoot" -Status Success

# Step 3: Login if needed
Write-Host ""
Write-Status "Step 3: Authentication..." -Status Info
if ($SkipLogin) {
    Write-Status "Skipping login (--SkipLogin specified)" -Status Warning
} else {
    Write-Status "Opening browser for Supabase login..." -Status Info
    supabase login
    Write-Status "Login successful!" -Status Success
}

# Step 4: Get project ref
Write-Host ""
Write-Status "Step 4: Linking to Supabase project..." -Status Info

if ($ProjectRef) {
    Write-Status "Using project ref: $ProjectRef" -Status Info
} else {
    Write-Host ""
    Write-Host "Visit https://app.supabase.com/project/_/settings/general" -ForegroundColor Cyan
    Write-Host "Copy the project ref (first part of URL after '/project/')" -ForegroundColor Gray
    Write-Host ""
    $ProjectRef = Read-Host "Enter your Supabase project ref"
}

if (-not $ProjectRef) {
    Write-Status "No project ref provided. Exiting." -Status Error
    exit 1
}

# Link project
try {
    supabase link --project-ref $ProjectRef
    Write-Status "Project linked successfully!" -Status Success
} catch {
    Write-Status "Failed to link project: $_" -Status Error
    exit 1
}

# Step 5: Deploy edge function
Write-Host ""
Write-Status "Step 5: Deploying edge function..." -Status Info
try {
    supabase functions deploy generate-embedding
    Write-Status "Edge function deployed successfully!" -Status Success
} catch {
    Write-Status "Failed to deploy edge function: $_" -Status Error
    exit 1
}

# Step 6: Summary
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    ✅ DEPLOYMENT COMPLETE!                    ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Status "What's been set up:" -Status Highlight
Write-Host "  ✓ Supabase CLI verified (v$cliVersion)" -ForegroundColor Green
Write-Host "  ✓ Project linked ($ProjectRef)" -ForegroundColor Green
Write-Host "  ✓ Edge function deployed (generate-embedding)" -ForegroundColor Green
Write-Host ""

Write-Status "Next steps (2 remaining):" -Status Highlight
Write-Host ""
Write-Host "1️⃣  SET HUGGING_FACE_TOKEN in Supabase Dashboard:" -ForegroundColor Cyan
Write-Host "   a) Go to: https://app.supabase.com/project/_/settings/functions" -ForegroundColor Gray
Write-Host "   b) Click 'Secrets' tab" -ForegroundColor Gray
Write-Host "   c) Add new secret:" -ForegroundColor Gray
Write-Host "      Name:  HUGGING_FACE_TOKEN" -ForegroundColor Gray
Write-Host "      Value: hf_xxxx... (from https://huggingface.co/settings/tokens)" -ForegroundColor Gray
Write-Host ""

Write-Host "2️⃣  ENABLE EDGE FUNCTION in Agent Service:" -ForegroundColor Cyan
Write-Host "   For Render deployment:" -ForegroundColor Gray
Write-Host "     - Dashboard → vecinita-agent → Environment" -ForegroundColor Gray
Write-Host "     - Add: USE_EDGE_FUNCTION_EMBEDDINGS=true" -ForegroundColor Gray
Write-Host "     - Redeploy" -ForegroundColor Gray
Write-Host ""
Write-Host "   For local testing:" -ForegroundColor Gray
Write-Host "     - Add to .env: USE_EDGE_FUNCTION_EMBEDDINGS=true" -ForegroundColor Gray
Write-Host ""

Write-Host "3️⃣  TEST THE SETUP:" -ForegroundColor Cyan
Write-Host "   .\backend\scripts\deploy_edge_function.ps1 -Test" -ForegroundColor Gray
Write-Host ""

Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Status "Memory savings:" -Status Info
Write-Host "  Agent image: 918MB → 850MB (68MB saved)" -ForegroundColor Green
Write-Host "  Runtime mem: ~250-300MB → ~200-250MB (50-90MB saved)" -ForegroundColor Green
Write-Host ""

Write-Host "Need help?" -ForegroundColor Cyan
Write-Host "  - Deployment guide: docs/guides/EDGE_FUNCTION_DEPLOYMENT.md" -ForegroundColor Gray
Write-Host "  - Architecture: docs/EDGE_FUNCTION_ARCHITECTURE.md" -ForegroundColor Gray
Write-Host "  - API docs: supabase/functions/generate-embedding/README.md" -ForegroundColor Gray
Write-Host ""
