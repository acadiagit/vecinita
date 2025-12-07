# LangSmith Quick Reference

## Start Tracing in 3 Steps

### 1. Start Your FastAPI Server

```bash
python -m src.main
# or
python scripts/run_fastapi.py
```

### 2. Make a Query

```bash
curl "http://localhost:8000/ask?question=What%20services%20does%20Vecinita%20offer?"
```

### 3. View Trace

Visit: <https://smith.langchain.com/projects/pr-trustworthy-sundial-70>

---

## Key Information

| Item | Value |
|------|-------|
| **Project Name** | `pr-trustworthy-sundial-70` |
| **Dashboard URL** | <https://smith.langchain.com/projects/pr-trustworthy-sundial-70> |
| **Endpoint** | <https://api.smith.langchain.com> |
| **Config Module** | `src/langsmith_config.py` |
| **Status** | ✓ Configured and Ready |

---

## Configuration Files

### Environment Variables (.env)

```env
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=pr-trustworthy-sundial-70
```

### Main Application (src/main.py)

```python
from .langsmith_config import initialize_langsmith

# On startup:
langsmith_config = initialize_langsmith()
print(f"[INFO] LangSmith Status: {langsmith_config['status']}")
```

---

## Common Tasks

### Verify Setup

```bash
python verify_langsmith_only.py
```

### Run Example Agent

```bash
python scripts/langsmith_agent_example.py
```

### Check Dashboard

1. Go to: <https://smith.langchain.com/projects/pr-trustworthy-sundial-70>
2. Look for recent runs
3. Click to inspect traces

### Run with Tracing Disabled (if needed)

```bash
export LANGSMITH_TRACING=false
python scripts/run_fastapi.py
```

---

## What Gets Traced Automatically

✓ FastAPI endpoint calls  
✓ LLM model invocations  
✓ Tool/function calls  
✓ Chain executions  
✓ Token usage  
✓ Execution time  
✓ Error logs  

---

## Viewing Traces

The LangSmith dashboard shows:

1. **Runs Tab** - All traced executions
2. **Datasets Tab** - Test data for evaluation
3. **Evaluators Tab** - Custom evaluation functions
4. **Feedback Tab** - Manual quality feedback

Each trace shows:

- Input question/prompt
- Output/response
- Tools used
- Token count
- Latency
- Errors (if any)

---

## Troubleshooting

**Q: Traces don't appear in dashboard?**  
A: Run `python verify_langsmith_only.py` to check configuration

**Q: How do I disable tracing temporarily?**  
A: Set `LANGSMITH_TRACING=false` in `.env` or terminal

**Q: Where's my API key?**  
A: In `.env` file as `LANGSMITH_API_KEY`

**Q: Can I use multiple projects?**  
A: Yes, change `LANGSMITH_PROJECT` in `.env`

---

## More Information

- Full Setup Guide: `docs/LANGSMITH_SETUP.md`
- Example Agent: `scripts/langsmith_agent_example.py`
- Config Module: `src/langsmith_config.py`
- LangSmith Docs: <https://docs.smith.langchain.com/>

---

**Last Updated**: December 6, 2025
