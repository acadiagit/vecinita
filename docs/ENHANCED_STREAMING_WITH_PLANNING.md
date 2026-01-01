# Enhanced Streaming with Planning Agent & Tool Progress Display

## Overview

The system now provides **real-time tool-specific progress updates**, a **planning agent** that analyzes queries before execution, and infrastructure for **interactive clarification**. Users see exactly which tool is running with human-readable messages in their language.

## Architecture Overview

```
User Query
    ↓
Frontend → /ask-stream endpoint
    ↓
Backend Streaming Response:
    ├─ [planning] Analyzing your question...
    ├─ [planning] Search plan created
    ├─ [static_response] Checking FAQ...
    ├─ [db_search] Searching database...
    ├─ [clarify_question] Asking clarifying questions...
    ├─ [web_search] Searching the web...
    └─ Final answer + sources + search plan
    ↓
Frontend displays progress bar with tool names
```

## Key Enhancements

### 1. Tool-Specific Progress Messages

**Backend**: `backend/src/agent/main.py` (lines ~140-160)

```python
TOOL_PROGRESS_MESSAGES = {
    'es': {
        'static_response': 'Buscando en preguntas frecuentes...',
        'db_search': 'Buscando en la base de datos...',
        'clarify_question': 'Formulando preguntas de aclaración...',
        'web_search': 'Buscando en internet...',
        'plan': 'Analizando tu pregunta y planificando la búsqueda...'
    },
    'en': {
        'static_response': 'Searching FAQs...',
        'db_search': 'Searching database...',
        'clarify_question': 'Asking clarifying questions...',
        'web_search': 'Searching the web...',
        'plan': 'Analyzing your question and planning the search...'
    }
}

def get_tool_progress_message(tool_name: str, language: str) -> str:
    """Get human-readable progress message for a tool."""
    msgs = TOOL_PROGRESS_MESSAGES.get(language, TOOL_PROGRESS_MESSAGES['en'])
    return msgs.get(tool_name, f'Executing {tool_name}...')
```

**Usage**: When a tool executes, emit:
```python
msg = get_tool_progress_message('db_search', lang_local)
yield f'data: {json.dumps({"type": "progress", "stage": "tool", "tool": "db_search", "message": msg})}\n\n'
```

### 2. Planning Agent Node

**Backend**: `backend/src/agent/main.py` (lines ~338-390)

The `planning_node()` function:
1. Analyzes the user's question
2. Identifies key concepts and search terms
3. Plans which tools to use and in what order
4. Stores the plan in the agent state

```python
def planning_node(state: AgentState) -> AgentState:
    """Planning node that analyzes the question and creates a search strategy."""
    # Calls LLM to create a structured search plan
    # Returns plan text for user visibility
    # Handles errors gracefully (continues without plan if fails)
```

**Integration**: Added to LangGraph workflow:
```python
workflow.add_edge(START, "planning")
workflow.add_edge("planning", "agent")
```

Plans flow: `START → planning → agent → [tools] → agent → END`

### 3. LangGraph Integration

**Backend**: `backend/src/agent/main.py` (lines ~453-463)

Updated workflow now includes planning node:

```python
workflow = StateGraph(AgentState)
workflow.add_node("planning", planning_node)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

workflow.add_edge(START, "planning")
workflow.add_edge("planning", "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")
```

### 4. Enhanced Streaming Endpoint

**Backend**: `backend/src/agent/main.py` (lines ~819-1045)

New `/ask-stream` endpoint supports:

- **Tool-specific progress tracking** via `_execute_agent_with_tool_progress()`
- **Plan visibility** in the response
- **Language-aware messages** (Spanish/English)
- **Interactive clarification** (framework ready)
- **Tool execution monitoring** with real-time updates

Example streaming response flow:

```json
{"type": "progress", "stage": "planning", "tool": "planning", "message": "Analyzing your question..."}
{"type": "progress", "stage": "agent_init", "tool": "agent", "message": "Initializing agent..."}
{"type": "progress", "stage": "tool", "tool": "db_search", "message": "Searching database..."}
{"type": "complete", "answer": "...", "sources": [...], "thread_id": "...", "plan": "..."}
```

### 5. Frontend Progress Bar with Tool Names

**Frontend**: `frontend/src/components/chat/ChatWidget.jsx` (lines ~150-210, ~315-330, ~447-462)

**Updated sendMessage()** function handles:

