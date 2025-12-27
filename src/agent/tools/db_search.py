"""Database search tool for Vecinita agent.

This tool performs vector similarity search against the Supabase database
to retrieve relevant document chunks for answering user questions.
"""

import logging
from typing import List, Dict, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _normalize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize document field names from Supabase response.

    Different Supabase schemas may use different field names.
    This function provides fallback logic to handle variations.

    Args:
        doc: Raw document dictionary from Supabase

    Returns:
        Normalized document with 'content', 'source_url', and 'similarity' fields
    """
    source = doc.get('source_url') or doc.get(
        'source') or doc.get('url') or 'Unknown source'
    content = doc.get('content') or doc.get(
        'text') or doc.get('chunk_text') or ''
    similarity = doc.get('similarity', 0.0)

    return {
        'content': content,
        'source_url': source,
        'similarity': similarity
    }


@tool
def db_search_tool(query: str) -> List[Dict[str, Any]]:
    """Search the internal knowledge base for relevant information.

    Use this tool to find information from the Vecinita document database.
    It performs vector similarity search to retrieve the most relevant content
    for answering the user's question.

    Args:
        query: The user's question or search query

    Returns:
        A list of relevant documents with content and source URLs.
        Each document contains 'content', 'source_url', and 'similarity' fields.
        Returns an empty list if no relevant documents are found.

    Example:
        >>> results = db_search_tool("What community services are available?")
        >>> for doc in results:
        ...     print(f"Source: {doc['source_url']}")
        ...     print(f"Content: {doc['content']}")
    """
    # This will be injected with actual clients at runtime
    # For now, this is a placeholder that will be properly bound in main.py
    raise NotImplementedError(
        "This tool must be bound with Supabase client and embedding model. "
        "Use create_db_search_tool() to create a properly configured instance."
    )


def create_db_search_tool(supabase_client, embedding_model, match_threshold: float = 0.3, match_count: int = 5):
    """Create a configured db_search tool with access to Supabase and embeddings.

    Args:
        supabase_client: Initialized Supabase client
        embedding_model: Initialized embedding model (HuggingFaceEmbeddings)
        match_threshold: Minimum similarity threshold (default: 0.3)
        match_count: Maximum number of results to return (default: 5)

    Returns:
        A configured tool function that can be used with LangGraph
    """
    @tool
    def db_search(query: str) -> List[Dict[str, Any]]:
        """Search the internal knowledge base for relevant information.

        Use this tool to find information from the Vecinita document database.
        It performs vector similarity search to retrieve the most relevant content
        for answering the user's question.

        Args:
            query: The user's question or search query

        Returns:
            A list of relevant documents with content and source URLs.
            Returns an empty list if no relevant documents are found.
        """
        try:
            logger.info(
                f"DB Search: Generating embedding for query: '{query}'")
            question_embedding = embedding_model.embed_query(query)
            logger.info(
                f"DB Search: Embedding generated. Dimension: {len(question_embedding)}")

            logger.info(
                "DB Search: Searching for similar documents in Supabase...")
            relevant_docs = supabase_client.rpc(
                "search_similar_documents",
                {
                    "query_embedding": question_embedding,
                    "match_threshold": match_threshold,
                    "match_count": match_count
                },
            ).execute()

            logger.info(
                f"DB Search: Found {len(relevant_docs.data) if relevant_docs.data else 0} relevant documents")

            if not relevant_docs.data:
                return []

            # Normalize document format using helper function
            results = [_normalize_document(doc) for doc in relevant_docs.data]

            return results

        except Exception as e:
            logger.error(f"DB Search: Error searching database: {e}")
            return []

    return db_search
