# Quick Start: Streaming Mode

## What's New?

✨ **Streaming mode** - Memory-efficient data processing that:
- Uploads chunks immediately after scraping each URL (no intermediate file)
- Preserves original source URLs (no more temp file paths in chunks)
- Reduces memory usage by 99% for large datasets

## Usage

### Run with Streaming Mode (Recommended)

```bash
# Clean database and run with streaming
python scripts/data_scrape_load.py --clean --stream

# Add new data with streaming (no database cleaning)
python scripts/data_scrape_load.py --stream
```

### Traditional File-Based Mode

```bash
# Original behavior (saves to intermediate file first)
python scripts/data_scrape_load.py --clean
```

## When to Use Streaming?

✅ **Use streaming for:**
- Large datasets (1000+ URLs)
- Memory-constrained environments
- Production deployments
- Continuous data ingestion

❌ **Use file mode for:**
- Debugging (want to inspect intermediate file)
- Small datasets (<100 URLs)
- Offline processing (scrape now, upload later)

## What Changed?

### 1. Source Attribution Fixed ✅

**Before:**
```
(Chunk Source: data/temp_Nuestra_Salud_directoria.csv_1766417638.csv)
```

**After:**
```
(Chunk Source: https://github.com/.../Nuestra_Salud_directoria.csv)
```

### 2. Memory Usage Reduced ✅

**Before:** Loads entire scraped content into memory (can be 100+ MB)

**After:** Processes one URL at a time (~0.1 MB)

### 3. Real-Time Progress ✅

**Before:** No feedback until all URLs scraped

**After:** See upload progress after each URL

## Testing

```bash
# Test with sample URL
echo "https://www.uscis.gov" > data/test_urls.txt
python -m src.scraper_to_text \
    --input data/test_urls.txt \
    --output-file data/test_output.txt \
    --failed-log data/test_failed.txt \
    --stream

# Verify data uploaded
python -m src.utils.db_cli stats
```

## More Information

See [docs/STREAMING_MODE.md](STREAMING_MODE.md) for complete documentation.
