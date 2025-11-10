# Vecinita LangGraph RAG Agent

A minimal retrieval-augmented generation (RAG) agent built with LangGraph for the Vecinita community project. This agent intelligently decides when to retrieve context from the Supabase vectorstore or respond directly to users.

## Architecture

The RAG agent follows this workflow:

```
┌─────────────────────────────────────────────────────────┐
│ 1. User Question                                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Generate Query or Respond                            │
│    - LLM decides: retrieve or respond directly          │
└─────────────────────────────────────────────────────────┘
                         ↓
            ┌────────────┴────────────┐
            ↓                         ↓
┌──────────────────────┐    ┌─────────────────┐
│ 3a. Retrieve Docs    │    │ 3b. Respond     │
│     from Supabase    │    │     Directly    │
└──────────────────────┘    └─────────────────┘
            ↓
┌──────────────────────┐
│ 4. Grade Documents   │
│    - Relevant?       │
└──────────────────────┘
            ↓
    ┌───────┴───────┐
    ↓               ↓
┌─────────┐   ┌──────────────┐
│ 5a. Gen │   │ 5b. Rewrite  │
│  Answer │   │   Question   │
└─────────┘   └──────────────┘
                      ↓
              (Back to step 2)
```

## Features

- **Intelligent Retrieval**: Agent decides when retrieval is needed
- **Document Grading**: Validates relevance of retrieved documents
- **Question Rewriting**: Improves queries that don't yield relevant results
- **Supabase Integration**: Uses your existing vectorstore
- **Multi-language Support**: Prompts for English and Spanish
- **Model Flexibility**: Works with OpenAI (GPT-4o) or Groq (Llama-3.1)

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables** in `.env`:
   ```env
   # Choose your model provider
   OPEN_API_KEY=your_openai_key  # For GPT-4o
   GROQ_API_KEY=your_groq_key    # For Llama-3.1
   
   # Supabase credentials
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_service_role_key
   DATABASE_URL=postgresql://...
   ```

3. **Ensure your Supabase database has the required schema**:
   - Table: `document_chunks`
   - Function: `search_similar_documents(query_embedding, match_threshold, match_count)`

## Usage

### Basic Example

```python
from rag_agent import create_rag_agent

# Initialize the agent
agent = create_rag_agent(
    model_name="llama-3.1-8b-instant",  # or "gpt-4o"
    temperature=0
)

# Ask a question
result = agent.query(
    "What information do you have about the Vecinita community?",
    verbose=True
)

print(result["answer"])
```

### Run the Example Script

```bash
python example_rag_usage.py
```

This will demonstrate:
1. Questions requiring retrieval
2. Simple questions answered directly
3. Interactive mode for testing

### Integration with FastAPI

You can integrate the agent into your existing `main.py`:

```python
from rag_agent import create_rag_agent

# Initialize agent at startup
agent = create_rag_agent()

@app.get("/ask_with_agent")
async def ask_with_agent(question: str):
    result = agent.query(question, verbose=False)
    return {
        "answer": result["answer"],
        "conversation_history": [
            msg.dict() for msg in result["conversation_history"]
        ]
    }
```

## Project Structure

```
vecinita/
├── agent_config.py          # Configuration and prompts
├── supabase_retriever.py    # Custom Supabase retriever
├── rag_agent.py             # Main LangGraph agent
├── example_rag_usage.py     # Example usage script
├── requirements.txt         # Dependencies
└── .env                     # Environment variables
```

## Configuration

Edit `agent_config.py` to customize:

- **Model Settings**: Change model name, temperature
- **Retrieval Parameters**: Adjust similarity threshold, max documents
- **Prompts**: Customize prompts for grading, rewriting, answering

## Key Components

### 1. Supabase Retriever (`supabase_retriever.py`)

Custom LangChain retriever that connects to your Supabase vectorstore:

```python
from supabase_retriever import get_supabase_retriever

retriever = get_supabase_retriever()
docs = retriever.get_relevant_documents("your question")
```

### 2. RAG Agent Nodes (`rag_agent.py`)

- **generate_query_or_respond**: Decides to retrieve or respond
- **grade_documents**: Validates document relevance
- **rewrite_question**: Improves unsuccessful queries
- **generate_answer**: Creates final response with citations

### 3. Configuration (`agent_config.py`)

Centralized prompts and settings for easy customization.

## Troubleshooting

### Import Errors

If you see import errors, install dependencies:
```bash
pip install -U langgraph "langchain[openai]" langchain-community langchain-text-splitters langchain-huggingface
```

### API Key Issues

Ensure your `.env` file has the correct API keys:
- `OPEN_API_KEY` for OpenAI models
- `GROQ_API_KEY` for Groq models
- `SUPABASE_URL` and `SUPABASE_KEY` for database access

### No Documents Retrieved

Check:
1. Your vectorstore has documents loaded (run `vector_loader.py`)
2. Similarity threshold in `agent_config.py` isn't too high
3. Embeddings model matches the one used for indexing

## Advanced Usage

### Visualize the Graph

```python
agent = create_rag_agent()
agent.visualize()  # Requires IPython and graphviz
```

### Custom Model Configuration

```python
agent = create_rag_agent(
    model_name="gpt-4o",
    temperature=0.3
)
```

### Access Conversation History

```python
result = agent.query("What is Vecinita?")
for msg in result["conversation_history"]:
    print(type(msg).__name__, msg)
```

## Next Steps

1. **Add more data**: Use `scraper_to_text.py` to collect more documents
2. **Load into vectorstore**: Use `vector_loader.py` to index new content
3. **Customize prompts**: Edit `agent_config.py` for your use case
4. **Deploy**: Integrate into FastAPI app or deploy as standalone service

## References

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [LangChain Retrievers](https://python.langchain.com/docs/modules/data_connection/retrievers/)
- [Original Tutorial](https://python.langchain.com/docs/tutorials/rag/)

## License

See LICENSE file in the repository.
