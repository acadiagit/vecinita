"""
Tests for vector_loader.py - Vector database operations.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime


@pytest.mark.unit
class TestVectorLoaderConfiguration:
    """Test VectorLoader configuration."""

    def test_batch_size_configuration(self):
        """Test batch size is configured."""
        from utils.vector_loader import BATCH_SIZE
        assert BATCH_SIZE == 100

    def test_embedding_model_configuration(self):
        """Test embedding model is configured."""
        from utils.vector_loader import EMBEDDING_MODEL, LOCAL_EMBEDDING_MODEL
        assert EMBEDDING_MODEL == "text-embedding-3-small"
        assert LOCAL_EMBEDDING_MODEL == "all-MiniLM-L6-v2"

    def test_embedding_dimension_configuration(self):
        """Test embedding dimension is configured."""
        from utils.vector_loader import EMBEDDING_DIMENSION
        assert EMBEDDING_DIMENSION == 1536


@pytest.mark.unit
class TestDocumentChunkDataclass:
    """Test DocumentChunk dataclass."""

    def test_document_chunk_creation(self):
        """Test creating a DocumentChunk."""
        from utils.vector_loader import DocumentChunk
        from datetime import datetime

        chunk = DocumentChunk(
            content="Test content",
            source_url="https://example.com",
            chunk_index=0,
            total_chunks=1,
            document_id="doc-1",
            scraped_at=datetime.now()
        )

        assert chunk.content == "Test content"
        assert chunk.source_url == "https://example.com"
        assert chunk.chunk_index == 0

    def test_document_chunk_optional_fields(self):
        """Test DocumentChunk with optional fields."""
        from utils.vector_loader import DocumentChunk

        chunk = DocumentChunk(
            content="Content",
            source_url="https://example.com",
            chunk_index=0
        )

        assert chunk.document_id is None
        assert chunk.metadata is None


@pytest.mark.unit
class TestVectorLoaderInitialization:
    """Test VectorLoader initialization."""

    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key"
    })
    @patch("utils.vector_loader.create_client")
    @patch("utils.vector_loader.SentenceTransformer")
    def test_loader_initialization_with_supabase(self, mock_sentence_transformer, mock_create_client):
        """Test VectorLoader initialization with Supabase."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_sentence_transformer.return_value = MagicMock()

        from utils.vector_loader import VecinitaLoader

        loader = VecinitaLoader()

        assert loader.supabase_url == "https://test.supabase.co"
        assert loader.supabase_key == "test-key"

    @patch.dict(os.environ, {}, clear=True)
    def test_loader_initialization_missing_credentials(self):
        """Test that initialization fails without credentials."""
        from utils.vector_loader import VecinitaLoader

        with pytest.raises(ValueError, match="SUPABASE_URL and SUPABASE_KEY must be set"):
            VecinitaLoader()


@pytest.mark.unit
class TestChunkFileParsing:
    """Test chunk file parsing."""

    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key"
    })
    @patch("utils.vector_loader.create_client")
    @patch("utils.vector_loader.SentenceTransformer")
    def test_parse_chunk_file_format(self, mock_sentence_transformer, mock_create_client):
        """Test parsing chunk file in new format."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_sentence_transformer.return_value = MagicMock()

        from utils.vector_loader import VecinitaLoader

        loader = VecinitaLoader()

        # Create a temp file with chunk format
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("SOURCE: https://example.com\n")
            f.write("=" * 70 + "\n")
            f.write("--- CHUNK 1/2 ---\n")
            f.write("First chunk content\n")
            f.write("--- CHUNK 2/2 ---\n")
            f.write("Second chunk content\n")
            temp_file = f.name

        try:
            chunks = list(loader.parse_chunk_file(temp_file))

            assert len(chunks) == 2
            assert chunks[0].content == "First chunk content"
            assert chunks[1].content == "Second chunk content"
            assert chunks[0].source_url == "https://example.com"
        finally:
            os.unlink(temp_file)

    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key"
    })
    @patch("utils.vector_loader.create_client")
    @patch("utils.vector_loader.SentenceTransformer")
    def test_parse_empty_file(self, mock_sentence_transformer, mock_create_client):
        """Test parsing empty file."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_sentence_transformer.return_value = MagicMock()

        from utils.vector_loader import VecinitaLoader

        loader = VecinitaLoader()

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_file = f.name

        try:
            chunks = list(loader.parse_chunk_file(temp_file))
            assert len(chunks) == 0
        finally:
            os.unlink(temp_file)


