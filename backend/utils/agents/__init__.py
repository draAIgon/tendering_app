"""
Agents package for tendering application

This package contains various AI agents for processing and analyzing tendering documents:
- DocumentClassificationAgent: Classifies and organizes document content using embeddings
- DocumentExtractionAgent: Extracts text, images, tables and metadata
- ComparisonAgent: Compares different proposals
- ComplianceValidationAgent: Validates document compliance and RUC verification
- RiskAnalyzerAgent: Analyzes risks in proposals
- ReportGenerationAgent: Generates comprehensive reports
"""

# Importaciones opcionales (evitar errores si no existen)
try:
    from .document_classification import DocumentClassificationAgent
except ImportError:
    DocumentClassificationAgent = None

try:
    from .document_extraction import DocumentExtractionAgent
except ImportError:
    DocumentExtractionAgent = None

try:
    from .validator import ComplianceValidationAgent
except ImportError:
    ComplianceValidationAgent = None

try:
    from .comparison import ComparisonAgent
except ImportError:
    ComparisonAgent = None

try:
    from .risk_analyzer import RiskAnalyzerAgent
except ImportError:
    RiskAnalyzerAgent = None

try:
    from .reporter import ReportGenerationAgent  
except ImportError:
    ReportGenerationAgent = None

__all__ = []

# Agregar clases disponibles dinámicamente
if DocumentClassificationAgent:
    __all__.append('DocumentClassificationAgent')
if DocumentExtractionAgent:
    __all__.append('DocumentExtractionAgent')
if ComplianceValidationAgent:
    __all__.append('ComplianceValidationAgent')
if ComparisonAgent:
    __all__.append('ComparisonAgent')
if RiskAnalyzerAgent:
    __all__.append('RiskAnalyzerAgent')
if ReportGenerationAgent:
    __all__.append('ReportGenerationAgent')