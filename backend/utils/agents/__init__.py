"""
Agents package for tendering application

This package contains various AI agents for processing and analyzing tendering documents:
- DocumentClassificationAgent: Classifies and organizes document content using embeddings
- DocumentExtractionAgent: Extracts text, images, tables and metadata
- ComparatorAgent: Compares different proposals
- ValidatorAgent: Validates document compliance
- RiskAnalyzerAgent: Analyzes risks in proposals
- ReporterAgent: Generates comprehensive reports
"""

from .document_classification import DocumentClassificationAgent
from .document_extraction import DocumentExtractionAgent

# Importaciones opcionales (evitar errores si no existen)
try:
    from .comparator import ComparatorAgent
except ImportError:
    pass

try:
    from .validator import ValidatorAgent
except ImportError:
    pass

try:
    from .risk_analyzer import RiskAnalyzerAgent
except ImportError:
    pass

try:
    from .reporter import ReporterAgent  
except ImportError:
    pass

try:
    from .proposal_comparison import ProposalComparisonAgent
except ImportError:
    pass

__all__ = [
    'DocumentClassificationAgent',
    'DocumentExtractionAgent',
    # Los demás se agregan dinámicamente si existen
]

# Agregar clases disponibles dinámicamente
if 'ComparatorAgent' in locals():
    __all__.append('ComparatorAgent')
if 'ValidatorAgent' in locals():
    __all__.append('ValidatorAgent')
if 'RiskAnalyzerAgent' in locals():
    __all__.append('RiskAnalyzerAgent')
if 'ReporterAgent' in locals():
    __all__.append('ReporterAgent')
if 'ProposalComparisonAgent' in locals():
    __all__.append('ProposalComparisonAgent')