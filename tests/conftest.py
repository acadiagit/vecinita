"""
Shared pytest fixtures and configuration for the Vecinita test suite.
"""
import os
import pytest
from dotenv import load_dotenv
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# Load environment variables for tests
load_dotenv()


@pytest.fixture(scope="session")
def env_vars():
    """Provide environment variables for tests."""
    return {
        "SUPABASE_URL": os.getenv("SUPABASE_URL", "https://test.supabase.co"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY", "test-key"),
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY", "test-groq-key"),
        "DATABASE_URL": os.getenv("DATABASE_URL", "postgresql://test"),
    }


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client for testing."""
    mock_client = Mock()
    mock_client.table = Mock(return_value=Mock())
    mock_client.rpc = Mock(return_value=Mock())
    return mock_client


@pytest.fixture
def mock_embedding_model():
    """Create a mock embedding model."""
    mock_model = Mock()
    mock_model.embed_query = Mock(
        return_value=[0.1] * 384)  # Mock embedding vector
    return mock_model


@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    mock_llm = Mock()
    mock_response = Mock()
    mock_response.content = "Test response from LLM"
    mock_llm.invoke = Mock(return_value=mock_response)
    return mock_llm


@pytest.fixture
def fastapi_client(env_vars, monkeypatch):
    """Create a FastAPI test client with env vars applied before app import.

    This ensures any environment-based configuration in `main` is picked up
    after tests set or mock environment variables.
    """
    # Ensure required env vars are set prior to importing the app module
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Patch dependencies before importing app
    from unittest.mock import MagicMock, patch
    with patch("src.agent.main.create_client") as mock_supabase, \
            patch("src.agent.main.ChatGroq") as mock_groq, \
            patch("src.agent.main.HuggingFaceEmbeddings") as mock_embeddings:

        # Setup mocks
        mock_supabase_client = MagicMock()
        mock_supabase_client.rpc.return_value.execute.return_value.data = []
        mock_supabase.return_value = mock_supabase_client

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response
        mock_groq.return_value = mock_llm

        mock_embedding_model = MagicMock()
        mock_embedding_model.embed_query.return_value = [0.1] * 384
        mock_embeddings.return_value = mock_embedding_model

        # Import after mocks are set
        from main import app
        return TestClient(app)


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    test_file = tmp_path / "test_input.txt"
    test_file.write_text("test content")
    return test_file


@pytest.fixture
def sample_documents():
    """Provide sample document data for testing."""
    return [
        {
            "id": "1",
            "content": "Sample document content about housing policy.",
            "source": "https://example.com/housing",
            "source_url": "https://example.com/housing",
            "created_at": "2024-01-01T00:00:00Z",
        },
        {
            "id": "2",
            "content": "Community resources and support services.",
            "source": "https://example.com/community",
            "source_url": "https://example.com/community",
            "created_at": "2024-01-02T00:00:00Z",
        },
    ]


@pytest.fixture
def sample_chunks():
    """Provide sample document chunks for testing."""
    return [
        {
            "content": "Chunk 1: Information about housing.",
            "source_url": "https://example.com/housing",
            "chunk_index": 0,
            "total_chunks": 2,
        },
        {
            "content": "Chunk 2: More housing information.",
            "source_url": "https://example.com/housing",
            "chunk_index": 1,
            "total_chunks": 2,
        },
    ]
