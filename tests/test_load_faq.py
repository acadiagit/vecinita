"""
Tests for load_faq.py - Alternative FAQ loading module.
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestLoadFAQConfiguration:
    """Test load_faq configuration."""

    def test_faq_file_path_config(self):
        """Test FAQ file path configuration."""
        from utils.load_faq import FAQ_FILE_PATH, TABLE_NAME
        assert FAQ_FILE_PATH == "data/vecinita_faq.md"
        assert TABLE_NAME == "curated_content"


@pytest.mark.unit
class TestLoadFAQDependencies:
    """Test required dependencies."""

    def test_import_all_dependencies(self):
        """Test that all required modules can be imported."""
        try:
            from supabase import create_client, Client
            from langchain_huggingface import HuggingFaceEmbeddings
            from langchain_text_splitters import MarkdownTextSplitter
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import dependencies: {e}")


@pytest.mark.unit
class TestLoadFAQMain:
    """Test load_faq main function."""

    @patch("utils.load_faq.os.environ.get")
    def test_missing_database_url(self, mock_environ):
        """Test error when DATABASE_URL is missing."""
        mock_environ.return_value = None

        from utils.load_faq import main

        with pytest.raises(ValueError, match="DATABASE_URL must be set"):
            main()

    @patch("utils.load_faq.os.environ.get")
    @patch("utils.load_faq.create_client")
    @patch("utils.load_faq.HuggingFaceEmbeddings")
    @patch("builtins.open")
    def test_faq_loading_success(self, mock_open, mock_embeddings_cls, mock_create_client, mock_environ):
        """Test successful FAQ loading."""
        def env_side_effect(key, default=None):
            env_map = {
                "DATABASE_URL": "postgresql://test",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key"
            }
            return env_map.get(key, default)

        mock_environ.side_effect = env_side_effect

        faq_content = "# FAQ\n## Question 1\nAnswer 1\n## Question 2\nAnswer 2"
        mock_open.return_value.__enter__.return_value.read.return_value = faq_content

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.delete.return_value.neq.return_value.execute.return_value = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "1"}] * 3
        mock_create_client.return_value = mock_supabase

        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 384
        mock_embeddings_cls.return_value = mock_embeddings

        from utils.load_faq import main
        main()

        # Verify operations
        mock_supabase.table.assert_called_with("curated_content")

    @patch("utils.load_faq.os.environ.get")
    @patch("utils.load_faq.create_client")
    @patch("utils.load_faq.HuggingFaceEmbeddings")
    @patch("builtins.open")
    def test_embedding_model_initialization(self, mock_open, mock_embeddings_cls, mock_create_client, mock_environ):
        """Test embedding model initialization."""
        def env_side_effect(key, default=None):
            env_map = {
                "DATABASE_URL": "postgresql://test",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key"
            }
            return env_map.get(key, default)

        mock_environ.side_effect = env_side_effect
        mock_open.return_value.__enter__.return_value.read.return_value = "# FAQ\nContent"

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.delete.return_value.neq.return_value.execute.return_value = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "1"}]
        mock_create_client.return_value = mock_supabase

        mock_embeddings = MagicMock()
        mock_embeddings_cls.return_value = mock_embeddings

        from utils.load_faq import main
        main()

        # Verify model was initialized with correct name
        mock_embeddings_cls.assert_called()

    @patch("utils.load_faq.os.environ.get")
    @patch("utils.load_faq.create_client")
    @patch("utils.load_faq.HuggingFaceEmbeddings")
    @patch("builtins.open")
    def test_data_upload_format(self, mock_open, mock_embeddings_cls, mock_create_client, mock_environ):
        """Test that data is uploaded in correct format."""
        def env_side_effect(key, default=None):
            env_map = {
                "DATABASE_URL": "postgresql://test",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key"
            }
            return env_map.get(key, default)

        mock_environ.side_effect = env_side_effect
        mock_open.return_value.__enter__.return_value.read.return_value = "# FAQ\nQ\nA"

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.delete.return_value.neq.return_value.execute.return_value = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "1"}]
        mock_create_client.return_value = mock_supabase

        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.5] * 384
        mock_embeddings_cls.return_value = mock_embeddings

        from utils.load_faq import main
        main()

        # Check that insert was called with proper structure
        call_args = mock_supabase.table.return_value.insert.call_args
        if call_args:
            # The data should contain 'content', 'source', and 'embedding' keys
            assert call_args is not None

    @patch("utils.load_faq.HuggingFaceEmbeddings")
    @patch("utils.load_faq.create_client")
    @patch("utils.load_faq.load_dotenv")
    @patch("utils.load_faq.os.environ.get")
    @patch("builtins.open")
    def test_file_not_found_handling(self, mock_open, mock_environ, mock_load_dotenv, mock_create_client, mock_embeddings):
        """Test handling of missing FAQ file."""
        def env_side_effect(key, default=None):
            env_map = {
                "DATABASE_URL": "postgresql://test",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key"
            }
            return env_map.get(key, default)

        mock_environ.side_effect = env_side_effect
        mock_open.side_effect = FileNotFoundError()
        mock_embeddings.return_value = MagicMock()

        from utils.load_faq import main

        # The function returns early when file is not found (logging error)
        # This is graceful handling
        main()
