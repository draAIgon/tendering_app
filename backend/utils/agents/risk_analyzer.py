import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
import numpy as np

# Importar funciones del sistema de embeddings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.embedding import get_embeddings_provider, txt_to_documents
from langchain_chroma import Chroma
from langchain.schema import Document

# Importar database manager para ubicaciones estandarizadas
from ..db_manager import get_standard_db_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskAnalyzerAgent:
    """
    Agente especializado en análisis de riesgos para procesos de licitación.
    Identifica y evalúa riesgos técnicos, económicos, legales y operacionales.
    """
    
    # Taxonomía de riesgos para licitaciones
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
                r'actualizaciones?\s+frecuentes?'
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
                r'flujo\s+de\s+caja\s+negativo'
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
                r'incumplimiento\s+legal'
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
                r'gesti[óo]n\s+de\s+cambios'
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
                r'sanciones?\s+internacionales?'
            ],
            'risk_factors': [
                'supplier_reliability', 'financial_stability', 'experience_level',
                'geographical_risks', 'reputation_risks'
            ]
        }
    }
    
    # Niveles de riesgo
    RISK_LEVELS = {
        'VERY_LOW': {'range': (0, 20), 'color': 'green', 'action': 'Monitoreo rutinario'},
        'LOW': {'range': (20, 40), 'color': 'lightgreen', 'action': 'Monitoreo regular'},
        'MEDIUM': {'range': (40, 60), 'color': 'yellow', 'action': 'Atención y mitigación'},
        'HIGH': {'range': (60, 80), 'color': 'orange', 'action': 'Mitigación urgente'},
        'VERY_HIGH': {'range': (80, 100), 'color': 'red', 'action': 'Intervención inmediata'}
    }
    
    def __init__(self, vector_db_path: Optional[Path] = None):
        # Use standardized database path
        if vector_db_path:
            self.vector_db_path = vector_db_path
        else:
            self.vector_db_path = get_standard_db_path('risk_analysis', 'global')
            
        self.embeddings_provider = None
        self.vector_db = None
        self.risk_assessment = {}
        self.mitigation_strategies = {}
        
        logger.info(f"RiskAnalyzerAgent iniciado con DB: {self.vector_db_path}")
        
    def initialize_embeddings(self, provider="auto", model=None):
        """Inicializa el sistema de embeddings para análisis semántico de riesgos"""
        try:
            self.embeddings_provider = get_embeddings_provider(provider=provider, model=model)
            logger.info("Sistema de embeddings inicializado para análisis de riesgos")
            return True
        except Exception as e:
            logger.error(f"Error inicializando embeddings: {e}")
            return False
    
    def setup_vector_database(self, documents: List[Document]):
        """Configura la base de datos vectorial con documentos para análisis"""
        if not self.embeddings_provider:
            logger.warning("Embeddings no disponibles, usando análisis basado en reglas")
            return True
            
        try:
            self.vector_db = Chroma(
                collection_name="risk_analysis",
                persist_directory=str(self.vector_db_path),
                embedding_function=self.embeddings_provider
            )
            
            if documents:
                self.vector_db.add_documents(documents)
                self.vector_db.persist()
                logger.info(f"Base de datos vectorial configurada con {len(documents)} documentos")
            
            return True
        except Exception as e:
            logger.error(f"Error configurando base de datos vectorial: {e}")
            return False
    
    def detect_risk_indicators(self, content: str, risk_category: str) -> Dict[str, Any]:
        """
        Detecta indicadores de riesgo en el contenido para una categoría específica
        
        Args:
            content: Contenido del documento
            risk_category: Categoría de riesgo a analizar
            
        Returns:
            Diccionario con indicadores encontrados y scores
        """
        
        if risk_category not in self.RISK_TAXONOMY:
            raise ValueError(f"Categoría de riesgo no válida: {risk_category}")
        
        category_info = self.RISK_TAXONOMY[risk_category]
        indicators = category_info['indicators']
        
        detected_indicators = []
        risk_mentions = []
        
        for indicator_pattern in indicators:
            matches = re.findall(indicator_pattern, content, re.IGNORECASE | re.UNICODE)
            if matches:
                detected_indicators.append({
                    'pattern': indicator_pattern,
                    'matches': matches,
                    'count': len(matches),
                    'severity': self._calculate_indicator_severity(indicator_pattern, len(matches))
                })
                
                # Buscar contexto alrededor de cada match
                for match in matches:
                    context = self._extract_context(content, match, window=100)
                    risk_mentions.append({
                        'indicator': indicator_pattern,
                        'match': match,
                        'context': context
                    })
        
        # Calcular score de riesgo para la categoría
        risk_score = self._calculate_category_risk_score(detected_indicators)
        
        # Búsqueda semántica adicional si está disponible
        semantic_risks = []
        if self.vector_db:
            try:
                risk_query = f"riesgos {risk_category.lower().replace('_', ' ')}"
                semantic_results = self.vector_db.similarity_search(risk_query, k=5)
                for doc in semantic_results:
                    semantic_risks.append({
                        'content': doc.page_content[:200] + "...",
                        'metadata': doc.metadata,
                        'relevance': 'high'  # Simplificado
                    })
            except Exception as e:
                logger.warning(f"Error en búsqueda semántica: {e}")
        
        return {
            'category': risk_category,
            'description': category_info['description'],
            'risk_score': risk_score,
            'risk_level': self._get_risk_level(risk_score),
            'indicators_detected': len(detected_indicators),
            'total_mentions': sum(ind['count'] for ind in detected_indicators),
            'detected_indicators': detected_indicators,
            'risk_mentions': risk_mentions[:10],  # Limitar a 10
            'semantic_risks': semantic_risks[:5],  # Top 5
            'weight': category_info['weight']
        }
    
    def analyze_document_risks(self, document_path: Optional[str] = None, 
                             content: Optional[str] = None,
                             document_type: str = "RFP",
                             doc_type: Optional[str] = None,
                             doc_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Análisis completo de riesgos de un documento
        
        Args:
            document_path: Ruta al documento
            content: Contenido del documento
            document_type: Tipo de documento (RFP, Proposal, Contract)
            doc_type: Alias para document_type (para compatibilidad)
            doc_id: ID del documento (opcional)
            
        Returns:
            Análisis completo de riesgos
        """
        
        # Support both parameter names for compatibility
        if doc_type:
            document_type = doc_type
        
        if not content and not document_path:
            raise ValueError("Debe proporcionar content o document_path")
        
        # Obtener contenido si se proporciona ruta
        if document_path and not content:
            try:
                from document_extraction import DocumentExtractionAgent
                extractor = DocumentExtractionAgent(document_path)
                content = extractor.extract_text()
            except Exception as e:
                logger.error(f"Error extrayendo contenido: {e}")
                return {"error": f"No se pudo extraer contenido: {e}"}
        
        logger.info(f"Iniciando análisis de riesgos para documento tipo {document_type}")
        
        risk_analysis = {
            'document_type': document_type,
            'analysis_timestamp': datetime.now().isoformat(),
            'content_length': len(content),
            'category_risks': {},
            'overall_assessment': {},
            'critical_risks': [],
            'mitigation_recommendations': [],
            'risk_matrix': {}
        }
        
        total_weighted_risk = 0
        
        # Analizar cada categoría de riesgo
        for category in self.RISK_TAXONOMY.keys():
            try:
                category_analysis = self.detect_risk_indicators(content, category)
                risk_analysis['category_risks'][category] = category_analysis
                
                # Contribución al riesgo total
                weighted_risk = category_analysis['risk_score'] * category_analysis['weight']
                total_weighted_risk += weighted_risk
                
                # Identificar riesgos críticos
                if category_analysis['risk_score'] > 70:
                    risk_analysis['critical_risks'].append({
                        'category': category,
                        'score': category_analysis['risk_score'],
                        'level': category_analysis['risk_level'],
                        'indicators': category_analysis['indicators_detected']
                    })
                    
            except Exception as e:
                logger.error(f"Error analizando categoría {category}: {e}")
                risk_analysis['category_risks'][category] = {
                    'error': str(e),
                    'risk_score': 0,
                    'weight': self.RISK_TAXONOMY[category]['weight']
                }
        
        # Evaluación general
        overall_risk_score = total_weighted_risk
        risk_analysis['overall_assessment'] = {
            'total_risk_score': round(overall_risk_score, 2),
            'risk_level': self._get_risk_level(overall_risk_score),
            'risk_distribution': self._calculate_risk_distribution(risk_analysis['category_risks']),
            'assessment_summary': self._generate_risk_summary(overall_risk_score, risk_analysis['critical_risks'])
        }
        
        # Generar recomendaciones de mitigación
        risk_analysis['mitigation_recommendations'] = self._generate_mitigation_recommendations(
            risk_analysis['category_risks'], overall_risk_score
        )
        
        # Matriz de riesgos
        risk_analysis['risk_matrix'] = self._create_risk_matrix(risk_analysis['category_risks'])
        
        self.risk_assessment = risk_analysis
        logger.info(f"Análisis de riesgos completado. Score general: {overall_risk_score:.1f}")
        
        return risk_analysis
    
    def compare_risk_profiles(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compara perfiles de riesgo entre múltiples documentos
        
        Args:
            documents: Lista de documentos con 'id', 'content' o 'path', y 'type'
            
        Returns:
            Comparación de perfiles de riesgo
        """
        
        if len(documents) < 2:
            raise ValueError("Se necesitan al menos 2 documentos para comparar")
        
        logger.info(f"Comparando perfiles de riesgo de {len(documents)} documentos")
        
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
        
        # Generar comparación
        comparison = {
            'comparison_timestamp': datetime.now().isoformat(),
            'documents_analyzed': len(documents),
            'successful_analyses': len([d for d in document_risks.values() if 'error' not in d]),
            'document_risks': document_risks,
            'risk_comparison': self._compare_risk_scores(document_risks),
            'category_comparison': self._compare_category_risks(document_risks),
            'recommendations': self._generate_comparative_recommendations(document_risks)
        }
        
        return comparison
    
    def identify_risk_patterns(self, content: str, pattern_type: str = "temporal") -> Dict[str, Any]:
        """
        Identifica patrones de riesgo específicos en el contenido
        
        Args:
            content: Contenido a analizar
            pattern_type: Tipo de patrón (temporal, financiero, operacional)
            
        Returns:
            Patrones de riesgo identificados
        """
        
        patterns = {}
        
        if pattern_type == "temporal":
            # Patrones temporales de riesgo
            deadline_patterns = re.findall(r'plazo[^.]{0,50}(\d+)\s*(días?|meses?)', content, re.IGNORECASE)
            overlapping_phases = re.findall(r'simultáneamente|paralelo|superpuesto', content, re.IGNORECASE)
            
            patterns['temporal'] = {
                'tight_deadlines': len([d for d in deadline_patterns if int(d[0]) < 30]),
                'overlapping_phases': len(overlapping_phases),
                'risk_score': min(100, len(deadline_patterns) * 10 + len(overlapping_phases) * 20)
            }
        
        elif pattern_type == "financial":
            # Patrones financieros de riesgo
            currency_mentions = re.findall(r'(dólar|euro|peso|moneda extranjera)', content, re.IGNORECASE)
            variable_costs = re.findall(r'(costo variable|precio fluctuante|ajuste)', content, re.IGNORECASE)
            
            patterns['financial'] = {
                'currency_exposure': len(currency_mentions),
                'variable_costs': len(variable_costs),
                'risk_score': min(100, len(currency_mentions) * 15 + len(variable_costs) * 10)
            }
        
        elif pattern_type == "operational":
            # Patrones operacionales
            dependencies = re.findall(r'(depende de|requiere|necesita)', content, re.IGNORECASE)
            complexity_indicators = re.findall(r'(complejo|complicado|difícil|crítico)', content, re.IGNORECASE)
            
            patterns['operational'] = {
                'dependencies': len(dependencies),
                'complexity_indicators': len(complexity_indicators),
                'risk_score': min(100, len(dependencies) * 5 + len(complexity_indicators) * 8)
            }
        
        return patterns
    
    def _calculate_indicator_severity(self, pattern: str, count: int) -> str:
        """Calcula la severidad de un indicador basado en el patrón y frecuencia"""
        high_severity_patterns = ['tecnología no probada', 'precio excesivamente bajo', 'normatividad cambiante']
        
        if any(hsp in pattern for hsp in high_severity_patterns):
            base_severity = 'HIGH'
        else:
            base_severity = 'MEDIUM'
        
        # Ajustar por frecuencia
        if count > 3:
            return 'VERY_HIGH'
        elif count > 1 and base_severity == 'HIGH':
            return 'VERY_HIGH'
        elif count > 1:
            return 'HIGH'
        else:
            return base_severity
    
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
    
    def _calculate_category_risk_score(self, indicators: List[Dict]) -> float:
        """Calcula el score de riesgo para una categoría basado en indicadores"""
        if not indicators:
            return 0.0
        
        severity_scores = {'LOW': 10, 'MEDIUM': 25, 'HIGH': 50, 'VERY_HIGH': 80}
        
        total_score = 0
        for indicator in indicators:
            base_score = severity_scores.get(indicator['severity'], 25)
            frequency_multiplier = min(2.0, 1 + (indicator['count'] - 1) * 0.2)
            total_score += base_score * frequency_multiplier
        
        # Normalizar a escala 0-100
        max_possible = len(indicators) * 80 * 2  # Máximo teórico
        normalized_score = min(100, (total_score / max_possible * 100) if max_possible > 0 else 0)
        
        return round(normalized_score, 2)
    
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
    
    def _generate_mitigation_recommendations(self, category_risks: Dict, overall_score: float) -> List[Dict]:
        """Genera recomendaciones de mitigación de riesgos"""
        recommendations = []
        
        # Recomendaciones por categoría - reducir umbral para más sensibilidad
        for category, data in category_risks.items():
            if 'error' in data:
                continue
                
            risk_score = data.get('risk_score', 0)
            indicators_detected = data.get('indicators_detected', 0)
            
            # Generar recomendaciones si hay riesgo moderado (>30) o indicadores detectados
            if risk_score > 30 or indicators_detected > 0:
                category_name = category.replace('_', ' ').title()
                
                # Determinar prioridad basada en score y número de indicadores
                if risk_score > 70 or indicators_detected > 3:
                    priority = 'HIGH'
                    estimated_impact = 'HIGH'
                elif risk_score > 50 or indicators_detected > 1:
                    priority = 'MEDIUM'
                    estimated_impact = 'MEDIUM'
                else:
                    priority = 'LOW'
                    estimated_impact = 'LOW'
                
                recommendation = {
                    'category': category,
                    'priority': priority,
                    'risk_score': risk_score,
                    'indicators_count': indicators_detected,
                    'recommendation': self._get_category_mitigation(category, risk_score),
                    'estimated_impact': estimated_impact
                }
                recommendations.append(recommendation)
        
        # Recomendaciones generales basadas en score total
        if overall_score > 80:
            recommendations.insert(0, {
                'category': 'GENERAL',
                'priority': 'CRITICAL',
                'risk_score': overall_score,
                'recommendation': 'Considerar rechazar la propuesta o requerir garantías adicionales significativas',
                'estimated_impact': 'VERY_HIGH'
            })
        elif overall_score > 60:
            recommendations.insert(0, {
                'category': 'GENERAL',
                'priority': 'HIGH',
                'risk_score': overall_score,
                'recommendation': 'Implementar plan de gestión de riesgos robusto antes de la ejecución',
                'estimated_impact': 'HIGH'
            })
        elif overall_score > 30:
            recommendations.insert(0, {
                'category': 'GENERAL',
                'priority': 'MEDIUM',
                'risk_score': overall_score,
                'recommendation': 'Implementar monitoreo adicional y controles básicos de riesgo',
                'estimated_impact': 'MEDIUM'
            })
        elif overall_score > 10:
            recommendations.insert(0, {
                'category': 'GENERAL',
                'priority': 'LOW',
                'risk_score': overall_score,
                'recommendation': 'Mantener monitoreo rutinario de factores de riesgo identificados',
                'estimated_impact': 'LOW'
            })
        
        return recommendations[:10]  # Máximo 10 recomendaciones
    
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
                'indicators': data.get('indicators_detected', 0)
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
        
        # Análisis por categorías
        avg_scores = {}
        for doc_id, risk_data in valid_docs.items():
            for category, cat_data in risk_data.get('category_risks', {}).items():
                if 'error' not in cat_data:
                    if category not in avg_scores:
                        avg_scores[category] = []
                    avg_scores[category].append(cat_data.get('risk_score', 0))
        
        # Categoría más problemática
        category_averages = {cat: sum(scores) / len(scores) for cat, scores in avg_scores.items() if scores}
        if category_averages:
            highest_risk_category = max(category_averages.items(), key=lambda x: x[1])
            if highest_risk_category[1] > 60:
                recommendations.append(f"Categoría más riesgosa: {highest_risk_category[0].replace('_', ' ')} (promedio: {highest_risk_category[1]:.1f}%)")
        
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
            
            logger.info(f"Análisis de riesgos guardado en: {output_path}")
        
        return self.risk_assessment
    
    def generate_risk_dashboard_data(self) -> Dict[str, Any]:
        """Genera datos optimizados para dashboard de riesgos"""
        
        if not self.risk_assessment:
            return {"error": "No hay datos de análisis disponibles"}
        
        dashboard_data = {
            'overall_risk': {
                'score': self.risk_assessment.get('overall_assessment', {}).get('total_risk_score', 0),
                'level': self.risk_assessment.get('overall_assessment', {}).get('risk_level', 'UNKNOWN'),
                'summary': self.risk_assessment.get('overall_assessment', {}).get('assessment_summary', '')
            },
            'category_breakdown': [],
            'critical_alerts': [],
            'top_recommendations': [],
            'risk_trends': {}
        }
        
        # Desglose por categorías para visualización
        for category, data in self.risk_assessment.get('category_risks', {}).items():
            if 'error' not in data:
                dashboard_data['category_breakdown'].append({
                    'name': category.replace('_', ' ').title(),
                    'score': data.get('risk_score', 0),
                    'level': data.get('risk_level', 'UNKNOWN'),
                    'indicators': data.get('indicators_detected', 0),
                    'weight': data.get('weight', 0) * 100
                })
        
        # Alertas críticas
        for risk in self.risk_assessment.get('critical_risks', []):
            dashboard_data['critical_alerts'].append({
                'category': risk['category'].replace('_', ' ').title(),
                'score': risk['score'],
                'level': risk['level']
            })
        
        # Top recomendaciones
        recommendations = self.risk_assessment.get('mitigation_recommendations', [])
        dashboard_data['top_recommendations'] = [
            {
                'priority': rec.get('priority', 'MEDIUM'),
                'category': rec.get('category', '').replace('_', ' ').title(),
                'text': rec.get('recommendation', ''),
                'impact': rec.get('estimated_impact', 'MEDIUM')
            }
            for rec in recommendations[:5]
        ]
        
        return dashboard_data