```javascript
if (update.type === 'progress') {
  setProgress({
    stage: update.stage,
    tool: update.tool,           // NEW: Tool name
    message: update.message      // NEW: Human-readable message
  })
}
```

**Enhanced Progress UI** (both embedded and floating modes):

```jsx
{progress && (
  <div className="flex flex-col gap-2 p-3 text-sm text-muted-foreground animate-pulse">
    <div className="flex items-center gap-3">
      <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
      <div className="flex flex-col gap-1 flex-1">
        {/* NEW: Tool name display */}
        <span className="font-semibold text-primary text-xs uppercase tracking-wide">
          {progress.tool ? `[${progress.tool.replace('_', ' ')}]` : 'Processing...'}
        </span>
        <span>{progress.message}</span>
      </div>
    </div>
    <div className="w-full bg-secondary rounded-full h-1 overflow-hidden">
      <div className="h-full bg-primary animate-pulse" style={{ width: '60%' }} />
    </div>
  </div>
)}
```

**Example display**:
```
[PLANNING]
Analyzing your question...
```

Progress bar animates while processing.

Then:
```
[DB_SEARCH]
Searching database...
```

Finally:
```
[WEB_SEARCH]
Searching the web...
```

## State Management

### AgentState (Enhanced)

```python
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    question: str
    language: str
    provider: str | None
    model: str | None
    plan: str | None  # NEW: Stores planning results
```

## Tool Progress Tracking

### Helper Function

**Backend**: `_execute_agent_with_tool_progress()` (lines ~782-798)

```python
def _execute_agent_with_tool_progress(initial_state, config):
    """Execute agent and yield tool execution updates."""
    executed_tools = set()
    
    for event in graph.stream(initial_state, config, stream_mode="updates"):
        if event:
            for node_name, node_update in event.items():
                if node_name == "tools" and node_update:
                    messages_list = node_update.get("messages", [])
                    for msg in messages_list:
                        if hasattr(msg, 'name') and msg.name:
                            tool_name = msg.name
                            if tool_name not in executed_tools:
                                executed_tools.add(tool_name)
                                yield tool_name
```

Used in streaming endpoint:
```python
for tool_name in _execute_agent_with_tool_progress(initial_state, config):
    if tool_name not in executed_tools:
        executed_tools.add(tool_name)
        tool_msg = get_tool_progress_message(tool_name, lang_local)
        yield f'data: {json.dumps({"type": "progress", "stage": "tool", "tool": tool_name, "message": tool_msg})}\n\n'
```

## Language Support

Both Spanish and English have complete tool progress messages:

**Spanish**:
- `static_response` → "Buscando en preguntas frecuentes..."
- `db_search` → "Buscando en la base de datos..."
- `clarify_question` → "Formulando preguntas de aclaración..."
- `web_search` → "Buscando en internet..."
- `plan` → "Analizando tu pregunta y planificando la búsqueda..."

**English**:
- `static_response` → "Searching FAQs..."
- `db_search` → "Searching database..."
- `clarify_question` → "Asking clarifying questions..."
- `web_search` → "Searching the web..."
- `plan` → "Analyzing your question and planning the search..."

Language is auto-detected from the query or specified via `lang` parameter.

## Interactive Clarification (Framework Ready)

The `/ask-stream` endpoint accepts a `clarification_response` parameter:

```
GET /ask-stream?question=...&clarification_response=...
```

When provided, the response is added to the agent's message history:

```python
if clarification_response:
    messages.append(HumanMessage(
        content=f"Based on your questions, here is my clarification: {clarification_response}"
    ))
```

**Frontend ready to support** receiving clarification questions:
```javascript
else if (update.type === 'clarification') {
  // Display questions to user
  // Wait for response
  // Re-submit with clarification_response parameter
}
```

## Message Format

### Progress Update
```json
{
  "type": "progress",
  "stage": "tool",
  "tool": "db_search",
  "message": "Searching database..."
}
```

### Complete Response
```json
{
  "type": "complete",
  "answer": "Here is the answer...",
  "sources": [
    {
      "title": "Document title...",
      "url": "https://...",
      "type": "document",
      "similarity": 0.95
    }
  ],
  "thread_id": "default",
  "plan": "Search plan text with concepts and strategy..."
}
```

### Error Response
```json
{
  "type": "error",
  "message": "Error description"
}
```

## Testing

### Backend Testing

1. Start backend:
```bash
cd backend
uv run -m uvicorn src.agent.main:app --reload
```

