# Essential Tests Directory

This directory contains essential test files for the tendering application backend.

## Essential Test Structure

### Agent Tests (Core Business Logic)
- `test_classification.py` - Document Classification Agent tests ✅
- `test_document_extraction.py` - Document Extraction Agent tests
- `test_risk_analyzer.py` - Risk Analyzer Agent tests  
- `test_comparator.py` - Comparator Agent tests
- `test_reporter.py` - Report Generation Agent tests
- `test_validator.py` - Compliance Validation Agent tests
- `test_proposal_comparison.py` - Proposal comparison functionality tests

### API Tests
- `api/test_api_core.py` - Core API endpoint tests (12 essential tests)
- `api/final_test.py` - Live API validation tests

## Running Tests

### Run All Tests
```bash
python tests/run_all_tests.py
```

### Run Agent Tests Only
```bash
python tests/run_agent_tests.py
```

### Run API Tests Only  
```bash
python tests/run_api_tests.py
```

### Run Individual Tests
```bash
python tests/test_classification.py
python tests/api/final_test.py
```

## Test Organization

All debugging and redundant test files have been removed. The current structure contains only essential tests that validate core agent functionality and API endpoints.

## Test Dependencies

The test suite requires:
- **OLLAMA server** running with `nomic-embed-text` model for embeddings
- **LibreOffice** for document conversion (optional)
- **Access to test documents** in the `documents/` and `LawData/` directories
- **Python dependencies**: All standard backend dependencies
