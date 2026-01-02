"""Database search tool for Vecinita agent.

This tool performs vector similarity search against the Supabase database
to retrieve relevant document chunks for answering user questions.
"""

import logging
from typing import List, Dict, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _normalize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize document field names from Supabase response."""
    source = (
        doc.get('source_url')
        or doc.get('source')
        or doc.get('url')
        or 'Unknown source'
    )
    content = (
        doc.get('content')
        or doc.get('text')
        or doc.get('chunk_text')
        or ''
    )
    similarity = doc.get('similarity', 0.0)

    return {
        'content': content,
        'source_url': source,
        'similarity': similarity
    }


def _format_db_error(e: Exception) -> str:
    """Return a human-friendly message describing common DB search failures."""
    msg = str(e).lower()

    if "search_similar_documents" in msg and ("not found" in msg or "does not exist" in msg):
        return "RPC function not found. Ensure schema is installed."

    if "connection" in msg or "timeout" in msg:
        return "Database connection error."

    if "unauthorized" in msg or "invalid api key" in msg:
        return "Supabase authentication failed."

    if "dimension" in msg or "pgvector" in msg:
        return "Embedding dimension mismatch."

    return "Unexpected database error"


@tool
def db_search_tool(query: str) -> str:
    """Placeholder for the actual db_search tool."""
    raise NotImplementedError("This tool must be bound with clients first.")


def create_db_search_tool(supabase_client, embedding_model, match_threshold: float = 0.3, match_count: int = 5):
    """Create a configured db_search tool with access to Supabase and embeddings."""
    
    @tool
    def db_search(query: str) -> str:
        """Search the internal knowledge base for relevant information.

        Args:
            query: The user's question or search query

        Returns:
            String: A stringified list of relevant documents.
        """
        try:
            logger.info(f"DB Search: Generating embedding for query: '{query}'")
            question_embedding = embedding_model.embed_query(query)
            
            logger.info("DB Search: Searching for similar documents in Supabase...")
            relevant_docs = supabase_client.rpc(
                "search_similar_documents",
                {
                    "query_embedding": question_embedding,
                    "match_threshold": match_threshold,
                    "match_count": match_count
                },
            ).execute()

            count = len(relevant_docs.data) if relevant_docs.data else 0
            logger.info(f"DB Search: Found {count} relevant documents")

            if not relevant_docs.data:
                return "No relevant documents found in the database."

            # Normalize document format
            results = [_normalize_document(doc) for doc in relevant_docs.data]

            # CRITICAL FIX: Convert List to String for Groq/Llama compatibility
            return str(results)

        except Exception as e:
            error_msg = f"DB Search Error: {_format_db_error(e)}: {e}"
            logger.error(error_msg)
            return error_msg

    return db_search
