#!/usr/bin/env python3
"""
DSPy-Enhanced Unified Comparison Agent 
Integrates document comparison with risk assessment and compliance validation
using DSPy for intelligent analysis and reasoning.
"""

import os
import re
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from collections import defaultdict

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# DSPy imports
import dspy
from dspy import Signature, InputField, OutputField, Predict, Module

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Importar utilidades del paquete
from ..db_manager import get_standard_db_path
from ..embedding import get_embeddings_provider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# DSPy Signatures for enhanced comparison analysis
class DocumentAnalysisSignature(Signature):
    """Análisis integral de documentos integrando contenido, estructura, aspectos técnicos y evaluación de riesgos.
    
    DIRECTRICES DE ANÁLISIS:
    - Evaluar la completitud del documento contra los requisitos de licitación
    - Evaluar especificaciones técnicas y cumplimiento normativo
    - Identificar riesgos potenciales y estrategias de mitigación
    - Proporcionar puntuación basada en múltiples criterios
    - Responder en español para documentos ecuatorianos
    """
    
    document_content: str = InputField(desc="Contenido completo del documento a analizar")
    document_type: str = InputField(desc="Tipo de documento: Pliego, Propuesta, Contrato")
    analysis_focus: str = InputField(desc="Enfoque específico: técnico, económico, cumplimiento, riesgo")
    risk_context: str = InputField(desc="Contexto de evaluación de riesgos del análisis previo")
    compliance_context: str = InputField(desc="Contexto de validación de cumplimiento")
    
    overall_score: int = OutputField(desc="Puntaje general de calidad del documento (0-100)")
    strengths: str = OutputField(desc="Fortalezas clave identificadas en el documento (en español)")
    weaknesses: str = OutputField(desc="Áreas que requieren mejora o atención (en español)")
    risk_factors: str = OutputField(desc="Factores de riesgo identificados con niveles de severidad (en español)")
    compliance_status: str = OutputField(desc="Resumen de evaluación de cumplimiento (en español)")
    recommendations: str = OutputField(desc="Recomendaciones específicas para mejora (en español)")

class ComparativeAnalysisSignature(Signature):
    """Análisis comparativo avanzado entre múltiples documentos usando inteligencia integrada.
    
    CRITERIOS DE COMPARACIÓN:
    - Completitud técnica y calidad
    - Competitividad económica y valor
    - Perfil de riesgo y estrategias de mitigación
    - Cumplimiento con requisitos normativos
    - Idoneidad general para objetivos del proyecto
    - Responder en español para contexto ecuatoriano
    """
    
    documents_data: str = InputField(desc="Datos JSON de todos los documentos con resultados de análisis")
    comparison_criteria: str = InputField(desc="Criterios específicos para enfocar durante la comparación")
    risk_assessments: str = InputField(desc="Resultados de análisis de riesgo para todos los documentos")
    compliance_results: str = InputField(desc="Resultados de validación de cumplimiento")
    
    ranking: str = OutputField(desc="Lista ordenada de documentos de mejor a peor con puntajes (en español)")
    comparative_summary: str = OutputField(desc="Resumen de diferencias clave entre documentos (en español)")
    selection_rationale: str = OutputField(desc="Justificación detallada para selección recomendada (en español)")
    risk_comparison: str = OutputField(desc="Comparación de perfiles de riesgo entre documentos (en español)")
    decision_factors: str = OutputField(desc="Factores críticos que deben influir en decisión final (en español)")

class TenderEvaluationSignature(Signature):
    """Specialized tender evaluation for proposal assessment in competitive bidding.
    
    EVALUATION FRAMEWORK:
    - Technical capability assessment (40%)
    - Economic proposal evaluation (35%) 
    - Compliance and legal requirements (25%)
    - Risk mitigation strategies
    - Past performance and experience
    """
    
    proposals_data: str = InputField(desc="Complete proposal data with technical, economic, and compliance info")
    evaluation_criteria: str = InputField(desc="Specific evaluation criteria and weights")
    rfp_requirements: str = InputField(desc="Original RFP requirements for comparison")
    
    technical_scores: str = OutputField(desc="Technical evaluation scores for each proposal")
    economic_evaluation: str = OutputField(desc="Economic analysis with cost-benefit assessment")
    final_ranking: str = OutputField(desc="Final ranking with weighted scores")
    award_recommendation: str = OutputField(desc="Recommendation for contract award")
    justification: str = OutputField(desc="Detailed justification for the recommendation")

class EnhancedComparisonModule(Module):
    """DSPy module for enhanced document comparison with integrated intelligence"""
    
    def __init__(self, vector_db: Optional[Chroma] = None, risk_analyzer: Optional[Any] = None, validator: Optional[Any] = None):
        super().__init__()
        self.vector_db = vector_db
        self.risk_analyzer = risk_analyzer
        self.validator = validator
        
        # Initialize DSPy components
        self.analyze_document = Predict(DocumentAnalysisSignature)
        self.comparative_analysis = Predict(ComparativeAnalysisSignature)
        self.tender_evaluation = Predict(TenderEvaluationSignature)
        
    def forward(self, documents: Dict[str, Dict], analysis_type: str = "comprehensive", 
               classification_contexts: Dict = None, validation_contexts: Dict = None) -> Dict[str, Any]:
        """Enhanced forward method with external context integration"""
        
        # Step 1: Individual document analysis with external context
        document_analyses = {}
        for doc_id, doc_data in documents.items():
            content = doc_data['content']
            doc_type = doc_data.get('doc_type', 'proposal')
            
            # Get risk assessment from external context if available
            risk_context = "{}"
            if classification_contexts and doc_id in classification_contexts:
                risk_analysis = classification_contexts[doc_id].get('risk_assessment', {})
                risk_context = json.dumps(risk_analysis, ensure_ascii=False, default=str)
            else:
                risk_context = '{"message": "Risk analysis should be provided by BiddingAnalysisSystem"}'
            
            # Get compliance validation from external context if available
            compliance_context = "{}"
            if validation_contexts and doc_id in validation_contexts:
                compliance_analysis = validation_contexts[doc_id]
                compliance_context = json.dumps(compliance_analysis, ensure_ascii=False, default=str)
            else:
                compliance_context = '{"message": "Compliance validation should be provided by BiddingAnalysisSystem"}'
            
            # Perform enhanced document analysis
            try:
                doc_analysis = self.analyze_document(
                    document_content=content[:2000],  # Limit content length for DSPy
                    document_type=doc_type,
                    analysis_focus=analysis_type,
                    risk_context=risk_context[:500],  # Limit context length
                    compliance_context=compliance_context[:500]
                )
                
                document_analyses[doc_id] = {
                    'analysis': doc_analysis,
                    'risk_assessment': json.loads(risk_context) if risk_context != "{}" else {},
                    'compliance_validation': json.loads(compliance_context) if compliance_context != "{}" else {},
                    'metadata': doc_data.get('metadata', {})
                }
            except Exception as e:
                logger.error(f"DSPy analysis failed for {doc_id}: {e}")
                document_analyses[doc_id] = {
                    'analysis': None,
                    'error': str(e),
                    'metadata': doc_data.get('metadata', {})
                }
        
        # Step 2: Comparative analysis
        documents_json = json.dumps({
            doc_id: {
                'content_summary': doc_data['content'][:500],
                'analysis': getattr(data.get('analysis'), '__dict__', {}) if data.get('analysis') else {},
                'metadata': data.get('metadata', {})
            }
            for doc_id, data in document_analyses.items()
        }, ensure_ascii=False, default=str)
        
        risk_assessments_json = json.dumps({
            doc_id: data.get('risk_assessment', {}) for doc_id, data in document_analyses.items()
        }, ensure_ascii=False, default=str)
        
        compliance_results_json = json.dumps({
            doc_id: data.get('compliance_validation', {}) for doc_id, data in document_analyses.items()
        }, ensure_ascii=False, default=str)
        
        try:
            if analysis_type == "tender":
                # Specialized tender evaluation
                comparison_result = self.tender_evaluation(
                    proposals_data=documents_json[:1500],
                    evaluation_criteria="technical:40%, economic:35%, compliance:25%",
                    rfp_requirements="Standard RFP requirements"
                )
            else:
                # General comparative analysis
                comparison_result = self.comparative_analysis(
                    documents_data=documents_json[:1500],
                    comparison_criteria=analysis_type,
                    risk_assessments=risk_assessments_json[:1000],
                    compliance_results=compliance_results_json[:1000]
                )
        except Exception as e:
            logger.error(f"DSPy comparative analysis failed: {e}")
            comparison_result = None
        
        return {
            'document_analyses': document_analyses,
            'comparative_result': comparison_result,
            'analysis_type': analysis_type,
            'timestamp': datetime.now().isoformat()
        }


