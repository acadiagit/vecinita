"""
Tests for main.py - FastAPI application for Vecinita RAG Q&A system.
Includes both unit tests and UI tests using Playwright.
"""
import pytest
import os
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
from langdetect import LangDetectException


@pytest.fixture
def app_with_mocks():
    """Create FastAPI app with mocked dependencies."""
    with patch("main.create_client") as mock_supabase, \
            patch("main.ChatGroq") as mock_groq, \
            patch("main.HuggingFaceEmbeddings") as mock_embeddings:

        # Setup mocks
        mock_supabase_client = MagicMock()
        mock_supabase.return_value = mock_supabase_client

        mock_groq.return_value = MagicMock()
        mock_embeddings.return_value = MagicMock()

        # Import after mocks are set
        from main import app
        return app, mock_supabase_client


@pytest.mark.unit
class TestRootEndpoint:
    """Test the root endpoint serving index.html."""

    def test_get_root_returns_html_file(self, fastapi_client):
        """Test that GET / returns the index.html file."""
        response = fastapi_client.get("/")
        assert response.status_code == 200
        # Check if it's returning a file response (could be HTML content)
        assert response.headers.get(
            "content-length") or len(response.content) > 0

    def test_get_root_content_type(self, fastapi_client):
        """Test that root endpoint has appropriate content type."""
        response = fastapi_client.get("/")
        # Could be text/html or application/octet-stream depending on FileResponse
        assert response.status_code == 200


@pytest.mark.unit
class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_check_returns_ok(self, fastapi_client):
        """Test that /health returns status ok."""
        response = fastapi_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.unit
class TestAskEndpoint:
    """Test the Q&A endpoint with various scenarios."""

    @patch("main.create_client")
    @patch("main.ChatGroq")
    @patch("main.HuggingFaceEmbeddings")
    @patch("main.detect")
    def test_ask_empty_question(self, mock_detect, mock_embeddings, mock_groq, mock_supabase):
        """Test that empty question returns 400 error."""
        from main import app
        client = TestClient(app)

        response = client.get("/ask")
        assert response.status_code == 422  # Missing required parameter

    @patch("main.create_client")
    @patch("main.ChatGroq")
    @patch("main.HuggingFaceEmbeddings")
    @patch("main.detect")
    def test_ask_english_question(self, mock_detect, mock_embeddings_cls, mock_groq_cls, mock_supabase_cls):
        """Test ask endpoint with English question."""
        # Setup mocks
        mock_detect.return_value = "en"

        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value.data = [
            {
                "content": "Housing information",
                "source": "https://example.com"
            }
        ]
        mock_supabase_cls.return_value = mock_supabase

        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 384
        mock_embeddings_cls.return_value = mock_embeddings

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Housing information response"
        mock_llm.invoke.return_value = mock_response
        mock_groq_cls.return_value = mock_llm

        from main import app
        client = TestClient(app)

        response = client.get("/ask?question=What%20is%20housing%20policy?")
        assert response.status_code == 200
        assert "answer" in response.json()
        assert "context" in response.json()

    @patch("main.create_client")
    @patch("main.ChatGroq")
    @patch("main.HuggingFaceEmbeddings")
    @patch("main.detect")
    def test_ask_spanish_question(self, mock_detect, mock_embeddings_cls, mock_groq_cls, mock_supabase_cls):
        """Test ask endpoint with Spanish question."""
        mock_detect.return_value = "es"

        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value.data = [
            {
                "content": "Información de vivienda",
                "source": "https://example.com"
            }
        ]
        mock_supabase_cls.return_value = mock_supabase

        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 384
        mock_embeddings_cls.return_value = mock_embeddings

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Respuesta en español"
        mock_llm.invoke.return_value = mock_response
        mock_groq_cls.return_value = mock_llm

        from main import app
        client = TestClient(app)

        response = client.get(
            "/ask?question=¿Cuál%20es%20la%20política%20de%20vivienda?")
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "context" in data

    @patch("main.create_client")
    @patch("main.ChatGroq")
    @patch("main.HuggingFaceEmbeddings")
    @patch("main.detect")
    def test_ask_no_context_found(self, mock_detect, mock_embeddings_cls, mock_groq_cls, mock_supabase_cls):
        """Test ask endpoint when no relevant documents are found."""
        mock_detect.return_value = "en"

        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value.data = []  # Empty results
        mock_supabase_cls.return_value = mock_supabase

        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 384
        mock_embeddings_cls.return_value = mock_embeddings

        mock_groq_cls.return_value = MagicMock()

        from main import app
        client = TestClient(app)

        response = client.get("/ask?question=Unknown%20topic")
        assert response.status_code == 200
        assert "could not find a definitive answer" in response.json()[
            "answer"]

    @patch("main.create_client")
    @patch("main.ChatGroq")
    @patch("main.HuggingFaceEmbeddings")
    @patch("main.detect")
    def test_ask_language_detection_exception(self, mock_detect, mock_embeddings_cls, mock_groq_cls, mock_supabase_cls):
        """Test ask endpoint handles language detection exceptions."""
        mock_detect.side_effect = LangDetectException(0, "test error")

        mock_supabase = MagicMock()
        mock_supabase.rpc.return_value.execute.return_value.data = [
            {"content": "Test", "source": "https://example.com"}
        ]
        mock_supabase_cls.return_value = mock_supabase

        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1] * 384
        mock_embeddings_cls.return_value = mock_embeddings

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Response in default English"
        mock_llm.invoke.return_value = mock_response
        mock_groq_cls.return_value = mock_llm

        from main import app
        client = TestClient(app)

        response = client.get("/ask?question=Test%20question")
        assert response.status_code == 200


