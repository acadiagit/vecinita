"""
Supabase Retriever for Vecinita RAG Agent
Custom retriever that connects to Supabase vectorstore
"""

import os
from typing import List
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from supabase import create_client, Client
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from src.agent_config import SIMILARITY_THRESHOLD, MAX_RETRIEVED_DOCS, EMBEDDING_MODEL_NAME

load_dotenv()


class SupabaseRetriever(BaseRetriever):
    """Custom retriever that queries Supabase vectorstore for similar documents."""

    supabase_client: Client
    embedding_model: HuggingFaceEmbeddings
    similarity_threshold: float = SIMILARITY_THRESHOLD
    max_docs: int = MAX_RETRIEVED_DOCS

    def __init__(self):
        """Initialize the Supabase retriever with credentials from environment."""
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

        supabase_client = create_client(supabase_url, supabase_key)
        embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME)

        super().__init__(
            supabase_client=supabase_client,
            embedding_model=embedding_model
        )

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        """Retrieve documents relevant to the query from Supabase.

        Args:
            query: The user's question to search for
            run_manager: Callback manager for the retriever run

        Returns:
            List of relevant documents with content and metadata
        """
        # Generate embedding for the query
        query_embedding = self.embedding_model.embed_query(query)

        # Query Supabase for similar documents
        try:
            response = self.supabase_client.rpc(
                "search_similar_documents",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": self.similarity_threshold,
                    "match_count": self.max_docs
                }
            ).execute()

            if not response.data:
                return []

            # Convert Supabase results to LangChain Documents
            documents = []
            for doc in response.data:
                documents.append(
                    Document(
                        page_content=doc.get("content", ""),
                        metadata={
                            "source": doc.get("source", "Unknown"),
                            "chunk_index": doc.get("chunk_index"),
                            "similarity": doc.get("similarity")
                        }
                    )
                )

            return documents

        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []


def get_supabase_retriever() -> SupabaseRetriever:
    """Factory function to create a Supabase retriever instance."""
    return SupabaseRetriever()
