import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import json

# DSPy imports
import dspy
from dspy import Signature, InputField, OutputField, Predict, Module

# Importar funciones del sistema de embeddings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.embedding import get_embeddings_provider
from langchain_chroma import Chroma
from langchain.schema import Document

# Importar database manager para ubicaciones estandarizadas
from ..db_manager import get_standard_db_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DSPy Signatures para análisis de riesgos
class RiskDetectionSignature(Signature):
    """Detectar y analizar riesgos en contenido de documentos de licitación.
    
    REGLAS CRÍTICAS para análisis de riesgos (documentos en español):
    - Si contiene 'tecnología no probada', 'obsolescencia técnica' → TECHNICAL_RISKS (HIGH)
    - Si contiene 'precio bajo', 'costos ocultos', 'inflación' → ECONOMIC_RISKS (HIGH)
    - Si contiene 'normatividad cambiante', 'regulación no clara' → LEGAL_RISKS (HIGH)
    - Si contiene 'recursos insuficientes', 'cronograma apretado' → OPERATIONAL_RISKS (MEDIUM)
    - Si contiene 'proveedor único', 'experiencia limitada' → SUPPLIER_RISKS (MEDIUM)
    
    Niveles: VERY_LOW (0-20), LOW (20-40), MEDIUM (40-60), HIGH (60-80), VERY_HIGH (80-100)
    """
    
    document_content: str = InputField(desc="Contenido del documento a analizar para riesgos")
    risk_category: str = InputField(desc="Categoría de riesgo específica a analizar")
    risk_indicators: str = InputField(desc="Indicadores de riesgo específicos para buscar")
    
    risk_score: int = OutputField(desc="Puntuación de riesgo entre 0-100 basada en indicadores encontrados")
    risk_level: str = OutputField(desc="Nivel de riesgo: VERY_LOW, LOW, MEDIUM, HIGH, o VERY_HIGH")
    detected_indicators: str = OutputField(desc="Lista de indicadores de riesgo específicos encontrados en el contenido")
    risk_context: str = OutputField(desc="Contexto y explicación detallada de los riesgos identificados")
    mitigation_suggestions: str = OutputField(desc="Sugerencias específicas de mitigación para los riesgos detectados")

class ComprehensiveRiskAnalysisSignature(Signature):
    """Análisis comprehensivo de riesgos para documentos completos de licitación"""
    
    full_document_content: str = InputField(desc="Contenido completo del documento")
    document_type: str = InputField(desc="Tipo de documento: RFP, Proposal, Contract")
    
    overall_risk_score: int = OutputField(desc="Puntuación general de riesgo (0-100)")
    critical_risks: str = OutputField(desc="Lista de riesgos críticos que requieren atención inmediata")
    risk_distribution: str = OutputField(desc="Distribución de riesgos por categorías")
    priority_recommendations: str = OutputField(desc="Recomendaciones prioritarias de mitigación")
    risk_summary: str = OutputField(desc="Resumen ejecutivo de la evaluación de riesgos")

class RiskComparisonSignature(Signature):
    """Comparar perfiles de riesgo entre múltiples documentos o propuestas"""
    
    document_risks: str = InputField(desc="Análisis de riesgos de múltiples documentos en formato JSON")
    comparison_focus: str = InputField(desc="Aspecto específico a comparar: overall, technical, economic, etc.")
    
    risk_ranking: str = OutputField(desc="Ranking de documentos por nivel de riesgo")
    comparative_analysis: str = OutputField(desc="Análisis comparativo detallado de riesgos")
    selection_recommendation: str = OutputField(desc="Recomendación de selección basada en análisis de riesgos")

class RiskAnalysisModule(Module):
    """Módulo DSPy para análisis de riesgos con integración ChromaDB"""
    
    def __init__(self, vector_db: Chroma, risk_taxonomy: Dict[str, Dict]):
        super().__init__()
        self.vector_db = vector_db
        self.risk_taxonomy = risk_taxonomy
        
        # Inicializar componentes DSPy
        self.detect_risks = Predict(RiskDetectionSignature)
        self.analyze_comprehensive = Predict(ComprehensiveRiskAnalysisSignature)
        self.compare_risks = Predict(RiskComparisonSignature)
        
    def forward(self, content: str, risk_category: str) -> Dict[str, Any]:
        """Procesar análisis de riesgo para una categoría específica"""
        
        # Obtener información de la taxonomía de riesgos
        category_info = self.risk_taxonomy.get(risk_category, {})
        risk_indicators = ", ".join(category_info.get('indicators', []))
        
        # Búsqueda semántica en ChromaDB para contexto adicional
        relevant_docs = []
        if self.vector_db:
            try:
                # Construir consulta específica para riesgos
                risk_query = f"riesgos {risk_category.lower().replace('_', ' ')} problemas peligros"
                semantic_results = self.vector_db.similarity_search_with_score(risk_query, k=5)
                
                for doc, score in semantic_results:
                    similarity_score = 1.0 - score if score <= 1.0 else max(0.0, 2.0 - score)
                    relevant_docs.append({
                        'content': doc.page_content[:300] + "...",
                        'similarity': similarity_score,
                        'metadata': doc.metadata
                    })
            except Exception as e:
                logger.warning(f"Error en búsqueda semántica para riesgos: {e}")
        
        # Análisis DSPy
        try:
            risk_analysis = self.detect_risks(
                document_content=content[:4000],  # Limitar contenido para DSPy
                risk_category=risk_category,
                risk_indicators=risk_indicators
            )
            
            # Extraer resultados
            risk_score = int(getattr(risk_analysis, 'risk_score', 50))
            risk_level = getattr(risk_analysis, 'risk_level', 'MEDIUM')
            detected_indicators = getattr(risk_analysis, 'detected_indicators', '')
            risk_context = getattr(risk_analysis, 'risk_context', '')
            mitigation_suggestions = getattr(risk_analysis, 'mitigation_suggestions', '')
            
            # Validar score dentro del rango
            risk_score = max(0, min(100, risk_score))
            
            return {
                'risk_score': risk_score,
                'risk_level': risk_level,
                'detected_indicators': detected_indicators.split(',') if detected_indicators else [],
                'risk_context': risk_context,
                'mitigation_suggestions': mitigation_suggestions.split(',') if mitigation_suggestions else [],
                'semantic_context': relevant_docs,
                'analysis_method': 'dspy_semantic'
            }
            
        except Exception as e:
            logger.error(f"Error en análisis DSPy para {risk_category}: {e}")
            # Fallback a análisis basado en reglas
            return self._fallback_rule_based_analysis(content, risk_category, category_info)
    
    def comprehensive_analysis(self, content: str, document_type: str) -> Dict[str, Any]:
        """Análisis comprehensivo de riesgos usando DSPy"""
        try:
            comprehensive_result = self.analyze_comprehensive(
                full_document_content=content[:5000],  # Limitar para DSPy
                document_type=document_type
            )
            
            return {
                'overall_risk_score': int(getattr(comprehensive_result, 'overall_risk_score', 50)),
                'critical_risks': getattr(comprehensive_result, 'critical_risks', '').split(','),
                'risk_distribution': getattr(comprehensive_result, 'risk_distribution', ''),
                'priority_recommendations': getattr(comprehensive_result, 'priority_recommendations', '').split(','),
                'risk_summary': getattr(comprehensive_result, 'risk_summary', ''),
                'analysis_method': 'dspy_comprehensive'
            }
            
        except Exception as e:
            logger.error(f"Error en análisis comprehensivo DSPy: {e}")
            return {
                'overall_risk_score': 50,
                'critical_risks': [],
                'risk_distribution': 'Análisis no disponible',
                'priority_recommendations': ['Implementar monitoreo adicional'],
                'risk_summary': 'Error en análisis comprehensivo',
                'analysis_method': 'fallback'
            }
    
    def compare_documents(self, document_risks: Dict[str, Any], focus: str = "overall") -> Dict[str, Any]:
        """Comparar riesgos entre documentos usando DSPy"""
        try:
            risks_json = json.dumps(document_risks, ensure_ascii=False)
            
            comparison_result = self.compare_risks(
                document_risks=risks_json[:4000],  # Limitar para DSPy
                comparison_focus=focus
            )
            
            return {
                'risk_ranking': getattr(comparison_result, 'risk_ranking', ''),
                'comparative_analysis': getattr(comparison_result, 'comparative_analysis', ''),
                'selection_recommendation': getattr(comparison_result, 'selection_recommendation', ''),
                'analysis_method': 'dspy_comparison'
            }
            
        except Exception as e:
            logger.error(f"Error en comparación DSPy: {e}")
            return {
                'risk_ranking': 'No disponible',
                'comparative_analysis': 'Error en comparación',
                'selection_recommendation': 'Realizar análisis manual',
                'analysis_method': 'fallback'
            }
    
    def _fallback_rule_based_analysis(self, content: str, risk_category: str, category_info: Dict) -> Dict[str, Any]:
        """Análisis de respaldo basado en reglas cuando DSPy falla"""
        indicators = category_info.get('indicators', [])
        detected_indicators = []
        risk_score = 0
        
        for indicator_pattern in indicators:
            matches = re.findall(indicator_pattern, content, re.IGNORECASE | re.UNICODE)
            if matches:
                detected_indicators.append(indicator_pattern)
                risk_score += len(matches) * 15  # Score base por indicador
        
        # Normalizar score
        risk_score = min(100, risk_score)
        
        # Determinar nivel de riesgo
        if risk_score < 20:
            risk_level = 'VERY_LOW'
        elif risk_score < 40:
            risk_level = 'LOW'
        elif risk_score < 60:
            risk_level = 'MEDIUM'
        elif risk_score < 80:
            risk_level = 'HIGH'
        else:
            risk_level = 'VERY_HIGH'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'detected_indicators': detected_indicators,
            'risk_context': f'Análisis basado en {len(detected_indicators)} indicadores detectados',
            'mitigation_suggestions': ['Implementar controles adicionales', 'Monitoreo regular'],
            'semantic_context': [],
            'analysis_method': 'rule_based_fallback'
        }

