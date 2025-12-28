# main.py
# FastAPI application for the Vecinita RAG Q&A system.
# This version includes an explicit rule for response language.
# Serves the index.html UI at the root "/" endpoint.

import os
import time
import logging
import traceback
from pathlib import Path
from fastapi.responses import FileResponse, JSONResponse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Annotated, List, TypedDict
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langdetect import detect, LangDetectException
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# Import tools
from .tools.db_search import create_db_search_tool
from .tools.static_response import static_response_tool
from .tools.web_search import create_web_search_tool

# Load environment variables from .env file
load_dotenv()

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Initialize FastAPI App ---
app = FastAPI()

# --- Add CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# --- Mount Static Files ---
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# --- Load Environment Variables & Validate ---
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
groq_api_key = os.environ.get("GROQ_API_KEY")
if not supabase_url or not supabase_key or not groq_api_key:
    raise ValueError("Supabase, Groq keys, and URL must be set.")

# --- Initialize Clients ---
try:
    logger.info("Initializing Supabase client...")
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client initialized successfully")

    logger.info("Initializing ChatGroq LLM...")
    llm = ChatGroq(temperature=0, groq_api_key=groq_api_key,
                   model_name="llama-3.1-8b-instant")
    logger.info("ChatGroq LLM initialized successfully")

    # Use all-MiniLM-L6-v2 with 384 dimensions by default.
    # If sentence-transformers is unavailable (CI minimal deps), fall back to FastEmbed.
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    logger.info(f"Initializing embedding model: {model_name}...")
    try:
        embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        logger.info("Embedding model initialized successfully (HuggingFace)")
    except Exception as emb_exc:
        logger.warning(
            f"HuggingFaceEmbeddings unavailable ({emb_exc}); falling back to FastEmbedEmbeddings."
        )
        embedding_model = FastEmbedEmbeddings()
        logger.info("Embedding model initialized successfully (FastEmbed)")
except Exception as e:
    logger.error(f"Failed to initialize clients: {e}")
    logger.error(traceback.format_exc())
    raise RuntimeError(f"Failed to initialize clients: {e}")

# --- Define LangGraph State ---


class AgentState(TypedDict):
    """State for the Vecinita agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    question: str
    language: str


# --- Initialize Tools ---
logger.info("Initializing agent tools...")
db_search_tool = create_db_search_tool(supabase, embedding_model)
web_search_tool = create_web_search_tool()
tools = [db_search_tool,
         static_response_tool, web_search_tool]
logger.info(f"Initialized {len(tools)} tools: {[tool.name for tool in tools]}")

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# --- Define Agent Node ---


def agent_node(state: AgentState) -> AgentState:
    """Agent node that calls the LLM with tool binding."""
    logger.info("Agent node: Processing messages...")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """Determine if the agent should continue or end."""
    last_message = state["messages"][-1]
    # If there are no tool calls, we're done
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return END
    return "tools"


# --- Build LangGraph ---
logger.info("Building LangGraph workflow...")
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

# Add edges
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")

# Compile with memory
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
logger.info("LangGraph workflow compiled successfully")

# --- API Endpoints ---

# --- THIS IS THE NEW ROOT ENDPOINT ---


@app.get("/", response_class=FileResponse)
async def get_ui():
    """Serves the main chat UI (index.html)"""
    # Get the directory of this file and construct the path to index.html
    index_path = Path(__file__).parent / "static" / "index.html"
    if not index_path.exists():
        # Provide a helpful error if the UI file is missing
        raise HTTPException(
            status_code=404,
            detail=f"UI not found. Expected file at: {index_path}. Ensure the static assets are built and available.",
        )
    return FileResponse(index_path)
# --- OLD "/ui" ENDPOINT IS NOW THE ROOT ---


@app.get("/favicon.ico", response_class=FileResponse)
async def get_favicon():
    """Serves the favicon"""
    favicon_path = Path(__file__).parent / "static" / "favicon.ico"
    if not favicon_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Favicon not found. Expected file at: {favicon_path}. Ensure the static assets are available.",
        )
    return FileResponse(favicon_path)


@app.get("/ask")
async def ask_question(question: str, thread_id: str = "default"):
    """Handles Q&A requests from the UI or API using LangGraph agent"""
    if not question:
        raise HTTPException(
            status_code=400, detail="Question parameter cannot be empty.")

    try:
        # Detect language
        try:
            lang = detect(question)
        except LangDetectException:
            lang = "en"
            logger.warning(
                f"Language detection failed for question: '{question}'. Defaulting to English.")

        logger.info(
            f"\n--- New request received: '{question}' (Detected Language: {lang}, Thread: {thread_id}) ---")

        # Try static response first for deterministic FAQ handling in both languages
        try:
            static_answer = static_response_tool.invoke({
                "query": question,
                "language": lang
            })
            if static_answer:
                logger.info(
                    "Returning static FAQ answer without invoking agent.")
                return {"answer": static_answer, "thread_id": thread_id}
        except Exception as static_exc:
            logger.warning(f"Static response check failed: {static_exc}")

        # Build system prompt based on language
        if lang == 'es':
            system_prompt = """
            Eres un asistente comunitario, servicial y profesional para el proyecto Vecinita.
            Tu objetivo es dar respuestas claras, concisas y precisas basadas en la información disponible.

            HERRAMIENTAS DISPONIBLES:
            1. static_response_tool: Usa PRIMERO para preguntas frecuentes sobre Vecinita
            2. db_search: Busca en la base de datos interna de documentos comunitarios
            3. web_search: Usa como ÚLTIMO RECURSO para buscar información externa

            REGLAS A SEGUIR:
            1. Intenta primero con static_response_tool para preguntas sobre Vecinita
            2. Si no hay respuesta estática, usa db_search para buscar en documentos internos
            3. Usa web_search como ÚLTIMO RECURSO para buscar información externa
            4. Al final de tu respuesta, DEBES citar la fuente. Ejemplo: "(Fuente: https://ejemplo.com)"
            5. Si no encuentras información, di: "No pude encontrar una respuesta definitiva en los documentos proporcionados."
            6. Responde SIEMPRE en español
            """
        else:  # Default to English
            system_prompt = """
            You are a helpful and professional community assistant for the Vecinita project.
            Your goal is to provide clear, concise, and accurate answers based on available information.

            AVAILABLE TOOLS:
            1. static_response_tool: Use FIRST for frequently asked questions about Vecinita
            2. db_search: Search the internal database of community documents
            3. web_search: Use as LAST RESORT for external information

            RULES TO FOLLOW:
            1. Try static_response_tool first for questions about Vecinita itself
            2. If no static answer, use db_search to find information in internal documents
            3. Only use web_search if other methods fail
            4. At the end of your answer, you MUST cite sources. Example: "(Source: https://example.com)"
            5. If you cannot find information, state: "I could not find a definitive answer in the provided documents."
            6. Always answer in English
            """

        # Create messages for the agent
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question)
        ]

        # Prepare state
        initial_state = {
            "messages": messages,
            "question": question,
            "language": lang
        }

        # Configure graph execution with thread_id for conversation history
        config = {"configurable": {"thread_id": thread_id}}

        logger.info("Invoking LangGraph agent...")
        result = graph.invoke(initial_state, config)
        logger.info("Agent execution completed")

        # Extract the final answer from messages
        final_message = result["messages"][-1]
        answer = final_message.content if hasattr(
            final_message, "content") else str(final_message)

        logger.info(f"Agent response: {answer[:200]}...")

        return {"answer": answer, "thread_id": thread_id}

    except Exception as e:
        logger.error(f"Error processing question '{question}': {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

# --end-of-file--
