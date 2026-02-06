#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VECINITA-RIOS: Database Search Tool
Path: src/agent/tools/db_search.py

PURPOSE:
Performs vector similarity search against Supabase document_chunks.
1. Fixes the 401 'Model-as-Key' error using explicit keyword arguments.
2. Uses verified 'langchain_core.tools' import for LangChain 1.2.x compatibility.
3. Provides factory function required by src.agent.main.

VERSION: 1.0.2 (Stable)
"""

import os
import logging
from typing import List, Dict, Any, Union
from langchain_openai import OpenAIEmbeddings
# Verified path for LangChain 1.2.x
from langchain_core.tools import Tool 
from sqlalchemy import create_engine, text

# Setup logging
logger = logging.getLogger(__name__)

def db_search(query: str, embedding_model: Any = "text-embedding-3-large") -> str:
    """
    Executes a RAG search. 
    Explicitly handles the OpenAI API Key to prevent 401 errors.
    """
    try:
        # 1. ORCHESTRATE EMBEDDINGS
        # Ensure model name isn't treated as the API key
        if isinstance(embedding_model, str):
            logger.info(f"Initializing OpenAIEmbeddings with model: {embedding_model}")
            embeddings = OpenAIEmbeddings(
                model=embedding_model, 
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        else:
            embeddings = embedding_model

        # 2. GENERATE VECTOR
        query_vector = embeddings.embed_query(query)

        # 3. DATABASE HANDSHAKE
        conn_str = os.getenv("SUPABASE_CONN_STR")
        if not conn_str:
            raise ValueError("SUPABASE_CONN_STR not found in environment")

        engine = create_engine(conn_str)
        
        with engine.connect() as connection:
            # Executes the RPC function defined in Supabase
            search_query = text("""
                SELECT content, source_url, similarity 
                FROM search_similar_documents(
                    query_embedding := :emb,
                    match_threshold := 0.1,
                    match_count := 5
                )
            """)
            
            result = connection.execute(search_query, {"emb": query_vector})
            rows = result.fetchall()

        if not rows:
            return "No relevant resources found in the directory for this query."

        # 4. FORMAT RESULTS
        formatted_results = []
        for row in rows:
            formatted_results.append(f"Source: {row[1]}\nContent: {row[0]}")

        return "\n\n---\n\n".join(formatted_results)

    except Exception as e:
        logger.critical(f"DB Search Error: {str(e)}")
        return "Database search currently unavailable due to an internal processing error."

def create_db_search_tool(supabase_client: Any = None, embedding_model: Any = None):
    """
    FACTORY FUNCTION: Now accepts 'supabase_client' and 'embedding_model' 
    to match the call signature in src.agent.main.
    """
    return Tool(
        name="db_search",
        # We pass a lambda or partial if we need to inject the model, 
        # but for now, the tool handles its own initialization.
        func=lambda query: db_search(query, embedding_model=embedding_model) if embedding_model else db_search(query),
        description="Search the Providence Resource Vault for health, school, and community resources."
    )

# -- end-of-file --
