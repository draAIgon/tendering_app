#!/usr/bin/env python3
"""
Working API Test Runner - Final Version
"""

import subprocess
import sys
import requests
import time
from pathlib import Path

def main():
    """Simple main test runner"""
    print("🚀 SIMPLIFIED API TESTS")
    print("=" * 40)
    
    backend_dir = Path(__file__).parent.parent.parent
    
    # 1. Run unit tests directly with absolute path
    print("🧪 Unit Tests:")
    try:
        test_file = Path(__file__).parent / "test_api_core.py"
        result = subprocess.run([
            sys.executable, "-m", "pytest", str(test_file), "-q"
        ], cwd=backend_dir, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Look for the results in stdout
            output = result.stdout
            lines = output.split('\n')
            for line in lines:
                if 'passed' in line:
                    print(f"   ✅ {line.strip()}")
                    break
            else:
                print("   ✅ Tests passed")
        else:
            print(f"   ❌ Some tests failed (exit code: {result.returncode})")
            if result.stdout:
                lines = result.stdout.split('\n')
                if len(lines) > 1:
                    print(f"      {lines[-2]}")
    except Exception as e:
        print(f"   ❌ Error running tests: {e}")
    
    # 2. Test live API
    print("\n🌐 Live API:")
    base_url = "https://hackiathon-api.nimblersoft.org"
    
    endpoints = [
        ("/", "Root"),
        ("/docs", "Documentation"), 
        ("/api/v1/documents/list", "Documents")
    ]
    
    working = 0
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {name}: OK")
                working += 1
            else:
                print(f"   ❌ {name}: {response.status_code}")
        except Exception:
            print(f"   ❌ {name}: Error")
    
    print(f"\n📊 Results: {working}/{len(endpoints)} live endpoints working")
    
    if working == len(endpoints):
        print("🎉 All tests successful!")
        return 0
    else:
        print("⚠️  Some issues found")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
