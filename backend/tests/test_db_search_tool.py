"""Unit tests for the database search tool.

Tests the db_search tool's ability to query the Supabase vector database
and retrieve relevant documents.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.agent.tools.db_search import create_db_search_tool


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    mock = Mock()
    return mock


@pytest.fixture
def mock_embedding_model():
    """Create a mock embedding model."""
    mock = Mock()
    mock.embed_query.return_value = [0.1] * 384  # 384-dim embedding
    return mock


@pytest.fixture
def db_search_tool(mock_supabase, mock_embedding_model):
    """Create a configured db_search tool with mocks."""
    return create_db_search_tool(mock_supabase, mock_embedding_model)


class TestDbSearchTool:
    """Test suite for database search tool."""

    def test_db_search_returns_empty_when_no_results(self, db_search_tool, mock_supabase):
        """Test that tool returns empty list when no documents found."""
        # Mock Supabase RPC response with no data
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=[])
        mock_supabase.rpc.return_value = mock_rpc

        results = db_search_tool.invoke("nonexistent topic")

        assert results == []
        assert isinstance(results, list)

    def test_db_search_returns_normalized_documents(self, db_search_tool, mock_supabase):
        """Test that tool normalizes and returns document results."""
        # Mock Supabase RPC response with documents
        mock_docs = [
            {
                "content": "Community health services",
                "source_url": "https://example.com/health",
                "similarity": 0.95
            },
            {
                "text": "Alternative text field",
                "source": "https://example.com/alt",
                "similarity": 0.85
            }
        ]
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=mock_docs)
        mock_supabase.rpc.return_value = mock_rpc

        results = db_search_tool.invoke("health services")

        assert len(results) == 2
        assert results[0]["content"] == "Community health services"
        assert results[0]["source_url"] == "https://example.com/health"
        assert results[0]["similarity"] == 0.95
        # Second result uses fallback field names
        assert results[1]["content"] == "Alternative text field"
        assert results[1]["source_url"] == "https://example.com/alt"

    def test_db_search_handles_missing_fields(self, db_search_tool, mock_supabase):
        """Test that tool handles documents with missing fields gracefully."""
        mock_docs = [
            {
                "content": "Some content",
                # Missing source_url, source, url - should default to 'Unknown source'
            },
            {
                # Missing content fields
                "source_url": "https://example.com"
            }
        ]
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=mock_docs)
        mock_supabase.rpc.return_value = mock_rpc

        results = db_search_tool.invoke("test")

        assert len(results) == 2
        assert results[0]["source_url"] == "Unknown source"
        assert results[1]["content"] == ""

    def test_db_search_calls_embedding_model(self, db_search_tool, mock_supabase, mock_embedding_model):
        """Test that tool calls embedding model to embed the query."""
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=[])
        mock_supabase.rpc.return_value = mock_rpc

        db_search_tool.invoke("test query")

        mock_embedding_model.embed_query.assert_called_once_with("test query")

    def test_db_search_calls_supabase_rpc_correctly(self, db_search_tool, mock_supabase, mock_embedding_model):
        """Test that tool calls Supabase RPC with correct parameters."""
        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=[])
        mock_supabase.rpc.return_value = mock_rpc

        db_search_tool.invoke("test query")

        # Verify RPC was called with correct function name and params
        mock_supabase.rpc.assert_called_once()
        call_args = mock_supabase.rpc.call_args
        assert call_args[0][0] == "search_similar_documents"

        params = call_args[0][1]
        assert "query_embedding" in params
        assert params["match_threshold"] == 0.3
        assert params["match_count"] == 5

    def test_db_search_with_custom_threshold_and_count(self, mock_supabase, mock_embedding_model):
        """Test that tool respects custom threshold and count parameters."""
        tool = create_db_search_tool(
            mock_supabase,
            mock_embedding_model,
            match_threshold=0.7,
            match_count=10
        )

        mock_rpc = Mock()
        mock_rpc.execute.return_value = Mock(data=[])
        mock_supabase.rpc.return_value = mock_rpc

        tool.invoke("test")

        params = mock_supabase.rpc.call_args[0][1]
        assert params["match_threshold"] == 0.7
        assert params["match_count"] == 10

    def test_db_search_error_handling(self, db_search_tool, mock_supabase):
        """Test that tool handles errors gracefully."""
        mock_supabase.rpc.side_effect = Exception("Database connection error")

        results = db_search_tool.invoke("test")

        # Should return empty list on error, not raise
        assert results == []

    def test_db_search_tool_has_correct_name_and_description(self, db_search_tool):
        """Test that tool has proper name and docstring."""
        assert db_search_tool.name == "db_search"
        assert "internal knowledge base" in db_search_tool.description.lower()
        assert "vector similarity" in db_search_tool.description.lower()
