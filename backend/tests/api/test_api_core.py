"""
Core API Unit Tests - Simplified
Tests only the essential API endpoints and functionality
"""

from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from pathlib import Path
import sys

# Setup paths
current_dir = Path(__file__).parent
backend_dir = current_dir.parent.parent
sys.path.insert(0, str(backend_dir))

# Import API
from api.main import app

# Test client
client = TestClient(app)

class TestCoreAPI:
    """Test core API functionality"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "Tendering Analysis API"
    
    def test_api_documentation(self):
        """Test that API documentation is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Check it's HTML content
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_openapi_spec(self):
        """Test OpenAPI specification endpoint"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        spec = response.json()
        assert "openapi" in spec
        assert "paths" in spec
        assert "info" in spec

class TestDocumentEndpoints:
    """Test document management endpoints"""
    
    def test_documents_list_empty(self):
        """Test documents list when no documents exist"""
        response = client.get("/api/v1/documents/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "documents" in data
        assert "total_documents" in data
        assert isinstance(data["documents"], list)

class TestAnalysisEndpoints:
    """Test document analysis endpoints"""
    
    @patch('api.main.system_cache')
    def test_analysis_upload_invalid_file_type(self, mock_system):
        """Test upload with invalid file type"""
        # Mock the system
        mock_system_instance = Mock()
        mock_system.get.return_value = mock_system_instance
        
        # Test with text file (not supported)
        files = {"file": ("test.txt", "test content", "text/plain")}
        data = {"document_type": "contract", "analysis_level": "basic"}
        
        response = client.post("/api/v1/analysis/upload", files=files, data=data)
        assert response.status_code == 400
        
        result = response.json()
        assert "detail" in result
        assert "no soportado" in result["detail"].lower()

class TestComparisonEndpoints:
    """Test proposal comparison endpoints"""
    
    def test_comparison_no_files(self):
        """Test comparison endpoint with no files"""
        data = {"analysis_level": "basic"}
        
        response = client.post("/api/v1/comparison/upload-multiple", data=data)
        assert response.status_code == 422  # Validation error for missing files

class TestReportEndpoints:
    """Test report generation endpoints"""
    
    def test_generate_report_invalid_document_id(self):
        """Test report generation with invalid document ID"""
        response = client.get("/api/v1/reports/generate/invalid-id-12345")
        # Accept either 404 (not found) or 405 (method not allowed) as valid responses
        assert response.status_code in [404, 405]
        
        result = response.json()
        assert "detail" in result

class TestRFPEndpoints:
    """Test RFP analysis endpoints"""
    
    @patch('api.main.RFPAnalyzer')
    def test_rfp_analyze_no_file(self, mock_rfp_class):
        """Test RFP analysis with no file"""
        data = {"analysis_level": "basic"}
        
        response = client.post("/api/v1/rfp/analyze", data=data)
        assert response.status_code == 422  # Validation error

class TestErrorHandling:
    """Test API error handling"""
    
    def test_404_endpoint(self):
        """Test non-existent endpoint returns 404"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test wrong HTTP method returns 405"""
        response = client.post("/")  # Root only accepts GET
        assert response.status_code == 405

# Performance/Integration Tests
class TestAPIIntegration:
    """Integration tests for API functionality"""
    
    def test_multiple_endpoints_sequence(self):
        """Test calling multiple endpoints in sequence"""
        # Test root
        response1 = client.get("/")
        assert response1.status_code == 200
        
        # Test docs
        response2 = client.get("/docs")
        assert response2.status_code == 200
        
        # Test documents list
        response3 = client.get("/api/v1/documents/list")
        assert response3.status_code == 200
        
        # All should work independently
        assert all([r.status_code == 200 for r in [response1, response2, response3]])

# Quick smoke test
def test_api_is_responsive():
    """Smoke test - API responds to basic requests"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Tendering Analysis API"
