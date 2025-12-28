"""
Database uploader for the VECINA scraper.
Handles uploading processed document chunks to Supabase vector database.
"""

import logging
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    LOCAL_EMBEDDINGS_AVAILABLE = True
except ImportError:
    LOCAL_EMBEDDINGS_AVAILABLE = False

log = logging.getLogger('vecinita_pipeline.uploader')
log.addHandler(logging.NullHandler())


@dataclass
class DocumentChunk:
    """Represents a single document chunk with metadata."""
    content: str
    source_url: str
    chunk_index: int
    total_chunks: Optional[int] = None
    loader_type: Optional[str] = None
    metadata: Optional[Dict] = None
    scraped_at: Optional[datetime] = None


class DatabaseUploader:
    """Uploads processed chunks to Supabase vector database."""

    def __init__(self, use_local_embeddings: bool = True):
        """
        Initialize database uploader.

        Args:
            use_local_embeddings: If True, use local embeddings. If False, requires OpenAI API key.
        """
        if not SUPABASE_AVAILABLE:
            raise ImportError(
                "Supabase client not installed. Install with: pip install supabase")

        self.use_local_embeddings = use_local_embeddings
        self.embedding_model = None
        self.supabase_client = None

        # Initialize embeddings
        if use_local_embeddings:
            if not LOCAL_EMBEDDINGS_AVAILABLE:
                raise ImportError(
                    "sentence-transformers not installed. Install with: pip install sentence-transformers")
            log.info("Initializing local embedding model (all-MiniLM-L6-v2)...")
            self.embedding_model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2"
            )
            log.info("✓ Local embedding model loaded (384 dimensions)")

        # Initialize Supabase connection
        self._init_supabase()

    def _init_supabase(self) -> None:
        """Initialize Supabase client."""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY environment variables are required"
            )

        self.supabase_client = create_client(supabase_url, supabase_key)
        log.info("✓ Supabase connection established")

    def upload_chunks(
        self,
        chunks: List[Dict],
        source_identifier: str,
        loader_type: str,
        batch_size: int = 50
    ) -> Tuple[int, int]:
        """
        Upload processed chunks to database.

        Args:
            chunks: List of chunk dicts with 'text' and 'metadata' keys
            source_identifier: URL or identifier of the source
            loader_type: Type of loader used (e.g., "Playwright", "Unstructured")
            batch_size: Number of chunks to upload in each batch

        Returns:
            Tuple of (successful_uploads, failed_uploads)
        """
        if not chunks:
            log.warning("No chunks to upload")
            return 0, 0

        if not self.supabase_client:
            log.error("Supabase client not initialized")
            return 0, len(chunks)

        log.info(f"--> Uploading {len(chunks)} chunks to database...")

        # Convert chunks to DocumentChunk objects with embeddings
        doc_chunks = []
        for idx, chunk_data in enumerate(chunks, 1):
            chunk_text = chunk_data.get('text', '')
            chunk_meta = chunk_data.get('metadata', {})

            doc_chunk = DocumentChunk(
                content=chunk_text,
                source_url=source_identifier,
                chunk_index=idx,
                total_chunks=len(chunks),
                loader_type=loader_type,
                metadata=chunk_meta,
                scraped_at=datetime.utcnow()
            )
            doc_chunks.append(doc_chunk)

        # Generate embeddings
        log.debug(f"--> Generating embeddings for {len(doc_chunks)} chunks...")
        try:
            embeddings = self._generate_embeddings(
                [chunk.content for chunk in doc_chunks]
            )
            if len(embeddings) != len(doc_chunks):
                log.error(
                    f"Embedding count mismatch: {len(embeddings)} embeddings for {len(doc_chunks)} chunks"
                )
                return 0, len(doc_chunks)
        except Exception as e:
            log.error(f"--> Failed to generate embeddings: {e}")
            return 0, len(doc_chunks)

        # Upload in batches
        successful = 0
        failed = 0

        for i in range(0, len(doc_chunks), batch_size):
            batch_chunks = doc_chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]

            success, fail = self._upload_batch(
                batch_chunks, batch_embeddings, source_identifier
            )
            successful += success
            failed += fail

        log.info(
            f"--> ✅ Upload complete: {successful} successful, {failed} failed"
        )
        return successful, failed

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if self.use_local_embeddings:
            return self._generate_local_embeddings(texts)
        else:
            raise NotImplementedError(
                "OpenAI embeddings not yet configured. Use local embeddings instead."
            )

    def _generate_local_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local model."""
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")

        log.debug(f"Generating {len(texts)} embeddings with local model...")
        embeddings = self.embedding_model.encode(
            texts,
            convert_to_numpy=False,
            show_progress_bar=False
        )
        return [emb.tolist() if hasattr(emb, 'tolist') else emb for emb in embeddings]

    def _upload_batch(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
        source_identifier: str
    ) -> Tuple[int, int]:
        """Upload a batch of chunks to Supabase."""
        if not chunks or not embeddings:
            return 0, 0

        # Prepare data for insertion
        records = []
        for chunk, embedding in zip(chunks, embeddings):
            record = {
                "content": chunk.content,
                "source_url": chunk.source_url,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                "embedding": embedding,
                # Persist loader_type inside metadata for traceability
                "metadata": {**(chunk.metadata or {}), **({"loader_type": chunk.loader_type} if chunk.loader_type else {})},
                "scraped_at": chunk.scraped_at.isoformat() if chunk.scraped_at else None,
            }
            records.append(record)

        # Upload to Supabase
        try:
            response = self.supabase_client.table(
                "document_chunks").insert(records).execute()

            successful = len(records)
            failed = 0

            log.debug(
                f"Batch upload successful: {successful} chunks to database"
            )
            return successful, failed

        except Exception as e:
            log.error(f"--> Batch upload failed: {e}")
            # Try uploading individually for better error reporting
            return self._upload_individual(chunks, embeddings)

    def _upload_individual(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]]
    ) -> Tuple[int, int]:
        """Upload chunks individually for better error handling."""
        successful = 0
        failed = 0

        for chunk, embedding in zip(chunks, embeddings):
            record = {
                "content": chunk.content,
                "source_url": chunk.source_url,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                "embedding": embedding,
                "metadata": {**(chunk.metadata or {}), **({"loader_type": chunk.loader_type} if chunk.loader_type else {})},
                "scraped_at": chunk.scraped_at.isoformat() if chunk.scraped_at else None,
            }

            try:
                self.supabase_client.table(
                    "document_chunks").insert([record]).execute()
                successful += 1
            except Exception as e:
                log.warning(
                    f"Failed to upload chunk from {chunk.source_url}: {e}"
                )
                failed += 1

        return successful, failed

    def close(self) -> None:
        """Clean up resources."""
        log.debug("DatabaseUploader closing...")