class RiskAnalyzerAgent:
    """
    Agente especializado en análisis de riesgos para procesos de licitación usando DSPy.
    Identifica y evalúa riesgos técnicos, económicos, legales y operacionales con inteligencia artificial.
    """
    
    # Taxonomía de riesgos para licitaciones (mantenida igual para compatibilidad)
    RISK_TAXONOMY = {
        'TECHNICAL_RISKS': {
            'description': 'Riesgos relacionados con aspectos técnicos',
            'weight': 0.3,
            'indicators': [
                r'tecnolog[íi]a\s+no\s+probada',
                r'especificaciones?\s+ambiguas?',
                r'compatibilidad\s+dudosa',
                r'falta\s+de\s+est[áa]ndares',
                r'obsolescencia\s+t[ée]cnica',
                r'dependencia\s+tecnol[óo]gica',
                r'integraci[óo]n\s+compleja',
                r'actualizaciones?\s+frecuentes?',
                r'complejidad\s+t[ée]cnica',
                r'riesgo\s+t[ée]cnico'
            ],
            'risk_factors': [
                'complexity', 'innovation_level', 'standards_compliance',
                'integration_challenges', 'scalability_issues'
            ]
        },
        'ECONOMIC_RISKS': {
            'description': 'Riesgos financieros y económicos',
            'weight': 0.25,
            'indicators': [
                r'precio\s+excesivamente\s+bajo',
                r'costos?\s+ocultos?',
                r'inflaci[óo]n\s+no\s+contemplada',
                r'variaci[óo]n\s+de\s+precios',
                r'moneda\s+extranjera',
                r'garant[íi]as?\s+insuficientes?',
                r'penalidades?\s+excesivas?',
                r'flujo\s+de\s+caja\s+negativo',
                r'riesgo\s+financiero',
                r'sobrecosto'
            ],
            'risk_factors': [
                'price_volatility', 'currency_risk', 'cash_flow',
                'guarantee_adequacy', 'cost_escalation'
            ]
        },
        'LEGAL_RISKS': {
            'description': 'Riesgos legales y regulatorios',
            'weight': 0.2,
            'indicators': [
                r'normatividad\s+cambiante',
                r'regulaci[óo]n\s+no\s+clara',
                r'conflicto\s+de\s+leyes',
                r'jurisdicci[óo]n\s+multiple',
                r'licencias?\s+pendientes?',
                r'propiedad\s+intelectual',
                r'responsabilidad\s+civil',
                r'incumplimiento\s+legal',
                r'riesgo\s+legal',
                r'marco\s+normativo'
            ],
            'risk_factors': [
                'regulatory_compliance', 'legal_clarity', 'ip_risks',
                'liability_exposure', 'permit_risks'
            ]
        },
        'OPERATIONAL_RISKS': {
            'description': 'Riesgos operacionales y de ejecución',
            'weight': 0.15,
            'indicators': [
                r'recursos?\s+insuficientes?',
                r'personal\s+no\s+calificado',
                r'cronograma\s+apretado',
                r'dependencias?\s+externas?',
                r'coordinaci[óo]n\s+compleja',
                r'comunicaci[óo]n\s+deficiente',
                r'control\s+de\s+calidad',
                r'gesti[óo]n\s+de\s+cambios',
                r'riesgo\s+operacional',
                r'problemas\s+operativos'
            ],
            'risk_factors': [
                'resource_adequacy', 'team_competency', 'schedule_feasibility',
                'external_dependencies', 'quality_control'
            ]
        },
        'SUPPLIER_RISKS': {
            'description': 'Riesgos relacionados con proveedores',
            'weight': 0.1,
            'indicators': [
                r'proveedor\s+[úu]nico',
                r'experiencia\s+limitada',
                r'estabilidad\s+financiera\s+dudosa',
                r'referencias?\s+negativas?',
                r'ubicaci[óo]n\s+remota',
                r'idioma\s+diferente',
                r'zona\s+de\s+conflicto',
                r'sanciones?\s+internacionales?',
                r'riesgo\s+proveedor',
                r'confiabilidad\s+dudosa'
            ],
            'risk_factors': [
                'supplier_reliability', 'financial_stability', 'experience_level',
                'geographical_risks', 'reputation_risks'
            ]
        }
    }
    
    # Niveles de riesgo (mantenidos igual)
    RISK_LEVELS = {
        'VERY_LOW': {'range': (0, 20), 'color': 'green', 'action': 'Monitoreo rutinario'},
        'LOW': {'range': (20, 40), 'color': 'lightgreen', 'action': 'Monitoreo regular'},
        'MEDIUM': {'range': (40, 60), 'color': 'yellow', 'action': 'Atención y mitigación'},
        'HIGH': {'range': (60, 80), 'color': 'orange', 'action': 'Mitigación urgente'},
        'VERY_HIGH': {'range': (80, 100), 'color': 'red', 'action': 'Intervención inmediata'}
    }
    
    def __init__(self, vector_db_path: Optional[Path] = None, llm_provider: str = "auto", llm_model: Optional[str] = None):
        """
        Inicializar el agente de análisis de riesgos con DSPy
        
        Args:
            vector_db_path: Ruta a la base de datos vectorial
            llm_provider: Proveedor LLM ("auto", "ollama", "openai")
            llm_model: Modelo específico a usar
        """
        # Usar ruta de base de datos estandarizada
        if vector_db_path:
            self.vector_db_path = vector_db_path
        else:
            self.vector_db_path = get_standard_db_path('risk_analysis', 'global')
            
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.embeddings_provider = None
        self.vector_db = None
        self.dspy_module = None
        self.risk_assessment = {}
        self.provider_info = {}
        
        logger.info(f"DSPy RiskAnalyzerAgent iniciado con DB: {self.vector_db_path}")
        
    def initialize_dspy_and_embeddings(self, provider="auto", model=None):
        """Inicializa DSPy con el modelo apropiado y los embeddings"""
        try:
            # Inicializar embeddings primero
            embeddings, used_provider, used_model = get_embeddings_provider(provider=provider, model=model)
            self.embeddings_provider = embeddings
            self.provider_info = {"provider": used_provider, "model": used_model}
            logger.info(f"Proveedor de embeddings inicializado: {used_provider} ({used_model})")
            
            # Inicializar DSPy basado en preferencia de proveedor
            if self.llm_provider == "auto":
                if used_provider == "ollama":
                    self._initialize_dspy_ollama()
                else:
                    self._initialize_dspy_openai()
            elif self.llm_provider == "ollama":
                self._initialize_dspy_ollama()
            elif self.llm_provider == "openai":
                self._initialize_dspy_openai()
            else:
                raise ValueError(f"Proveedor LLM no soportado: {self.llm_provider}")
                
            return True
        except Exception as e:
            logger.error(f"Error inicializando DSPy y embeddings: {e}")
            return False
    
    def _initialize_dspy_ollama(self):
        """Inicializar DSPy con Ollama LLM"""
        try:
            # Verificar modelos disponibles en Ollama
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code == 200:
                models = response.json()
                available_models = [model["name"] for model in models.get("models", [])]
                
                # Filtrar modelos de embeddings y elegir modelo de lenguaje apropiado
                language_models = [model for model in available_models 
                                 if not any(embed_keyword in model.lower() 
                                           for embed_keyword in ['embed', 'embedding'])]
                
                # Elegir modelo de lenguaje apropiado
                if self.llm_model and self.llm_model in language_models:
                    chosen_model = self.llm_model
                elif any("llama" in model.lower() for model in language_models):
                    chosen_model = next(model for model in language_models if "llama" in model.lower())
                elif language_models:
                    chosen_model = language_models[0]
                else:
                    # Si no hay modelos de lenguaje, descargar uno liviano
                    logger.info("No se encontraron modelos de lenguaje. Descargando llama3.2:1b...")
                    import subprocess
                    subprocess.run(["ollama", "pull", "llama3.2:1b"], check=True)
                    chosen_model = "llama3.2:1b"
                
                # Inicializar DSPy con nueva clase LM para Ollama
                from dspy import LM
                lm = LM(model=f"ollama/{chosen_model}", api_base="http://localhost:11434")
                dspy.settings.configure(lm=lm)
                
                logger.info(f"DSPy inicializado con Ollama: {chosen_model}")
            else:
                raise ConnectionError("No se puede conectar a Ollama")
                
        except Exception as e:
            logger.error(f"Error inicializando DSPy con Ollama: {e}")
            # Fallback a OpenAI si está disponible
            self._initialize_dspy_openai()
    
    def _initialize_dspy_openai(self):
        """Inicializar DSPy con OpenAI LLM"""
        try:
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY no configurado")
            
            from dspy import LM
            model_name = self.llm_model or "gpt-3.5-turbo"
            lm = LM(model=f"openai/{model_name}", max_tokens=3000)
            dspy.settings.configure(lm=lm)
            
            logger.info(f"DSPy inicializado con OpenAI: {model_name}")
            
        except Exception as e:
            logger.error(f"Error inicializando DSPy con OpenAI: {e}")
            raise
    
    def setup_vector_database(self, documents: List[Document]):
        """Configura la base de datos vectorial con documentos para análisis"""
        if not self.embeddings_provider:
            logger.warning("Embeddings no disponibles, usando análisis básico")
            return True
            
        try:
            self.vector_db = Chroma(
                collection_name="risk_analysis",
                persist_directory=str(self.vector_db_path),
                embedding_function=self.embeddings_provider
            )
            
            if documents:
                self.vector_db.add_documents(documents)
                # ChromaDB auto-persiste en versiones nuevas
                try:
                    self.vector_db.persist()
                except AttributeError:
                    pass  # persist() no existe en versiones nuevas
                    
                logger.info(f"Base de datos vectorial configurada con {len(documents)} documentos")
            
            return True
        except Exception as e:
            logger.error(f"Error configurando base de datos vectorial: {e}")
            return False
    
    def detect_risk_indicators(self, content: str, risk_category: str) -> Dict[str, Any]:
        """
        Detecta indicadores de riesgo usando DSPy y ChromaDB
        
        Args:
            content: Contenido del documento
            risk_category: Categoría de riesgo a analizar
            
        Returns:
            Diccionario con indicadores encontrados y análisis DSPy
        """
        
        if risk_category not in self.RISK_TAXONOMY:
            raise ValueError(f"Categoría de riesgo no válida: {risk_category}")
        
        # Inicializar módulo DSPy si es necesario
        if not self.dspy_module:
            if not self.initialize_dspy_and_embeddings():
                logger.warning("No se pudo inicializar DSPy, usando análisis basado en reglas")
                return self._detect_risk_indicators_fallback(content, risk_category)
            self.dspy_module = RiskAnalysisModule(self.vector_db, self.RISK_TAXONOMY)
        
        try:
            # Usar DSPy para análisis de riesgo
            analysis_result = self.dspy_module.forward(content, risk_category)
            
            category_info = self.RISK_TAXONOMY[risk_category]
            
            return {
                'category': risk_category,
                'description': category_info['description'],
                'risk_score': analysis_result['risk_score'],
                'risk_level': analysis_result['risk_level'],
                'detected_indicators': analysis_result['detected_indicators'],
                'risk_context': analysis_result['risk_context'],
                'mitigation_suggestions': analysis_result['mitigation_suggestions'],
                'semantic_context': analysis_result['semantic_context'],
                'weight': category_info['weight'],
                'analysis_method': analysis_result['analysis_method'],
                'total_mentions': len(analysis_result['detected_indicators'])
            }
            
        except Exception as e:
            logger.error(f"Error en análisis DSPy para {risk_category}: {e}")
            return self._detect_risk_indicators_fallback(content, risk_category)
    
    def _detect_risk_indicators_fallback(self, content: str, risk_category: str) -> Dict[str, Any]:
        """Análisis de respaldo cuando DSPy no está disponible"""
        category_info = self.RISK_TAXONOMY[risk_category]
        indicators = category_info['indicators']
        
        detected_indicators = []
        risk_mentions = []
        
        for indicator_pattern in indicators:
            matches = re.findall(indicator_pattern, content, re.IGNORECASE | re.UNICODE)
            if matches:
                detected_indicators.append(indicator_pattern)
                for match in matches:
                    context = self._extract_context(content, match, window=100)
                    risk_mentions.append({
                        'indicator': indicator_pattern,
                        'match': match,
                        'context': context
                    })
        
        # Calcular score de riesgo básico
        risk_score = min(100, len(detected_indicators) * 20 + len(risk_mentions) * 5)
        risk_level = self._get_risk_level(risk_score)
        
        return {
            'category': risk_category,
            'description': category_info['description'],
            'risk_score': risk_score,
            'risk_level': risk_level,
            'detected_indicators': detected_indicators,
            'indicators_detected': len(detected_indicators),  # Count field for test compatibility
            'risk_context': f'Análisis básico: {len(detected_indicators)} indicadores detectados',
            'mitigation_suggestions': ['Implementar controles adicionales', 'Monitoreo regular'],
            'semantic_context': [],
            'weight': category_info['weight'],
            'analysis_method': 'rule_based_fallback',
            'total_mentions': len(risk_mentions)
        }
    
    def analyze_document_risks(self, document_path: Optional[str] = None, 
                              content: Optional[str] = None,
                              document_type: str = "RFP",
                              analysis_level: str = "comprehensive") -> Dict[str, Any]:
        """
        Análisis completo de riesgos de un documento usando DSPy
        
        Args:
            document_path: Ruta al documento
            content: Contenido del documento
            document_type: Tipo de documento (RFP, Proposal, Contract)
            analysis_level: Nivel de análisis (basic, standard, comprehensive)
            
        Returns:
            Análisis completo de riesgos con DSPy
        """
        
        if not content and not document_path:
            raise ValueError("Debe proporcionar content o document_path")
        
        # Obtener contenido si se proporciona ruta
        if document_path and not content:
            try:
                from .document_extraction import DocumentExtractionAgent
                extractor = DocumentExtractionAgent(document_path)
                content = extractor.extract_text()
            except Exception as e:
                logger.error(f"Error extrayendo contenido: {e}")
                return {"error": f"No se pudo extraer contenido: {e}"}
        
        logger.info(f"Iniciando análisis de riesgos DSPy para documento tipo {document_type}")
        
        # Inicializar DSPy si es necesario
        if not self.dspy_module:
            if not self.initialize_dspy_and_embeddings():
                logger.warning("DSPy no disponible, usando análisis básico")
                return self._analyze_document_risks_fallback(content, document_type)
            self.dspy_module = RiskAnalysisModule(self.vector_db, self.RISK_TAXONOMY)
        
        risk_analysis = {
            'document_type': document_type,
            'analysis_timestamp': datetime.now().isoformat(),
            'content_length': len(content),
            'analysis_level': analysis_level,
            'dspy_enabled': True,
            'category_risks': {},
            'overall_assessment': {},
            'critical_risks': [],
            'mitigation_recommendations': [],
            'risk_matrix': {},
            'dspy_comprehensive_analysis': {}
        }
        
        total_weighted_risk = 0
        
        # Análisis por categorías usando DSPy
        for category in self.RISK_TAXONOMY.keys():
            try:
                category_analysis = self.detect_risk_indicators(content, category)
                
                # Asegurar que indicators_detected está presente como conteo
                if 'detected_indicators' in category_analysis:
                    indicators_count = len(category_analysis['detected_indicators'])
                    category_analysis['indicators_detected'] = indicators_count
                else:
                    category_analysis['indicators_detected'] = 0
                    
                risk_analysis['category_risks'][category] = category_analysis
                
                # Contribución al riesgo total
                weighted_risk = category_analysis['risk_score'] * category_analysis['weight']
                total_weighted_risk += weighted_risk
                
                # Identificar riesgos críticos (umbral reducido para DSPy)
                if category_analysis['risk_score'] > 60:  # Reducido de 70 a 60
                    risk_analysis['critical_risks'].append({
                        'category': category,
                        'score': category_analysis['risk_score'],
                        'level': category_analysis['risk_level'],
                        'indicators': len(category_analysis['detected_indicators']),
                        'context': category_analysis['risk_context']
                    })
                    
            except Exception as e:
                logger.error(f"Error analizando categoría {category}: {e}")
                risk_analysis['category_risks'][category] = {
                    'error': str(e),
                    'risk_score': 0,
                    'weight': self.RISK_TAXONOMY[category]['weight']
                }
        
        # Análisis comprehensivo usando DSPy
        if analysis_level in ['comprehensive', 'standard']:
            try:
                comprehensive_analysis = self.dspy_module.comprehensive_analysis(content, document_type)
                risk_analysis['dspy_comprehensive_analysis'] = comprehensive_analysis
                
                # Ajustar score general si DSPy sugiere algo diferente
                dspy_overall_score = comprehensive_analysis.get('overall_risk_score', total_weighted_risk)
                if abs(dspy_overall_score - total_weighted_risk) > 20:
                    # Promediar si hay gran diferencia
                    total_weighted_risk = (total_weighted_risk + dspy_overall_score) / 2
                    
            except Exception as e:
                logger.warning(f"Error en análisis comprehensivo DSPy: {e}")
        
        # Evaluación general
        overall_risk_score = total_weighted_risk
        risk_analysis['overall_assessment'] = {
            'total_risk_score': round(overall_risk_score, 2),
            'risk_level': self._get_risk_level(overall_risk_score),
            'risk_distribution': self._calculate_risk_distribution(risk_analysis['category_risks']),
            'assessment_summary': self._generate_risk_summary(overall_risk_score, risk_analysis['critical_risks']),
            'dspy_enhanced': True
        }
        
        # Generar recomendaciones mejoradas con DSPy
        risk_analysis['mitigation_recommendations'] = self._generate_mitigation_recommendations_dspy(
            risk_analysis['category_risks'], overall_risk_score
        )
        
        # Matriz de riesgos
        risk_analysis['risk_matrix'] = self._create_risk_matrix(risk_analysis['category_risks'])
        
        self.risk_assessment = risk_analysis
        logger.info(f"Análisis de riesgos DSPy completado. Score general: {overall_risk_score:.1f}")
        
        return risk_analysis
    
    def _analyze_document_risks_fallback(self, content: str, document_type: str) -> Dict[str, Any]:
        """Análisis de respaldo cuando DSPy no está disponible"""
        logger.warning("Usando análisis de riesgo básico sin DSPy")
        
        risk_analysis = {
            'document_type': document_type,
            'analysis_timestamp': datetime.now().isoformat(),
            'content_length': len(content),
            'dspy_enabled': False,
            'category_risks': {},
            'overall_assessment': {},
            'critical_risks': [],
            'mitigation_recommendations': []
        }
        
        total_weighted_risk = 0
        
        # Análisis básico por categorías
        for category in self.RISK_TAXONOMY.keys():
            try:
                category_analysis = self._detect_risk_indicators_fallback(content, category)
                risk_analysis['category_risks'][category] = category_analysis
                
                weighted_risk = category_analysis['risk_score'] * category_analysis['weight']
                total_weighted_risk += weighted_risk
                
                if category_analysis['risk_score'] > 70:
                    risk_analysis['critical_risks'].append({
                        'category': category,
                        'score': category_analysis['risk_score'],
                        'level': category_analysis['risk_level'],
                        'indicators': len(category_analysis['detected_indicators'])
                    })
                    
            except Exception as e:
                logger.error(f"Error en análisis básico {category}: {e}")
        
        # Evaluación general básica
        risk_analysis['overall_assessment'] = {
            'total_risk_score': round(total_weighted_risk, 2),
            'risk_level': self._get_risk_level(total_weighted_risk),
            'risk_distribution': self._calculate_risk_distribution(risk_analysis['category_risks']),
            'assessment_summary': f"Análisis básico sin DSPy. Score: {total_weighted_risk:.1f}%"
        }
        
        return risk_analysis
    
    def compare_risk_profiles(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compara perfiles de riesgo entre múltiples documentos usando DSPy
        
        Args:
            documents: Lista de documentos con 'id', 'content' o 'path', y 'type'
            
        Returns:
            Comparación de perfiles de riesgo mejorada con DSPy
        """
        
        if len(documents) < 2:
            raise ValueError("Se necesitan al menos 2 documentos para comparar")
        
        logger.info(f"Comparando perfiles de riesgo DSPy de {len(documents)} documentos")
        
        document_risks = {}
        
        # Analizar cada documento
        for doc in documents:
            doc_id = doc.get('id', f"doc_{len(document_risks)}")
            try:
                risk_analysis = self.analyze_document_risks(
                    document_path=doc.get('path'),
                    content=doc.get('content'),
                    document_type=doc.get('type', 'RFP')
                )
                document_risks[doc_id] = risk_analysis
            except Exception as e:
                logger.error(f"Error analizando documento {doc_id}: {e}")
                document_risks[doc_id] = {'error': str(e)}
        
        # Generar comparación básica
        comparison = {
            'comparison_timestamp': datetime.now().isoformat(),
            'documents_analyzed': len(documents),
            'successful_analyses': len([d for d in document_risks.values() if 'error' not in d]),
            'document_risks': document_risks,
            'risk_comparison': self._compare_risk_scores(document_risks),
            'category_comparison': self._compare_category_risks(document_risks),
            'recommendations': self._generate_comparative_recommendations(document_risks),
            'dspy_enabled': True
        }
        
        # Análisis DSPy si está disponible
        if self.dspy_module:
            try:
                dspy_comparison = self.dspy_module.compare_documents(document_risks, "overall")
                comparison['dspy_comparison_analysis'] = dspy_comparison
            except Exception as e:
                logger.warning(f"Error en comparación DSPy: {e}")
        
        return comparison
    
    def _generate_mitigation_recommendations_dspy(self, category_risks: Dict, overall_score: float) -> List[Dict]:
        """Genera recomendaciones de mitigación mejoradas con insights de DSPy"""
        recommendations = []
        
        # Recomendaciones por categoría con sensibilidad aumentada para DSPy
        for category, data in category_risks.items():
            if 'error' in data:
                continue
                
            risk_score = data.get('risk_score', 0)
            indicators_detected = data.get('total_mentions', 0)
            dspy_suggestions = data.get('mitigation_suggestions', [])
            
            # DSPy puede detectar riesgos más sutiles, usar umbral más bajo
            if risk_score > 25 or indicators_detected > 0:
                category_name = category.replace('_', ' ').title()
                
                # Determinar prioridad
                if risk_score > 65 or indicators_detected > 3:
                    priority = 'HIGH'
                    estimated_impact = 'HIGH'
                elif risk_score > 45 or indicators_detected > 1:
                    priority = 'MEDIUM'
                    estimated_impact = 'MEDIUM'
                else:
                    priority = 'LOW'
                    estimated_impact = 'LOW'
                
                # Usar sugerencias DSPy si están disponibles
                if dspy_suggestions and isinstance(dspy_suggestions, list) and len(dspy_suggestions) > 0:
                    main_recommendation = dspy_suggestions[0]
                else:
                    main_recommendation = self._get_category_mitigation(category, risk_score)
                
                recommendation = {
                    'category': category,
                    'priority': priority,
                    'risk_score': risk_score,
                    'indicators_count': indicators_detected,
                    'recommendation': main_recommendation,
                    'estimated_impact': estimated_impact,
                    'dspy_enhanced': len(dspy_suggestions) > 0,
                    'additional_suggestions': dspy_suggestions[1:3] if len(dspy_suggestions) > 1 else []
                }
                recommendations.append(recommendation)
        
        # Recomendaciones generales ajustadas para DSPy
        if overall_score > 75:
            recommendations.insert(0, {
                'category': 'GENERAL',
                'priority': 'CRITICAL',
                'risk_score': overall_score,
                'recommendation': 'Considerar rechazar la propuesta o requerir garantías adicionales significativas',
                'estimated_impact': 'VERY_HIGH',
                'dspy_enhanced': True
            })
        elif overall_score > 55:
            recommendations.insert(0, {
                'category': 'GENERAL',
                'priority': 'HIGH',
                'risk_score': overall_score,
                'recommendation': 'Implementar plan de gestión de riesgos robusto antes de la ejecución',
                'estimated_impact': 'HIGH',
                'dspy_enhanced': True
            })
        elif overall_score > 30:
            recommendations.insert(0, {
                'category': 'GENERAL',
                'priority': 'MEDIUM',
                'risk_score': overall_score,
                'recommendation': 'Implementar monitoreo adicional y controles básicos de riesgo',
                'estimated_impact': 'MEDIUM',
                'dspy_enhanced': True
            })
        
        return recommendations[:12]  # Máximo 12 recomendaciones
    
    # Métodos de utilidad (mantenidos del original)
    def _extract_context(self, content: str, match: str, window: int = 100) -> str:
        """Extrae contexto alrededor de una coincidencia"""
        try:
            start_idx = content.lower().find(match.lower())
            if start_idx == -1:
                return match
            
            context_start = max(0, start_idx - window)
            context_end = min(len(content), start_idx + len(match) + window)
            
            context = content[context_start:context_end]
            return f"...{context}..." if context_start > 0 or context_end < len(content) else context
        except:
            return match
    
    def _get_risk_level(self, score: float) -> str:
        """Determina el nivel de riesgo basado en el score"""
        for level, info in self.RISK_LEVELS.items():
            if info['range'][0] <= score < info['range'][1]:
                return level
        return 'VERY_HIGH' if score >= 80 else 'VERY_LOW'
    
    def _calculate_risk_distribution(self, category_risks: Dict) -> Dict[str, float]:
        """Calcula la distribución de riesgos por categoría"""
        total_weighted = sum(
            data.get('risk_score', 0) * data.get('weight', 0)
            for data in category_risks.values()
            if 'error' not in data
        )
        
        distribution = {}
        for category, data in category_risks.items():
            if 'error' not in data:
                contribution = (data.get('risk_score', 0) * data.get('weight', 0)) / total_weighted * 100 if total_weighted > 0 else 0
                distribution[category] = round(contribution, 2)
        
        return distribution
    
    def _generate_risk_summary(self, overall_score: float, critical_risks: List[Dict]) -> str:
        """Genera un resumen del análisis de riesgos"""
        risk_level = self._get_risk_level(overall_score)
        
        if risk_level == 'VERY_LOW':
            summary = f"Riesgo muy bajo ({overall_score:.1f}%). Proyecto con riesgo mínimo."
        elif risk_level == 'LOW':
            summary = f"Riesgo bajo ({overall_score:.1f}%). Proyecto viable con monitoreo estándar."
        elif risk_level == 'MEDIUM':
            summary = f"Riesgo moderado ({overall_score:.1f}%). Requiere atención y planificación de mitigación."
        elif risk_level == 'HIGH':
            summary = f"Riesgo alto ({overall_score:.1f}%). Requiere estrategias de mitigación antes de proceder."
        else:
            summary = f"Riesgo muy alto ({overall_score:.1f}%). Proyecto altamente riesgoso, considerar rechazo."
        
        if critical_risks:
            summary += f" Se identificaron {len(critical_risks)} riesgos críticos que requieren atención inmediata."
        
        return summary
    
    def _get_category_mitigation(self, category: str, risk_score: float) -> str:
        """Obtiene recomendaciones de mitigación específicas por categoría"""
        mitigations = {
            'TECHNICAL_RISKS': [
                'Requerir pruebas de concepto y prototipos',
                'Exigir certificaciones técnicas adicionales',
                'Implementar revisiones técnicas por fases',
                'Definir criterios de aceptación más estrictos'
            ],
            'ECONOMIC_RISKS': [
                'Solicitar garantías financieras adicionales',
                'Implementar cláusulas de ajuste de precios',
                'Requerir seguro de cumplimiento extendido',
                'Establecer hitos de pago más frecuentes'
            ],
            'LEGAL_RISKS': [
                'Revisar marco legal con especialistas',
                'Incluir cláusulas de cambio regulatorio',
                'Definir jurisdicción y ley aplicable claramente',
                'Obtener asesoría legal especializada'
            ],
            'OPERATIONAL_RISKS': [
                'Implementar plan de gestión de calidad robusto',
                'Definir puntos de control más frecuentes',
                'Requerir plan de contingencia detallado',
                'Establecer métricas de desempeño claras'
            ],
            'SUPPLIER_RISKS': [
                'Realizar due diligence exhaustivo del proveedor',
                'Requerir referencias comerciales verificables',
                'Implementar monitoreo continuo del proveedor',
                'Definir proveedores alternativos'
            ]
        }
        
        category_mitigations = mitigations.get(category, ['Implementar controles adicionales de monitoreo'])
        
        if risk_score > 80:
            return f"{category_mitigations[0]}. Considerar alternativas debido al alto riesgo."
        elif risk_score > 60:
            return category_mitigations[0]
        else:
            return category_mitigations[-1] if len(category_mitigations) > 1 else category_mitigations[0]
    
    def _create_risk_matrix(self, category_risks: Dict) -> Dict[str, Any]:
        """Crea una matriz de riesgos"""
        matrix = {'low_impact': [], 'medium_impact': [], 'high_impact': []}
        
        for category, data in category_risks.items():
            if 'error' in data:
                continue
                
            risk_score = data.get('risk_score', 0)
            
            risk_item = {
                'category': category.replace('_', ' ').title(),
                'score': risk_score,
                'level': data.get('risk_level', 'UNKNOWN'),
                'indicators': data.get('total_mentions', 0),
                'dspy_enhanced': data.get('analysis_method', '').startswith('dspy')
            }
            
            if risk_score < 30:
                matrix['low_impact'].append(risk_item)
            elif risk_score < 60:
                matrix['medium_impact'].append(risk_item)
            else:
                matrix['high_impact'].append(risk_item)
        
        return matrix
    
    def _compare_risk_scores(self, document_risks: Dict) -> Dict[str, Any]:
        """Compara scores de riesgo entre documentos"""
        valid_docs = {k: v for k, v in document_risks.items() if 'error' not in v}
        
        if not valid_docs:
            return {'error': 'No hay documentos válidos para comparar'}
        
        scores = {}
        for doc_id, risk_data in valid_docs.items():
            overall_score = risk_data.get('overall_assessment', {}).get('total_risk_score', 0)
            scores[doc_id] = overall_score
        
        sorted_docs = sorted(scores.items(), key=lambda x: x[1])
        
        return {
            'lowest_risk': sorted_docs[0] if sorted_docs else None,
            'highest_risk': sorted_docs[-1] if sorted_docs else None,
            'average_risk': sum(scores.values()) / len(scores) if scores else 0,
            'risk_spread': (sorted_docs[-1][1] - sorted_docs[0][1]) if len(sorted_docs) > 1 else 0,
            'all_scores': scores
        }
    
    def _compare_category_risks(self, document_risks: Dict) -> Dict[str, Any]:
        """Compara riesgos por categoría entre documentos"""
        category_comparison = {}
        
        valid_docs = {k: v for k, v in document_risks.items() if 'error' not in v}
        
        for category in self.RISK_TAXONOMY.keys():
            category_scores = {}
            for doc_id, risk_data in valid_docs.items():
                category_data = risk_data.get('category_risks', {}).get(category, {})
                if 'error' not in category_data:
                    category_scores[doc_id] = category_data.get('risk_score', 0)
            
            if category_scores:
                sorted_category = sorted(category_scores.items(), key=lambda x: x[1])
                category_comparison[category] = {
                    'lowest_risk': sorted_category[0],
                    'highest_risk': sorted_category[-1],
                    'average': sum(category_scores.values()) / len(category_scores),
                    'all_scores': category_scores
                }
        
        return category_comparison
    
    def _generate_comparative_recommendations(self, document_risks: Dict) -> List[str]:
        """Genera recomendaciones basadas en la comparación de riesgos"""
        recommendations = []
        
        valid_docs = {k: v for k, v in document_risks.items() if 'error' not in v}
        
        if len(valid_docs) < 2:
            return recommendations
        
        # Encontrar el documento con menor riesgo
        scores = {}
        for doc_id, risk_data in valid_docs.items():
            scores[doc_id] = risk_data.get('overall_assessment', {}).get('total_risk_score', 100)
        
        lowest_risk_doc = min(scores.items(), key=lambda x: x[1])
        highest_risk_doc = max(scores.items(), key=lambda x: x[1])
        
        recommendations.append(f"Documento con menor riesgo: {lowest_risk_doc[0]} ({lowest_risk_doc[1]:.1f}%)")
        
        if highest_risk_doc[1] - lowest_risk_doc[1] > 20:
            recommendations.append(f"Diferencia significativa de riesgo detectada. Evitar {highest_risk_doc[0]} ({highest_risk_doc[1]:.1f}%)")
        
        return recommendations[:5]
    
    def export_risk_assessment(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Exporta el análisis de riesgos a un archivo JSON
        
        Args:
            output_path: Ruta donde guardar el reporte
            
        Returns:
            El análisis de riesgos
        """
        
        if not self.risk_assessment:
            raise ValueError("No hay análisis de riesgos para exportar")
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.risk_assessment, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Análisis de riesgos DSPy guardado en: {output_path}")
        
        return self.risk_assessment
    
    def generate_risk_dashboard_data(self) -> Dict[str, Any]:
        """Genera datos optimizados para dashboard de riesgos con información DSPy"""
        
        if not self.risk_assessment:
            return {"error": "No hay datos de análisis disponibles"}
        
        dashboard_data = {
            'overall_risk': {
                'score': self.risk_assessment.get('overall_assessment', {}).get('total_risk_score', 0),
                'level': self.risk_assessment.get('overall_assessment', {}).get('risk_level', 'UNKNOWN'),
                'summary': self.risk_assessment.get('overall_assessment', {}).get('assessment_summary', ''),
                'dspy_enhanced': self.risk_assessment.get('dspy_enabled', False)
            },
            'category_breakdown': [],
            'critical_alerts': [],
            'top_recommendations': [],
            'dspy_insights': {}
        }
        
        # Desglose por categorías para visualización
        for category, data in self.risk_assessment.get('category_risks', {}).items():
            if 'error' not in data:
                dashboard_data['category_breakdown'].append({
                    'name': category.replace('_', ' ').title(),
                    'score': data.get('risk_score', 0),
                    'level': data.get('risk_level', 'UNKNOWN'),
                    'indicators': data.get('total_mentions', 0),
                    'weight': data.get('weight', 0) * 100,
                    'dspy_method': data.get('analysis_method', 'unknown'),
                    'context': data.get('risk_context', '')[:100] + '...' if data.get('risk_context') else ''
                })
        
        # Alertas críticas
        for risk in self.risk_assessment.get('critical_risks', []):
            dashboard_data['critical_alerts'].append({
                'category': risk['category'].replace('_', ' ').title(),
                'score': risk['score'],
                'level': risk['level'],
                'context': risk.get('context', '')[:100] + '...' if risk.get('context') else ''
            })
        
        # Top recomendaciones con información DSPy
        recommendations = self.risk_assessment.get('mitigation_recommendations', [])
        dashboard_data['top_recommendations'] = [
            {
                'priority': rec.get('priority', 'MEDIUM'),
                'category': rec.get('category', '').replace('_', ' ').title(),
                'text': rec.get('recommendation', ''),
                'impact': rec.get('estimated_impact', 'MEDIUM'),
                'dspy_enhanced': rec.get('dspy_enhanced', False),
                'additional_suggestions': rec.get('additional_suggestions', [])
            }
            for rec in recommendations[:6]  # Top 6
        ]
        
        # Insights DSPy si están disponibles
        if self.risk_assessment.get('dspy_comprehensive_analysis'):
            dspy_analysis = self.risk_assessment['dspy_comprehensive_analysis']
            dashboard_data['dspy_insights'] = {
                'comprehensive_score': dspy_analysis.get('overall_risk_score', 0),
                'ai_summary': dspy_analysis.get('risk_summary', ''),
                'ai_recommendations': dspy_analysis.get('priority_recommendations', [])[:3]
            }
        
        return dashboard_data

    # Métodos de compatibilidad hacia atrás
    def initialize_embeddings(self, provider="auto", model=None):
        """Método de compatibilidad - delega a la versión DSPy"""
        return self.initialize_dspy_and_embeddings(provider, model)
    
    def identify_risk_patterns(self, content: str, pattern_type: str = "temporal") -> Dict[str, Any]:
        """
        Identifica patrones de riesgo específicos en el contenido
        (Mantenido del original para compatibilidad)
        """
        patterns = {}
        
        if pattern_type == "temporal":
            deadline_patterns = re.findall(r'plazo[^.]{0,50}(\d+)\s*(días?|meses?)', content, re.IGNORECASE)
            overlapping_phases = re.findall(r'simultáneamente|paralelo|superpuesto', content, re.IGNORECASE)
            
            patterns['temporal'] = {
                'tight_deadlines': len([d for d in deadline_patterns if int(d[0]) < 30]),
                'overlapping_phases': len(overlapping_phases),
                'risk_score': min(100, len(deadline_patterns) * 10 + len(overlapping_phases) * 20)
            }
        
        elif pattern_type == "financial":
            currency_mentions = re.findall(r'(dólar|euro|peso|moneda extranjera)', content, re.IGNORECASE)
            variable_costs = re.findall(r'(costo variable|precio fluctuante|ajuste)', content, re.IGNORECASE)
            
            patterns['financial'] = {
                'currency_exposure': len(currency_mentions),
                'variable_costs': len(variable_costs),
                'risk_score': min(100, len(currency_mentions) * 15 + len(variable_costs) * 10)
            }
        
        elif pattern_type == "operational":
            dependencies = re.findall(r'(depende de|requiere|necesita)', content, re.IGNORECASE)
            complexity_indicators = re.findall(r'(complejo|complicado|difícil|crítico)', content, re.IGNORECASE)
            
            patterns['operational'] = {
                'dependencies': len(dependencies),
                'complexity_indicators': len(complexity_indicators),
                'risk_score': min(100, len(dependencies) * 5 + len(complexity_indicators) * 8)
            }
        
        return patterns

    def analyze_document_risks_with_context(self, 
                                          document_path: Optional[str] = None,
                                          content: Optional[str] = None,
                                          document_type: str = "RFP",
                                          doc_id: Optional[str] = None,
                                          additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Análisis de riesgos enriquecido con contexto de clasificación y validación
        
        Args:
            document_path: Ruta al documento (opcional si se proporciona content)
            content: Contenido del documento (opcional si se proporciona document_path)
            document_type: Tipo de documento (RFP, propuesta, etc.)
            doc_id: ID del documento para bases de datos
            additional_context: Contexto adicional de clasificación y validación
            
        Returns:
            Análisis de riesgos enriquecido con información contextual
        """
        
        logger.info("Iniciando análisis de riesgos con contexto enriquecido")
        
        # Realizar análisis base
        base_analysis = self.analyze_document_risks(
            document_path=document_path,
            content=content,
            document_type=document_type
        )
        
        # Verificar que el análisis base es válido
        if not base_analysis or not isinstance(base_analysis, dict):
            logger.error("El análisis base no devolvió un diccionario válido")
            return {
                'error': 'Error en análisis base de riesgos',
                'context_enhanced': False,
                'timestamp': datetime.now().isoformat()
            }
        
        # Si hay error en el análisis base, retornarlo tal como está
        if 'error' in base_analysis:
            return base_analysis
        
        # Si no hay contexto adicional, devolver análisis base
        if not additional_context:
            return base_analysis
        
        # Enriquecer análisis con contexto adicional
        enhanced_analysis = base_analysis.copy()
        enhanced_analysis['context_enhanced'] = True
        enhanced_analysis['additional_context'] = additional_context
        enhanced_analysis['context_based_adjustments'] = {}
        
        try:
            # Ajustar scores basado en resultados de clasificación
            if 'classification' in additional_context:
                classification_data = additional_context['classification']
                
                # Penalizar por secciones faltantes críticas
                missing_sections = classification_data.get('missing_sections', [])
                critical_missing = [s for s in missing_sections if any(
                    keyword in s.lower() for keyword in [
                        'técnico', 'económico', 'legal', 'riesgo', 'garantía', 
                        'experiencia', 'cronograma', 'presupuesto'
                    ]
                )]
                
                if critical_missing:
                    missing_penalty = len(critical_missing) * 5  # 5% por sección crítica faltante
                    enhanced_analysis['context_based_adjustments']['missing_critical_sections'] = {
                        'penalty': missing_penalty,
                        'missing_sections': critical_missing,
                        'impact': 'Incremento de riesgo por información faltante'
                    }
                    
                    # Aplicar penalty al score general
                    if 'overall_assessment' in enhanced_analysis:
                        current_score = enhanced_analysis['overall_assessment'].get('total_risk_score', 0)
                        enhanced_score = min(100, current_score + missing_penalty)
                        enhanced_analysis['overall_assessment']['total_risk_score'] = enhanced_score
                        enhanced_analysis['overall_assessment']['context_adjusted'] = True
                
                # Analizar confianza de clasificación
                confidence_scores = classification_data.get('confidence_scores', [])
                if confidence_scores:
                    avg_confidence = sum(confidence_scores) / len(confidence_scores)
                    if avg_confidence < 0.6:  # Baja confianza en clasificación
                        confidence_penalty = (0.6 - avg_confidence) * 20  # Hasta 20% penalty
                        enhanced_analysis['context_based_adjustments']['low_classification_confidence'] = {
                            'penalty': confidence_penalty,
                            'average_confidence': avg_confidence,
                            'impact': 'Incremento de riesgo por baja confianza en clasificación'
                        }
                        
                        if 'overall_assessment' in enhanced_analysis:
                            current_score = enhanced_analysis['overall_assessment'].get('total_risk_score', 0)
                            enhanced_score = min(100, current_score + confidence_penalty)
                            enhanced_analysis['overall_assessment']['total_risk_score'] = enhanced_score
            
            # Ajustar scores basado en resultados de validación
            if 'validation' in additional_context:
                validation_data = additional_context['validation']
                compliance_score = validation_data.get('compliance_score', 100)
                
                if compliance_score < 80:  # Bajo cumplimiento
                    compliance_penalty = (80 - compliance_score) * 0.5  # 0.5% por punto bajo 80%
                    enhanced_analysis['context_based_adjustments']['low_compliance'] = {
                        'penalty': compliance_penalty,
                        'compliance_score': compliance_score,
                        'impact': 'Incremento de riesgo por bajo cumplimiento normativo'
                    }
                    
                    if 'overall_assessment' in enhanced_analysis:
                        current_score = enhanced_analysis['overall_assessment'].get('total_risk_score', 0)
                        enhanced_score = min(100, current_score + compliance_penalty)
                        enhanced_analysis['overall_assessment']['total_risk_score'] = enhanced_score
                
                # Penalizar por violaciones específicas
                violations = validation_data.get('violations', [])
                if violations:
                    violation_penalty = len(violations) * 3  # 3% por violación
                    enhanced_analysis['context_based_adjustments']['compliance_violations'] = {
                        'penalty': violation_penalty,
                        'violations_count': len(violations),
                        'violations': violations[:3],  # Mostrar solo primeras 3
                        'impact': 'Incremento de riesgo por violaciones de cumplimiento'
                    }
                    
                    if 'overall_assessment' in enhanced_analysis:
                        current_score = enhanced_analysis['overall_assessment'].get('total_risk_score', 0)
                        enhanced_score = min(100, current_score + violation_penalty)
                        enhanced_analysis['overall_assessment']['total_risk_score'] = enhanced_score
            
            # Ajustar scores basado en validación RUC
            if 'ruc_validation' in additional_context:
                ruc_data = additional_context['ruc_validation']
                ruc_score = ruc_data.get('overall_score', 100)
                
                if ruc_score < 70:  # Baja validación RUC
                    ruc_penalty = (70 - ruc_score) * 0.3  # 0.3% por punto bajo 70%
                    enhanced_analysis['context_based_adjustments']['ruc_validation_issues'] = {
                        'penalty': ruc_penalty,
                        'ruc_score': ruc_score,
                        'verification_level': ruc_data.get('validation_level', 'UNKNOWN'),
                        'impact': 'Incremento de riesgo por problemas en validación de RUC'
                    }
                    
                    if 'overall_assessment' in enhanced_analysis:
                        current_score = enhanced_analysis['overall_assessment'].get('total_risk_score', 0)
                        enhanced_score = min(100, current_score + ruc_penalty)
                        enhanced_analysis['overall_assessment']['total_risk_score'] = enhanced_score
            
            # Generar recomendaciones contextualizadas adicionales
            context_recommendations = []
            
            for adjustment_type, adjustment_data in enhanced_analysis.get('context_based_adjustments', {}).items():
                if adjustment_type == 'missing_critical_sections':
                    context_recommendations.append({
                        'category': 'DOCUMENT_COMPLETENESS',
                        'priority': 'HIGH',
                        'recommendation': f"Solicitar información faltante en secciones críticas: {', '.join(adjustment_data.get('missing_sections', [])[:3])}",
                        'dspy_enhanced': False,
                        'context_based': True
                    })
                elif adjustment_type == 'low_compliance':
                    context_recommendations.append({
                        'category': 'REGULATORY_COMPLIANCE', 
                        'priority': 'HIGH',
                        'recommendation': f"Revisar cumplimiento normativo (score actual: {adjustment_data.get('compliance_score', 0)}%). Solicitar documentación adicional.",
                        'dspy_enhanced': False,
                        'context_based': True
                    })
                elif adjustment_type == 'ruc_validation_issues':
                    context_recommendations.append({
                        'category': 'SUPPLIER_VERIFICATION',
                        'priority': 'MEDIUM',
                        'recommendation': f"Verificar validez de RUCs del contratista (score: {adjustment_data.get('ruc_score', 0)}%)",
                        'dspy_enhanced': False,
                        'context_based': True
                    })
            
            # Añadir recomendaciones contextuales
            if context_recommendations:
                existing_recommendations = enhanced_analysis.get('mitigation_recommendations', [])
                enhanced_analysis['mitigation_recommendations'] = existing_recommendations + context_recommendations
            
            # Actualizar nivel de riesgo si el score cambió significativamente
            if 'overall_assessment' in enhanced_analysis:
                new_score = enhanced_analysis['overall_assessment'].get('total_risk_score', 0)
                new_level = self._get_risk_level(new_score)
                enhanced_analysis['overall_assessment']['risk_level'] = new_level
                enhanced_analysis['overall_assessment']['context_enhancement_applied'] = True
            
            logger.info("Análisis de riesgos enriquecido con contexto completado exitosamente")
            
        except Exception as e:
            logger.error(f"Error enriqueciendo análisis con contexto: {e}")
            enhanced_analysis['context_enhancement_error'] = str(e)
        
        return enhanced_analysis
