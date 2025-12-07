# main.py
"""
Vecinita FastAPI RAG Q&A System

A FastAPI-based Retrieval-Augmented Generation (RAG) system that provides intelligent
question-answering capabilities for the Vecinita community project. The system retrieves
relevant documents from a Supabase vector store and uses advanced language models to
generate context-aware, accurate responses.

Features:
    - Multi-language support (English & Spanish with automatic detection)
    - Multiple LLM providers with intelligent fallback (Groq, OpenAI, Ollama)
    - Vector-based document retrieval from Supabase
    - CORS support for cross-origin requests
    - Comprehensive error handling and logging
    - RESTful API with Swagger documentation

Environment Variables:
    SUPABASE_URL (required): Supabase project URL
    SUPABASE_KEY (required): Supabase API key
    GROQ_API_KEY (optional): Groq API key for LLM access
    OPEN_API_KEY (optional): OpenAI API key for GPT models
    OLLAMA_BASE_URL (optional): Local Ollama server URL (default: http://localhost:11434)
    OLLAMA_MODEL (optional): Model to use with Ollama (default: llama3.2)

API Endpoints:
    GET / - Health check and welcome message
    GET /ask?question=<str> - Query the RAG system with a question

Example Usage:
    curl "http://localhost:8000/ask?question=What%20services%20does%20Vecinita%20offer?"
    curl "http://localhost:8000/ask?question=¿Qué%20servicios%20ofrece%20Vecinita?"

Author: Vecinita Team
Version: 1.0.0
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langdetect import detect, LangDetectException
from .langsmith_config import initialize_langsmith

try:
    from langchain_ollama import OllamaLLM
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("[WARNING] Ollama not available. Install with: pip install langchain-ollama")

# Load environment variables from .env file
load_dotenv()

# --- Initialize LangSmith for Tracing and Monitoring ---
langsmith_config = initialize_langsmith()
print(f"[INFO] LangSmith Status: {langsmith_config['status']}")
if langsmith_config['tracing_enabled']:
    print(f"[INFO] Traces will be sent to project: {langsmith_config['project']}")


# --- Pydantic Response Models ---
class DocumentSource(BaseModel):
    """
    Represents a source document used in the RAG pipeline.

    Attributes:
        source (str): URL or identifier of the document source
        content (str): Text content of the document snippet
    """
    source: str = Field(...,
                        description="URL or identifier of the source document")
    content: str = Field(...,
                         description="Text content from the source document")

    class Config:
        json_schema_extra = {
            "example": {
                "source": "https://vecinita.org/services",
                "content": "Vecinita provides community support services including..."
            }
        }


class HealthResponse(BaseModel):
    """
    Health check response model.

    Attributes:
        status (str): Status of the API ("ok" when healthy)
        message (str): Welcome message or additional status information
    """
    status: str = Field(..., description="API status indicator")
    message: str = Field(..., description="Welcome message or status details")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "message": "Welcome to the Vecinita Q&A API!"
            }
        }


class AskResponse(BaseModel):
    """
    Response model for the /ask endpoint.

    This model represents the complete response from the RAG system,
    including the generated answer and the source documents used.

    Attributes:
        answer (str): The generated answer to the user's question,
                     including source citations
        context (List[DocumentSource]): List of source documents that
                                       were used to generate the answer
    """
    answer: str = Field(
        ...,
        description="Generated answer with source citations",
        example="Vecinita offers community services including..."
    )
    context: List[DocumentSource] = Field(
        default_factory=list,
        description="Source documents used to answer the question"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Vecinita offers community services including education, healthcare, and social support. (Source: https://vecinita.org/services)",
                "context": [
                    {
                        "source": "https://vecinita.org/services",
                        "content": "Our services include education programs, healthcare access..."
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """
    Error response model for API errors.

    Attributes:
        detail (str): Detailed error message
        status_code (int): HTTP status code
    """
    detail: str = Field(..., description="Error message details")
    status_code: int = Field(..., description="HTTP status code")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Question parameter cannot be empty.",
                "status_code": 400
            }
        }


# --- Initialize FastAPI App ---
app = FastAPI(
    title="Vecinita Q&A API",
    description="Retrieval-Augmented Generation (RAG) system for community Q&A",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# --- Add CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# --- Load Environment Variables & Validate ---
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
groq_api_key = os.environ.get("GROQ_API_KEY")
openai_api_key = os.environ.get("OPEN_API_KEY")
ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2")

print(f"[DEBUG] SUPABASE_URL: {'✓ set' if supabase_url else '✗ MISSING'}")
print(f"[DEBUG] SUPABASE_KEY: {'✓ set' if supabase_key else '✗ MISSING'}")
print(f"[DEBUG] GROQ_API_KEY: {'✓ set' if groq_api_key else '✗ MISSING'}")
print(f"[DEBUG] OPEN_API_KEY: {'✓ set' if openai_api_key else '✗ MISSING'}")
print(f"[DEBUG] OLLAMA_BASE_URL: {ollama_base_url}")
print(f"[DEBUG] OLLAMA_MODEL: {ollama_model}")

if not supabase_url or not supabase_key:
    missing = []
    if not supabase_url:
        missing.append("SUPABASE_URL")
    if not supabase_key:
        missing.append("SUPABASE_KEY")
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing)}. Check your .env file.")

if not groq_api_key and not openai_api_key and not OLLAMA_AVAILABLE:
    raise ValueError(
        "At least one LLM provider is required: GROQ_API_KEY, OPEN_API_KEY, or local Ollama. "
        "Install Ollama from https://ollama.ai or set an API key in .env file."
    )

# --- Initialize Clients ---
# Store multiple LLM options with priority: API services first, local LLM as final fallback
llm_primary = None
llm_fallback = None
llm_local = None

try:
    print("[DEBUG] Initializing Supabase client...")
    supabase: Client = create_client(supabase_url, supabase_key)
    print("[DEBUG] Supabase client initialized.")

    # Try to initialize Groq first (faster, free tier available)
    if groq_api_key:
        try:
            print("[DEBUG] Initializing ChatGroq LLM (primary)...")
            llm_primary = ChatGroq(
                temperature=0,
                groq_api_key=groq_api_key,
                model_name="llama-3.1-8b-instant"
            )
            print("[DEBUG] ✓ ChatGroq LLM initialized as primary.")
        except Exception as e:
            print(f"[WARNING] Failed to initialize Groq: {e}")

    # Initialize OpenAI as fallback or primary
    if openai_api_key:
        try:
            print("[DEBUG] Initializing ChatOpenAI LLM (fallback)...")
            openai_llm = ChatOpenAI(
                temperature=0,
                api_key=openai_api_key,
                model_name="gpt-4o-mini"
            )
            if llm_primary is None:
                llm_primary = openai_llm
                print("[DEBUG] ✓ ChatOpenAI LLM initialized as primary.")
            else:
                llm_fallback = openai_llm
                print("[DEBUG] ✓ ChatOpenAI LLM initialized as fallback.")
        except Exception as e:
            print(f"[WARNING] Failed to initialize OpenAI: {e}")

    # Initialize local Ollama as final fallback
    if OLLAMA_AVAILABLE:
        try:
            print("[DEBUG] Initializing Ollama (local LLM)...")
            llm_local = OllamaLLM(
                model=ollama_model,
                base_url=ollama_base_url,
                temperature=0
            )
            # Quick test to see if Ollama is actually running
            test_response = llm_local.invoke("test")
            print("[DEBUG] ✓ Ollama LLM initialized and responding.")

            # If no API services available, promote local to primary
            if llm_primary is None:
                llm_primary = llm_local
                llm_local = None
                print(
                    "[DEBUG] ✓ Ollama LLM promoted to primary (no API keys available).")
        except Exception as e:
            print(f"[WARNING] Ollama not available or not running: {e}")
            print(
                "[INFO] To use local LLM, install Ollama from https://ollama.ai and run: ollama pull llama3.2")
            llm_local = None

    if llm_primary is None:
        raise RuntimeError(
            "No LLM could be initialized. Options:\n"
            "1. Set GROQ_API_KEY or OPEN_API_KEY in .env file\n"
            "2. Install and run Ollama: https://ollama.ai"
        )

    # Try to load embeddings - use FastEmbed as primary (HuggingFace has numpy 2.x conflicts)
    print("[DEBUG] Loading embeddings model...")
    embedding_model = None
    try:
        print("[DEBUG] Attempting to load FastEmbed embeddings model...")
        from fastembed.embedding import FlagEmbedding
        embedding_model = FlagEmbedding(model_name="BAAI/bge-small-en-v1.5", cache_dir=None)
        print("[DEBUG] ✓ FastEmbed embeddings loaded successfully.")
    except ImportError as e:
        print(f"[WARNING] FastEmbed not available: {e}")
        print("[INFO] To enable embeddings: pip install fastembed")
        print("[INFO] Continuing without embeddings - RAG functionality will be limited")
        embedding_model = None
    
    if embedding_model is None:
        print("[WARNING] No embedding model loaded. RAG retrieval will be disabled.")
except Exception as e:
    print(f"[ERROR] Failed to initialize clients: {e}")
    raise RuntimeError(f"Failed to initialize clients: {e}")

# --- API Endpoints ---


@app.get("/")
def read_root():
    """
    Root endpoint - redirects to ReDoc documentation.

    Returns:
        RedirectResponse: Redirects to /redoc
    """
    return RedirectResponse(url="/redoc")


@app.get("/ask", response_model=AskResponse)
async def ask_question(question: str):
    """
    Ask a question and receive an answer based on the Vecinita knowledge base.

    This endpoint implements a Retrieval-Augmented Generation (RAG) workflow:
    1. Detects the question language (English or Spanish)
    2. Generates embeddings for the question
    3. Searches Supabase vector store for relevant documents
    4. Uses an LLM to generate a contextual answer based on retrieved documents
    5. Returns the answer with source citations

    The system supports multiple LLM providers with automatic fallback:
    - Primary: Groq (fast, free tier available)
    - Fallback: OpenAI (GPT-4 class models)
    - Local: Ollama (offline capability)

    Args:
        question (str): The user's question (required parameter).
                       Supports both English and Spanish.

    Returns:
        AskResponse: Response containing:
            - answer (str): The generated answer with source citations
            - context (List[DocumentSource]): List of source documents used to answer the question

    Raises:
        HTTPException 400: If question parameter is empty
        HTTPException 503: If all LLM providers fail
        HTTPException 500: For other unexpected errors

    Examples:
        English Query:
            GET /ask?question=What%20services%20does%20Vecinita%20offer?

            Response:
            {
                "answer": "Vecinita offers community services including... (Source: https://example.com)",
                "context": [
                    {"source": "https://example.com", "content": "..."}
                ]
            }

        Spanish Query:
            GET /ask?question=¿Qué%20servicios%20ofrece%20Vecinita?

            Response (in Spanish):
            {
                "answer": "Vecinita ofrece servicios comunitarios incluyendo... (Fuente: https://example.com)",
                "context": [...]
            }

    Note:
        - Questions are automatically detected for language
        - Responses are generated in the detected language
        - All answers include source citations
        - The system retrieves top 5 relevant documents (match_count: 5)
        - Relevance threshold is 0.3 on similarity score
    """
    if not question:
        raise HTTPException(
            status_code=400, detail="Question parameter cannot be empty.")

    try:
        lang = detect(question)
    except LangDetectException:
        lang = "en"

    print(
        f"\n--- New request received: '{question}' (Detected Language: {lang}) ---")

    try:
        # --- Greeting/Casual Question Detection ---
        greeting_keywords_en = [
            'hello', 'hi', 'hey', 'what\'s up', 'whats up', 'how are you', 'how\'re you',
            'yo', 'sup', 'wassup', 'good morning', 'good afternoon', 'good evening',
            'greetings', 'howdy', 'aloha', 'welcome', 'thanks', 'thank you'
        ]
        greeting_keywords_es = [
            'hola', 'holas', 'hey', '¿qué tal?', 'que tal', '¿cómo estás?', 'como estás',
            '¿cómo está?', 'como está', 'buenos días', 'buenas tardes', 'buenas noches',
            'buenos días', 'gracias', 'muchas gracias', 'harlequin', 'saludos'
        ]

        question_lower = question.lower().strip()
        is_greeting = False

        if lang == 'es':
            is_greeting = any(
                kw in question_lower for kw in greeting_keywords_es)
        else:
            is_greeting = any(
                kw in question_lower for kw in greeting_keywords_en)

        # If greeting detected, respond directly without document search
        if is_greeting:
            print("[DEBUG] Greeting detected - responding without document retrieval")
            if lang == 'es':
                direct_responses = [
                    "¡Hola! 👋 Soy el asistente de Vecinita. ¿En qué puedo ayudarte hoy? Puedo responder preguntas sobre los servicios, programas y recursos comunitarios de Vecinita.",
                    "¡Saludos! 🙌 Estoy aquí para ayudarte con preguntas sobre Vecinita. ¿Qué te gustaría saber?",
                    "¡Bienvenido! Welcome to Vecinita. ¿Cómo puedo asistirte hoy?",
                ]
                response_text = direct_responses[hash(
                    question) % len(direct_responses)]
            else:
                direct_responses = [
                    "Hey there! 👋 I'm the Vecinita assistant. What can I help you with today? I can answer questions about Vecinita's services, programs, and community resources.",
                    "What's up! 🙌 I'm here to help with any questions about Vecinita. What would you like to know?",
                    "Welcome! 🎉 I'm ready to help. What can I tell you about Vecinita?",
                ]
                response_text = direct_responses[hash(
                    question) % len(direct_responses)]

            return {"answer": response_text, "context": []}

        if lang == 'es':
            prompt_template_str = """
            Eres un asistente comunitario, servicial y profesional para el proyecto Vecinita.
            Tu objetivo es dar respuestas claras, concisas y precisas basadas únicamente en el siguiente contexto.

            Reglas a seguir:
            1. Responde directamente a la pregunta del usuario utilizando la información de la sección 'CONTEXTO'.
            2. No inventes información ni utilices conocimientos fuera del contexto proporcionado.
            3. Al final de tu respuesta, DEBES citar la fuente de la información. Por ejemplo: "(Fuente: https://ejemplo.com)".
            4. Si el contexto no contiene la información para responder, DEBES decir: "No pude encontrar una respuesta definitiva en los documentos proporcionados."
            5. Debes responder en español.

            CONTEXTO:
            {context}

            PREGUNTA:
            {question}

            RESPUESTA:
            """
        else:  # Default to English
            prompt_template_str = """
            You are a helpful and professional community assistant for the Vecinita project.
            Your goal is to provide clear, concise, and accurate answers based *only* on the following context.

            Follow these rules:
            1. Directly answer the user's question using the information from the 'CONTEXT' section below.
            2. Do not make up information or use any knowledge outside of the provided context.
            3. At the end of your answer, you MUST cite the source of the information. For example: "(Source: https://example.com)".
            4. If the context does not contain the information to answer, you MUST state: "I could not find a definitive answer in the provided documents."
            5. You must answer in English.

            CONTEXT:
            {context}

            QUESTION:
            {question}

            ANSWER:
            """

        print("[DEBUG] Generating question embedding...")
        question_embedding = embedding_model.embed_query(question)
        print(
            f"[DEBUG] Embedding generated (dimension: {len(question_embedding)})")

        print("[DEBUG] Calling Supabase RPC 'search_similar_documents'...")
        relevant_docs = supabase.rpc(
            "search_similar_documents",
            {"query_embedding": question_embedding,
                "match_threshold": 0.3, "match_count": 5},
        ).execute()
        print(
            f"[DEBUG] Supabase returned {len(relevant_docs.data) if relevant_docs.data else 0} documents.")

        if not relevant_docs.data:
            answer = "No pude encontrar una respuesta definitiva en los documentos proporcionados." if lang == 'es' else "I could not find a definitive answer in the provided documents."
            return {"answer": answer, "context": []}

        context_text = "\n\n---\n\n".join(
            [f"Content from {doc['source']}:\n{doc['content']}" for doc in relevant_docs.data])
        prompt_template = ChatPromptTemplate.from_template(prompt_template_str)
        prompt = prompt_template.format(
            context=context_text, question=question)

        # Retry mechanism with cascading fallback: Primary → Fallback → Local
        response = None
        last_error = None
        providers_tried = []

        # Try primary LLM first
        try:
            print("[DEBUG] Invoking primary LLM...")
            response = llm_primary.invoke(prompt)
            print("[DEBUG] ✓ Primary LLM response received.")
            providers_tried.append("primary")
        except Exception as primary_error:
            print(f"[WARNING] Primary LLM failed: {primary_error}")
            last_error = primary_error
            providers_tried.append("primary (failed)")

            # Try fallback LLM if available
            if llm_fallback:
                try:
                    print("[DEBUG] Invoking fallback LLM...")
                    response = llm_fallback.invoke(prompt)
                    print("[DEBUG] ✓ Fallback LLM response received.")
                    providers_tried.append("fallback")
                except Exception as fallback_error:
                    print(
                        f"[WARNING] Fallback LLM also failed: {fallback_error}")
                    last_error = fallback_error
                    providers_tried.append("fallback (failed)")

            # Try local LLM as final fallback
            if response is None and llm_local:
                try:
                    print("[DEBUG] Invoking local Ollama LLM (final fallback)...")
                    response_text = llm_local.invoke(prompt)
                    # Ollama returns string directly, wrap it in an object

                    class LocalResponse:
                        def __init__(self, text):
                            self.content = text
                    response = LocalResponse(response_text)
                    print("[DEBUG] ✓ Local Ollama LLM response received.")
                    providers_tried.append("local")
                except Exception as local_error:
                    print(f"[ERROR] Local LLM also failed: {local_error}")
                    last_error = local_error
                    providers_tried.append("local (failed)")

        if response is None:
            error_msg = (
                f"All LLM providers failed. Providers tried: {', '.join(providers_tried)}. "
                f"Last error: {str(last_error)}. "
                f"Install Ollama from https://ollama.ai for offline support."
            )
            raise HTTPException(status_code=503, detail=error_msg)

        return {"answer": response.content, "context": relevant_docs.data}

    except Exception as e:
        import traceback
        print(f"[ERROR] Exception in /ask endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# --- Development GUI Endpoint ---
DEV_GUI_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Vecinita RAG Agent - Dev GUI</title>
    <style>
      * { box-sizing: border-box; }
      body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        margin: 0;
        padding: 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
      }
      .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
      }
      .header {
        text-align: center;
        color: white;
        margin-bottom: 2rem;
      }
      .header h1 { margin: 0; font-size: 2.5rem; }
      .header p { margin: 0.5rem 0 0; opacity: 0.9; }
      .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
      @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
      .card {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
      }
      .card h2 { margin: 0 0 1.5rem; font-size: 1.4rem; color: #333; }
      .form-group { margin-bottom: 1.5rem; }
      label { display: block; margin-bottom: 0.5rem; font-weight: 600; color: #555; }
      input, textarea {
        width: 100%;
        padding: 0.75rem;
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        font-size: 1rem;
        font-family: inherit;
        transition: border-color 0.2s;
      }
      input:focus, textarea:focus {
        outline: none;
        border-color: #667eea;
      }
      textarea { resize: vertical; min-height: 120px; }
      .button-group { display: flex; gap: 1rem; }
      button {
        flex: 1;
        padding: 0.875rem 1.5rem;
        border: none;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
      }
      .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }
      .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4); }
      .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
      .btn-secondary {
        background: #f3f4f6;
        color: #333;
      }
      .btn-secondary:hover { background: #e5e7eb; }
      .status {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        display: none;
      }
      .status.show { display: block; }
      .status.loading { background: #dbeafe; color: #1e40af; }
      .status.success { background: #dcfce7; color: #166534; }
      .status.error { background: #fee2e2; color: #991b1b; }
      .output-section {
        background: #f9fafb;
        border-radius: 8px;
        padding: 1.5rem;
        margin-top: 1.5rem;
      }
      .output-title { font-weight: 600; color: #374151; margin-bottom: 0.75rem; }
      .output-content {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 1rem;
        max-height: 300px;
        overflow-y: auto;
        white-space: pre-wrap;
        word-break: break-word;
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 0.875rem;
        line-height: 1.5;
        color: #1f2937;
      }
      .context-item {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 0.75rem;
      }
      .context-source { font-weight: 600; color: #667eea; font-size: 0.875rem; }
      .context-preview { margin-top: 0.5rem; color: #666; font-size: 0.875rem; }
      .empty-state { color: #9ca3af; text-align: center; padding: 2rem; }
    </style>
  </head>
  <body>
    <div class="container">
      <div class="header">
        <h1>🏘️ Vecinita RAG Agent</h1>
        <p>Development GUI - Ask questions about Vecinita services</p>
      </div>

      <div class="grid">
        <!-- Input Section -->
        <div class="card">
          <h2>Ask a Question</h2>
          <div id="status" class="status"></div>
          <div class="form-group">
            <label for="question">Question</label>
            <textarea id="question" placeholder="Ask in English or Spanish...&#10;e.g., What services does Vecinita offer?"></textarea>
          </div>
          <div class="button-group">
            <button class="btn-primary" id="askBtn">Ask</button>
            <button class="btn-secondary" id="clearBtn">Clear</button>
          </div>
          <div class="output-section">
            <div class="output-title">Response Status</div>
            <div class="output-content" id="statusOutput">Awaiting query...</div>
          </div>
        </div>

        <!-- Output Section -->
        <div class="card">
          <h2>Answer</h2>
          <div class="output-section">
            <div class="output-title">Generated Answer</div>
            <div class="output-content" id="answerOutput" style="min-height: 150px;">No answer yet...</div>
          </div>
          <div class="output-section">
            <div class="output-title">Source Documents</div>
            <div id="contextOutput" style="max-height: 250px; overflow-y: auto;">
              <div class="empty-state">No sources retrieved yet...</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <script>
      const API_BASE = window.location.origin;
      const questionInput = document.getElementById('question');
      const askBtn = document.getElementById('askBtn');
      const clearBtn = document.getElementById('clearBtn');
      const statusEl = document.getElementById('status');
      const statusOutput = document.getElementById('statusOutput');
      const answerOutput = document.getElementById('answerOutput');
      const contextOutput = document.getElementById('contextOutput');

      function setStatus(message, type = 'info') {
        statusEl.textContent = message;
        statusEl.className = `status show ${type}`;
      }

      function clearOutputs() {
        statusOutput.textContent = 'Awaiting query...';
        answerOutput.textContent = 'No answer yet...';
        contextOutput.innerHTML = '<div class="empty-state">No sources retrieved yet...</div>';
      }

      async function ask() {
        const q = questionInput.value.trim();
        if (!q) {
          setStatus('Please enter a question.', 'error');
          return;
        }

        askBtn.disabled = true;
        setStatus('Sending question...', 'loading');
        clearOutputs();

        try {
          statusOutput.textContent = 'Processing...';
          const url = new URL('/ask', API_BASE);
          url.searchParams.set('question', q);

          const res = await fetch(url.toString());
          if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${res.status}`);
          }

          const data = await res.json();
          setStatus('✓ Answer generated successfully!', 'success');
          statusOutput.textContent = 'Request successful';

          answerOutput.textContent = data.answer || 'No answer generated';

          const ctx = Array.isArray(data.context) ? data.context : [];
          if (ctx.length === 0) {
            contextOutput.innerHTML = '<div class="empty-state">No source documents returned.</div>';
          } else {
            contextOutput.innerHTML = ctx
              .map(
                (doc) =>
                  `<div class="context-item">
                    <div class="context-source">📄 ${doc.source || 'Unknown source'}</div>
                    <div class="context-preview">${(doc.content || '').substring(0, 300)}${doc.content && doc.content.length > 300 ? '...' : ''}</div>
                  </div>`
              )
              .join('');
          }
        } catch (err) {
          console.error(err);
          setStatus(`Error: ${err.message}`, 'error');
          statusOutput.textContent = `Error: ${err.message}`;
        } finally {
          askBtn.disabled = false;
        }
      }

      clearBtn.addEventListener('click', () => {
        questionInput.value = '';
        clearOutputs();
        statusEl.className = 'status';
      });

      askBtn.addEventListener('click', ask);
      questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) ask();
      });
    </script>
  </body>
</html>
"""


@app.get("/dev-gui")
async def dev_gui():
    """
    Development GUI for testing the RAG agent.

    Returns:
        HTMLResponse: Interactive chat interface for testing queries

    Example:
        GET /dev-gui

        Opens an interactive web interface for querying the RAG system
    """
    return HTMLResponse(content=DEV_GUI_HTML)


# --end-of-file
