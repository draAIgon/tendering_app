#!/usr/bin/env python3
"""
Simple test runner for essential API tests
Runs core API functionality tests
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run essential API tests"""
    print("🚀 Running Essential API Tests")
    print("=" * 60)
    
    api_tests_dir = Path(__file__).parent / "api"
    
    # Run the core API tests
    core_test = api_tests_dir / "test_api_core.py"
    final_test = api_tests_dir / "final_test.py"
    
    passed = 0
    total = 2
    
    if core_test.exists():
        print("\n🧪 Running Core API Tests (pytest-based)...")
        try:
            result = subprocess.run([sys.executable, "-m", "pytest", str(core_test), "-v"], 
                                  cwd=Path(__file__).parent.parent,
                                  text=True)
            if result.returncode == 0:
                print("✅ Core API Tests - PASSED")
                passed += 1
            else:
                print("❌ Core API Tests - FAILED")
        except Exception as e:
            print(f"❌ Core API Tests - ERROR: {e}")
    else:
        print("⚠️  Core API test file not found")
    
    if final_test.exists():
        print("\n🧪 Running Final API Tests (live endpoint tests)...")
        try:
            result = subprocess.run([sys.executable, str(final_test)], 
                                  cwd=api_tests_dir,
                                  text=True)
            if result.returncode == 0:
                print("✅ Final API Tests - PASSED")
                passed += 1
            else:
                print("❌ Final API Tests - FAILED")
        except Exception as e:
            print(f"❌ Final API Tests - ERROR: {e}")
    else:
        print("⚠️  Final API test file not found")
    
    print(f"\n{'='*60}")
    print(f"📊 API TESTS SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All API tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} API tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
