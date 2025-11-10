# vecinita

VECINA asistan

## 🆕 LangGraph RAG Agent

This project now includes a **LangGraph-based RAG agent** that intelligently decides when to retrieve documents from the Supabase vectorstore.

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Verify setup
python setup_check.py

# Run example
python example_rag_usage.py
```

### Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get started in 3 steps
- **[Full Documentation](RAG_AGENT_README.md)** - Complete guide
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - What we built

### Key Features

✅ Intelligent retrieval - decides when to search vs respond directly  
✅ Document grading - validates relevance  
✅ Question rewriting - improves unsuccessful queries  
✅ Multi-language support - English & Spanish  
✅ Supabase integration - uses your existing vectorstore
