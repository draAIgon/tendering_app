#!/usr/bin/env python3
"""
Debug Script - Test caching issue
"""

import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"
TEST_DOCUMENT_PATH = Path("/home/hackiathon/workspace/tendering_app/documents/EJEMPLO DE CONTRATO - RETO 1.pdf")

def debug_caching_issue():
    print("🔍 Debugging caching issue...")
    
    # 1. Check initial cache state
    print("\n1. Checking initial system status...")
    response = requests.get(f"{BASE_URL}/api/v1/utils/system-status")
    if response.status_code == 200:
        status = response.json()
        print(f"   Initial cache: {status['cache_stats']}")
    
    # 2. Upload document and track document_id
    print("\n2. Uploading document...")
    if TEST_DOCUMENT_PATH.exists():
        with open(TEST_DOCUMENT_PATH, 'rb') as f:
            files = {"file": ("EJEMPLO_DE_CONTRATO_RETO_1.pdf", f, "application/pdf")}
            data = {
                "document_type": "contract",
                "analysis_level": "standard", 
                "provider": "auto"
            }
            
            response = requests.post(f"{BASE_URL}/api/v1/analysis/upload", files=files, data=data, timeout=60)
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.text}")
        return False
    
    result = response.json()
    document_id = result["document_id"]
    print("   ✅ Upload successful")
    print(f"   Document ID: {document_id}")
    print(f"   Analysis stages: {result.get('analysis_result', {}).get('stages', {}).keys()}")
    
    # 3. Check cache state after upload
    print("\n3. Checking cache state after upload...")
    response = requests.get(f"{BASE_URL}/api/v1/utils/system-status")
    if response.status_code == 200:
        status = response.json()
        print(f"   Cache after upload: {status['cache_stats']}")
    
    # 4. Add debug endpoint call to see cache keys
    print("\n4. Checking available analyses...")
    response = requests.get(f"{BASE_URL}/api/v1/analysis/list")
    if response.status_code == 200:
        analyses = response.json()
        print(f"   Total analyses: {analyses['total_analyses']}")
        for analysis in analyses.get('analyses', []):
            print(f"   - ID: {analysis['document_id']}, Status: {analysis['status']}, Source: {analysis['source']}")
    
    # 5. Try to retrieve analysis directly
    print(f"\n5. Attempting to retrieve analysis with ID: {document_id}")
    response = requests.get(f"{BASE_URL}/api/v1/analysis/{document_id}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Retrieved successfully from: {result.get('source', 'unknown')}")
        return True
    else:
        print(f"   ❌ Failed: {response.text}")
        
        # 6. Try to check what's actually in the cache by listing documents
        print("\n6. Checking document list...")
        response = requests.get(f"{BASE_URL}/api/v1/documents/list")
        if response.status_code == 200:
            docs = response.json()
            print(f"   Total documents in system: {docs['total_documents']}")
            for doc in docs.get('documents', []):
                print(f"   - ID: {doc['id']}, Type: {doc['type']}, Status: {doc['status']}")
    
    return False

if __name__ == "__main__":
    success = debug_caching_issue()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
