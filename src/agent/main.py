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
from dotenv import load_dotenv
from supabase import create_client, Client
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langdetect import detect, LangDetectException

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

    # Use all-MiniLM-L6-v2 with 384 dimensions or all-mpnet-base-v2 with 768 dimensions
    # The schema was created for 1536 dimensions, but we'll use 384 for faster inference
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    logger.info(f"Initializing embedding model: {model_name}...")
    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    logger.info("Embedding model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize clients: {e}")
    logger.error(traceback.format_exc())
    raise RuntimeError(f"Failed to initialize clients: {e}")

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
async def ask_question(question: str):
    """Handles Q&A requests from the UI or API"""
    if not question:
        raise HTTPException(
            status_code=400, detail="Question parameter cannot be empty.")

    try:
        lang = detect(question)
    except LangDetectException:
        lang = "en"
        logger.warning(
            f"Language detection failed for question: '{question}'. Defaulting to English.")

    logger.info(
        f"\n--- New request received: '{question}' (Detected Language: {lang}) ---")

    try:
        logger.debug(f"Building prompt template for language: {lang}")
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

        logger.info("Generating embedding for question...")
        question_embedding = embedding_model.embed_query(question)
        logger.info(
            f"Embedding generated. Dimension: {len(question_embedding)}")

        logger.info("Searching for similar documents in Supabase...")
        relevant_docs = supabase.rpc(
            "search_similar_documents",
            {"query_embedding": question_embedding,
                "match_threshold": 0.3, "match_count": 5},
        ).execute()
        logger.info(
            f"Found {len(relevant_docs.data) if relevant_docs.data else 0} relevant documents")

        if not relevant_docs.data:
            answer = "No pude encontrar una respuesta definitiva en los documentos proporcionados." if lang == 'es' else "I could not find a definitive answer in the provided documents."
            logger.info(
                "No relevant documents found. Returning fallback message.")
            return {"answer": answer, "context": []}

        # Debug: Log the structure of the first document to see available fields
        if relevant_docs.data:
            logger.debug(
                f"Sample document keys: {list(relevant_docs.data[0].keys())}")

        logger.debug("Building context from retrieved documents...")
        # Handle different possible field names (source_url, source, url, etc.)
        context_parts = []
        for doc in relevant_docs.data:
            source = doc.get('source_url') or doc.get(
                'source') or doc.get('url') or 'Unknown source'
            content = doc.get('content') or doc.get(
                'text') or doc.get('chunk_text') or ''
            context_parts.append(f"Content from {source}:\n{content}")

        context_text = "\n\n---\n\n".join(context_parts)
        logger.debug(
            f"Context built. Total length: {len(context_text)} characters")

        logger.info("Creating prompt template and formatting prompt...")
        prompt_template = ChatPromptTemplate.from_template(prompt_template_str)
        prompt = prompt_template.format(
            context=context_text, question=question)
        logger.debug(f"Prompt length: {len(prompt)} characters")

        logger.info("Invoking LLM with prompt...")
        response = llm.invoke(prompt)
        logger.info("LLM response received successfully")

        return {"answer": response.content, "context": relevant_docs.data}

    except Exception as e:
        logger.error(f"Error processing question '{question}': {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return JSONResponse({"status": "ok"})

# --end-of-file--