class ComparisonAgent:
    """
    Enhanced Unified agent for document and proposal comparison with DSPy intelligence.
    Integrates risk assessment and compliance validation for comprehensive analysis.
    """

    # Enhanced comparison modes with DSPy integration
    COMPARISON_MODES = {
        'GENERAL': {
            'CONTENT_SIMILARITY': {
                'weight': 0.25,
                'description': 'Similitud semántica del contenido',
                'method': 'embedding_similarity'
            },
            'STRUCTURAL_COMPLIANCE': {
                'weight': 0.25,
                'description': 'Cumplimiento estructural y organizacional',
                'method': 'structural_analysis'
            },
            'TECHNICAL_COMPLETENESS': {
                'weight': 0.25,
                'description': 'Completitud técnica y especificaciones',
                'method': 'technical_analysis'
            },
            'ECONOMIC_COMPETITIVENESS': {
                'weight': 0.25,
                'description': 'Competitividad económica y financiera',
                'method': 'economic_analysis'
            }
        },
        'TENDER_EVALUATION': {
            'TECHNICAL': {
                'weight': 0.4,
                'description': 'Capacidad técnica',
                'subcriteria': {
                    'technical_specifications': {'weight': 0.3, 'keywords': ['especificaciones técnicas', 'requisitos técnicos', 'tecnología']},
                    'experience': {'weight': 0.25, 'keywords': ['experiencia', 'proyectos anteriores', 'referencias']},
                    'methodology': {'weight': 0.25, 'keywords': ['metodología', 'enfoque', 'plan de trabajo']},
                    'team_qualifications': {'weight': 0.2, 'keywords': ['equipo', 'personal', 'certificaciones']}
                }
            },
            'ECONOMIC': {
                'weight': 0.35,
                'description': 'Propuesta económica',
                'subcriteria': {
                    'total_price': {'weight': 0.5, 'keywords': ['precio total', 'valor', 'costo']},
                    'payment_terms': {'weight': 0.2, 'keywords': ['forma de pago', 'términos', 'anticipo']},
                    'cost_breakdown': {'weight': 0.2, 'keywords': ['desglose', 'detalle de costos', 'presupuesto']},
                    'value_for_money': {'weight': 0.1, 'keywords': ['relación precio-calidad', 'valor agregado']}
                }
            },
            'COMPLIANCE': {
                'weight': 0.25,
                'description': 'Cumplimiento normativo',
                'subcriteria': {
                    'legal_compliance': {'weight': 0.4, 'keywords': ['cumplimiento legal', 'normatividad', 'regulaciones']},
                    'document_completeness': {'weight': 0.3, 'keywords': ['documentos completos', 'requisitos', 'anexos']},
                    'deadlines_compliance': {'weight': 0.3, 'keywords': ['plazos', 'cronograma', 'fechas de entrega']}
                }
            }
        }
    }

    def __init__(self, vector_db_path: Optional[Path] = None, llm_provider: str = "auto"):
        self.vector_db_path = vector_db_path or get_standard_db_path('comparison', 'global')
        self.embeddings_provider = None
        self.vector_db = None
        self.documents: Dict[str, Any] = {}
        self.comparison_results: Dict[str, Any] = {}
        self.cached_embeddings: Dict[str, Any] = {}
        
        # Initialize integrated agents
        self.risk_analyzer = None
        self.validator = None
        self.dspy_module = None
        
        # Initialize DSPy LLM
        self._initialize_dspy_llm(llm_provider)
        
        logger.info(f"Enhanced ComparisonAgent iniciado con DB: {self.vector_db_path}")

    def _initialize_dspy_llm(self, provider: str = "auto"):
        """Initialize DSPy with appropriate LLM"""
        try:
            if provider == "auto" or provider == "ollama":
                # Try Ollama first for local processing
                try:
                    lm = dspy.LM(model="ollama/llama3.2:3b", api_base="http://localhost:11434")
                    dspy.settings.configure(lm=lm)
                    logger.info("DSPy configured with Ollama local LLM")
                    return
                except Exception as e:
                    logger.warning(f"Failed to initialize Ollama for DSPy: {e}")
            
            if provider == "auto" or provider == "openai":
                # Fallback to OpenAI
                import os
                if os.getenv("OPENAI_API_KEY"):
                    lm = dspy.LM(model="gpt-3.5-turbo", max_tokens=2000)
                    dspy.settings.configure(lm=lm)
                    logger.info("DSPy configured with OpenAI GPT-3.5-turbo")
                    return
                else:
                    logger.warning("OpenAI API key not found")
            
            # Fallback to a simple dummy LLM for testing
            logger.warning("No LLM available, using dummy LLM for DSPy")
            lm = dspy.LM(model="dummy")  # Use dummy model for testing
            dspy.settings.configure(lm=lm)
            
        except Exception as e:
            logger.error(f"Error initializing DSPy LLM: {e}")
            # Use dummy for testing
            try:
                lm = dspy.LM(model="dummy")
                dspy.settings.configure(lm=lm)
            except Exception as e2:
                logger.error(f"Failed to initialize dummy LLM: {e2}")
                # If all else fails, don't configure DSPy
                pass

    def initialize_embeddings(self, provider: str = "auto", model: Optional[str] = None) -> bool:
        """Inicializa embeddings y agentes integrados."""
        try:
            # Initialize embeddings
            embeddings_result = get_embeddings_provider(provider=provider, model=model)
            if isinstance(embeddings_result, tuple):
                self.embeddings_provider = embeddings_result[0]
            else:
                self.embeddings_provider = embeddings_result
                
            logger.info("Enhanced sistema de embeddings inicializado")
            return True
        except Exception as e:
            logger.error(f"Error inicializando embeddings y agentes: {e}")
            return False

    def _initialize_dspy_module(self) -> bool:
        """Initialize DSPy module for enhanced analysis"""
        try:
            self.dspy_module = EnhancedComparisonModule()
            logger.info("DSPy comparison module initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing DSPy module: {e}")
            return False

    def analyze_document(self, document_content: str, doc_name: str, 
                        classification_context: Dict = None, validation_context: Dict = None) -> Dict[str, Any]:
        """Enhanced document analysis using DSPy intelligence with classification and validation context
        
        Args:
            document_content: Pre-extracted text content from DocumentExtractionAgent
            doc_name: Name/identifier for the document
            classification_context: Classification results from BiddingAnalysisSystem
            validation_context: Validation results from BiddingAnalysisSystem
        """
        try:
            if not self.dspy_module:
                self._initialize_dspy_module()
            
            # Validate input content
            if not document_content or not document_content.strip():
                return {"error": "No se proporcionó contenido del documento"}
            
            # Prepare document data for DSPy module
            documents_data = {
                doc_name: {
                    'content': document_content,
                    'doc_type': self._get_document_type_from_context(classification_context, doc_name),
                    'metadata': {}
                }
            }
            
            # Prepare contexts for DSPy module
            classification_contexts = {}
            validation_contexts = {}
            
            if classification_context:
                classification_contexts[doc_name] = classification_context
            
            if validation_context:
                validation_contexts[doc_name] = validation_context
            
            # Get analysis from DSPy using forward method
            dspy_result = self.dspy_module.forward(
                documents=documents_data,
                analysis_type="comprehensive",
                classification_contexts=classification_contexts,
                validation_contexts=validation_contexts
            )
            
            # Extract analysis for this document
            doc_key = doc_name
            document_analysis = dspy_result.get('document_analyses', {}).get(doc_key, {})
            analysis_result = document_analysis.get('analysis')
            
            # Use risk assessment from context if available
            risk_analysis = {}
            if classification_context and 'risk_assessment' in classification_context:
                # Use provided risk assessment context from API
                risk_analysis = classification_context['risk_assessment']
            else:
                # No risk analysis available - ComparisonAgent should only receive results
                risk_analysis = {"message": "Risk analysis not provided - should be calculated by BiddingAnalysisSystem"}
            
            # Use compliance validation from context if available
            compliance_validation = {}
            if validation_context:
                # Use provided validation context from API
                compliance_validation = validation_context
            else:
                # No validation available - ComparisonAgent should only receive results
                compliance_validation = {"message": "Compliance validation not provided - should be calculated by BiddingAnalysisSystem"}
            
            # Include external classification context if provided
            classification_results = classification_context or {}
            
            # Combine all analyses
            enhanced_analysis = {
                "document_name": doc_name,
                "dspy_analysis": analysis_result,
                "risk_analysis": risk_analysis,
                "compliance_validation": compliance_validation,
                "classification_context": classification_results,
                "validation_context": validation_context or {},
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_method": "DSPy Enhanced Analysis with Context Integration"
            }
            
            # Store in documents registry
            doc_key = doc_name
            self.documents[doc_key] = enhanced_analysis
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"Error in DSPy document analysis: {e}")
            return {"error": f"Error en análisis DSPy: {str(e)}"}

    def compare_documents(self, doc1_content: str, doc2_content: str, 
                         doc1_name: str, doc2_name: str,
                         comparison_mode: str = "GENERAL",
                         doc1_analysis: Dict = None, doc2_analysis: Dict = None) -> Dict[str, Any]:
        """Enhanced document comparison using DSPy intelligence with pre-analyzed document data
        
        Args:
            doc1_content: Pre-extracted text content from DocumentExtractionAgent for document 1
            doc2_content: Pre-extracted text content from DocumentExtractionAgent for document 2
            doc1_name: Name/identifier for document 1
            doc2_name: Name/identifier for document 2
            comparison_mode: Comparison mode (GENERAL, TENDER_EVALUATION, etc.)
            doc1_analysis: Pre-analyzed results from BiddingAnalysisSystem for document 1
            doc2_analysis: Pre-analyzed results from BiddingAnalysisSystem for document 2
        """
        try:
            if not self.dspy_module:
                self._initialize_dspy_module()
            
            # Use provided analyses or analyze documents if not provided
            if not doc1_analysis:
                doc1_analysis = self.analyze_document(doc1_content, doc1_name)
            if not doc2_analysis:
                doc2_analysis = self.analyze_document(doc2_content, doc2_name)
            
            # Prepare documents data for DSPy module
            documents_data = {
                doc1_name: {
                    'content': doc1_content,
                    'doc_type': self._get_document_type_from_context(doc1_analysis.get('classification_context'), doc1_name),
                    'metadata': {}
                },
                doc2_name: {
                    'content': doc2_content,
                    'doc_type': self._get_document_type_from_context(doc2_analysis.get('classification_context'), doc2_name),
                    'metadata': {}
                }
            }
            
            # Prepare contexts for DSPy module (using analysis contexts)
            classification_contexts = {}
            validation_contexts = {}
            
            if doc1_analysis and 'classification_context' in doc1_analysis:
                classification_contexts[doc1_name] = doc1_analysis['classification_context']
            if doc2_analysis and 'classification_context' in doc2_analysis:
                classification_contexts[doc2_name] = doc2_analysis['classification_context']
                
            if doc1_analysis and 'validation_context' in doc1_analysis:
                validation_contexts[doc1_name] = doc1_analysis['validation_context']
            if doc2_analysis and 'validation_context' in doc2_analysis:
                validation_contexts[doc2_name] = doc2_analysis['validation_context']
            
            # Get comparison from DSPy using forward method
            dspy_result = self.dspy_module.forward(
                documents=documents_data,
                analysis_type=comparison_mode.lower(),
                classification_contexts=classification_contexts,
                validation_contexts=validation_contexts
            )
            
            comparison_result = dspy_result.get('comparative_result')
            
            # Calculate enhanced scoring
            enhanced_scoring = self._calculate_enhanced_scoring(
                doc1_analysis, doc2_analysis, comparison_mode
            )
            
            # Compile comprehensive results
            comprehensive_comparison = {
                "document1": doc1_name,
                "document2": doc2_name,
                "comparison_mode": comparison_mode,
                "dspy_comparison": comparison_result,
                "enhanced_scoring": enhanced_scoring,
                "individual_analyses": {
                    "document1": doc1_analysis,
                    "document2": doc2_analysis
                },
                "comparison_timestamp": datetime.now().isoformat(),
                "comparison_method": "DSPy Enhanced Comparison"
            }
            
            # Store results
            result_key = f"{doc1_name}_vs_{doc2_name}"
            self.comparison_results[result_key] = comprehensive_comparison
            
            return comprehensive_comparison
            
        except Exception as e:
            logger.error(f"Error in DSPy document comparison: {e}")
            return {"error": f"Error en comparación DSPy: {str(e)}"}

    def evaluate_tender_proposals(self, proposals_data: List[Dict], 
                                 tender_requirements: str = None) -> Dict[str, Any]:
        """Enhanced tender evaluation using DSPy intelligence with pre-analyzed proposal data
        
        Args:
            proposals_data: List of dicts with keys: 'content', 'name', 'analysis' (from BiddingAnalysisSystem)
            tender_requirements: Optional tender requirements description
        """
        try:
            if not self.dspy_module:
                self._initialize_dspy_module()
            
            evaluated_proposals = []
            
            for proposal_data in proposals_data:
                try:
                    proposal_name = proposal_data['name']
                    proposal_content = proposal_data['content']
                    proposal_analysis = proposal_data.get('analysis')
                    
                    # Prepare documents data for DSPy tender evaluation
                    documents_data = {
                        proposal_name: {
                            'content': proposal_content,
                            'doc_type': 'proposal',
                            'metadata': {}
                        }
                    }
                    
                    # Prepare contexts for DSPy module (using proposal analysis contexts)
                    classification_contexts = {}
                    validation_contexts = {}
                    
                    if proposal_analysis and 'classification_context' in proposal_analysis:
                        classification_contexts[proposal_name] = proposal_analysis['classification_context']
                    
                    if proposal_analysis and 'validation_context' in proposal_analysis:
                        validation_contexts[proposal_name] = proposal_analysis['validation_context']
                    
                    # Get tender evaluation from DSPy using forward method
                    dspy_result = self.dspy_module.forward(
                        documents=documents_data,
                        analysis_type="tender",
                        classification_contexts=classification_contexts,
                        validation_contexts=validation_contexts
                    )
                    
                    evaluation_result = dspy_result.get('comparative_result')
                    
                    # Get individual analysis for scoring
                    proposal_dspy_analysis = dspy_result.get('document_analyses', {}).get(proposal_name, {})
                    
                    # Calculate comprehensive scoring
                    comprehensive_score = self._calculate_tender_score(proposal_analysis or proposal_dspy_analysis, evaluation_result)
                    
                    evaluated_proposal = {
                        "proposal_name": proposal_name,
                        "dspy_evaluation": evaluation_result,
                        "comprehensive_score": comprehensive_score,
                        "detailed_analysis": proposal_analysis or proposal_dspy_analysis,
                        "evaluation_timestamp": datetime.now().isoformat()
                    }
                    
                    evaluated_proposals.append(evaluated_proposal)
                    
                except Exception as e:
                    logger.error(f"Error evaluating proposal {proposal_name}: {e}")
                    evaluated_proposals.append({
                        "proposal_name": proposal_name,
                        "error": f"Error en evaluación: {str(e)}"
                    })
            
            # Rank proposals
            ranked_proposals = self._rank_proposals(evaluated_proposals)
            
            # Generate summary report
            evaluation_summary = {
                "total_proposals": len(proposals_data),
                "successfully_evaluated": len([p for p in evaluated_proposals if "error" not in p]),
                "evaluation_method": "DSPy Enhanced Tender Evaluation",
                "evaluation_timestamp": datetime.now().isoformat(),
                "ranked_proposals": ranked_proposals,
                "detailed_evaluations": evaluated_proposals
            }
            
            return evaluation_summary
            
        except Exception as e:
            logger.error(f"Error in DSPy tender evaluation: {e}")
            return {"error": f"Error en evaluación DSPy: {str(e)}"}

    def _get_document_type_from_context(self, classification_context: Dict, doc_name: str) -> str:
        """Extract document type from classification context provided by DocumentClassificationAgent"""
        if not classification_context:
            return 'document'  # Default fallback
        
        # Look for document type in classification results
        if 'document_type' in classification_context:
            return classification_context['document_type'].lower()
        
        # Look for document type in classification categories
        if 'document_category' in classification_context:
            return classification_context['document_category'].lower()
        
        # Look for inferred type from filename analysis (if provided by classifier)
        if 'inferred_type' in classification_context:
            return classification_context['inferred_type'].lower()
        
        # Fallback to default
        return 'document'

    def _get_comparison_criteria(self, comparison_mode: str) -> str:
        """Get comparison criteria description for DSPy"""
        criteria = self.COMPARISON_MODES.get(comparison_mode, self.COMPARISON_MODES['GENERAL'])
        criteria_text = f"Comparison mode: {comparison_mode}\n"
        for criterion, config in criteria.items():
            criteria_text += f"- {criterion} (weight: {config['weight']}): {config['description']}\n"
        return criteria_text

    def _extract_score_from_analysis(self, analysis: Dict, criterion: str) -> float:
        """Extract numerical score from analysis result with enhanced risk weighting"""
        try:
            # Try to find relevant scores in the analysis
            dspy_analysis = analysis.get("dspy_analysis", {})
            risk_analysis = analysis.get("risk_analysis", {})
            compliance = analysis.get("compliance_validation", {})
            classification_context = analysis.get("classification_context", {})
            
            # Handle risk assessment with enhanced penalty for high-risk documents
            if criterion == "RISK_ASSESSMENT" or criterion == "TECHNICAL":
                if risk_analysis and "overall_risk_score" in risk_analysis:
                    risk_score = risk_analysis.get("overall_risk_score", 0.5)
                    # Convert risk to positive score with stronger penalty for high risk
                    if risk_score > 0.8:  # Very high risk
                        return 0.1  # Very low score
                    elif risk_score > 0.6:  # High risk
                        return 0.3  # Low score
                    elif risk_score > 0.4:  # Medium risk
                        return 0.6  # Medium score
                    else:  # Low risk
                        return 0.9  # High score
                elif classification_context and "risk_assessment" in classification_context:
                    risk_data = classification_context["risk_assessment"]
                    risk_score = risk_data.get("overall_risk_score", 0.5)
                    # Same enhanced penalty logic
                    if risk_score > 0.8:
                        return 0.1
                    elif risk_score > 0.6:
                        return 0.3
                    elif risk_score > 0.4:
                        return 0.6
                    else:
                        return 0.9
                else:
                    return 0.5  # Default neutral score
            
            # Handle compliance scoring
            elif criterion == "COMPLIANCE":
                if compliance and "compliance_score" in compliance:
                    compliance_score = compliance.get("compliance_score", 0.5)
                    return compliance_score
                elif compliance and "overall_compliance" in compliance:
                    return compliance.get("overall_compliance", 0.5)
                else:
                    return 0.5
            
            # Handle economic scoring
            elif criterion == "ECONOMIC":
                if risk_analysis and "overall_risk_score" in risk_analysis:
                    risk_score = risk_analysis.get("overall_risk_score", 0.5)
                    # Economic offers from high-risk tenders should be penalized
                    base_score = 0.7  # Default economic score
                    if risk_score > 0.8:
                        return base_score * 0.3  # Heavy penalty
                    elif risk_score > 0.6:
                        return base_score * 0.6  # Medium penalty
                    else:
                        return base_score
                else:
                    return 0.7
            
            # Default scoring from DSPy analysis
            else:
                if hasattr(dspy_analysis, 'overall_score'):
                    score = float(dspy_analysis.overall_score) / 100.0  # Convert to 0-1 scale
                    return min(1.0, max(0.0, score))
                elif isinstance(dspy_analysis, dict):
                    if 'overall_score' in dspy_analysis:
                        score = float(dspy_analysis['overall_score']) / 100.0
                        return min(1.0, max(0.0, score))
                    return dspy_analysis.get('quality_score', 0.5)
                else:
                    return 0.5  # Default neutral score
                    
        except Exception as e:
            logger.warning(f"Error extrayendo score para {criterion}: {e}")
            return 0.5

    def _calculate_tender_score(self, proposal_analysis: Dict, evaluation_result: Any) -> Dict[str, float]:
        """Calculate comprehensive tender score"""
        try:
            scores = {}
            
            # Technical score
            technical_score = 0.7  # Default
            if hasattr(evaluation_result, 'technical_score'):
                technical_score = float(evaluation_result.technical_score)
            scores['technical'] = technical_score
            
            # Economic score
            economic_score = 0.6  # Default
            if hasattr(evaluation_result, 'economic_score'):
                economic_score = float(evaluation_result.economic_score)
            scores['economic'] = economic_score
            
            # Compliance score
            compliance_data = proposal_analysis.get("compliance_validation", {})
            compliance_score = compliance_data.get("compliance_score", 0.5)
            scores['compliance'] = compliance_score
            
            # Risk score (inverted)
            risk_data = proposal_analysis.get("risk_analysis", {})
            risk_score = 1.0 - risk_data.get("overall_risk_score", 0.5)
            scores['risk_mitigation'] = risk_score
            
            # Calculate weighted total using TENDER_EVALUATION weights
            tender_criteria = self.COMPARISON_MODES['TENDER_EVALUATION']
            total_score = (
                scores['technical'] * tender_criteria['TECHNICAL']['weight'] +
                scores['economic'] * tender_criteria['ECONOMIC']['weight'] +
                scores['compliance'] * tender_criteria['COMPLIANCE']['weight'] +
                scores['risk_mitigation'] * 0.1  # Risk mitigation weight
            )
            
            scores['total'] = total_score
            return scores
            
        except Exception as e:
            logger.error(f"Error calculating tender score: {e}")
            return {'technical': 0.5, 'economic': 0.5, 'compliance': 0.5, 'risk_mitigation': 0.5, 'total': 0.5}

    def _rank_proposals(self, evaluated_proposals: List[Dict]) -> List[Dict]:
        """Rank proposals by comprehensive score"""
        try:
            # Filter out proposals with errors
            valid_proposals = [p for p in evaluated_proposals if "error" not in p]
            
            # Sort by total score descending
            ranked = sorted(
                valid_proposals, 
                key=lambda x: x.get("comprehensive_score", {}).get("total", 0),
                reverse=True
            )
            
            # Add ranking information
            for i, proposal in enumerate(ranked):
                proposal["rank"] = i + 1
                proposal["percentile"] = (len(ranked) - i) / len(ranked) * 100 if ranked else 0
            
            return ranked
            
        except Exception as e:
            logger.error(f"Error ranking proposals: {e}")
            return evaluated_proposals

    def _calculate_enhanced_scoring(self, doc1_analysis: Dict, doc2_analysis: Dict, 
                                  comparison_mode: str) -> Dict[str, Any]:
        """Calculate enhanced scoring incorporating risk and compliance factors with Spanish output"""
        try:
            scoring = {}
            criteria = self.COMPARISON_MODES.get(comparison_mode, self.COMPARISON_MODES['GENERAL'])
            
            # Calculate individual criterion scores
            for criterion, config in criteria.items():
                doc1_score = self._extract_score_from_analysis(doc1_analysis, criterion)
                doc2_score = self._extract_score_from_analysis(doc2_analysis, criterion)
                
                scoring[criterion] = {
                    "document1_score": doc1_score,
                    "document2_score": doc2_score,
                    "winner": "document1" if doc1_score > doc2_score else "document2" if doc2_score > doc1_score else "empate",
                    "score_difference": abs(doc1_score - doc2_score),
                    "weight": config['weight'],
                    "weighted_contribution": {
                        "document1": doc1_score * config['weight'],
                        "document2": doc2_score * config['weight']
                    },
                    "descripcion": config.get('description', 'Criterio de evaluación')
                }
            
            # Calculate base overall scores
            overall_doc1 = sum(s["weighted_contribution"]["document1"] for s in scoring.values())
            overall_doc2 = sum(s["weighted_contribution"]["document2"] for s in scoring.values())
            
            # Apply additional risk penalty for tender evaluations
            risk_penalty_doc1 = 0
            risk_penalty_doc2 = 0
            
            if comparison_mode == "TENDER_EVALUATION":
                # Extract risk scores for penalty calculation
                risk1 = self._get_risk_score(doc1_analysis)
                risk2 = self._get_risk_score(doc2_analysis)
                
                # Apply progressive penalty for high-risk documents
                if risk1 > 0.8:
                    risk_penalty_doc1 = 0.3  # 30% penalty for very high risk
                elif risk1 > 0.6:
                    risk_penalty_doc1 = 0.15  # 15% penalty for high risk
                elif risk1 > 0.4:
                    risk_penalty_doc1 = 0.05  # 5% penalty for medium risk
                
                if risk2 > 0.8:
                    risk_penalty_doc2 = 0.3  # 30% penalty for very high risk
                elif risk2 > 0.6:
                    risk_penalty_doc2 = 0.15  # 15% penalty for high risk
                elif risk2 > 0.4:
                    risk_penalty_doc2 = 0.05  # 5% penalty for medium risk
                
                # Apply penalties
                overall_doc1 = overall_doc1 * (1.0 - risk_penalty_doc1)
                overall_doc2 = overall_doc2 * (1.0 - risk_penalty_doc2)
            
            # Determine winner with meaningful threshold
            score_difference = abs(overall_doc1 - overall_doc2)
            threshold = 0.05  # 5% threshold for meaningful difference
            
            if score_difference < threshold:
                winner = "empate"
                winner_reason = "Diferencia mínima entre documentos"
            elif overall_doc1 > overall_doc2:
                winner = "document1"
                winner_reason = f"Documento 1 superior por {score_difference:.3f} puntos"
            else:
                winner = "document2"
                winner_reason = f"Documento 2 superior por {score_difference:.3f} puntos"
            
            # Generate Spanish recommendations
            recommendations = self._generate_spanish_recommendations(
                doc1_analysis, doc2_analysis, scoring, risk_penalty_doc1, risk_penalty_doc2
            )
            
            scoring["overall"] = {
                "document1_total": overall_doc1,
                "document2_total": overall_doc2,
                "overall_winner": winner,
                "winner_reason": winner_reason,
                "score_difference": score_difference,
                "risk_penalty_doc1": risk_penalty_doc1,
                "risk_penalty_doc2": risk_penalty_doc2,
                "recommendations": recommendations
            }
            
            return scoring
            
        except Exception as e:
            logger.error(f"Error calculando scoring mejorado: {e}")
            return {"error": "Error en cálculo de puntajes"}

    def _get_risk_score(self, analysis: Dict) -> float:
        """Extract risk score from analysis data"""
        try:
            # Try risk_analysis first
            risk_analysis = analysis.get("risk_analysis", {})
            if risk_analysis and "overall_risk_score" in risk_analysis:
                return risk_analysis["overall_risk_score"]
            
            # Try classification context
            classification_context = analysis.get("classification_context", {})
            if classification_context and "risk_assessment" in classification_context:
                risk_data = classification_context["risk_assessment"]
                return risk_data.get("overall_risk_score", 0.5)
            
            # Try direct risk context in analysis
            if "risk_assessment" in analysis:
                return analysis["risk_assessment"].get("overall_risk_score", 0.5)
                
            return 0.5  # Default medium risk
        except Exception as e:
            logger.warning(f"Error extrayendo score de riesgo: {e}")
            return 0.5

    def _generate_spanish_recommendations(self, doc1_analysis: Dict, doc2_analysis: Dict, 
                                        scoring: Dict, penalty1: float, penalty2: float) -> List[str]:
        """Generate recommendations in Spanish based on analysis"""
        recommendations = []
        
        try:
            # Analyze winner per criterion
            winners_count = {"document1": 0, "document2": 0, "empate": 0}
            for criterion, data in scoring.items():
                if criterion != "overall":
                    winners_count[data["winner"]] += 1
            
            # Risk-based recommendations
            risk1 = self._get_risk_score(doc1_analysis)
            risk2 = self._get_risk_score(doc2_analysis)
            
            if penalty1 > 0.2:
                recommendations.append("⚠️ Documento 1 presenta riesgos muy altos que afectan significativamente su evaluación")
            elif penalty1 > 0.1:
                recommendations.append("⚠️ Documento 1 presenta riesgos considerables que deben ser evaluados cuidadosamente")
            
            if penalty2 > 0.2:
                recommendations.append("⚠️ Documento 2 presenta riesgos muy altos que afectan significativamente su evaluación")
            elif penalty2 > 0.1:
                recommendations.append("⚠️ Documento 2 presenta riesgos considerables que deben ser evaluados cuidadosamente")
            
            # Risk comparison
            if abs(risk1 - risk2) > 0.3:
                safer_doc = "Documento 1" if risk1 < risk2 else "Documento 2"
                recommendations.append(f"📊 {safer_doc} presenta un perfil de riesgo significativamente menor")
            
            # Winner-based recommendations
            overall_winner = scoring.get("overall", {}).get("overall_winner", "empate")
            if overall_winner == "document1":
                recommendations.append("🏆 Se recomienda el Documento 1 como la mejor opción")
            elif overall_winner == "document2":
                recommendations.append("🏆 Se recomienda el Documento 2 como la mejor opción")
            else:
                recommendations.append("⚖️ Ambos documentos presentan características similares - se requiere evaluación adicional")
            
            # Specific criterion recommendations
            best_criteria_doc1 = [k for k, v in scoring.items() if k != "overall" and v["winner"] == "document1"]
            best_criteria_doc2 = [k for k, v in scoring.items() if k != "overall" and v["winner"] == "document2"]
            
            if best_criteria_doc1:
                criteria_names = [scoring[c].get("descripcion", c) for c in best_criteria_doc1[:2]]
                recommendations.append(f"💪 Documento 1 destaca en: {', '.join(criteria_names)}")
            
            if best_criteria_doc2:
                criteria_names = [scoring[c].get("descripcion", c) for c in best_criteria_doc2[:2]]
                recommendations.append(f"💪 Documento 2 destaca en: {', '.join(criteria_names)}")
            
            # Risk mitigation recommendations
            if max(risk1, risk2) > 0.7:
                recommendations.append("🔍 Se recomienda realizar evaluación adicional de riesgos antes de la adjudicación")
            
            if abs(penalty1 - penalty2) > 0.1:
                lower_penalty_doc = "Documento 1" if penalty1 < penalty2 else "Documento 2"
                recommendations.append(f"🛡️ {lower_penalty_doc} presenta menores riesgos regulatorios y operacionales")
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {e}")
            recommendations.append("Error generando recomendaciones detalladas")
        
        return recommendations[:6]  # Limit to 6 most important recommendations

    def add_document(self, doc_id: str, content: str, doc_type: str = "proposal",
                     metadata: Optional[Dict] = None):
        """
        Registra un documento/propuesta en el sistema de comparación.
        """
        if not content or not content.strip():
            raise ValueError(f"Empty content for document {doc_id}")

        metadata = metadata or {}

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " "],
        )

        chunks = splitter.split_text(content)
        documents: List[Document] = []

        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) > 50:  # Solo chunks “sustanciosos”
                doc_metadata = {
                    'doc_id': doc_id,
                    'doc_type': doc_type,
                    'chunk_id': i,
                    'chunk_count': len(chunks),
                    **metadata
                }
                documents.append(Document(page_content=chunk, metadata=doc_metadata))

        self.documents[doc_id] = {
            'content': content,
            'doc_type': doc_type,
            'metadata': metadata,
            'documents': documents,
            'added_at': datetime.now().isoformat(),
            'analysis': {}
        }

        logger.info(f"Documento {doc_id} añadido con {len(documents)} chunks")

    # Aliases por compatibilidad
    def load_proposal(self, proposal_id: str, content: str, metadata: Optional[Dict] = None):
        return self.add_document(proposal_id, content, doc_type='proposal', metadata=metadata)

    def add_proposal(self, proposal_id: str, content: str, metadata: Optional[Dict] = None):
        return self.add_document(proposal_id, content, doc_type='proposal', metadata=metadata)

    def setup_vector_database(self) -> bool:
        """Crea la base vectorial y evita duplicados con IDs estables."""
        if not self.embeddings_provider:
            logger.warning("Embeddings no disponibles, comparación limitada a análisis textual")
            return True

        if not self.documents:
            raise ValueError("No hay documentos cargados")

        # Recolectar todos los documentos
        all_documents: List[Document] = []
        ids: List[str] = []

        for doc_id, doc_data in self.documents.items():
            for d in doc_data['documents']:
                all_documents.append(d)
                raw = (f"{doc_id}|{d.metadata.get('chunk_id')}|{d.page_content}").encode("utf-8")
                ids.append(hashlib.sha1(raw).hexdigest())

        try:
            Path(self.vector_db_path).mkdir(parents=True, exist_ok=True)
            self.vector_db = Chroma(
                collection_name="comparison",
                persist_directory=str(self.vector_db_path),
                embedding_function=self.embeddings_provider
            )
            if all_documents:
                self.vector_db.add_documents(all_documents, ids=ids)
                # Try to persist if the method exists (older ChromaDB versions)
                try:
                    self.vector_db.persist()
                except AttributeError:
                    # Newer ChromaDB versions auto-persist
                    pass
            logger.info(f"Base de datos vectorial configurada con {len(all_documents)} documentos")
            return True
        except Exception as e:
            logger.error(f"Error configurando base de datos vectorial: {e}")
            return False

    def analyze_content_similarity(self, doc1_id: str, doc2_id: str) -> Dict[str, Any]:
        """Analiza similitud de contenido entre dos documentos."""
        if doc1_id not in self.documents or doc2_id not in self.documents:
            raise ValueError("Uno o ambos documentos no encontrados")

        content1 = self.documents[doc1_id]['content']
        content2 = self.documents[doc2_id]['content']

        similarity_analysis: Dict[str, Any] = {
            'comparison_type': 'content_similarity',
            'doc1_id': doc1_id,
            'doc2_id': doc2_id,
            'comparison_timestamp': datetime.now().isoformat(),
            'semantic_similarity': 0.0,
            'metrics': {}
        }

        # Jaccard simple
        words1 = set(re.findall(r'\b\w+\b', content1.lower()))
        words2 = set(re.findall(r'\b\w+\b', content2.lower()))
        common_words = words1.intersection(words2)
        all_words = words1.union(words2)
        jaccard_similarity = len(common_words) / len(all_words) if all_words else 0

        similarity_analysis['metrics']['jaccard_similarity'] = jaccard_similarity
        similarity_analysis['metrics']['common_words_count'] = len(common_words)
        similarity_analysis['metrics']['unique_words_doc1'] = len(words1 - words2)
        similarity_analysis['metrics']['unique_words_doc2'] = len(words2 - words1)
        similarity_analysis['semantic_similarity'] = jaccard_similarity  # fallback

        # Semántica si hay vector DB
        if self.vector_db:
            try:
                results1 = self.vector_db.similarity_search(
                    content1[:500], k=3, filter={'doc_id': doc1_id}
                )
                results2 = self.vector_db.similarity_search(
                    content2[:500], k=3, filter={'doc_id': doc2_id}
                )

                content1_chunks = ' '.join([doc.page_content for doc in results1])
                content2_chunks = ' '.join([doc.page_content for doc in results2])

                semantic_words1 = set(re.findall(r'\b[a-záéíóúñ]{4,}\b', content1_chunks.lower()))
                semantic_words2 = set(re.findall(r'\b[a-záéíóúñ]{4,}\b', content2_chunks.lower()))

                semantic_common = semantic_words1.intersection(semantic_words2)
                semantic_all = semantic_words1.union(semantic_words2)
                semantic_similarity = len(semantic_common) / len(semantic_all) if semantic_all else 0
                similarity_analysis['metrics']['semantic_similarity'] = semantic_similarity
            except Exception as e:
                logger.warning(f"Error en análisis semántico: {e}")

        # Score combinado (0–100)
        if 'semantic_similarity' in similarity_analysis['metrics']:
            combined_score = (jaccard_similarity * 0.3 +
                              similarity_analysis['metrics']['semantic_similarity'] * 0.7) * 100
        else:
            combined_score = jaccard_similarity * 100

        similarity_analysis['overall_similarity_score'] = round(combined_score, 2)
        return similarity_analysis

    def analyze_structural_compliance(self, doc1_id: str, doc2_id: str,
                                      required_sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """Compara cumplimiento estructural entre documentos."""
        if not required_sections:
            required_sections = [
                r'(resumen\s+ejecutivo|executive\s+summary)',
                r'(objeto|prop[óo]sito|purpose)',
                r'(metodolog[íi]a|methodology)',
                r'(cronograma|timeline|schedule)',
                r'(presupuesto|budget|cost)',
                r'(equipo|team|personal)',
                r'(experiencia|experience)',
                r'(conclusiones|conclusions?)'
            ]

        structural_analysis: Dict[str, Any] = {
            'comparison_type': 'structural_compliance',
            'doc1_id': doc1_id,
            'doc2_id': doc2_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'required_sections_count': len(required_sections),
            'doc1_analysis': {},
            'doc2_analysis': {},
            'comparative_analysis': {}
        }

        for doc_id, analysis_key in [(doc1_id, 'doc1_analysis'), (doc2_id, 'doc2_analysis')]:
            content = self.documents[doc_id]['content']
            found_sections, missing_sections = [], []

            for section_pattern in required_sections:
                if re.search(section_pattern, content, re.IGNORECASE):
                    found_sections.append(section_pattern)
                else:
                    missing_sections.append(section_pattern)

            structural_analysis[analysis_key] = {
                'sections_found': len(found_sections),
                'sections_missing': len(missing_sections),
                'compliance_percentage': (len(found_sections) / len(required_sections)) * 100,
                'found_sections': found_sections,
                'missing_sections': missing_sections,
                'content_length': len(content),
                'estimated_completeness': min(100, len(content) / 5000 * 100)
            }

        doc1_compliance = structural_analysis['doc1_analysis']['compliance_percentage']
        doc2_compliance = structural_analysis['doc2_analysis']['compliance_percentage']

        structural_analysis['comparative_analysis'] = {
            'better_compliance': doc1_id if doc1_compliance > doc2_compliance else doc2_id,
            'compliance_difference': abs(doc1_compliance - doc2_compliance),
            'both_complete': doc1_compliance >= 80 and doc2_compliance >= 80,
            'relative_completeness': {
                doc1_id: structural_analysis['doc1_analysis']['estimated_completeness'],
                doc2_id: structural_analysis['doc2_analysis']['estimated_completeness']
            }
        }
        return structural_analysis

    def analyze_technical_completeness(self, doc1_id: str, doc2_id: str) -> Dict[str, Any]:
        """Compara completitud técnica entre documentos."""
        technical_keywords = [
            'especificaciones', 'requirements', 'arquitectura', 'tecnología',
            'implementación', 'integración', 'desarrollo', 'testing',
            'seguridad', 'performance', 'escalabilidad', 'mantenimiento',
            'certificaciones', 'estándares', 'protocolos', 'apis'
        ]

        technical_analysis: Dict[str, Any] = {
            'comparison_type': 'technical_completeness',
            'doc1_id': doc1_id,
            'doc2_id': doc2_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'technical_keywords': technical_keywords,
            'doc1_analysis': {},
            'doc2_analysis': {},
            'comparative_analysis': {}
        }

        for doc_id, analysis_key in [(doc1_id, 'doc1_analysis'), (doc2_id, 'doc2_analysis')]:
            content = self.documents[doc_id]['content'].lower()
            keyword_matches: Dict[str, int] = {}
            total_matches = 0

            for keyword in technical_keywords:
                matches = len(re.findall(rf'\b{re.escape(keyword)}\b', content, re.IGNORECASE))
                keyword_matches[keyword] = matches
                total_matches += matches

            technical_patterns = [
                r'\d+\s*(gb|mb|ghz|mhz)',
                r'iso\s*\d+',
                r'version\s*\d+\.\d+',
                r'(mysql|postgresql|oracle|mongodb)',
                r'(java|python|\.net|php|javascript)',
            ]

            pattern_matches = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in technical_patterns)

            technical_analysis[analysis_key] = {
                'keyword_matches': keyword_matches,
                'total_keyword_matches': total_matches,
                'pattern_matches': pattern_matches,
                'technical_density': total_matches / len(content.split()) * 1000 if content else 0,
                'technical_completeness_score': min(100, (total_matches + pattern_matches) * 2)
            }

        score1 = technical_analysis['doc1_analysis']['technical_completeness_score']
        score2 = technical_analysis['doc2_analysis']['technical_completeness_score']

        technical_analysis['comparative_analysis'] = {
            'more_technical': doc1_id if score1 > score2 else doc2_id,
            'technical_difference': abs(score1 - score2),
            'both_technically_complete': score1 >= 60 and score2 >= 60,
            'technical_coverage_comparison': {doc1_id: score1, doc2_id: score2}
        }

        # Claves útiles para tests/consumo
        technical_analysis['technical_completeness'] = {doc1_id: score1, doc2_id: score2}
        technical_analysis['completeness_comparison'] = technical_analysis['comparative_analysis']['technical_coverage_comparison']
        return technical_analysis

    def analyze_economic_competitiveness(self, doc1_id: str, doc2_id: str) -> Dict[str, Any]:
        """Compara competitividad económica entre propuestas."""
        economic_analysis: Dict[str, Any] = {
            'comparison_type': 'economic_competitiveness',
            'doc1_id': doc1_id,
            'doc2_id': doc2_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'doc1_analysis': {},
            'doc2_analysis': {},
            'comparative_analysis': {}
        }

        price_patterns = [
            r'\$\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'([0-9,]+(?:\.[0-9]{2})?)\s*pesos',
            r'valor\s+total[:\s]*([0-9,]+(?:\.[0-9]{2})?)',
            r'costo[:\s]*([0-9,]+(?:\.[0-9]{2})?)'
        ]
        economic_keywords = [
            'precio', 'costo', 'valor', 'presupuesto', 'financiamiento',
            'pago', 'facturación', 'anticipo', 'descuento', 'ahorro'
        ]

        for doc_id, analysis_key in [(doc1_id, 'doc1_analysis'), (doc2_id, 'doc2_analysis')]:
            content = self.documents[doc_id]['content']

            found_prices: List[float] = []
            for pattern in price_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    try:
                        found_prices.append(float(match.replace(',', '')))
                    except Exception:
                        continue

            economic_mentions = sum(len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE))
                                    for keyword in economic_keywords)

            value_terms = ['descuento', 'bonificación', 'valor agregado', 'beneficio adicional', 'incluye']
            value_mentions = sum(len(re.findall(rf'\b{term}\b', content, re.IGNORECASE)) for term in value_terms)

            economic_analysis[analysis_key] = {
                'prices_found': found_prices,
                'estimated_total_price': max(found_prices) if found_prices else None,
                'economic_mentions': economic_mentions,
                'value_added_mentions': value_mentions,
                'economic_completeness': min(100, economic_mentions * 5),
                'value_proposition_score': min(100, value_mentions * 10)
            }

        price1 = economic_analysis['doc1_analysis']['estimated_total_price']
        price2 = economic_analysis['doc2_analysis']['estimated_total_price']

        comparative_analysis: Dict[str, Any] = {}
        if price1 and price2:
            comparative_analysis['price_comparison'] = {
                'cheaper_option': doc1_id if price1 < price2 else doc2_id,
                'price_difference': abs(price1 - price2),
                'price_difference_percentage': abs(price1 - price2) / min(price1, price2) * 100,
                'both_prices_found': True
            }
        else:
            comparative_analysis['price_comparison'] = {
                'both_prices_found': False,
                'doc1_has_price': price1 is not None,
                'doc2_has_price': price2 is not None
            }

        econ1 = economic_analysis['doc1_analysis']['economic_completeness']
        econ2 = economic_analysis['doc2_analysis']['economic_completeness']
        comparative_analysis['economic_completeness_comparison'] = {
            'more_complete': doc1_id if econ1 > econ2 else doc2_id,
            'completeness_difference': abs(econ1 - econ2),
            doc1_id: econ1,
            doc2_id: econ2
        }

        economic_analysis['comparative_analysis'] = comparative_analysis
        economic_analysis['economic_competitiveness'] = {doc1_id: econ1, doc2_id: econ2}
        economic_analysis['cost_analysis'] = {doc1_id: price1 or 0, doc2_id: price2 or 0}
        return economic_analysis

    def extract_technical_scores(self, proposal_id: str) -> Dict[str, float]:
        """Extrae puntajes técnicos por subcriterio (modo licitación)."""
        if proposal_id not in self.documents:
            raise ValueError(f"Propuesta {proposal_id} no encontrada")

        content = self.documents[proposal_id]['content']
        technical_scores: Dict[str, float] = {}

        for subcriterion, info in self.COMPARISON_MODES['TENDER_EVALUATION']['TECHNICAL']['subcriteria'].items():
            keyword_matches = sum(
                len(re.findall(rf'\b{re.escape(keyword)}\b', content, re.IGNORECASE))
                for keyword in info['keywords']
            )

            semantic_relevance = 0
            if self.vector_db:
                try:
                    query = ' '.join(info['keywords'])
                    results = self.vector_db.similarity_search(query, k=5, filter={'doc_id': proposal_id})
                    semantic_relevance = len(results) * 10
                except Exception:
                    semantic_relevance = 0

            raw_score = (keyword_matches * 5) + (semantic_relevance * 0.1)
            technical_scores[subcriterion] = min(100, raw_score)

        return technical_scores

    def extract_economic_data(self, proposal_id: str) -> Dict[str, Any]:
        """Extrae datos económicos de una propuesta (modo licitación)."""
        if proposal_id not in self.documents:
            raise ValueError(f"Propuesta {proposal_id} no encontrada")

        content = self.documents[proposal_id]['content']
        metadata = self.documents[proposal_id]['metadata']

        economic_data: Dict[str, Any] = {
            'total_price': None,
            'currency': None,
            'payment_terms': [],
            'cost_breakdown': {},
            'value_added_services': []
        }

        price_patterns = [
            r'\$?\s*([0-9,]+(?:\.[0-9]{2})?)\s*(?:pesos|cop|usd|dollars?)',
            r'valor\s+total[:\s]*\$?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'precio[:\s]*\$?\s*([0-9,]+(?:\.[0-9]{2})?)'
        ]

        for pattern in price_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    price_str = matches[0].replace(',', '')
                    economic_data['total_price'] = float(price_str)
                    break
                except Exception:
                    continue

        if economic_data['total_price'] is None and 'price' in metadata:
            economic_data['total_price'] = metadata['price']

        payment_patterns = [
            r'(anticipo\s+del?\s+\d+%)',
            r'(pago\s+contra\s+entrega)',
            r'(\d+%\s+al?\s+inicio)',
            r'(\d+\s+cuotas?)'
        ]
        for pattern in payment_patterns:
            economic_data['payment_terms'].extend(re.findall(pattern, content, re.IGNORECASE))

        return economic_data

    def calculate_compliance_score(self, proposal_id: str,
                                   rfp_requirements: Optional[List[str]] = None) -> Dict[str, float]:
        """Calcula puntajes de cumplimiento (modo licitación)."""
        if proposal_id not in self.documents:
            raise ValueError(f"Propuesta {proposal_id} no encontrada")

        content = self.documents[proposal_id]['content']
        compliance_scores: Dict[str, float] = {}

        required_sections = [
            'propuesta técnica', 'propuesta económica', 'experiencia',
            'certificaciones', 'cronograma', 'equipo de trabajo'
        ]
        found_sections = sum(
            1 for section in required_sections
            if re.search(rf'\b{re.escape(section)}\b', content, re.IGNORECASE)
        )
        compliance_scores['document_completeness'] = (found_sections / len(required_sections)) * 100

        legal_keywords = ['cumplimiento', 'normatividad', 'regulación', 'ley', 'decreto']
        legal_mentions = sum(len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE)) for keyword in legal_keywords)
        compliance_scores['legal_compliance'] = min(100, legal_mentions * 10)

        deadline_keywords = ['plazo', 'cronograma', 'entrega', 'fecha']
        deadline_mentions = sum(len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE)) for keyword in deadline_keywords)
        compliance_scores['deadlines_compliance'] = min(100, deadline_mentions * 15)

        return compliance_scores

    def semantic_similarity_analysis(self, proposal1_id: str, proposal2_id: str,
                                     query: str = "propuesta técnica") -> Dict[str, Any]:
        """Analiza similaridad semántica entre dos propuestas enfocada por query."""
        if not self.vector_db:
            return {"error": "Base de datos vectorial no disponible"}

        try:
            results1 = self.vector_db.similarity_search(query, k=5, filter={'doc_id': proposal1_id})
            results2 = self.vector_db.similarity_search(query, k=5, filter={'doc_id': proposal2_id})

            content1 = ' '.join([doc.page_content for doc in results1])
            content2 = ' '.join([doc.page_content for doc in results2])

            keywords1 = set(re.findall(r'\b[a-záéíóúñ]{4,}\b', content1.lower()))
            keywords2 = set(re.findall(r'\b[a-záéíóúñ]{4,}\b', content2.lower()))

            common_keywords = keywords1.intersection(keywords2)
            unique1 = keywords1 - keywords2
            unique2 = keywords2 - keywords1

            return {
                'query': query,
                'proposal1_relevant_docs': len(results1),
                'proposal2_relevant_docs': len(results2),
                'common_themes': list(common_keywords)[:10],
                'unique_to_proposal1': list(unique1)[:10],
                'unique_to_proposal2': list(unique2)[:10],
                'similarity_percentage': (len(common_keywords) / max(len(keywords1), len(keywords2)) * 100
                                          if (keywords1 or keywords2) else 0)
            }
        except Exception as e:
            logger.error(f"Error en análisis de similaridad: {e}")
            return {"error": str(e)}

    def comprehensive_comparison(self, doc1_id: str, doc2_id: str,
                                 mode: str = "GENERAL",
                                 weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Comparación integral entre dos documentos."""
        if doc1_id not in self.documents or doc2_id not in self.documents:
            raise ValueError("Uno o ambos documentos no encontrados")
        if mode not in self.COMPARISON_MODES:
            raise ValueError(f"Modo de comparación no válido: {mode}")

        if not weights:
            weights = {dim: info['weight'] for dim, info in self.COMPARISON_MODES[mode].items()}

        logger.info(f"Iniciando comparación comprehensiva entre {doc1_id} y {doc2_id} en modo {mode}")

        comprehensive_comparison: Dict[str, Any] = {
            'comparison_id': f"{doc1_id}_vs_{doc2_id}_{int(datetime.now().timestamp())}",
            'doc1_id': doc1_id,
            'doc2_id': doc2_id,
            'comparison_mode': mode,
            'comparison_timestamp': datetime.now().isoformat(),
            'weights_used': weights,
            'dimension_analyses': {},
            'overall_scores': {},
            'winner': None,
            'summary': {},
            'recommendations': []
        }

        total_score_doc1 = 0.0
        total_score_doc2 = 0.0

        if mode == "GENERAL":
            try:
                content_analysis = self.analyze_content_similarity(doc1_id, doc2_id)
                comprehensive_comparison['dimension_analyses']['content_similarity'] = content_analysis
                similarity_score = content_analysis['overall_similarity_score']
                doc1_content_score = similarity_score
                doc2_content_score = 100 - similarity_score
                total_score_doc1 += doc1_content_score * weights.get('CONTENT_SIMILARITY', 0.25)
                total_score_doc2 += doc2_content_score * weights.get('CONTENT_SIMILARITY', 0.25)
            except Exception as e:
                logger.error(f"Error en análisis de similitud de contenido: {e}")

            try:
                structural_analysis = self.analyze_structural_compliance(doc1_id, doc2_id)
                comprehensive_comparison['dimension_analyses']['structural_compliance'] = structural_analysis
                struct1 = structural_analysis['doc1_analysis']['compliance_percentage']
                struct2 = structural_analysis['doc2_analysis']['compliance_percentage']
                total_score_doc1 += struct1 * weights.get('STRUCTURAL_COMPLIANCE', 0.25)
                total_score_doc2 += struct2 * weights.get('STRUCTURAL_COMPLIANCE', 0.25)
            except Exception as e:
                logger.error(f"Error en análisis estructural: {e}")

            try:
                technical_analysis = self.analyze_technical_completeness(doc1_id, doc2_id)
                comprehensive_comparison['dimension_analyses']['technical_completeness'] = technical_analysis
                tech1 = technical_analysis['doc1_analysis']['technical_completeness_score']
                tech2 = technical_analysis['doc2_analysis']['technical_completeness_score']
                total_score_doc1 += tech1 * weights.get('TECHNICAL_COMPLETENESS', 0.25)
                total_score_doc2 += tech2 * weights.get('TECHNICAL_COMPLETENESS', 0.25)
            except Exception as e:
                logger.error(f"Error en análisis técnico: {e}")

            try:
                economic_analysis = self.analyze_economic_competitiveness(doc1_id, doc2_id)
                comprehensive_comparison['dimension_analyses']['economic_competitiveness'] = economic_analysis
                econ1 = economic_analysis['doc1_analysis']['economic_completeness']
                econ2 = economic_analysis['doc2_analysis']['economic_completeness']
                total_score_doc1 += econ1 * weights.get('ECONOMIC_COMPETITIVENESS', 0.25)
                total_score_doc2 += econ2 * weights.get('ECONOMIC_COMPETITIVENESS', 0.25)
            except Exception as e:
                logger.error(f"Error en análisis económico: {e}")

        comprehensive_comparison['overall_scores'] = {
            doc1_id: round(total_score_doc1, 2),
            doc2_id: round(total_score_doc2, 2)
        }

        if total_score_doc1 > total_score_doc2:
            comprehensive_comparison['winner'] = doc1_id
            score_difference = total_score_doc1 - total_score_doc2
        else:
            comprehensive_comparison['winner'] = doc2_id
            score_difference = total_score_doc2 - total_score_doc1

        comprehensive_comparison['summary'] = {
            'winner': comprehensive_comparison['winner'],
            'score_difference': round(score_difference, 2),
            'close_competition': score_difference < 10,
            'decisive_winner': score_difference > 20,
            'analysis_completeness': len(comprehensive_comparison['dimension_analyses'])
        }

        comprehensive_comparison['recommendations'] = self._generate_comparison_recommendations(
            comprehensive_comparison
        )

        self.comparison_results[comprehensive_comparison['comparison_id']] = comprehensive_comparison
        logger.info(f"Comparación completada. Ganador: {comprehensive_comparison['winner']}")
        return comprehensive_comparison

    def compare_multiple_documents(self, doc_paths: List[Path],
                                   comparison_type: str = "comprehensive",
                                   classification_contexts: Dict[str, Dict] = None,
                                   validation_contexts: Dict[str, Dict] = None) -> Dict[str, Any]:
        """Enhanced multiple document comparison using DSPy intelligence."""
        if len(doc_paths) < 2:
            raise ValueError("Se necesitan al menos 2 documentos para comparar")

        logger.info(f"Comparando {len(doc_paths)} documentos con DSPy: {[p.name for p in doc_paths]}")
        
        if not self.dspy_module:
            self._initialize_dspy_module()

        multi_comparison: Dict[str, Any] = {
            'comparison_id': f"dspy_multi_{int(datetime.now().timestamp())}",
            'document_paths': [str(p) for p in doc_paths],
            'total_documents': len(doc_paths),
            'comparison_type': comparison_type,
            'comparison_timestamp': datetime.now().isoformat(),
            'comparison_method': "DSPy Enhanced Multi-Document Analysis",
            'individual_analyses': {},
            'pairwise_comparisons': {},
            'ranking': [],
            'cluster_analysis': {},
            'summary_statistics': {}
        }

        # Step 1: Analyze each document individually with context
        document_analyses = {}
        for i, doc_path in enumerate(doc_paths):
            doc_name = doc_path.name
            try:
                classification_ctx = classification_contexts.get(doc_name) if classification_contexts else None
                validation_ctx = validation_contexts.get(doc_name) if validation_contexts else None
                
                analysis = self.analyze_document(
                    doc_path, doc_name, 
                    classification_ctx, validation_ctx
                )
                document_analyses[doc_name] = analysis
                multi_comparison['individual_analyses'][doc_name] = analysis
                logger.info(f"Analyzed document {doc_name} with DSPy intelligence")
            except Exception as e:
                logger.error(f"Error analyzing document {doc_name}: {e}")
                document_analyses[doc_name] = {"error": str(e)}
                multi_comparison['individual_analyses'][doc_name] = {"error": str(e)}

        # Step 2: Pairwise comparisons using DSPy
        comparison_scores: Dict[str, List[float]] = defaultdict(list)
        
        for i, doc1_path in enumerate(doc_paths):
            for j, doc2_path in enumerate(doc_paths):
                if i < j:
                    doc1_name = doc1_path.name
                    doc2_name = doc2_path.name
                    
                    try:
                        classification_ctx1 = classification_contexts.get(doc1_name) if classification_contexts else None
                        validation_ctx1 = validation_contexts.get(doc1_name) if validation_contexts else None
                        classification_ctx2 = classification_contexts.get(doc2_name) if classification_contexts else None
                        validation_ctx2 = validation_contexts.get(doc2_name) if validation_contexts else None
                        
                        comparison = self.compare_documents(
                            doc1_path, doc2_path, comparison_type,
                            classification_ctx1, validation_ctx1
                        )
                        
                        key = f"{doc1_name}_vs_{doc2_name}"
                        multi_comparison['pairwise_comparisons'][key] = comparison
                        
                        # Extract scores for ranking
                        if 'enhanced_scoring' in comparison:
                            scoring = comparison['enhanced_scoring']
                            if 'overall' in scoring:
                                doc1_score = scoring['overall'].get('document1_total', 0)
                                doc2_score = scoring['overall'].get('document2_total', 0)
                                comparison_scores[doc1_name].append(doc1_score)
                                comparison_scores[doc2_name].append(doc2_score)
                        
                        logger.info(f"Compared {doc1_name} vs {doc2_name} with DSPy")
                    except Exception as e:
                        logger.error(f"Error comparing {doc1_name} vs {doc2_name}: {e}")

        # Step 3: Generate ranking based on DSPy comparisons
        if comparison_scores:
            avg_scores: List[tuple] = []
            for doc_path in doc_paths:
                doc_name = doc_path.name
                if comparison_scores.get(doc_name):
                    avg_score = sum(comparison_scores[doc_name]) / len(comparison_scores[doc_name])
                    avg_scores.append((doc_name, avg_score))
                else:
                    avg_scores.append((doc_name, 0.0))

            avg_scores.sort(key=lambda x: x[1], reverse=True)
            multi_comparison['ranking'] = [
                {
                    'rank': i + 1, 
                    'document_name': doc_name, 
                    'average_score': round(score, 2),
                    'analysis_quality': document_analyses.get(doc_name, {}).get('dspy_analysis', {}),
                    'risk_profile': document_analyses.get(doc_name, {}).get('risk_analysis', {}),
                    'compliance_status': document_analyses.get(doc_name, {}).get('compliance_validation', {})
                }
                for i, (doc_name, score) in enumerate(avg_scores)
            ]

        # Step 4: Enhanced cluster analysis using DSPy intelligence
        if len(doc_paths) >= 3:
            multi_comparison['cluster_analysis'] = self._analyze_document_clusters_dspy(
                document_analyses
            )

        # Step 5: Generate summary statistics
        multi_comparison['summary_statistics'] = self._calculate_dspy_multi_comparison_stats(
            multi_comparison
        )

        logger.info(f"DSPy multi-document comparison completed. Top document: {multi_comparison['ranking'][0]['document_name'] if multi_comparison['ranking'] else 'None'}")
        return multi_comparison

    def compare_proposals(self, rfp_requirements: Optional[List[str]] = None) -> Dict[str, Any]:
        """Compara todas las propuestas cargadas (modo licitación)."""
        proposal_docs = {doc_id: doc_data for doc_id, doc_data in self.documents.items()
                         if doc_data['doc_type'] == 'proposal'}

        if len(proposal_docs) < 2:
            raise ValueError("Se necesitan al menos 2 propuestas para comparar")

        logger.info(f"Comparando {len(proposal_docs)} propuestas")

        comparison_results: Dict[str, Any] = {
            'comparison_timestamp': datetime.now().isoformat(),
            'total_proposals': len(proposal_docs),
            'proposals': {},
            'ranking': [],
            'summary_statistics': {}
        }

        for proposal_id in proposal_docs.keys():
            logger.info(f"Analizando propuesta {proposal_id}")
            try:
                technical_scores = self.extract_technical_scores(proposal_id)
                economic_data = self.extract_economic_data(proposal_id)
                compliance_scores = self.calculate_compliance_score(proposal_id, rfp_requirements)

                technical_weighted = sum(
                    score * self.COMPARISON_MODES['TENDER_EVALUATION']['TECHNICAL']['subcriteria'][sub]['weight']
                    for sub, score in technical_scores.items()
                )
                compliance_weighted = sum(
                    score * self.COMPARISON_MODES['TENDER_EVALUATION']['COMPLIANCE']['subcriteria'][sub]['weight']
                    for sub, score in compliance_scores.items()
                )

                economic_score = 50  # neutral
                if economic_data['total_price']:
                    all_prices = [self.extract_economic_data(pid).get('total_price', 0) for pid in proposal_docs.keys()]
                    valid_prices = [p for p in all_prices if p and p > 0]
                    if valid_prices:
                        min_price, max_price = min(valid_prices), max(valid_prices)
                        if max_price > min_price:
                            economic_score = 100 - ((economic_data['total_price'] - min_price) / (max_price - min_price)) * 100
                        else:
                            economic_score = 100

                total_score = (
                    technical_weighted * self.COMPARISON_MODES['TENDER_EVALUATION']['TECHNICAL']['weight'] +
                    economic_score * self.COMPARISON_MODES['TENDER_EVALUATION']['ECONOMIC']['weight'] +
                    compliance_weighted * self.COMPARISON_MODES['TENDER_EVALUATION']['COMPLIANCE']['weight']
                )

                proposal_analysis = {
                    'proposal_id': proposal_id,
                    'metadata': self.documents[proposal_id]['metadata'],
                    'scores': {
                        'technical': technical_scores,
                        'technical_weighted': technical_weighted,
                        'economic': economic_score,
                        'economic_data': economic_data,
                        'compliance': compliance_scores,
                        'compliance_weighted': compliance_weighted,
                        'total_score': total_score
                    },
                    'strengths': self._identify_strengths(technical_scores, economic_score, compliance_scores),
                    'weaknesses': self._identify_weaknesses(technical_scores, economic_score, compliance_scores)
                }
                comparison_results['proposals'][proposal_id] = proposal_analysis

            except Exception as e:
                logger.error(f"Error analizando propuesta {proposal_id}: {e}")
                comparison_results['proposals'][proposal_id] = {'error': str(e), 'scores': {'total_score': 0}}

        valid = [(pid, data) for pid, data in comparison_results['proposals'].items() if 'error' not in data]
        ranking = sorted(valid, key=lambda x: x[1]['scores']['total_score'], reverse=True)
        comparison_results['ranking'] = [
            {
                'rank': i + 1,
                'proposal_id': pid,
                'total_score': data['scores']['total_score'],
                'company': data['metadata'].get('company', 'N/A'),
                'price': data['scores']['economic_data'].get('total_price', 'N/A')
            }
            for i, (pid, data) in enumerate(ranking)
        ]

        scores = [data['scores']['total_score'] for _, data in valid]
        if scores:
            comparison_results['summary_statistics'] = {
                'average_score': sum(scores) / len(scores),
                'highest_score': max(scores),
                'lowest_score': min(scores),
                'score_spread': max(scores) - min(scores),
                'winner': ranking[0][0] if ranking else None
            }

        # Nota: aquí self.comparison_results se usa como “último resultado de propuestas”
        self.comparison_results = comparison_results
        logger.info("Comparación de propuestas completada")
        return comparison_results

    def _identify_strengths(self, technical: Dict, economic: float, compliance: Dict) -> List[str]:
        strengths: List[str] = []
        strengths += [f"Excelente {k.replace('_', ' ')}" for k, v in technical.items() if v > 70]
        if economic > 80:
            strengths.append("Propuesta económica muy competitiva")
        strengths += [f"Alto cumplimiento en {k.replace('_', ' ')}" for k, v in compliance.items() if v > 80]
        return strengths[:5]

    def _identify_weaknesses(self, technical: Dict, economic: float, compliance: Dict) -> List[str]:
        weaknesses: List[str] = []
        weaknesses += [f"Deficiencia en {k.replace('_', ' ')}" for k, v in technical.items() if v < 40]
        if economic < 30:
            weaknesses.append("Propuesta económica poco competitiva")
        weaknesses += [f"Bajo cumplimiento en {k.replace('_', ' ')}" for k, v in compliance.items() if v < 50]
        return weaknesses[:5]

    def _generate_comparison_recommendations(self, comparison_result: Dict) -> List[str]:
        recommendations: List[str] = []
        winner = comparison_result.get('winner')
        score_diff = comparison_result.get('summary', {}).get('score_difference', 0)

        if winner:
            recommendations.append(f"Se recomienda el documento {winner} como superior")
        if score_diff < 5:
            recommendations.append("La diferencia es mínima, considerar criterios adicionales")
        elif score_diff > 30:
            recommendations.append("Diferencia decisiva en favor del ganador")

        dims = comparison_result.get('dimension_analyses', {})
        if 'structural_compliance' in dims:
            better = dims['structural_compliance']['comparative_analysis']['better_compliance']
            recommendations.append(f"Mejor cumplimiento estructural: {better}")
        if 'economic_competitiveness' in dims:
            econ = dims['economic_competitiveness']['comparative_analysis'].get('price_comparison', {})
            if econ.get('both_prices_found'):
                recommendations.append(f"Opción económicamente más competitiva: {econ['cheaper_option']}")
        return recommendations[:5]

    def _analyze_document_clusters(self, doc_ids: List[str]) -> Dict[str, Any]:
        """Análisis simple de clusters por similitud."""
        clusters: Dict[str, Any] = {'similar_documents': [], 'outliers': []}
        try:
            similarity_threshold = 70.0  # FIX: los puntajes son 0–100
            similar_pairs: List[tuple] = []

            for i, doc1_id in enumerate(doc_ids):
                for j, doc2_id in enumerate(doc_ids):
                    if i < j:
                        try:
                            similarity = self.analyze_content_similarity(doc1_id, doc2_id)
                            if similarity['overall_similarity_score'] >= similarity_threshold:
                                similar_pairs.append((doc1_id, doc2_id, similarity['overall_similarity_score']))
                        except Exception:
                            continue

            clusters['similar_pairs'] = similar_pairs
            clusters['similarity_threshold'] = similarity_threshold
        except Exception as e:
            logger.error(f"Error en análisis de clusters: {e}")
            clusters['error'] = str(e)
        return clusters

    def _calculate_multi_comparison_stats(self, multi_comparison: Dict) -> Dict[str, Any]:
        stats = {
            'total_documents': len(multi_comparison['document_ids']),
            'total_comparisons': len(multi_comparison['pairwise_comparisons']),
            'successful_comparisons': 0,
            'failed_comparisons': 0,
            'average_score_range': 0
        }
        for comparison in multi_comparison['pairwise_comparisons'].values():
            if 'error' not in comparison:
                stats['successful_comparisons'] += 1
            else:
                stats['failed_comparisons'] += 1

        if multi_comparison['ranking']:
            scores = [item['average_score'] for item in multi_comparison['ranking']]
            stats['average_score_range'] = (max(scores) - min(scores)) if scores else 0
        return stats

    def _analyze_document_clusters_dspy(self, document_analyses: Dict[str, Dict]) -> Dict[str, Any]:
        """Enhanced cluster analysis using DSPy intelligence."""
        try:
            if not self.dspy_module:
                self._initialize_dspy_module()
            
            clusters = {
                'similar_documents': [],
                'outliers': [],
                'thematic_groups': {},
                'risk_clusters': {},
                'compliance_clusters': {},
                'analysis_method': 'DSPy Enhanced Clustering'
            }
            
            # Group documents by similarity using DSPy analysis
            similarity_threshold = 0.7
            similar_pairs = []
            
            doc_names = list(document_analyses.keys())
            for i, doc1_name in enumerate(doc_names):
                for j, doc2_name in enumerate(doc_names):
                    if i < j:
                        try:
                            doc1_analysis = document_analyses[doc1_name]
                            doc2_analysis = document_analyses[doc2_name]
                            
                            # Calculate similarity based on DSPy analysis
                            similarity_score = self._calculate_dspy_similarity(doc1_analysis, doc2_analysis)
                            
                            if similarity_score > similarity_threshold:
                                similar_pairs.append({
                                    'document1': doc1_name,
                                    'document2': doc2_name,
                                    'similarity_score': similarity_score
                                })
                        except Exception as e:
                            logger.warning(f"Error calculating similarity between {doc1_name} and {doc2_name}: {e}")
            
            clusters['similar_pairs'] = similar_pairs
            clusters['similarity_threshold'] = similarity_threshold
            
            # Risk-based clustering
            risk_groups = {'LOW': [], 'MEDIUM': [], 'HIGH': []}
            for doc_name, analysis in document_analyses.items():
                if 'risk_analysis' in analysis and analysis['risk_analysis']:
                    risk_score = analysis['risk_analysis'].get('overall_risk_score', 0.5)
                    if risk_score < 0.3:
                        risk_groups['LOW'].append(doc_name)
                    elif risk_score < 0.7:
                        risk_groups['MEDIUM'].append(doc_name)
                    else:
                        risk_groups['HIGH'].append(doc_name)
            
            clusters['risk_clusters'] = risk_groups
            
            # Compliance-based clustering
            compliance_groups = {'COMPLIANT': [], 'PARTIAL': [], 'NON_COMPLIANT': []}
            for doc_name, analysis in document_analyses.items():
                if 'compliance_validation' in analysis and analysis['compliance_validation']:
                    compliance_score = analysis['compliance_validation'].get('compliance_score', 0.5)
                    if compliance_score > 0.8:
                        compliance_groups['COMPLIANT'].append(doc_name)
                    elif compliance_score > 0.5:
                        compliance_groups['PARTIAL'].append(doc_name)
                    else:
                        compliance_groups['NON_COMPLIANT'].append(doc_name)
            
            clusters['compliance_clusters'] = compliance_groups
            
            return clusters
        except Exception as e:
            logger.error(f"Error in DSPy cluster analysis: {e}")
            return {"error": str(e), "analysis_method": "DSPy Enhanced Clustering"}

    def _calculate_dspy_similarity(self, doc1_analysis: Dict, doc2_analysis: Dict) -> float:
        """Calculate similarity between two DSPy document analyses."""
        try:
            similarity_factors = []
            
            # DSPy analysis similarity
            if 'dspy_analysis' in doc1_analysis and 'dspy_analysis' in doc2_analysis:
                dspy1 = doc1_analysis['dspy_analysis']
                dspy2 = doc2_analysis['dspy_analysis']
                
                # Compare key points if available
                if hasattr(dspy1, 'key_points') and hasattr(dspy2, 'key_points'):
                    kp1_words = set(str(dspy1.key_points).lower().split())
                    kp2_words = set(str(dspy2.key_points).lower().split())
                    if kp1_words or kp2_words:
                        jaccard_sim = len(kp1_words.intersection(kp2_words)) / len(kp1_words.union(kp2_words))
                        similarity_factors.append(jaccard_sim)
                
                # Compare quality scores if available
                if hasattr(dspy1, 'quality_score') and hasattr(dspy2, 'quality_score'):
                    score1 = float(dspy1.quality_score) if dspy1.quality_score else 0.5
                    score2 = float(dspy2.quality_score) if dspy2.quality_score else 0.5
                    score_similarity = 1 - abs(score1 - score2)
                    similarity_factors.append(score_similarity)
            
            # Risk analysis similarity
            if 'risk_analysis' in doc1_analysis and 'risk_analysis' in doc2_analysis:
                risk1 = doc1_analysis['risk_analysis'].get('overall_risk_score', 0.5)
                risk2 = doc2_analysis['risk_analysis'].get('overall_risk_score', 0.5)
                risk_similarity = 1 - abs(risk1 - risk2)
                similarity_factors.append(risk_similarity)
            
            # Compliance similarity
            if 'compliance_validation' in doc1_analysis and 'compliance_validation' in doc2_analysis:
                comp1 = doc1_analysis['compliance_validation'].get('compliance_score', 0.5)
                comp2 = doc2_analysis['compliance_validation'].get('compliance_score', 0.5)
                comp_similarity = 1 - abs(comp1 - comp2)
                similarity_factors.append(comp_similarity)
            
            # Return average similarity if factors available, otherwise 0.5
            return sum(similarity_factors) / len(similarity_factors) if similarity_factors else 0.5
            
        except Exception as e:
            logger.warning(f"Error calculating DSPy similarity: {e}")
            return 0.5

    def _calculate_dspy_multi_comparison_stats(self, multi_comparison: Dict) -> Dict[str, Any]:
        """Calculate enhanced statistics for DSPy multi-document comparison."""
        stats = {
            'total_documents': multi_comparison['total_documents'],
            'total_comparisons': len(multi_comparison['pairwise_comparisons']),
            'successful_comparisons': 0,
            'failed_comparisons': 0,
            'average_score_range': 0,
            'analysis_method': 'DSPy Enhanced Statistics',
            'risk_statistics': {},
            'compliance_statistics': {},
            'quality_statistics': {}
        }
        
        # Count successful vs failed comparisons
        for comparison in multi_comparison['pairwise_comparisons'].values():
            if 'error' not in comparison:
                stats['successful_comparisons'] += 1
            else:
                stats['failed_comparisons'] += 1

        # Calculate score ranges
        if multi_comparison['ranking']:
            scores = [item['average_score'] for item in multi_comparison['ranking']]
            stats['average_score_range'] = (max(scores) - min(scores)) if scores else 0
        
        # Risk statistics
        risk_scores = []
        for doc_name, analysis in multi_comparison['individual_analyses'].items():
            if 'risk_analysis' in analysis and analysis['risk_analysis']:
                risk_score = analysis['risk_analysis'].get('overall_risk_score', 0.5)
                risk_scores.append(risk_score)
        
        if risk_scores:
            stats['risk_statistics'] = {
                'average_risk': sum(risk_scores) / len(risk_scores),
                'highest_risk': max(risk_scores),
                'lowest_risk': min(risk_scores),
                'risk_spread': max(risk_scores) - min(risk_scores)
            }
        
        # Compliance statistics
        compliance_scores = []
        for doc_name, analysis in multi_comparison['individual_analyses'].items():
            if 'compliance_validation' in analysis and analysis['compliance_validation']:
                comp_score = analysis['compliance_validation'].get('compliance_score', 0.5)
                compliance_scores.append(comp_score)
        
        if compliance_scores:
            stats['compliance_statistics'] = {
                'average_compliance': sum(compliance_scores) / len(compliance_scores),
                'highest_compliance': max(compliance_scores),
                'lowest_compliance': min(compliance_scores),
                'compliance_spread': max(compliance_scores) - min(compliance_scores)
            }
        
        return stats

    def generate_comparison_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Genera reporte detallado de comparación de propuestas (usa el último resultado de compare_proposals()).
        """
        if not self.comparison_results:
            raise ValueError("No hay resultados de comparación disponibles")

        enhanced_report = self.comparison_results.copy()

        if 'ranking' in enhanced_report and len(enhanced_report['ranking']) >= 2 and self.vector_db:
            top = enhanced_report['ranking'][:3]
            pairwise: List[Dict[str, Any]] = []
            for i in range(len(top)):
                for j in range(i + 1, len(top)):
                    p1 = top[i]['proposal_id']
                    p2 = top[j]['proposal_id']
                    similarity = self.semantic_similarity_analysis(p1, p2)
                    pairwise.append({'proposal1': p1, 'proposal2': p2, 'similarity_analysis': similarity})
            enhanced_report['pairwise_comparisons'] = pairwise

        enhanced_report['recommendations'] = self._generate_proposal_recommendations()

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_report, f, ensure_ascii=False, indent=2)
            logger.info(f"Reporte de comparación guardado en: {output_path}")

        return enhanced_report

    def _generate_proposal_recommendations(self) -> List[str]:
        recommendations: List[str] = []
        if not self.comparison_results or 'ranking' not in self.comparison_results:
            return recommendations

        ranking = self.comparison_results['ranking']
        if ranking:
            winner = ranking[0]
            recommendations.append(
                f"Se recomienda la propuesta {winner['proposal_id']} como ganadora con score {winner['total_score']:.1f}"
            )
        if len(ranking) > 1:
            diff = ranking[0]['total_score'] - ranking[1]['total_score']
            if diff < 10:
                recommendations.append(f"La diferencia con el segundo lugar es mínima ({diff:.1f} pts). Considerar negociación.")

        proposals = self.comparison_results.get('proposals', {})
        technical_scores = {pid: data['scores']['technical_weighted'] for pid, data in proposals.items() if 'error' not in data}
        if technical_scores:
            best_tech = max(technical_scores.items(), key=lambda x: x[1])
            recommendations.append(f"Mejor propuesta técnica: {best_tech[0]} ({best_tech[1]:.1f} pts)")

        economic_scores = {pid: data['scores']['economic'] for pid, data in proposals.items() if 'error' not in data}
        if economic_scores:
            best_econ = max(economic_scores.items(), key=lambda x: x[1])
            recommendations.append(f"Mejor propuesta económica: {best_econ[0]} ({best_econ[1]:.1f} pts)")
        return recommendations

    def export_comparison_results(self, comparison_id: str, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Exporta un resultado puntual (de comprehensive_comparison) a JSON.
        """
        if comparison_id not in self.comparison_results:
            raise ValueError(f"Comparación {comparison_id} no encontrada")

        results = self.comparison_results[comparison_id]
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"Resultados exportados a: {output_path}")
        return results

    def clear_documents(self):
        """Limpia documentos y comparaciones almacenadas."""
        self.documents = {}
        self.comparison_results = {}
        self.cached_embeddings = {}
        logger.info("Todos los documentos y comparaciones han sido limpiados")

    def clear_proposals(self):
        """Alias de clear_documents (retrocompat)."""
        self.clear_documents()

    def get_comparison_summary(self, comparison_id: str) -> Dict[str, Any]:
        """Resumen ejecutivo de una comparación puntual."""
        if comparison_id not in self.comparison_results:
            raise ValueError(f"Comparación {comparison_id} no encontrada")
        c = self.comparison_results[comparison_id]
        return {
            'comparison_id': comparison_id,
            'documents_compared': [c.get('doc1_id'), c.get('doc2_id')],
            'winner': c.get('winner'),
            'score_difference': c.get('summary', {}).get('score_difference', 0),
            'analysis_completeness': len(c.get('dimension_analyses', {})),
            'key_recommendations': c.get('recommendations', [])[:3],
            'timestamp': c.get('comparison_timestamp')
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Estado actual del agente de comparación."""
        return {
            'embeddings_initialized': self.embeddings_provider is not None,
            'vector_db_initialized': self.vector_db is not None,
            'documents_loaded': len(self.documents),
            'comparison_results': len(self.comparison_results),
            'vector_db_path': str(self.vector_db_path),
            'supported_modes': list(self.COMPARISON_MODES.keys())
        }