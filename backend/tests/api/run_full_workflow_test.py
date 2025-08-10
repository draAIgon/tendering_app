#!/usr/bin/env python3
"""
Full Workflow Test Runner
========================

This script runs the comprehensive full workflow test for the Tendering Analysis API.
It tests the complete process from document upload to report generation.

Usage:
    python run_full_workflow_test.py [--quick] [--verbose]
    
Options:
    --quick     Run only the quick standalone test
    --verbose   Show detailed output from pytest
    --help      Show this help message
"""

import argparse
import subprocess
import sys
import requests
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_FILE = Path(__file__).parent / "test_full_workflow.py"

def check_api_server():
    """Check if API server is running"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            server_info = response.json()
            print(f"✅ API Server running: {server_info.get('name', 'Unknown')}")
            print(f"   Version: {server_info.get('version', 'Unknown')}")
            print(f"   URL: {BASE_URL}")
            return True
        else:
            print(f"❌ API Server responding but with error: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to API server at {BASE_URL}")
        print("   Make sure the server is running with:")
        print("   cd /home/hackiathon/workspace/tendering_app/backend")
        print("   python api/main.py")
        return False
    except Exception as e:
        print(f"❌ Error checking API server: {e}")
        return False

def run_quick_test():
    """Run the quick standalone workflow test"""
    print("🚀 Running Quick Workflow Test...")
    print("=" * 50)
    
    try:
        # Import and run the quick test
        sys.path.append(str(TEST_FILE.parent))
        from test_full_workflow import run_quick_workflow_test
        
        success = run_quick_workflow_test()
        
        if success:
            print("\n🎉 Quick workflow test PASSED!")
            return True
        else:
            print("\n❌ Quick workflow test FAILED!")
            return False
            
    except Exception as e:
        print(f"❌ Error running quick test: {e}")
        return False

def run_full_pytest():
    """Run the full pytest suite for the workflow"""
    print("🧪 Running Full Workflow Test Suite...")
    print("=" * 50)
    
    # Prepare pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        str(TEST_FILE),
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--show-capture=no",  # Don't show captured output
        "-x"  # Stop on first failure
    ]
    
    try:
        # Run pytest
        result = subprocess.run(cmd, capture_output=False, text=True, timeout=300)
        
        if result.returncode == 0:
            print("\n🎉 Full workflow test suite PASSED!")
            return True
        else:
            print(f"\n❌ Full workflow test suite FAILED! (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n⏰ Test suite timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"\n❌ Error running test suite: {e}")
        return False

def show_test_info():
    """Show information about the test suite"""
    print("📋 Full Workflow Test Suite Information")
    print("=" * 50)
    print(f"Test file: {TEST_FILE}")
    print(f"API URL: {BASE_URL}")
    print("")
    print("Test Coverage:")
    print("  ✅ System status and API availability")
    print("  ✅ Document upload and comprehensive analysis")
    print("  ✅ Analysis result retrieval")
    print("  ✅ JSON report generation")
    print("  ✅ HTML report generation")
    print("  ✅ Semantic search functionality")
    print("  ✅ Database management operations")
    print("  ✅ Document export functionality")
    print("  ✅ Document listing")
    print("  ✅ Error handling (invalid formats, nonexistent docs)")
    print("  ✅ Performance testing (response times, concurrency)")
    print("  ✅ Cleanup operations")
    print("")
    print("Supported Document Types: PDF, DOC, DOCX, TXT")
    print("Analysis Levels: basic, standard, comprehensive")
    print("Report Formats: JSON, HTML")
    print("")

def main():
    parser = argparse.ArgumentParser(description="Run full workflow tests for Tendering Analysis API")
    parser.add_argument("--quick", action="store_true", help="Run only quick standalone test")
    parser.add_argument("--verbose", action="store_true", help="Show detailed pytest output")
    parser.add_argument("--info", action="store_true", help="Show test suite information")
    
    args = parser.parse_args()
    
    if args.info:
        show_test_info()
        return 0
    
    print("🎯 Full Workflow Test Runner")
    print("=" * 40)
    
    # Check if API server is running
    if not check_api_server():
        print("\n💡 To start the API server:")
        print("   cd /home/hackiathon/workspace/tendering_app/backend")
        print("   python api/main.py")
        return 1
    
    print("")
    
    # Run appropriate test
    if args.quick:
        success = run_quick_test()
    else:
        success = run_full_pytest()
    
    # Summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("   The full workflow is working correctly")
        return 0
    else:
        print("❌ TESTS FAILED!")
        print("   Check the output above for details")
        return 1

if __name__ == "__main__":
    exit(main())
