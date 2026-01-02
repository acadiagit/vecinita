# Source Title Cleanup - Fix for Metadata Display Issue

## Problem

Link cards in the chat interface were displaying raw scraper metadata headers instead of clean document titles:

**Before:**
```
DOCUMENTS_LOADED: 1 | DOCUMENTS_PROCESSED: 1 | CHUNKS: 1 Tra...
```

**Root Cause:**
The scraper includes metadata headers at the beginning of the `content` field:
```
DOCUMENTS_LOADED: 1 | DOCUMENTS_PROCESSED: 1 | CHUNKS: 2
An Organization of Opportunity
Through the compassionate delivery...
```

The backend was trying to use a `title` field that doesn't exist in the database response, so it fell back to displaying the URL. However, the frontend was receiving the content and showing it, which included the metadata header.

## Solution

### Backend Fix (main.py lines 1036-1080)

Added intelligent title extraction logic in the source aggregation code:

```python
# Extract clean title from content by removing scraper metadata header
content_text = d.get("content", "")
clean_title = None

# Check if content starts with scraper metadata header
if content_text.startswith("DOCUMENTS_LOADED:"):
    # Find the end of the metadata line (first newline)
    lines = content_text.split('\n', 2)
    if len(lines) >= 2:
        # Use the first non-empty line after metadata as title
        for line in lines[1:]:
            stripped = line.strip()
            if stripped and len(stripped) > 3:
                # Take first 100 chars as title
                clean_title = stripped[:100] + ("..." if len(stripped) > 100 else "")
                break

# Fallback chain if no clean title extracted
if not clean_title and content_text:
    first_line = content_text.split('\n')[0].strip()
    if first_line and len(first_line) > 3:
        clean_title = first_line[:100] + ("..." if len(first_line) > 100 else "")

if not clean_title:
    # Use filename from URL or domain name
    parsed = urlparse(url)
    path_parts = parsed.path.rstrip('/').split('/')
    if path_parts and path_parts[-1]:
        clean_title = path_parts[-1]
    else:
        clean_title = parsed.netloc or "Internal Document"
```

### Title Extraction Logic

**Priority order:**
1. **First content line after metadata header** - Most meaningful for scraped content
2. **First line of content** - If no metadata header present
3. **Filename from URL path** - For file-based sources (PDFs, docs)
4. **Domain name** - For web page URLs
5. **"Internal Document"** - Final fallback

**Processing rules:**
- Skip lines with < 3 characters (empty or very short)
- Limit title to 100 characters with ellipsis if longer
- Strip whitespace before evaluation

## Result

**After:**
```
An Organization of Opportunity
dhs.ri.gov
```

Clean, user-friendly titles that represent the actual document content instead of scraper metadata.

## Files Modified

### Backend
- `backend/src/agent/main.py` (lines 1036-1080)
  - Enhanced source aggregation in `/ask` endpoint
  - Added title extraction logic
  - Handles both metadata header removal and fallback cases

### Frontend (no changes needed)
- `frontend/src/components/chat/LinkCard.jsx` 
  - Already correctly displays title prop
  - No modifications required

## Testing

### Test Case 1: Metadata Header Present
**Input content:**
```
DOCUMENTS_LOADED: 1 | DOCUMENTS_PROCESSED: 1 | CHUNKS: 1
Rhode Island Department of Human Services
Providing support to families...
```

**Expected title:** `Rhode Island Department of Human Services`

### Test Case 2: No Metadata Header
**Input content:**
```
Community Health Resources
Available services include...
```

**Expected title:** `Community Health Resources`

### Test Case 3: PDF File
**Input URL:** `https://example.com/reports/annual-report-2024.pdf`

**Expected title:** `annual-report-2024.pdf`

### Test Case 4: Web Page
**Input URL:** `https://dhs.ri.gov/programs/health`

**Expected title:** `health` (filename) or `dhs.ri.gov` (domain)

## Future Improvements

### Option 1: Store Clean Title During Scraping
Modify the scraper to extract and store a `document_title` field in the database schema (already exists but unused):

```python
# In vector_loader.py or scraper
document_title = extract_title_from_html(raw_html)  # Use <title> tag
chunk_data = {
    "content": content,
    "document_title": document_title,
    "source_url": url,
    ...
}
```

### Option 2: Remove Metadata from Content
Update scraper to store metadata separately:

```python
# Store clean content without metadata header
clean_content = content.split('\n', 1)[-1] if content.startswith("DOCUMENTS_LOADED:") else content

# Store metadata in metadata JSONB field
metadata = {
    "documents_loaded": 1,
    "documents_processed": 1,
    "chunks": 2,
    ...
}
```

### Option 3: Extract from HTML <title>
During scraping, extract the page title from HTML:

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html_content, 'html.parser')
page_title = soup.find('title').get_text().strip() if soup.find('title') else None
```

## Related Issues

### Database Search (Separate Issue)
The database search was returning no results due to `is_processed = false` flag. This is a separate issue from the title display problem.

**Fix:** Run `backend/scripts/mark_chunks_processed.sql` to mark rows as searchable.

**Status:** SQL script created, awaiting user execution.

## Notes

- This fix is **backward compatible** - works with existing database content
- No database schema changes required
- No frontend changes needed
- Handles both old (with metadata header) and future (without header) content formats
- Title length limited to 100 chars to prevent UI overflow

## Verification

After deploying this change:

1. **Restart backend:** `docker-compose restart backend` or `uv run uvicorn src.agent.main:app --reload`
2. **Test query:** Ask any question that triggers database search
3. **Verify:** Link cards should show clean titles instead of "DOCUMENTS_LOADED: ..."

Example test:
```bash
curl "http://localhost:8000/ask?question=rhode%20island%20health%20services"
```

Check the `sources` array in the streaming response - titles should be clean content lines, not metadata headers.
