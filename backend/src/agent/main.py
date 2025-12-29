# main.py
# FastAPI application for the Vecinita RAG Q&A system.
# This version includes an explicit rule for response language.
# Serves the index.html UI at the root "/" endpoint.

import os
import json
import time
import logging
import traceback
from pathlib import Path
from fastapi.responses import FileResponse, JSONResponse
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Annotated, List, TypedDict
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
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
from .tools.static_response import static_response_tool, list_faqs
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
openai_api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_API_KEY")
ollama_base_url = os.environ.get("OLLAMA_BASE_URL")
ollama_model = os.environ.get("OLLAMA_MODEL") or "llama3.2"
if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL and key must be set.")

# --- Initialize Clients ---
try:
    logger.info("Initializing Supabase client...")
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client initialized successfully")

    # Initialize default LLM: prefer local Llama (Ollama), fallback to Groq Llama, then OpenAI
    if ollama_base_url:
        logger.info("Initializing ChatOllama (Llama) LLM...")
        llm = ChatOllama(temperature=0, model=ollama_model, base_url=ollama_base_url)
        logger.info(f"ChatOllama initialized successfully (model={ollama_model})")
    elif groq_api_key:
        logger.info("Initializing ChatGroq LLM (Llama default)...")
        llm = ChatGroq(temperature=0, groq_api_key=groq_api_key,
                       model_name="llama-3.1-8b-instant")
        logger.info("ChatGroq LLM initialized successfully")
    elif openai_api_key:
        logger.info("Initializing ChatOpenAI LLM...")
        llm = ChatOpenAI(temperature=0, api_key=openai_api_key, model="gpt-4o-mini")
        logger.info("ChatOpenAI LLM initialized successfully")
    else:
        raise RuntimeError("No LLM provider configured. Set OLLAMA_BASE_URL or GROQ_API_KEY or OPENAI_API_KEY/OPEN_API_KEY.")

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
    provider: str | None
    model: str | None


# --- Initialize Tools ---
logger.info("Initializing agent tools...")
db_search_tool = create_db_search_tool(supabase, embedding_model)
web_search_tool = create_web_search_tool()
tools = [db_search_tool,
         static_response_tool, web_search_tool]
logger.info(f"Initialized {len(tools)} tools: {[tool.name for tool in tools]}")

def _get_llm_with_tools(provider: str | None, model: str | None):
    """Create an LLM bound with tools based on requested provider/model.

    Supported providers: 'llama' (Ollama preferred, Groq fallback), 'openai'.
    Defaults: provider='llama', model from OLLAMA_MODEL or 'llama3.2';
    for OpenAI, default model='gpt-4o-mini'.
    """
    selected_provider = (provider or "llama").lower()
    if selected_provider == "llama":
        # Prefer local Ollama
        if ollama_base_url:
            use_model = model or ollama_model or "llama3.2"
            local_llm = ChatOllama(temperature=0, model=use_model, base_url=ollama_base_url)
            return local_llm.bind_tools(tools)
        # Fallback to Groq-hosted Llama if available
        if groq_api_key:
            use_model = model or "llama-3.1-8b-instant"
            groq_llm = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name=use_model)
            return groq_llm.bind_tools(tools)
        # Last resort: if nothing available, raise
        raise RuntimeError("Llama provider requested but neither Ollama nor Groq are configured.")
    elif selected_provider == "openai":
        if not openai_api_key:
            raise RuntimeError("OpenAI provider requested but OPENAI_API_KEY/OPEN_API_KEY is not set.")
        use_model = model or "gpt-4o-mini"
        openai_llm = ChatOpenAI(temperature=0, api_key=openai_api_key, model=use_model)
        return openai_llm.bind_tools(tools)
    else:
        raise RuntimeError(f"Unsupported provider: {selected_provider}. Use 'llama' or 'openai'.")

# --- Define Agent Node ---


