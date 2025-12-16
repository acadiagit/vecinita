"""
Tests for faq_loader.py - FAQ loading and embedding generation.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import tempfile


@pytest.mark.unit
class TestFAQLoaderConfiguration:
    """Test FAQ loader configuration."""

    def test_faq_file_path_configuration(self):
        """Test that FAQ file path is properly configured."""
        from utils.faq_loader import FAQ_FILE_PATH, TABLE_NAME
        assert FAQ_FILE_PATH == "data/vecinita_faq.md"
        assert TABLE_NAME == "curated_content"


@pytest.mark.unit
class TestFAQLoaderDependencies:
    """Test that all required dependencies are available."""

    def test_import_supabase(self):
        """Test that Supabase can be imported."""
        try:
            from supabase import create_client, Client
            assert True
        except ImportError:
            pytest.fail("Supabase import failed")

    def test_import_langchain_huggingface(self):
        """Test that LangChain HuggingFace embeddings can be imported."""
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            assert True
        except ImportError:
            pytest.fail("LangChain HuggingFace import failed")

    def test_import_markdown_splitter(self):
        """Test that MarkdownTextSplitter can be imported."""
        try:
            from langchain_text_splitters import MarkdownTextSplitter
            assert True
        except ImportError:
            pytest.fail("MarkdownTextSplitter import failed")


@pytest.mark.unit
class TestFAQMainFunction:
    """Test FAQ loader main function."""

    @patch("utils.faq_loader.os.environ.get")
    @patch("utils.faq_loader.create_client")
    @patch("utils.faq_loader.HuggingFaceEmbeddings")
    @patch("builtins.open")
    def test_missing_database_url(self, mock_open, mock_embeddings, mock_create_client, mock_environ):
        """Test that function raises error when DATABASE_URL is missing."""
        mock_environ.side_effect = lambda key, default=None: None

        from utils.faq_loader import main

        with pytest.raises(ValueError, match="DATABASE_URL must be set"):
            main()

    @patch("utils.faq_loader.load_dotenv")
    @patch("utils.faq_loader.os.environ.get")
    @patch("utils.faq_loader.create_client")
    @patch("utils.faq_loader.HuggingFaceEmbeddings")
    @patch("builtins.open")
    def test_faq_file_not_found(self, mock_open, mock_embeddings, mock_create_client, mock_environ, mock_load_dotenv):
        """Test handling of missing FAQ file."""
        mock_environ.side_effect = lambda key, default=None: "postgresql://test" if key == "DATABASE_URL" else "test"

        mock_open.side_effect = FileNotFoundError("File not found")

        from utils.faq_loader import main

        # The function returns early when file is not found (logging error)
        # This is graceful handling
        main()

    @patch("utils.faq_loader.os.environ.get")
    @patch("utils.faq_loader.create_client")
    @patch("utils.faq_loader.HuggingFaceEmbeddings")
    @patch("builtins.open")
    def test_successful_faq_load(self, mock_open, mock_embeddings_cls, mock_create_client, mock_environ):
        """Test successful FAQ loading."""
        # Setup environment
        def env_side_effect(key, default=None):
            env_map = {
                "DATABASE_URL": "postgresql://test",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key"
            }
            return env_map.get(key, default)

        mock_environ.side_effect = env_side_effect

        # Setup file mock
        faq_content = "# FAQ\n## Q1\nAnswer 1\n## Q2\nAnswer 2"
        mock_open.return_value.__enter__.return_value.read.return_value = faq_content

        # Setup Supabase mock
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.delete.return_value.neq.return_value.execute.return_value = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "1"}] * 3
        mock_create_client.return_value = mock_supabase

        # Setup embeddings mock
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 384
        mock_embeddings_cls.return_value = mock_embeddings

        from utils.faq_loader import main

        # Should execute without errors
        main()

        # Verify database operations were called
        mock_supabase.table.assert_called_with("curated_content")

    @patch("utils.faq_loader.os.environ.get")
    @patch("utils.faq_loader.create_client")
    @patch("utils.faq_loader.HuggingFaceEmbeddings")
    @patch("builtins.open")
    def test_embedding_generation(self, mock_open, mock_embeddings_cls, mock_create_client, mock_environ):
        """Test that embeddings are generated for each chunk."""
        def env_side_effect(key, default=None):
            env_map = {
                "DATABASE_URL": "postgresql://test",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key"
            }
            return env_map.get(key, default)

        mock_environ.side_effect = env_side_effect

        faq_content = "# FAQ\n## Q1\nAnswer 1\n## Q2\nAnswer 2"
        mock_open.return_value.__enter__.return_value.read.return_value = faq_content

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.delete.return_value.neq.return_value.execute.return_value = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "1"}] * 3
        mock_create_client.return_value = mock_supabase

        mock_embeddings = MagicMock()
        test_embedding = [0.2] * 384
        mock_embeddings.embed_query.return_value = test_embedding
        mock_embeddings_cls.return_value = mock_embeddings

        from utils.faq_loader import main
        main()

        # Verify embeddings were generated
        assert mock_embeddings.embed_query.called

    @patch("utils.faq_loader.os.environ.get")
    @patch("utils.faq_loader.create_client")
    @patch("utils.faq_loader.HuggingFaceEmbeddings")
    @patch("builtins.open")
    def test_database_truncation_before_insert(self, mock_open, mock_embeddings_cls, mock_create_client, mock_environ):
        """Test that old FAQs are deleted before inserting new ones."""
        def env_side_effect(key, default=None):
            env_map = {
                "DATABASE_URL": "postgresql://test",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key"
            }
            return env_map.get(key, default)

        mock_environ.side_effect = env_side_effect

        faq_content = "# FAQ\nContent"
        mock_open.return_value.__enter__.return_value.read.return_value = faq_content

        mock_supabase = MagicMock()
        mock_delete_chain = MagicMock()
        mock_supabase.table.return_value.delete.return_value = mock_delete_chain
        mock_delete_chain.neq.return_value.execute.return_value = None
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "1"}]
        mock_create_client.return_value = mock_supabase

        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 384
        mock_embeddings_cls.return_value = mock_embeddings

        from utils.faq_loader import main
        main()

        # Verify delete was called
        mock_delete_chain.neq.assert_called()

    @patch("utils.faq_loader.os.environ.get")
    @patch("utils.faq_loader.create_client")
    @patch("utils.faq_loader.HuggingFaceEmbeddings")
    @patch("builtins.open")
    def test_successful_insert_confirmation(self, mock_open, mock_embeddings_cls, mock_create_client, mock_environ):
        """Test successful insert confirmation message."""
        def env_side_effect(key, default=None):
            env_map = {
                "DATABASE_URL": "postgresql://test",
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_KEY": "test-key"
            }
            return env_map.get(key, default)

        mock_environ.side_effect = env_side_effect

        faq_content = "# FAQ\nQuestion?\nAnswer."
        mock_open.return_value.__enter__.return_value.read.return_value = faq_content

        mock_supabase = MagicMock()
        mock_supabase.table.return_value.delete.return_value.neq.return_value.execute.return_value = None

        # Return same number of chunks as were uploaded
        num_chunks = 2
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": str(i)} for i in range(num_chunks)]
        mock_create_client.return_value = mock_supabase

        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 384
        mock_embeddings_cls.return_value = mock_embeddings

        from utils.faq_loader import main
        main()

        # Verify insert was called
        mock_supabase.table.return_value.insert.assert_called()
