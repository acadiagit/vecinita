#!/bin/bash
#
# data_scrape_load.sh
# Orchestrator script for the VECINA data pipeline (Bash version)
# Default mode: Additive. Adds new content without deleting old data.
# Use "--clean" flag to wipe the database and start fresh.
#
# Usage:
#   bash scripts/data_scrape_load.sh
#   bash scripts/data_scrape_load.sh --clean
#

# --- Configuration ---
CHUNK_FILE="data/new_content_chunks.txt"
LINKS_FILE="data/extracted_links.txt"
MAIN_URL_FILE="data/urls.txt"
FAILED_URL_LOG="data/failed_urls.txt"
SCRAPER_MODULE="src.utils.scraper.main"
LOADER_SCRIPT="src/utils/vector_loader.py"
APP_CONTAINER_NAME="vecinita-app"

# Exit immediately if any command fails
set -e

# --- 1. Check for --clean Flag ---
if [ "$1" == "--clean" ]; then
    echo "--- ⚠️  CLEAN MODE DETECTED ---"
    echo "This script will TRUNCATE (delete all data) from the database."
    read -p "Are you sure you want to continue? (y/n) " -n 1 -r
    echo    # (move to a new line)
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Operation cancelled."
        exit 1
    fi
    
    echo "--- 1. CLEANING DATABASE ---"
    # Set password from your .env file
    export PGPASSWORD='batesvecinita2025' 

    psql --host=db.dosbzlhijkeircyainwz.supabase.co \
         --port=5432 \
         --username=postgres \
         --dbname=postgres \
         --set=sslmode=require \
         -c "TRUNCATE TABLE public.document_chunks, public.search_queries, public.processing_queue;"
else
    echo "--- ADDITIVE MODE ---"
    echo "New content will be added to the existing database."
fi

echo "--- 2. CLEANING OLD LOG/CHUNK FILES ---"
# We still clean the local log/chunk files for this *specific run*
rm -f "$CHUNK_FILE" "$FAILED_URL_LOG" "$LINKS_FILE" "vecinita_loader.log"
touch "$CHUNK_FILE" # Create a new empty chunk file

echo "--- 3. RUNNING INITIAL SCRAPE ---"
# This run uses the "smart" logic and logs any failures.
python -m $SCRAPER_MODULE \
    --input "$MAIN_URL_FILE" \
    --output-file "$CHUNK_FILE" \
    --failed-log "$FAILED_URL_LOG" \
    --links-file "$LINKS_FILE"

echo "--- 4. RE-RUNNING FAILED URLS WITH PLAYWRIGHT ---"
# Check if the failed log exists and is not empty
if [ -s "$FAILED_URL_LOG" ]; then
    echo "Found $(wc -l < $FAILED_URL_LOG) failed URLs. Re-running with Playwright..."
    
    # This run forces Playwright for all URLs in the failed log
    # It appends the new chunks to the *same* output file
    python -m $SCRAPER_MODULE \
        --input "$FAILED_URL_LOG" \
        --output-file "$CHUNK_FILE" \
        --failed-log "$FAILED_URL_LOG" \
        --links-file "$LINKS_FILE" \
        --loader playwright
else
    echo "No failed URLs found. Skipping re-run."
fi

echo "--- 5. LOADING NEW DATA INTO DATABASE ---"
# Now, we load *only* the new chunks.
# Your vector_loader.py script will add new chunks.
# The database's "unique_content_source" constraint will 
# automatically reject any exact duplicates you accidentally re-scraped.
python $LOADER_SCRIPT "$CHUNK_FILE"

echo "--- 6. RESTARTING APPLICATION ---"
docker restart "$APP_CONTAINER_NAME"

echo "--- ✅ PIPELINE COMPLETE! ---"
echo "📄 Chunks saved to: $CHUNK_FILE"
echo "🔗 Links saved to: $LINKS_FILE"
echo "❌ Failed URLs logged to: $FAILED_URL_LOG"
