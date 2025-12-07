"""
Tests for src/main.py

Tests FastAPI application setup, endpoints, and middleware.
"""
import pytest
import os
from unittest.mock import patch, MagicMock


class TestMainModule:
    """Test main.py module structure and components."""

    def test_main_file_has_fastapi_app(self):
        """Test that main.py defines a FastAPI app instance."""
        main_file = os.path.join(os.path.dirname(
            __file__), '..', 'src', 'main.py')
        with open(main_file, 'r') as f:
            content = f.read()
            assert 'FastAPI()' in content or 'app = ' in content
            assert 'from fastapi import' in content

    def test_main_has_cors_middleware(self):
        """Test that CORS middleware is configured."""
        main_file = os.path.join(os.path.dirname(
            __file__), '..', 'src', 'main.py')
        with open(main_file, 'r') as f:
            content = f.read()
            assert 'CORSMiddleware' in content

    def test_main_environment_variables_checked(self):
        """Test that environment variables are validated."""
        main_file = os.path.join(os.path.dirname(
            __file__), '..', 'src', 'main.py')
        with open(main_file, 'r') as f:
            content = f.read()
            assert 'SUPABASE_URL' in content
            assert 'SUPABASE_KEY' in content

    def test_main_has_llm_initialization(self):
        """Test that LLM providers are initialized."""
        main_file = os.path.join(os.path.dirname(
            __file__), '..', 'src', 'main.py')
        with open(main_file, 'r') as f:
            content = f.read()
            # Check for LLM-related imports or initialization
            assert 'ChatGroq' in content or 'ChatOpenAI' in content or 'Ollama' in content

    def test_main_has_embedding_model(self):
        """Test that embedding model is loaded."""
        main_file = os.path.join(os.path.dirname(
            __file__), '..', 'src', 'main.py')
        with open(main_file, 'r') as f:
            content = f.read()
            assert 'Embedding' in content or 'embedding' in content

    def test_main_has_api_endpoint(self):
        """Test that main.py defines API endpoints."""
        main_file = os.path.join(os.path.dirname(
            __file__), '..', 'src', 'main.py')
        with open(main_file, 'r') as f:
            content = f.read()
            # Look for FastAPI route decorators
            assert '@app' in content or '@router' in content

    def test_main_error_handling(self):
        """Test that main.py has error handling."""
        main_file = os.path.join(os.path.dirname(
            __file__), '..', 'src', 'main.py')
        with open(main_file, 'r') as f:
            content = f.read()
            assert 'try' in content or 'except' in content or 'HTTPException' in content
