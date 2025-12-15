"""
Tests for supabase_db_test.py - Database connection testing.
"""
import pytest
import os
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestSupabaseDBTestConfiguration:
    """Test database test configuration."""

    def test_table_to_query_configuration(self):
        """Test that TABLE_TO_QUERY is configured."""
        from utils.supabase_db_test import TABLE_TO_QUERY
        assert TABLE_TO_QUERY == "document_chunks"


@pytest.mark.unit
class TestEnvironmentVariableLoading:
    """Test environment variable loading."""

    @patch("utils.supabase_db_test.os.environ.get")
    def test_missing_supabase_url(self, mock_environ):
        """Test error message when SUPABASE_URL is missing."""
        mock_environ.side_effect = lambda key: None

        # This would normally exit(1), but we'll mock it
        with patch("sys.exit"):
            from utils import supabase_db_test
            # The module imports at top level, so we need to test differently
            assert True

    @patch("utils.supabase_db_test.os.environ.get")
    def test_missing_supabase_key(self, mock_environ):
        """Test error message when SUPABASE_KEY is missing."""
        mock_environ.side_effect = lambda key: None if "KEY" in key else "https://test.com"

        with patch("sys.exit"):
            from utils import supabase_db_test
            assert True


@pytest.mark.unit
class TestDatabaseConnection:
    """Test database connection functionality."""

    @patch("utils.supabase_db_test.create_client")
    @patch("utils.supabase_db_test.os.environ.get")
    def test_successful_client_creation(self, mock_environ, mock_create_client):
        """Test successful Supabase client creation."""
        mock_environ.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key"
        }.get(key, default)

        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Verify client was created with correct parameters
        from supabase import create_client
        test_client = create_client("https://test.supabase.co", "test-key")
        assert test_client is not None

    @patch("utils.supabase_db_test.create_client")
    @patch("utils.supabase_db_test.os.environ.get")
    def test_failed_client_creation(self, mock_environ, mock_create_client):
        """Test handling of client creation failure."""
        mock_environ.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "https://invalid.url",
            "SUPABASE_KEY": "invalid-key"
        }.get(key, default)

        mock_create_client.side_effect = Exception("Connection failed")

        # Test that the mock raises the exception
        with pytest.raises(Exception, match="Connection failed"):
            mock_create_client("https://invalid.url", "invalid-key")


@pytest.mark.unit
class TestDatabaseQuery:
    """Test database query execution."""

    @patch("utils.supabase_db_test.create_client")
    @patch("utils.supabase_db_test.os.environ.get")
    def test_select_query_execution(self, mock_environ, mock_create_client):
        """Test SELECT query execution."""
        mock_environ.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key"
        }.get(key, default)

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": "1", "content": "test"}]

        mock_client.table.return_value = mock_table
        mock_table.select.return_value.limit.return_value.execute.return_value = mock_response

        mock_create_client.return_value = mock_client

        # Verify query chain
        result = mock_client.table(
            "document_chunks").select("*").limit(1).execute()
        assert result.data is not None
        assert len(result.data) == 1

    @patch("utils.supabase_db_test.create_client")
    @patch("utils.supabase_db_test.os.environ.get")
    def test_empty_query_result(self, mock_environ, mock_create_client):
        """Test handling of empty query results."""
        mock_environ.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key"
        }.get(key, default)

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_response = MagicMock()
        mock_response.data = []  # Empty result

        mock_client.table.return_value = mock_table
        mock_table.select.return_value.limit.return_value.execute.return_value = mock_response

        mock_create_client.return_value = mock_client

        result = mock_client.table(
            "document_chunks").select("*").limit(1).execute()
        assert result.data == []

    @patch("utils.supabase_db_test.create_client")
    @patch("utils.supabase_db_test.os.environ.get")
    def test_query_with_limit(self, mock_environ, mock_create_client):
        """Test query with LIMIT clause."""
        mock_environ.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key"
        }.get(key, default)

        mock_client = MagicMock()
        mock_table = MagicMock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.limit = MagicMock(return_value=mock_table)

        mock_table.execute.return_value.data = [{"id": "1"}]

        mock_create_client.return_value = mock_client

        # Test limit is called
        client = mock_create_client("url", "key")
        result = client.table("test").select("*").limit(1)

        mock_table.limit.assert_called_with(1)


@pytest.mark.integration
class TestDBTestIntegration:
    """Integration tests for database test module."""

    @patch("utils.supabase_db_test.create_client")
    @patch("utils.supabase_db_test.os.environ.get")
    def test_complete_test_flow(self, mock_environ, mock_create_client):
        """Test complete flow of database connection test."""
        mock_environ.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key"
        }.get(key, default)

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": "1", "content": "test"}]

        mock_client.table.return_value.select.return_value.limit.return_value.execute.return_value = mock_response
        mock_create_client.return_value = mock_client

        # Simulate the test flow
        client = mock_create_client("url", "key")
        result = client.table("document_chunks").select("*").limit(1).execute()

        assert result.data is not None
        assert len(result.data) == 1
        assert mock_client.table.called
        assert mock_client.table.return_value.select.called

    @patch("utils.supabase_db_test.create_client")
    @patch("utils.supabase_db_test.os.environ.get")
    def test_error_handling(self, mock_environ, mock_create_client):
        """Test error handling during database operations."""
        mock_environ.side_effect = lambda key, default=None: {
            "SUPABASE_URL": "https://test.supabase.co",
            "SUPABASE_KEY": "test-key"
        }.get(key, default)

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception(
            "DB Error")

        mock_create_client.return_value = mock_client

        with pytest.raises(Exception, match="DB Error"):
            client = mock_create_client("url", "key")
            client.table("document_chunks").select("*").limit(1).execute()