def agent_node(state: AgentState) -> AgentState:
    """Agent node that calls the LLM with tool binding."""
    logger.info("Agent node: Processing messages...")
    # Select LLM per request
    llm_with_tools = _get_llm_with_tools(state.get("provider"), state.get("model"))
    # Rate-limit handling: retry on Groq 429 errors with suggested wait
    # Import groq lazily to avoid hard dependency in environments where it's unavailable
    try:
        import re
        import groq  # type: ignore
    except Exception:
        re = None
        groq = None

    attempts = 0
    max_attempts = 3
    last_exc = None
    while attempts < max_attempts:
        try:
            response = llm_with_tools.invoke(state["messages"])
            return {"messages": [response]}
        except Exception as e:
            last_exc = e
            is_rate_limit = e.__class__.__name__ == "RateLimitError" or (
                groq is not None and isinstance(
                    e, getattr(groq, "RateLimitError", Exception))
            )
            if not is_rate_limit:
                raise
            # Parse suggested wait time from message, fallback to 5s
            wait_seconds = 5.0
            msg = str(e)
            if re is not None:
                m = re.search(r"try again in ([0-9]+(?:\.[0-9]+)?)s", msg)
                if m:
                    try:
                        wait_seconds = float(m.group(1))
                    except Exception:
                        pass
            logger.warning(
                f"Groq rate limit hit. Waiting {wait_seconds:.2f}s before retry ({attempts+1}/{max_attempts})."
            )
            time.sleep(wait_seconds)
            attempts += 1
    # If all retries failed, re-raise the last exception
    raise last_exc


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

# --- Helper: Deterministic static FAQ matcher ---


def _find_static_faq_answer(question: str, language: str) -> str | None:
    try:
        import string
        import unicodedata
        q = question.lower().strip()
        table = str.maketrans('', '', string.punctuation + "¿¡")
        q_clean = q.translate(table)
        # Remove accents for robust matching

        def _unaccent(s: str) -> str:
            return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
        q_unaccent = _unaccent(q_clean)
        faqs = list_faqs(language) or {}
        # Exact match against original
        if q in faqs:
            return faqs[q]
        # Exact match against cleaned
        for k, v in faqs.items():
            if k.translate(table) == q_clean:
                return v
        # Partial match using cleaned strings
        if len(q_clean) >= 10:
            for k, v in faqs.items():
                k_clean = k.translate(table)
                k_unaccent = _unaccent(k_clean)
                if (
                    k_clean in q_clean or q_clean in k_clean or
                    k_unaccent in q_unaccent or q_unaccent in k_unaccent
                ):
                    return v
        return None
    except Exception:
        return None

# --- THIS IS THE NEW ROOT ENDPOINT ---


@app.get("/", response_class=FileResponse)
async def get_ui():
    """Serves the main chat UI (index.html). Falls back to alternate locations if needed."""
    # Primary: alongside this module (backend/src/agent/static/index.html)
    primary = Path(__file__).parent / "static" / "index.html"
    # Fallback: legacy root layout (repo/src/agent/static/index.html)
    legacy = Path(__file__).parents[3] / "src" / \
        "agent" / "static" / "index.html"
    for candidate in (primary, legacy):
        if candidate.exists():
            return FileResponse(candidate)
    # Provide a helpful error if the UI file is missing
    raise HTTPException(
        status_code=404,
        detail=(
            "UI not found. Checked: "
            f"{primary} and {legacy}. "
            "If you are using the separate frontend, open http://localhost:3000. "
            "For local backend dev after the repo restructure, run from the backend folder: "
            "'cd backend && uv run -m uvicorn src.agent.main:app --reload'"
        ),
    )
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


@app.get("/health")
async def health():
    """Simple healthcheck endpoint used by Docker Compose."""
    return {"status": "ok"}


