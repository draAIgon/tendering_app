#!/usr/bin/env python3
"""
Ultra Simple API Test Runner
Just runs the essential tests and reports results clearly
"""

import subprocess
import sys
import requests
import time
from pathlib import Path

# Configuration
BASE_URL = "https://hackiathon-api.nimblersoft.org"
CURRENT_DIR = Path(__file__).parent
BACKEND_DIR = CURRENT_DIR.parent

def run_unit_tests():
    """Run unit tests and return (passed, failed)"""
    print("🧪 Running unit tests...")
    
    try:
        # Run the core API tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/api/test_api_core.py",  # Use relative path from backend dir
            "-v", "--tb=no"
        ], cwd=BACKEND_DIR, capture_output=True, text=True, timeout=60)
        
        # Parse the final summary line
        output = result.stdout
        print(f"DEBUG: Exit code = {result.returncode}")
        print("DEBUG: Last few lines of output:")
        for line in output.split('\n')[-5:]:
            if line.strip():
                print(f"  '{line.strip()}'")
        
        if result.returncode == 0:
            # All tests passed - look for "=== X passed in Y ==="
            for line in output.split('\n'):
                if '===' in line and ' passed in ' in line:
                    try:
                        # Extract from "=== 12 passed in 2.39s ==="
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'passed':
                                passed = int(parts[i-1])
                                print(f"✅ Unit tests: {passed} passed")
                                return passed, 0
                    except (ValueError, IndexError):
                        pass
        else:
            # Some tests failed - look for "=== X failed, Y passed in Z ==="
            for line in output.split('\n'):
                if '===' in line and ' failed, ' in line and ' passed in ' in line:
                    try:
                        # Extract from "=== 1 failed, 11 passed in 2.55s ==="
                        parts = line.split()
                        failed = int(parts[1])  # Number after "==="
                        passed_idx = parts.index('passed')
                        passed = int(parts[passed_idx - 1])
                        print(f"⚠️  Unit tests: {passed} passed, {failed} failed")
                        return passed, failed
                    except (ValueError, IndexError):
                        pass
        
        print("❌ Could not parse test results")
        return 0, 1
        
    except Exception as e:
        print(f"❌ Unit test error: {e}")
        return 0, 1

def test_live_api():
    """Test live API endpoints"""
    print(f"🌐 Testing live API at {BASE_URL}...")
    
    endpoints = [
        ("/", "Root"),
        ("/docs", "Docs"), 
        ("/openapi.json", "OpenAPI"),
        ("/api/v1/documents/list", "Documents")
    ]
    
    passed = 0
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {name}: OK")
                passed += 1
            else:
                print(f"  ❌ {name}: {response.status_code}")
        except Exception:
            print(f"  ❌ {name}: Error")
    
    print(f"📊 Live API: {passed}/{len(endpoints)} endpoints working")
    return passed, len(endpoints)

def main():
    """Main test runner"""
    print("🚀 API TEST SUITE")
    print("=" * 50)
    
    start_time = time.time()
    
    # Run unit tests
    unit_passed, unit_failed = run_unit_tests()
    
    # Test live API  
    live_passed, live_total = test_live_api()
    
    # Summary
    duration = time.time() - start_time
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print(f"🧪 Unit Tests: {unit_passed} passed, {unit_failed} failed")
    print(f"🌐 Live API: {live_passed}/{live_total} endpoints OK")
    print(f"⏱️  Duration: {duration:.1f}s")
    
    # Overall status
    total_issues = unit_failed + (live_total - live_passed)
    if total_issues == 0:
        print("🎉 ALL TESTS PASSED!")
        exit_code = 0
    elif unit_failed == 0:
        print("✅ UNIT TESTS PASSED (Live API has minor issues)")
        exit_code = 0
    else:
        print("❌ TESTS HAVE FAILURES")
        exit_code = 1
    
    print("=" * 50)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