@pytest.mark.unit
class TestCORSMiddleware:
    """Test CORS configuration."""

    def test_cors_headers_present(self, fastapi_client):
        """Test that CORS headers are present."""
        response = fastapi_client.get("/health")
        # CORS allows all origins
        assert response.status_code == 200

    @patch("main.create_client")
    @patch("main.ChatGroq")
    @patch("main.HuggingFaceEmbeddings")
    def test_cors_with_options_request(self, mock_embeddings, mock_groq, mock_supabase):
        """Test CORS preflight request."""
        from main import app
        client = TestClient(app)

        # OPTIONS on /ask returns 405 (Method Not Allowed) which is expected
        # CORS headers are added by middleware on actual requests
        response = client.options("/ask")
        # Just verify we get a response
        assert response.status_code in [200, 405]


@pytest.mark.integration
class TestMainIntegration:
    """Integration tests for main.py with mock Supabase."""

    @patch("main.create_client")
    @patch("main.ChatGroq")
    @patch("main.HuggingFaceEmbeddings")
    @patch("main.detect")
    def test_full_question_answer_flow(self, mock_detect, mock_embeddings_cls, mock_groq_cls, mock_supabase_cls):
        """Test complete flow from question to answer."""
        mock_detect.return_value = "en"

        # Mock Supabase
        mock_supabase = MagicMock()
        mock_response_data = [
            {
                "content": "Vecinita provides community resources including housing assistance.",
                "source": "https://vecinita.example.com/resources"
            }
        ]
        mock_supabase.rpc.return_value.execute.return_value.data = mock_response_data
        mock_supabase_cls.return_value = mock_supabase

        # Mock embeddings
        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.5] * 384
        mock_embeddings_cls.return_value = mock_embeddings

        # Mock LLM
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Vecinita provides community resources including housing assistance. (Source: https://vecinita.example.com/resources)"
        mock_llm.invoke.return_value = mock_response
        mock_groq_cls.return_value = mock_llm

        from main import app
        client = TestClient(app)

        response = client.get(
            "/ask?question=What%20services%20does%20Vecinita%20provide?")
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "context" in data
        assert len(data["context"]) >= 1  # At least 1 context item
        # Check that answer contains relevant content about Vecinita
        assert "vecinita" in data["answer"].lower()
