#!/usr/bin/env python3
"""
Simple test runner for essential agent tests
Runs all the core agent functionality tests
"""

import sys
import subprocess
from pathlib import Path

def run_test(test_file, description):
    """Run a single test file"""
    print(f"\n{'='*60}")
    print(f"🧪 Running {description}")
    print('='*60)
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=False, 
                              cwd=Path(__file__).parent,
                              text=True)
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Run all essential agent tests"""
    print("🚀 Running Essential Agent Tests")
    print("=" * 60)
    
    tests_dir = Path(__file__).parent
    tests = [
        (tests_dir / "test_classification.py", "Document Classification Agent"),
        (tests_dir / "test_document_extraction.py", "Document Extraction Agent"),
        (tests_dir / "test_risk_analyzer.py", "Risk Analyzer Agent"),
        (tests_dir / "test_reporter.py", "Report Generation Agent"),
        (tests_dir / "test_ruc_validator.py", "RUC Validation Agent"),
        (tests_dir / "test_validator.py", "Compliance Validation Agent"),
        (tests_dir / "test_comparison.py", "Comparison Agent"),
        (tests_dir / "test_integrated_analysis.py", "Integrated Analysis Agent"),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_file, description in tests:
        if test_file.exists():
            if run_test(test_file, description):
                passed += 1
        else:
            print(f"⚠️  {description} - Test file not found: {test_file}")
    
    print(f"\n{'='*60}")
    print("📊 AGENT TESTS SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All agent tests passed!")
        return 0
    else:
        print(f"⚠️  {total - passed} agent tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
