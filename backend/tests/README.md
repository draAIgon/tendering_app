# Backend Tests

This directory contains comprehensive test files for all agents in the tendering app backend.

## Structure

```
tests/
├── __init__.py                        # Tests package init
├── run_tests.py                       # Main test runner for all agents
├── test_classification.py             # Document classification agent tests
├── test_document_extraction.py        # Document extraction agent tests
├── test_risk_analyzer.py              # Risk analysis agent tests
├── test_comparator.py                 # Document comparison agent tests
├── test_validator.py                  # Compliance validation agent tests
├── test_reporter.py                   # Report generation agent tests
├── test_proposal_comparison.py        # Proposal comparison agent tests
└── README.md                          # This file
```

## Agent Test Coverage

### 🧪 **DocumentClassificationAgent** (`test_classification.py`)
- ✅ Basic classification and section identification
- ✅ Semantic search capabilities 
- ✅ Key requirement extraction
- Tests document categorization using 9-category taxonomy

### 📄 **DocumentExtractionAgent** (`test_document_extraction.py`)
- ✅ Basic text extraction from PDFs
- ✅ Complete document processing pipeline
- ✅ Error handling for missing documents
- ✅ Multi-document processing (legal documents)

### 🚨 **RiskAnalyzerAgent** (`test_risk_analyzer.py`)
- ✅ Risk identification and categorization (5 risk types)
- ✅ Risk scoring and severity assessment
- ✅ Risk mitigation strategy generation
- ✅ Multi-dimensional risk analysis

### 🔄 **ComparatorAgent** (`test_comparator.py`)
- ✅ Basic document comparison
- ✅ Multi-document similarity analysis
- ✅ Semantic similarity calculations
- ✅ Custom comparison criteria evaluation

### ✅ **ComplianceValidationAgent** (`test_validator.py`)
- ✅ Basic compliance validation
- ✅ Document completeness checking
- ✅ Regulatory compliance verification
- ✅ Technical requirements validation

### 📊 **ReportGenerationAgent** (`test_reporter.py`)
- ✅ Basic report generation (6 report types)
- ✅ Multiple report formats (JSON, HTML, PDF)
- ✅ Custom report configuration
- ✅ Export format validation

### 📋 **ProposalComparisonAgent** (`test_proposal_comparison.py`)
- ✅ Basic proposal comparison
- ✅ Technical aspect comparison
- ✅ Economic evaluation and ranking
- ✅ Compliance level assessment

## Database Structure

All tests use organized database paths under the `db` directory:

- `backend/db/test_classification/` - Document classification test database
- `backend/db/test_risk_analysis/` - Risk analysis test database
- `backend/db/test_comparator/` - Document comparison test database
- `backend/db/test_compliance_validation/` - Compliance validation test database
- `backend/db/test_proposal_comparison/` - Proposal comparison test database
- `backend/db/test_reports/` - Report generation output directory

## Running Tests

### Run all tests:
```bash
cd /home/hackiathon/workspace/tendering_app/backend
python tests/run_tests.py
```

### Run specific test suite:
```bash
cd /home/hackiathon/workspace/tendering_app/backend
python tests/test_classification.py        # Document classification
python tests/test_document_extraction.py   # Document extraction
python tests/test_risk_analyzer.py         # Risk analysis
python tests/test_comparator.py            # Document comparison
python tests/test_validator.py             # Compliance validation
python tests/test_reporter.py              # Report generation
python tests/test_proposal_comparison.py   # Proposal comparison
```

## Test Dependencies

The test suite requires:
- **OLLAMA server** running with `nomic-embed-text` model for embeddings
- **LibreOffice** for document conversion (optional)
- **Access to test documents** in the `documents/` and `LawData/` directories
- **Python dependencies**: All standard backend dependencies

## Test Results Summary

Each test suite includes:
- ✅ **Basic functionality tests** - Core agent capabilities
- ✅ **Advanced feature tests** - Specialized functions
- ✅ **Error handling tests** - Graceful failure scenarios
- ✅ **Integration tests** - Cross-agent functionality

### Current Test Status
- **7 Agent Test Suites** covering all backend agents
- **28+ Individual Test Functions** with comprehensive coverage
- **Database Organization** with dedicated test collections
- **Comprehensive Logging** for debugging and monitoring

## Performance Notes

- Tests use OLLAMA for local embedding generation (no API costs)
- Database persistence allows for faster repeated test runs
- Each agent maintains separate test databases to avoid conflicts
- Tests are designed to work with existing project documents

## Adding New Tests

When adding new tests:
1. Follow the existing naming pattern: `test_{agent_name}.py`
2. Use the organized database structure: `db_dir / "test_{agent_name}"`
3. Include comprehensive error handling and logging
4. Add the test to the main runner in `run_tests.py`
5. Update this README with test coverage details
