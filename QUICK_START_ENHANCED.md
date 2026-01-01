# Quick Start: Enhanced Streaming & Planning Agent

## Start the Backend

```bash
cd backend
uv run -m uvicorn src.agent.main:app --reload
```

The backend will start on `http://localhost:8000`

## Start the Frontend (if running separately)

```bash
cd frontend
npm run dev
```

The frontend will start on `http://localhost:5173`

## Test the New Features

### 1. Test Tool-Specific Progress

Send a query that requires database search:

**Query**: "Where can I find resources for my children?"

**Expected in progress bar**:
- `[STATIC_RESPONSE]` - Checking FAQs...
- `[DB_SEARCH]` - Searching database...
- (If no results) `[CLARIFY_QUESTION]` - Asking clarifying questions...
- (If still no results) `[WEB_SEARCH]` - Searching the web...

### 2. Test Planning

Send any query and watch for:

```
[PLANNING]
Analyzing your question and planning the search...
```

The planning agent will analyze your question and create a search strategy before executing tools.

### 3. Verify Language Support

**Spanish Query**:
```
¿Dónde puedo encontrar recursos para los niños?
```

Progress messages will automatically appear in Spanish:
- `[DB_SEARCH]` - Buscando en la base de datos...
- `[CLARIFY_QUESTION]` - Formulando preguntas de aclaración...

**English Query**:
```
Where can I find resources for children?
```

Progress messages in English:
- `[DB_SEARCH]` - Searching database...
- `[CLARIFY_QUESTION]` - Asking clarifying questions...

## Monitoring Backend Logs

Watch for these log messages to understand what's happening:

```
Agent response (streaming): Here is the answer...
Executing tool: db_search
Search plan created: KEY CONCEPTS: [...], PLAN: [...]
Extracted X sources from tool calls (streaming)
```

## Key Features to Try

1. **Real-time tool visibility**: See exactly which tool is running
2. **Language detection**: Send queries in Spanish or English
3. **Search planning**: Backend analyzes your question first
4. **Progress animation**: Animated bar while processing
5. **Source attribution**: Click sources to see where answers came from

## Debug Mode

To see more detailed logs, enable debug logging in backend:

In `backend/src/agent/main.py`, change logging level:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Then restart the backend.

## API Endpoints

### Traditional Endpoint (no streaming)
```
GET /ask?question=Where are resources for children?
```

### Enhanced Streaming Endpoint (NEW)
```
GET /ask-stream?question=Where are resources for children?&lang=en
```

### With Clarification Response
```
GET /ask-stream?question=Where are doctors?&clarification_response=I'm looking for pediatricians in the downtown area
```

## Response Format

### Progress Updates (as received)
```json
{"type": "progress", "stage": "tool", "tool": "db_search", "message": "Searching database..."}
```

### Final Response
```json
{
  "type": "complete",
  "answer": "Here are resources for your children...",
  "sources": [
    {"title": "Resource 1", "url": "https://...", "type": "document"},
    {"title": "Resource 2", "url": "https://...", "type": "link"}
  ],
  "plan": "KEY CONCEPTS: children, resources\nSEARCH PLAN: 1. Check FAQ, 2. Search database..."
}
```

## Troubleshooting

### Progress bar not showing
- Check browser Network tab → `/ask-stream` request status
- Verify streaming response is coming (should be `text/event-stream`)
- Check browser console for JavaScript errors

### Tools not appearing
- Enable DEBUG logging in backend
- Check logs for "Executing tool:" messages
- Verify `/ask-stream` endpoint is being called (not `/ask`)

### Language not auto-detecting
- Try explicit lang parameter: `&lang=es` or `&lang=en`
- Check that langdetect library is installed: `uv sync`

### Planning not running
- Watch logs for "Search plan created" messages
- It may fail gracefully and continue without a plan

## Next: Interactive Clarification

The framework for interactive clarification is ready. When you're ready, you can:

1. Show clarification questions to users
2. Collect their responses
3. Re-submit with `clarification_response` parameter

The planning agent will then use the clarification to refine the search.

## Performance Notes

- Planning adds ~2-3 seconds to first query
- Tool execution is now tracked in real-time
- Streaming provides better UX even with slow LLMs
- Progress updates help with perceived latency

## What Changed

### Backend
- Added planning agent node
- Tool-specific progress messages in Spanish/English
- Real-time tool execution tracking
- Plan storage and display in responses

### Frontend  
- Progress bar now shows tool names
- Tool names displayed as `[TOOL_NAME]` in uppercase
- Plan included in final response
- Ready for interactive clarification UI

Enjoy the enhanced experience! 🚀
