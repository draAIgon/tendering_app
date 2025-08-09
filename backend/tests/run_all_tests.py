#!/usr/bin/env python3
"""
Main test runner for the tendering app
Runs all essential tests (agents and API)
"""

import sys
import subprocess
from pathlib import Path

def run_test_suite(script_name, description):
    """Run a test suite"""
    print(f"\n{'='*70}")
    print(f"🏃 {description}")
    print('='*70)
    
    script_path = Path(__file__).parent / script_name
    
    try:
        result = subprocess.run([sys.executable, str(script_path)], 
                              cwd=Path(__file__).parent,
                              text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    """Run all test suites"""
    print("🚀 Tendering App - Essential Test Runner")
    print("=" * 70)
    
    suites = [
        ("run_agent_tests.py", "Agent Tests (Classification, Extraction, Risk Analysis, etc.)"),
        ("run_api_tests.py", "API Tests (Core endpoints and live API validation)"),
    ]
    
    passed_suites = 0
    total_suites = len(suites)
    
    for script, description in suites:
        if run_test_suite(script, description):
            passed_suites += 1
            print(f"✅ {description} - PASSED")
        else:
            print(f"❌ {description} - FAILED")
    
    print(f"\n{'='*70}")
    print(f"🏆 FINAL TEST RESULTS")
    print(f"{'='*70}")
    print(f"Test Suites Passed: {passed_suites}/{total_suites}")
    
    if passed_suites == total_suites:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"⚠️  {total_suites - passed_suites} test suite(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
