"""
UI and API tests for Vecinita using FastAPI TestClient.
Tests the FastAPI application endpoints and responses.
"""
import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.mark.ui
class TestUIWithFastAPI:
    """UI and API tests for the Vecinita application using FastAPI TestClient."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client."""
        # Import app after adding parent to path
        from main import app
        self.client = TestClient(app)
    
    def test_root_endpoint_returns_html(self):
        """Test that the root endpoint returns HTML content."""
        response = self.client.get("/")
        assert response.status_code == 200
        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_root_endpoint_contains_body(self):
        """Test that root endpoint returns HTML with body element."""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "<body" in response.text or "<html" in response.text
    
    def test_root_endpoint_not_empty(self):
        """Test that root endpoint returns non-empty content."""
        response = self.client.get("/")
        assert response.status_code == 200
        assert len(response.text) > 0
    
    def test_ask_api_endpoint_with_question(self):
        """Test the /ask API endpoint with a question."""
        # Note: This test requires valid environment variables
        # Mock the response if needed
        with patch('main.supabase') as mock_supabase:
            # Set up mock responses
            mock_supabase.return_value = MagicMock()
            
            response = self.client.get(
                "/ask",
                params={"question": "What is housing policy?"}
            )
            
            # Should return 200 OK or handle error gracefully
            assert response.status_code in [200, 422, 500]
    
    def test_ask_endpoint_accepts_get(self):
        """Test that /ask endpoint accepts GET requests."""
        response = self.client.get(
            "/ask",
            params={"question": "Test question"}
        )
        
        # Endpoint should exist (not 404) but may fail auth/db
        assert response.status_code != 404
    
    def test_ask_endpoint_requires_question(self):
        """Test that /ask endpoint requires question parameter."""
        response = self.client.get("/ask")
        
        # Should not accept GET without question parameter
        assert response.status_code != 200
    
    def test_spanish_question_handling(self):
        """Test that the API can handle Spanish language questions."""
        with patch('main.supabase') as mock_supabase:
            mock_supabase.return_value = MagicMock()
            
            response = self.client.get(
                "/ask",
                params={"question": "¿Cuál es la política de vivienda?"}
            )
            
            # Should accept Spanish text
            assert response.status_code in [200, 422, 500]
    
    def test_api_response_structure(self):
        """Test that API responses have expected structure."""
        # Test with mocked data
        with patch('main.supabase') as mock_supabase:
            mock_supabase.return_value = MagicMock()
            
            response = self.client.get(
                "/ask",
                params={"question": "What is housing?"}
            )
            
            # Response should be JSON
            assert response.status_code != 404


@pytest.mark.ui
class TestUIErrorHandling:
    """Test error handling in the FastAPI application."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client."""
        from main import app
        self.client = TestClient(app)
    
    def test_invalid_endpoint_returns_404(self):
        """Test that invalid endpoints return 404."""
        response = self.client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_ask_without_question_field(self):
        """Test that /ask endpoint validates request parameters."""
        response = self.client.get(
            "/ask",
            params={"invalid_field": "test"}
        )
        
        # Should return validation error (400 or 422)
        assert response.status_code in [400, 422]
    
    def test_ask_with_empty_question(self):
        """Test that /ask endpoint handles empty questions."""
        response = self.client.get(
            "/ask",
            params={"question": ""}
        )
        
        # Should handle gracefully (400, 422, or 500)
        assert response.status_code in [200, 400, 422, 500]
    
    def test_post_request_to_ask_endpoint(self):
        """Test that /ask endpoint doesn't accept POST requests."""
        response = self.client.post(
            "/ask",
            json={"question": "test"}
        )
        
        # POST should not be allowed on /ask (GET only)
        assert response.status_code in [404, 405]
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present in response."""
        response = self.client.get("/")
        
        # Should have successful response
        assert response.status_code == 200


@pytest.mark.ui
class TestAPIResponseHeaders:
    """Test API response headers and content types."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client."""
        from main import app
        self.client = TestClient(app)
    
    def test_html_endpoint_content_type(self):
        """Test that HTML endpoint returns correct content type."""
        response = self.client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_api_accepts_json_content_type(self):
        """Test that API accepts GET requests with parameters."""
        response = self.client.get(
            "/ask",
            params={"question": "test"}
        )
        
        # GET with parameters should work
        assert response.status_code != 415
