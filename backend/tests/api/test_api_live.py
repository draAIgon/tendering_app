"""
Live API Tests - Simplified
Tests the actual deployed API at https://hackiathon-api.nimblersoft.org/
"""

import pytest
import requests
import time
from pathlib import Path

# Configuration
BASE_URL = "https://hackiathon-api.nimblersoft.org"
TIMEOUT = 10

class TestLiveAPI:
    """Test the live deployed API"""
    
    @pytest.fixture(scope="class")
    def api_available(self):
        """Check if API is available before running tests"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def test_api_is_accessible(self, api_available):
        """Test that the API is accessible"""
        if not api_available:
            pytest.skip("API is not accessible")
        
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Tendering Analysis API"
        assert "version" in data
    
    def test_api_documentation_available(self, api_available):
        """Test API documentation is accessible"""
        if not api_available:
            pytest.skip("API is not accessible")
        
        response = requests.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_openapi_spec_available(self, api_available):
        """Test OpenAPI specification is available"""
        if not api_available:
            pytest.skip("API is not accessible")
        
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=TIMEOUT)
        assert response.status_code == 200
        
        spec = response.json()
        assert "openapi" in spec
        assert "paths" in spec
        
        # Count available endpoints
        paths = spec.get("paths", {})
        assert len(paths) > 10  # Should have multiple endpoints
    
    def test_documents_endpoint(self, api_available):
        """Test documents endpoint works"""
        if not api_available:
            pytest.skip("API is not accessible")
        
        response = requests.get(f"{BASE_URL}/api/v1/documents/list", timeout=TIMEOUT)
        assert response.status_code == 200
        
        data = response.json()
        assert "documents" in data
        assert "total_documents" in data
    
    def test_api_response_time(self, api_available):
        """Test API response time is reasonable"""
        if not api_available:
            pytest.skip("API is not accessible")
        
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)
        duration = time.time() - start_time
        
        assert response.status_code == 200
        assert duration < 2.0  # Should respond within 2 seconds
    
    def test_error_handling(self, api_available):
        """Test API error handling"""
        if not api_available:
            pytest.skip("API is not accessible")
        
        # Test 404 for non-existent endpoint
        response = requests.get(f"{BASE_URL}/api/v1/nonexistent", timeout=TIMEOUT)
        assert response.status_code == 404

# Quick connectivity test
def test_api_connectivity():
    """Quick test to verify API connectivity"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        assert response.status_code == 200
        print(f"✅ API is accessible at {BASE_URL}")
    except Exception as e:
        pytest.skip(f"API not accessible: {e}")
