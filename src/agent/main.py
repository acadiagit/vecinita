## src/agent/main.py 04/02/2026
import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

# Corrected Imports based on the factory pattern in db_search.py
from src.agent.tools.db_search import create_db_search_tool

# --- 1. Configuration & Environment ---
# Mapping the keys from your .env to the variables the app expects
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# Handle the mismatch: checks for OPEN_API_KEY first, falls back to OPENAI_API_KEY
OPENAI_API_KEY = os.getenv("OPEN_API_KEY") or os.getenv("OPENAI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
    print("❌ ERROR: Missing required environment variables (SUPABASE or OPENAI)")

# --- 2. Initialization ---
app = FastAPI(title="Vecinita API", version="1.0.0")

# Enable CORS for GUI connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize the Search Tool using the Factory
# We use 'text-embedding-3-large' to match your 2574-chunk load
db_search = create_db_search_tool(
    supabase_client=supabase,
    embedding_model="text-embedding-3-large"
)

# --- 3. Data Models ---
class ChatMessage(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]

# --- 4. Endpoints ---

@app.get("/health")
async def health_check():
    """Verify the server is alive and the database is reachable."""
    try:
        supabase.table("document_chunks").select("id", count="exact").limit(1).execute()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatMessage):
    """
    Main RAG endpoint. 
    Uses the db_search tool to query the 2574 chunks in Supabase.
    """
    try:
        # 1. Retrieve relevant context from Supabase
        # The factory-created tool handles the embedding and similarity search
        context = db_search.run(payload.message)
        
        # 2. In a full implementation, you'd pass 'context' and 'message' 
        # to an LLM chain here. For now, we return the retrieved context.
        return {
            "answer": context,
            "sources": ["Providence Resource Vault"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
##END-OF-FILE
