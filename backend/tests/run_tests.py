#!/usr/bin/env python3
"""
Test runner for the tendering app backend
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

def run_classification_tests():
    """Run the document classification tests"""
    print("🧪 Running Document Classification Tests...")
    from tests.test_classification import main
    main()

def run_extraction_tests():
    """Run the document extraction tests"""
    print("🧪 Running Document Extraction Tests...")
    from tests.test_document_extraction import main
    main()

def run_risk_analyzer_tests():
    """Run the risk analyzer tests"""
    print("🧪 Running Risk Analyzer Tests...")
    from tests.test_risk_analyzer import main
    main()

def run_comparator_tests():
    """Run the comparator tests"""
    print("🧪 Running Comparator Tests...")
    from tests.test_comparator import main
    main()

def run_validator_tests():
    """Run the compliance validator tests"""
    print("🧪 Running Compliance Validator Tests...")
    from tests.test_validator import main
    main()

def run_reporter_tests():
    """Run the reporter tests"""
    print("🧪 Running Reporter Tests...")
    from tests.test_reporter import main
    main()

def run_proposal_comparison_tests():
    """Run the proposal comparison tests"""
    print("🧪 Running Proposal Comparison Tests...")
    from tests.test_proposal_comparison import main
    main()

def main():
    """Main test runner"""
    print("🚀 Starting Test Suite")
    print("=" * 50)
    
    tests = [
        ("Document Classification", run_classification_tests),
        ("Document Extraction", run_extraction_tests),
        ("Risk Analyzer", run_risk_analyzer_tests),
        ("Document Comparator", run_comparator_tests),
        ("Compliance Validator", run_validator_tests),
        ("Report Generator", run_reporter_tests),
        ("Proposal Comparison", run_proposal_comparison_tests),
    ]
    
    passed_tests = []
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} tests...")
        try:
            test_func()
            passed_tests.append(test_name)
            print(f"✅ {test_name} tests completed successfully")
        except Exception as e:
            failed_tests.append(test_name)
            print(f"❌ {test_name} tests failed: {e}")
    
    # Final summary
    print(f"\n{'='*50}")
    print("🏆 FINAL TEST SUMMARY")
    print('='*50)
    
    total_tests = len(tests)
    passed_count = len(passed_tests)
    failed_count = len(failed_tests)
    
    print(f"Total test suites: {total_tests}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print(f"Success rate: {(passed_count/total_tests)*100:.1f}%")
    
    if passed_tests:
        print(f"\n✅ Successful test suites:")
        for test_name in passed_tests:
            print(f"  • {test_name}")
    
    if failed_tests:
        print(f"\n❌ Failed test suites:")
        for test_name in failed_tests:
            print(f"  • {test_name}")
    
    print(f"\n🏁 Test suite completed!")
    
    if passed_count == total_tests:
        print("🎉 All test suites passed!")
    else:
        print(f"⚠️  {failed_count} test suite(s) failed")

if __name__ == "__main__":
    main()