2. Test streaming endpoint:
```bash
curl "http://localhost:8000/ask-stream?query=Where%20can%20I%20find%20resources%20for%20children?"
```

3. Observe tool-specific progress messages in the stream

### Frontend Testing

1. Open frontend UI
2. Send a query like "Where's a doctor near me?"
3. **Verify progress bar shows**:
   - `[PLANNING]` - Analyzing your question...
   - `[DB_SEARCH]` - Searching database...
   - (Optional) `[CLARIFY_QUESTION]` - Asking clarifying questions...
   - (Optional) `[WEB_SEARCH]` - Searching the web...
4. **Final answer displays** with sources

## Files Modified

1. **backend/src/agent/main.py**
   - Added `TOOL_PROGRESS_MESSAGES` dictionary (lines ~140-160)
   - Added `get_tool_progress_message()` function (lines ~162-166)
   - Added `planning_node()` function (lines ~338-390)
   - Updated `AgentState` with `plan` field
   - Updated LangGraph workflow to include planning node
   - Replaced `/ask-stream` endpoint (lines ~819-1045)
   - Added `_execute_agent_with_tool_progress()` helper (lines ~782-798)

2. **frontend/src/components/chat/ChatWidget.jsx**
   - Updated `sendMessage()` to track `tool` in progress state (line ~166-168)
   - Enhanced progress bar UI in embedded mode (lines ~315-330)
   - Enhanced progress bar UI in floating dialog mode (lines ~447-462)
   - Added tool name display with uppercase formatting

## Next Steps

### Immediate (Optional)
- Test streaming with various queries
- Verify tool names display correctly in UI
- Check plan visibility in responses

### Short Term (If Needed)
- Implement interactive clarification UI (show questions, collect answers)
- Add plan display/tooltip in UI showing search strategy
- Performance test with slow LLM providers

### Long Term
- Add more granular progress updates (show specific search terms)
- Calculate estimated time remaining based on historical data
- Cache planning results for similar questions
- Add metrics on tool usage patterns

## Troubleshooting

**Progress bar not showing**:
- Check that `/ask-stream` endpoint is being called (not `/ask`)
- Verify browser console for streaming errors
- Check backend logs for tool execution events

**Tool names not displaying**:
- Ensure `progress.tool` is being set in frontend state
- Check that backend is emitting `"tool": "tool_name"` in progress messages

**Plans not visible**:
- Verify `plan` field is included in complete response
- Check if planning_node is executing (search logs for "Search plan created")

**No streaming updates**:
- Ensure LLM provider is configured (Groq, Ollama, etc.)
- Check for rate limiting errors
- Verify TextDecoder is working in browser (Chrome 43+, Firefox 19+)

## Architecture Diagram

```
LangGraph Workflow:
┌─────────────────────────────────────────────────┐
│ START                                           │
│   ↓                                             │
│ [planning_node]                                 │
│   Analyzes question → creates search plan       │
│   Stores plan in state                          │
│   ↓                                             │
│ [agent_node]                                    │
│   Calls LLM with tools available                │
│   ↓                                             │
│ [conditional_edges]                             │
│   Has tool calls? → YES → [tools_node]          │
│                           ↓                     │
│                     Execute tools               │
│                           ↓                     │
│                      Back to agent              │
│   Has tool calls? → NO → END                    │
└─────────────────────────────────────────────────┘

Streaming Flow:
┌─────────────────────────────────────────────────┐
│ SSE Connection                                  │
│   ↓                                             │
│ yield: {"type": "progress", ... "planning" ...}│
│   ↓                                             │
│ yield: {"type": "progress", ... "db_search" ...}
│   ↓                                             │
│ yield: {"type": "complete", ... "plan": ...}   │
│   ↓                                             │
│ Connection closes                               │
└─────────────────────────────────────────────────┘
```

## Summary

The system now provides:

✅ **Tool visibility**: Users see exactly which tool is running  
✅ **Human-readable messages**: In user's language (Spanish/English)  
✅ **Planning phase**: Questions analyzed before tool execution  
✅ **Search transparency**: Plan shared with user showing strategy  
✅ **Real-time feedback**: Progress updates via SSE streaming  
✅ **Interactive framework**: Ready for clarification questions  
✅ **Error resilience**: Graceful handling of planning failures  

This creates a more transparent, responsive, and user-friendly Q&A assistant experience.