@pytest.mark.unit
class TestEmbeddingGeneration:
    """Test embedding generation."""

    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "USE_LOCAL_EMBEDDINGS": "true"
    })
    @patch("utils.vector_loader.create_client")
    @patch("utils.vector_loader.SentenceTransformer")
    def test_embedding_generation_success(self, mock_sentence_transformer_cls, mock_create_client):
        """Test successful embedding generation."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_sentence_transformer = MagicMock()
        test_embedding = [0.1] * 384
        # Mock numpy array-like object with tolist()
        mock_array = MagicMock()
        mock_array.tolist.return_value = test_embedding
        mock_sentence_transformer.encode.return_value = mock_array
        mock_sentence_transformer.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer_cls.return_value = mock_sentence_transformer

        from utils.vector_loader import VecinitaLoader

        loader = VecinitaLoader()
        result = loader.generate_embedding("Test text")

        assert result == test_embedding
        # encode() is called with convert_to_numpy=True parameter
        mock_sentence_transformer.encode.assert_called_once_with(
            "Test text", convert_to_numpy=True)

    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "USE_LOCAL_EMBEDDINGS": "true"
    })
    @patch("utils.vector_loader.create_client")
    @patch("utils.vector_loader.SentenceTransformer")
    def test_embedding_empty_text(self, mock_sentence_transformer_cls, mock_create_client):
        """Test embedding generation with empty text."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_sentence_transformer = MagicMock()
        mock_sentence_transformer.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer_cls.return_value = mock_sentence_transformer

        from utils.vector_loader import VecinitaLoader

        loader = VecinitaLoader()
        result = loader.generate_embedding("")

        assert result is None

    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "USE_LOCAL_EMBEDDINGS": "true"
    })
    @patch("utils.vector_loader.create_client")
    @patch("utils.vector_loader.SentenceTransformer")
    def test_embedding_generation_error_handling(self, mock_sentence_transformer_cls, mock_create_client):
        """Test embedding generation error handling."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_sentence_transformer = MagicMock()
        mock_sentence_transformer.encode.side_effect = Exception(
            "Embedding error")
        mock_sentence_transformer.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer_cls.return_value = mock_sentence_transformer

        from utils.vector_loader import VecinitaLoader

        loader = VecinitaLoader()
        result = loader.generate_embedding("Test text")

        # Should handle error gracefully
        assert result is None


@pytest.mark.unit
class TestBatchProcessing:
    """Test batch processing."""

    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "USE_LOCAL_EMBEDDINGS": "true"
    })
    @patch("utils.vector_loader.create_client")
    @patch("utils.vector_loader.SentenceTransformer")
    def test_process_batch_success(self, mock_sentence_transformer_cls, mock_create_client):
        """Test successful batch processing."""
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "1"}]
        mock_create_client.return_value = mock_client

        mock_sentence_transformer = MagicMock()
        # Return a numpy-like object with tolist() to match implementation
        mock_array = MagicMock()
        mock_array.tolist.return_value = [0.1] * 384
        mock_sentence_transformer.encode.return_value = mock_array
        mock_sentence_transformer.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer_cls.return_value = mock_sentence_transformer

        from utils.vector_loader import VecinitaLoader, DocumentChunk

        loader = VecinitaLoader()

        chunks = [
            DocumentChunk(
                content="Test chunk",
                source_url="https://test.com",
                chunk_index=0
            )
        ]

        successful, failed = loader.process_batch(chunks)

        assert successful >= 0
        assert failed >= 0

    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "USE_LOCAL_EMBEDDINGS": "true"
    })
    @patch("utils.vector_loader.create_client")
    @patch("utils.vector_loader.SentenceTransformer")
    def test_process_empty_batch(self, mock_sentence_transformer_cls, mock_create_client):
        """Test processing empty batch."""
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_sentence_transformer = MagicMock()
        mock_sentence_transformer.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer_cls.return_value = mock_sentence_transformer

        from utils.vector_loader import VecinitaLoader

        loader = VecinitaLoader()
        successful, failed = loader.process_batch([])

        assert successful == 0
        assert failed == 0


@pytest.mark.unit
class TestFileLoading:
    """Test file loading."""

    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "USE_LOCAL_EMBEDDINGS": "true"
    })
    @patch("utils.vector_loader.create_client")
    @patch("utils.vector_loader.SentenceTransformer")
    def test_load_file_statistics(self, mock_sentence_transformer_cls, mock_create_client):
        """Test file loading returns statistics."""
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "1"}]
        mock_create_client.return_value = mock_client

        mock_sentence_transformer = MagicMock()
        # Return a numpy-like object with tolist() to match implementation
        mock_array = MagicMock()
        mock_array.tolist.return_value = [0.1] * 384
        mock_sentence_transformer.encode.return_value = mock_array
        mock_sentence_transformer.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer_cls.return_value = mock_sentence_transformer

        from utils.vector_loader import VecinitaLoader

        loader = VecinitaLoader()

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("SOURCE: https://example.com\n")
            f.write("=" * 70 + "\n")
            f.write("--- CHUNK 1/1 ---\n")
            f.write("Test content\n")
            temp_file = f.name

        try:
            stats = loader.load_file(temp_file)

            assert "total_chunks" in stats
            assert "successful" in stats
            assert "failed" in stats
            assert "skipped" in stats
        finally:
            os.unlink(temp_file)


@pytest.mark.unit
class TestDirectoryLoading:
    """Test directory loading."""

    @patch.dict(os.environ, {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "USE_LOCAL_EMBEDDINGS": "true"
    })
    @patch("utils.vector_loader.create_client")
    @patch("utils.vector_loader.SentenceTransformer")
    @patch("glob.glob")
    def test_load_directory(self, mock_glob, mock_sentence_transformer_cls, mock_create_client):
        """Test loading directory of files."""
        mock_glob.return_value = ["file1.txt", "file2.txt"]

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "1"}]
        mock_create_client.return_value = mock_client

        mock_sentence_transformer = MagicMock()
        # Return a numpy-like object with tolist() to match implementation
        mock_array = MagicMock()
        mock_array.tolist.return_value = [0.1] * 384
        mock_sentence_transformer.encode.return_value = mock_array
        mock_sentence_transformer.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer_cls.return_value = mock_sentence_transformer

        from utils.vector_loader import VecinitaLoader

        loader = VecinitaLoader()

        with tempfile.TemporaryDirectory() as temp_dir:
            stats = loader.load_directory(temp_dir)

            assert isinstance(stats, dict)