@app.get("/ask")
async def ask_question(
    question: str | None = Query(default=None),
    query: str | None = Query(default=None),
    thread_id: str = "default",
    lang: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    model: str | None = Query(default=None),
):
    """Handles Q&A requests from the UI or API using LangGraph agent"""
    # Accept both 'question' and legacy 'query' parameter names
    if question is None and query is not None:
        question = query
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question parameter cannot be empty. Use 'question' or 'query'.",
        )

    try:
        # Detect language unless explicitly provided
        if not lang:
            try:
                lang = detect(question)
            except LangDetectException:
                lang = "en"
                logger.warning(
                    "Language detection failed for question: '%s'. Defaulting to English.", question)
            # Heuristic override: treat as Spanish if question contains Spanish punctuation or accents
            if lang != 'es':
                if any(ch in question for ch in ['¿', '¡', 'á', 'é', 'í', 'ó', 'ú', 'ñ']):
                    lang = 'es'

        logger.info(
            f"\n--- New request received: '{question}' (Detected Language: {lang}, Thread: {thread_id}) ---")

        # Try static response first for deterministic FAQ handling in both languages
        local_static = _find_static_faq_answer(question, lang)
        if local_static:
            logger.info("Returning static FAQ answer (local matcher).")
            return {"answer": local_static, "thread_id": thread_id}
        # Fallback to tool-based static matcher (optional)
        try:
            static_answer = static_response_tool.invoke({
                "query": question,
                "language": lang
            })
            if static_answer:
                logger.info(
                    "Returning static FAQ answer without invoking agent (tool).")
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
            "language": lang,
            "provider": provider,
            "model": model,
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

        # Aggregate structured sources from tools (db + web)
        sources: list[dict] = []
        try:
            # DB sources
            db_results = db_search_tool.invoke({"query": question})
            if isinstance(db_results, str) and db_results:
                db_results = json.loads(db_results)
            if isinstance(db_results, list):
                for d in db_results[:5]:
                    url = d.get("source_url") or ""
                    if url:
                        entry = {
                            "title": d.get("title") or "Internal Document",
                            "url": url,
                            "type": "document",
                        }
                        lower = url.lower()
                        entry["isDownload"] = any(lower.endswith(ext) for ext in [
                            ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv"
                        ])
                        sources.append(entry)
        except Exception:
            pass

        try:
            # Web sources
            web_results = web_search_tool.invoke({"query": question})
            if isinstance(web_results, str) and web_results:
                web_results = json.loads(web_results)
            if isinstance(web_results, list):
                for r in web_results[:5]:
                    url = r.get("url") or ""
                    if url:
                        entry = {
                            "title": r.get("title") or "Web Result",
                            "url": url,
                            "type": "link",
                            "isDownload": url.lower().endswith(".pdf"),
                        }
                        sources.append(entry)
        except Exception:
            pass

        return {"answer": answer, "sources": sources, "thread_id": thread_id}

    except Exception as e:
        logger.error("Error processing question '%s': %s", question, str(e))
        logger.error("Full traceback:\n%s", traceback.format_exc())
        # Graceful handling of Groq rate limits: return a friendly message instead of 500
        try:
            import re
            import groq  # type: ignore
        except Exception:
            re = None
            groq = None
        is_rate_limit = e.__class__.__name__ == "RateLimitError" or (
            groq is not None and isinstance(
                e, getattr(groq, "RateLimitError", Exception))
        )
        if is_rate_limit:
            wait_seconds = 10.0
            msg = str(e)
            if re is not None:
                m = re.search(r"try again in ([0-9]+(?:\.[0-9]+)?)s", msg)
                if m:
                    try:
                        wait_seconds = float(m.group(1))
                    except Exception:
                        pass
            # Language-aware fallback
            if 'lang' in locals() and lang == 'es':
                fallback = (
                    f"El asistente está limitado por tasa temporalmente. Intenta nuevamente en {wait_seconds:.0f} segundos. "
                    "Si necesitas una descripción rápida: Vecinita es un asistente comunitario de preguntas y respuestas (Q&A)."
                )
            else:
                fallback = (
                    f"The assistant is temporarily rate limited. Please try again in {wait_seconds:.0f} seconds. "
                    "Quick summary: Vecinita is a community Q&A assistant."
                )
            return {"answer": fallback, "thread_id": thread_id}
        # Non-rate-limit errors: propagate as HTTP 500
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

@app.get("/config")
def config():
    """Expose available providers/models based on environment for frontend discovery."""
    providers = []
    models = {}
    # Llama via Ollama/Groq
    try:
        providers.append({"key": "llama", "label": "Llama"})
        models["llama"] = [ollama_model or "llama3.2"]
    except Exception:
        pass
    # OpenAI if key present
    if openai_api_key:
        providers.append({"key": "openai", "label": "OpenAI"})
        models["openai"] = ["gpt-4o-mini"]
    return {"providers": providers, "models": models}

# --end-of-file--
