# Quick Start Guide - Vecinita LangGraph RAG Agent

## 🚀 Get Started in 3 Steps

### Step 1: Install Dependencies

```powershell
pip install -r requirements.txt
```

This will install:
- `langgraph` - The graph orchestration framework
- `langchain-openai` - For GPT-4o support
- `langchain-community` - Community integrations
- All other required packages

### Step 2: Verify Setup

```powershell
python setup_check.py
```

This script will check:
- ✅ Environment variables are set correctly
- ✅ All Python packages are installed
- ✅ Supabase connection is working
- ✅ Embedding model can be loaded

**Fix any issues before proceeding!**

### Step 3: Run the Example

```powershell
python example_rag_usage.py
```

This will demonstrate:
1. Questions that require retrieval from vectorstore
2. Simple greetings answered directly (no retrieval)
3. Interactive mode to test your own questions

## 📝 What You Just Built

You now have a **LangGraph RAG agent** that:

1. **Decides** when to retrieve documents vs. respond directly
2. **Retrieves** relevant documents from your Supabase vectorstore
3. **Grades** retrieved documents for relevance
4. **Rewrites** questions if documents aren't relevant
5. **Generates** final answers with source citations

## 🎯 Next Steps

### Option A: Test the Agent

```python
from rag_agent import create_rag_agent

agent = create_rag_agent(model_name="llama-3.1-8b-instant")
result = agent.query("What is in the Vecinita documents?")
print(result["answer"])
```

### Option B: Integrate with FastAPI

See `fastapi_integration_example.py` for code to add to your `main.py`:

```python
from rag_agent import create_rag_agent

# Initialize at startup
rag_agent = create_rag_agent()

# Add new endpoint
@app.get("/ask_agent")
async def ask_with_agent(question: str):
    result = rag_agent.query(question, verbose=False)
    return {"answer": result["answer"]}
```

Then test:
```
http://localhost:8000/ask_agent?question=Hello
```

### Option C: Customize for Your Needs

Edit `agent_config.py` to adjust:
- Prompts (make them more specific to Vecinita)
- Retrieval parameters (similarity threshold, max docs)
- Model settings (temperature, model name)

## 🔍 Understanding the Files

| File | Purpose |
|------|---------|
| `rag_agent.py` | Main LangGraph agent implementation |
| `supabase_retriever.py` | Custom retriever for Supabase |
| `agent_config.py` | Configuration and prompts |
| `example_rag_usage.py` | Example usage script |
| `setup_check.py` | Environment verification |
| `RAG_AGENT_README.md` | Full documentation |

## 🐛 Troubleshooting

### "No module named 'langgraph'"
```powershell
pip install langgraph
```

### "OPEN_API_KEY must be set"
Add to your `.env` file:
```env
OPEN_API_KEY=sk-...
# OR
GROQ_API_KEY=gsk_...
```

### "Could not connect to Supabase"
Check your `.env` file has:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key
```

### "No documents retrieved"
1. Check that you've loaded documents using `vector_loader.py`
2. Lower the similarity threshold in `agent_config.py`
3. Verify your embedding model matches the one used for indexing

## 💡 Tips

1. **Start with Groq** (free tier) using `llama-3.1-8b-instant`
2. **Load sample data** first to test retrieval
3. **Use verbose=True** to see the agent's decision-making process
4. **Compare responses** between original `/ask` and new `/ask_agent`

## 📚 Learn More

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Original Tutorial](https://python.langchain.com/docs/tutorials/rag/)
- Full docs: `RAG_AGENT_README.md`

---

**Ready to go?** Run `python setup_check.py` to verify everything is configured correctly! 🎉
