import os
import logging
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Graph and Tool Imports
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
import operator

# LLM and Database Imports
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from supabase import create_client, Client
from dotenv import load_dotenv

# Tool Imports
from src.agent.tools.db_search import create_db_search_tool
from src.agent.tools.web_search import create_web_search_tool
from src.agent.tools.static_response import static_response_tool
# FIX: Use the correct function name found in the file
from src.agent.data.agent_rules import get_system_rules

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Initialization ---
logger.info("Initializing Supabase client...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logger.info("Supabase client initialized successfully")

logger.info("Initializing ChatGroq LLM...")
llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant", groq_api_key=GROQ_API_KEY)
logger.info("ChatGroq LLM initialized successfully")

logger.info("Initializing embedding model: sentence-transformers/all-MiniLM-L6-v2...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
logger.info("Embedding model initialized successfully (HuggingFace)")

# --- Tools Setup ---
logger.info("Initializing agent tools...")

# Create the tool instances using the factory functions
db_search = create_db_search_tool(supabase, embeddings)
web_search = create_web_search_tool()

tools = [db_search, static_response_tool, web_search]
llm_with_tools = llm.bind_tools(tools)
logger.info(f"Initialized {len(tools)} tools: {[t.name for t in tools]}")

# --- Graph Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]

def agent_node(state: AgentState):
    logger.info("Agent node: Processing messages...")
    try:
        # Inject the system prompt fresh for every turn using the correct function name
        system_prompt = get_system_rules()
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"Error in agent_node: {e}")
        raise e

def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        logger.info(f"Agent decided to use tools: {len(last_message.tool_calls)} calls")
        return "tools"
    logger.info("Agent decided to end conversation")
    return END

logger.info("Building LangGraph workflow...")
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
from langgraph.prebuilt import ToolNode
tool_node = ToolNode(tools)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)
workflow.add_edge("tools", "agent")

graph = workflow.compile()
logger.info("LangGraph workflow compiled successfully")

# --- FastAPI Setup ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str

@app.get("/ask")
async def ask_question_get(question: str):
    return await ask_question(question)

@app.post("/ask")
async def ask_question_post(request: QuestionRequest):
    return await ask_question(request.question)

async def ask_question(question: str):
    logger.info(f"\n--- New request received: '{question}' (Detected Language: en, Thread: new) ---")
    
    try:
        initial_state = {"messages": [("user", question)]}
        
        # Unique Thread ID for every request to prevent memory bloat
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        
        result = graph.invoke(initial_state, config)
        
        final_message = result["messages"][-1].content
        logger.info("Agent execution completed")
        logger.info(f"Agent response: {final_message[:200]}...")
        
        return {"answer": final_message, "thread_id": config["configurable"]["thread_id"]}
        
    except Exception as e:
        logger.error(f"Error processing question '{question}': {e}")
        logger.error("Full traceback:", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
# Mount the static directory to serve index.html at the root
# Updated to point to the location we found: src/agent/static
static_path = "src/agent/static"

if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
    logger.info(f"Serving frontend from {static_path}")
elif os.path.exists("vecinita-ui/dist"):
     app.mount("/", StaticFiles(directory="vecinita-ui/dist", html=True), name="static")
else:
    logger.warning(f"No static frontend directory found at {static_path} or vecinita-ui/dist. Running API only.")
