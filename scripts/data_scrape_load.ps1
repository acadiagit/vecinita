#
# data_scrape_load.ps1
# Orchestrator script for the VECINA data pipeline (PowerShell version)
# Default mode: Additive. Adds new content without deleting old data.
# Use -Clean flag to wipe the database and start fresh.
#
# Usage:
#   .\scripts\data_scrape_load.ps1
#   .\scripts\data_scrape_load.ps1 -Clean
#

param(
    [switch]$Clean
)

# --- Configuration ---
$ChunkFile = "data/new_content_chunks.txt"
$LinksFile = "data/extracted_links.txt"
$MainUrlFile = "data/urls.txt"
$FailedUrlLog = "data/failed_urls.txt"
$ScraperModule = "src.utils.scraper.main"
$LoaderScript = "src/utils/vector_loader.py"
$AppContainerName = "vecinita-app"

# --- Helper function to write colored messages ---
function Write-Section {
    param([string]$Message)
    Write-Host ""
    Write-Host "--- $Message ---" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

# --- 1. Check for -Clean Flag ---
if ($Clean) {
    Write-Section "[WARNING] CLEAN MODE DETECTED"
    Write-Host "This script will TRUNCATE (delete all data) from the database." -ForegroundColor Red
    
    $confirmation = Read-Host "Are you sure you want to continue? (y/n)"
    
    if ($confirmation -notmatch '^[Yy]$') {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        exit 1
    }
    
    Write-Section "1. CLEANING DATABASE"
    
    # Set password environment variable
    $env:PGPASSWORD = 'batesvecinita2025'
    
    try {
        psql --host=db.dosbzlhijkeircyainwz.supabase.co `
             --port=5432 `
             --username=postgres `
             --dbname=postgres `
             --set=sslmode=require `
             -c "TRUNCATE TABLE public.document_chunks, public.search_queries, public.processing_queue;"
        
        Write-Success "[OK] Database cleaned successfully."
    }
    catch {
        Write-Error-Custom "[ERR] Failed to clean database: $_"
        exit 1
    }
}
else {
    Write-Section "ADDITIVE MODE"
    Write-Host "New content will be added to the existing database."
}

# --- 2. CLEANING OLD LOG/CHUNK FILES ---
Write-Section "2. CLEANING OLD LOG/CHUNK FILES"

Remove-Item -Path $ChunkFile -Force -ErrorAction SilentlyContinue
Remove-Item -Path $FailedUrlLog -Force -ErrorAction SilentlyContinue
Remove-Item -Path $LinksFile -Force -ErrorAction SilentlyContinue
Remove-Item -Path "vecinita_loader.log" -Force -ErrorAction SilentlyContinue

# Create a new empty chunk file
New-Item -Path $ChunkFile -ItemType File -Force | Out-Null
Write-Success "[OK] Old files cleaned."

# --- 3. RUNNING INITIAL SCRAPE ---
Write-Section "3. RUNNING INITIAL SCRAPE"

try {
    python -m $ScraperModule `
        --input $MainUrlFile `
        --output-file $ChunkFile `
        --failed-log $FailedUrlLog `
        --links-file $LinksFile
    
    Write-Success "[OK] Initial scrape completed."
}
catch {
    Write-Error-Custom "[ERR] Scraper failed: $_"
    exit 1
}

# --- 4. RE-RUNNING FAILED URLS WITH PLAYWRIGHT ---
Write-Section "4. RE-RUNNING FAILED URLS WITH PLAYWRIGHT"

if ((Test-Path $FailedUrlLog) -and ((Get-Item $FailedUrlLog).Length -gt 0)) {
    $failedCount = @(Get-Content $FailedUrlLog).Count
    Write-Host "Found $failedCount failed URLs. Re-running with Playwright..."
    
    try {
        python -m $ScraperModule `
            --input $FailedUrlLog `
            --output-file $ChunkFile `
            --failed-log $FailedUrlLog `
            --links-file $LinksFile `
            --loader playwright
        
        Write-Success "[OK] Playwright re-run completed."
    }
    catch {
        Write-Error-Custom "[ERR] Playwright re-run failed: $_"
        exit 1
    }
}
else {
    Write-Host "No failed URLs found. Skipping re-run."
}

# --- 5. LOADING NEW DATA INTO DATABASE ---
Write-Section "5. LOADING NEW DATA INTO DATABASE"

try {
    python $LoaderScript $ChunkFile
    Write-Success "[OK] Data loaded into database."
}
catch {
    Write-Error-Custom "[ERR] Data loading failed: $_"
    exit 1
}

# --- 6. RESTARTING APPLICATION ---
Write-Section "6. RESTARTING APPLICATION"

try {
    docker restart $AppContainerName
    Write-Success "[OK] Application restarted."
}
catch {
    Write-Error-Custom "[ERR] Failed to restart container: $_"
    exit 1
}

# --- COMPLETE ---
Write-Section "[OK] PIPELINE COMPLETE!"
Write-Host ""
Write-Host "[FILE] Chunks saved to: $ChunkFile" -ForegroundColor Green
Write-Host "[LINK] Links saved to: $LinksFile" -ForegroundColor Green
Write-Host "[ERR] Failed URLs logged to: $FailedUrlLog" -ForegroundColor Yellow
