import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import json
import numpy as np
from collections import defaultdict

# Importar funciones del sistema de embeddings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from Embedding import get_embeddings_provider
from langchain.vectorstores import Chroma
from langchain.schema import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComparatorAgent:
    """
    Agente especializado en comparaciones detalladas entre documentos, propuestas,
    y oferentes. Proporciona análisis comparativo multi-dimensional usando 
    técnicas de NLP y análisis semántico.
    """
    
    # Criterios de comparación configurables
    COMPARISON_DIMENSIONS = {
        'CONTENT_SIMILARITY': {
            'weight': 0.2,
            'description': 'Similitud semántica del contenido',
            'method': 'embedding_similarity'
        },
        'STRUCTURAL_COMPLIANCE': {
            'weight': 0.25,
            'description': 'Cumplimiento estructural y organizacional',
            'method': 'structural_analysis'
        },
        'TECHNICAL_COMPLETENESS': {
            'weight': 0.2,
            'description': 'Completitud técnica y especificaciones',
            'method': 'technical_analysis'
        },
        'ECONOMIC_COMPETITIVENESS': {
            'weight': 0.2,
            'description': 'Competitividad económica y financiera',
            'method': 'economic_analysis'
        },
        'RISK_PROFILE': {
            'weight': 0.15,
            'description': 'Perfil de riesgo y mitigación',
            'method': 'risk_analysis'
        }
    }
    
    def __init__(self, vector_db_path: Optional[Path] = None):
        self.vector_db_path = vector_db_path or Path("./comparator_db")
        self.embeddings_provider = None
        self.vector_db = None
        self.documents = {}
        self.comparison_results = {}
        
    def initialize_embeddings(self, provider="auto", model=None):
        """Inicializa el sistema de embeddings para comparaciones semánticas"""
        try:
            self.embeddings_provider = get_embeddings_provider(provider=provider, model=model)
            logger.info("Sistema de embeddings inicializado para comparaciones")
            return True
        except Exception as e:
            logger.error(f"Error inicializando embeddings: {e}")
            return False
    
    def add_document(self, doc_id: str, content: str, doc_type: str = "proposal", 
                    metadata: Optional[Dict] = None):
        """
        Añade un documento al sistema de comparación
        
        Args:
            doc_id: Identificador único del documento
            content: Contenido del documento
            doc_type: Tipo de documento (proposal, rfp, contract, etc.)
            metadata: Metadatos adicionales
        """
        
        if not metadata:
            metadata = {}
        
        # Procesar contenido en chunks para análisis detallado
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " "]
        )
        
        chunks = splitter.split_text(content)
        documents = []
        
        for i, chunk in enumerate(chunks):
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
    
    def setup_vector_database(self):
        """Configura la base de datos vectorial con todos los documentos"""
        if not self.embeddings_provider:
            logger.warning("Embeddings no disponibles, comparación limitada a análisis textual")
            return True
            
        if not self.documents:
            raise ValueError("No hay documentos cargados")
        
        # Recopilar todos los documentos
        all_documents = []
        for doc_id, doc_data in self.documents.items():
            all_documents.extend(doc_data['documents'])
        
        # Crear base de datos vectorial
        self.vector_db = Chroma(
            collection_name="document_comparison",
            persist_directory=str(self.vector_db_path),
            embedding_function=self.embeddings_provider
        )
        
        self.vector_db.add_documents(all_documents)
        self.vector_db.persist()
        
        logger.info(f"Base de datos vectorial configurada con {len(all_documents)} documentos")
        return True
    
    def analyze_content_similarity(self, doc1_id: str, doc2_id: str) -> Dict[str, Any]:
        """
        Analiza la similitud de contenido entre dos documentos
        
        Args:
            doc1_id: ID del primer documento
            doc2_id: ID del segundo documento
            
        Returns:
            Análisis de similitud de contenido
        """
        
        if doc1_id not in self.documents or doc2_id not in self.documents:
            raise ValueError("Uno o ambos documentos no encontrados")
        
        content1 = self.documents[doc1_id]['content']
        content2 = self.documents[doc2_id]['content']
        
        similarity_analysis = {
            'comparison_type': 'content_similarity',
            'doc1_id': doc1_id,
            'doc2_id': doc2_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'metrics': {}
        }
        
        # Análisis básico de texto
        words1 = set(re.findall(r'\b\w+\b', content1.lower()))
        words2 = set(re.findall(r'\b\w+\b', content2.lower()))
        
        common_words = words1.intersection(words2)
        all_words = words1.union(words2)
        
        jaccard_similarity = len(common_words) / len(all_words) if all_words else 0
        
        similarity_analysis['metrics']['jaccard_similarity'] = jaccard_similarity
        similarity_analysis['metrics']['common_words_count'] = len(common_words)
        similarity_analysis['metrics']['unique_words_doc1'] = len(words1 - words2)
        similarity_analysis['metrics']['unique_words_doc2'] = len(words2 - words1)
        
        # Análisis semántico si está disponible
        if self.vector_db:
            try:
                # Buscar contenido similar entre documentos
                doc1_results = self.vector_db.similarity_search(
                    content1[:500], k=10, filter={'doc_id': doc2_id}
                )
                doc2_results = self.vector_db.similarity_search(
                    content2[:500], k=10, filter={'doc_id': doc1_id}
                )
                
                semantic_matches = len(doc1_results) + len(doc2_results)
                similarity_analysis['metrics']['semantic_similarity'] = min(100, semantic_matches * 5)
                
                # Extraer temas comunes
                common_themes = []
                for result in doc1_results[:5]:
                    theme = result.page_content[:100].strip()
                    common_themes.append(theme)
                
                similarity_analysis['common_themes'] = common_themes
                
            except Exception as e:
                logger.warning(f"Error en análisis semántico: {e}")
                similarity_analysis['metrics']['semantic_similarity'] = 0
        
        # Score combinado de similitud (0-100)
        if 'semantic_similarity' in similarity_analysis['metrics']:
            combined_score = (
                jaccard_similarity * 30 + 
                similarity_analysis['metrics']['semantic_similarity'] * 0.7
            )
        else:
            combined_score = jaccard_similarity * 100
        
        similarity_analysis['overall_similarity_score'] = round(combined_score, 2)
        
        return similarity_analysis
    
    def analyze_structural_compliance(self, doc1_id: str, doc2_id: str, 
                                    required_sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compara el cumplimiento estructural entre documentos
        
        Args:
            doc1_id: ID del primer documento
            doc2_id: ID del segundo documento
            required_sections: Secciones requeridas para evaluar
            
        Returns:
            Análisis de cumplimiento estructural comparativo
        """
        
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
        
        structural_analysis = {
            'comparison_type': 'structural_compliance',
            'doc1_id': doc1_id,
            'doc2_id': doc2_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'required_sections_count': len(required_sections),
            'doc1_analysis': {},
            'doc2_analysis': {},
            'comparative_analysis': {}
        }
        
        # Analizar cada documento
        for doc_id, analysis_key in [(doc1_id, 'doc1_analysis'), (doc2_id, 'doc2_analysis')]:
            content = self.documents[doc_id]['content']
            found_sections = []
            missing_sections = []
            
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
                'estimated_completeness': min(100, len(content) / 5000 * 100)  # Basado en 5000 chars promedio
            }
        
        # Análisis comparativo
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
        """
        Compara la completitud técnica entre documentos
        
        Args:
            doc1_id: ID del primer documento
            doc2_id: ID del segundo documento
            
        Returns:
            Análisis de completitud técnica comparativa
        """
        
        technical_keywords = [
            'especificaciones', 'requirements', 'arquitectura', 'tecnología',
            'implementación', 'integración', 'desarrollo', 'testing',
            'seguridad', 'performance', 'escalabilidad', 'mantenimiento',
            'certificaciones', 'estándares', 'protocolos', 'apis'
        ]
        
        technical_analysis = {
            'comparison_type': 'technical_completeness',
            'doc1_id': doc1_id,
            'doc2_id': doc2_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'technical_keywords': technical_keywords,
            'doc1_analysis': {},
            'doc2_analysis': {},
            'comparative_analysis': {}
        }
        
        # Analizar cada documento
        for doc_id, analysis_key in [(doc1_id, 'doc1_analysis'), (doc2_id, 'doc2_analysis')]:
            content = self.documents[doc_id]['content'].lower()
            
            keyword_matches = {}
            total_matches = 0
            
            for keyword in technical_keywords:
                matches = len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE))
                keyword_matches[keyword] = matches
                total_matches += matches
            
            # Buscar patrones técnicos específicos
            technical_patterns = [
                r'\d+\s*(gb|mb|ghz|mhz)', # Especificaciones técnicas
                r'iso\s*\d+', # Estándares ISO
                r'version\s*\d+\.\d+', # Versiones de software
                r'(mysql|postgresql|oracle|mongodb)', # Bases de datos
                r'(java|python|\.net|php|javascript)', # Tecnologías
            ]
            
            pattern_matches = 0
            for pattern in technical_patterns:
                pattern_matches += len(re.findall(pattern, content, re.IGNORECASE))
            
            technical_analysis[analysis_key] = {
                'keyword_matches': keyword_matches,
                'total_keyword_matches': total_matches,
                'pattern_matches': pattern_matches,
                'technical_density': total_matches / len(content.split()) * 1000 if content else 0,
                'technical_completeness_score': min(100, (total_matches + pattern_matches) * 2)
            }
        
        # Análisis comparativo
        score1 = technical_analysis['doc1_analysis']['technical_completeness_score']
        score2 = technical_analysis['doc2_analysis']['technical_completeness_score']
        
        technical_analysis['comparative_analysis'] = {
            'more_technical': doc1_id if score1 > score2 else doc2_id,
            'technical_difference': abs(score1 - score2),
            'both_technically_complete': score1 >= 60 and score2 >= 60,
            'technical_coverage_comparison': {
                doc1_id: score1,
                doc2_id: score2
            }
        }
        
        return technical_analysis
    
    def analyze_economic_competitiveness(self, doc1_id: str, doc2_id: str) -> Dict[str, Any]:
        """
        Compara la competitividad económica entre propuestas
        
        Args:
            doc1_id: ID del primer documento
            doc2_id: ID del segundo documento
            
        Returns:
            Análisis de competitividad económica comparativa
        """
        
        economic_analysis = {
            'comparison_type': 'economic_competitiveness',
            'doc1_id': doc1_id,
            'doc2_id': doc2_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'doc1_analysis': {},
            'doc2_analysis': {},
            'comparative_analysis': {}
        }
        
        # Patrones para extraer información económica
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
        
        # Analizar cada documento
        for doc_id, analysis_key in [(doc1_id, 'doc1_analysis'), (doc2_id, 'doc2_analysis')]:
            content = self.documents[doc_id]['content']
            
            # Extraer precios
            found_prices = []
            for pattern in price_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    try:
                        price = float(match.replace(',', ''))
                        found_prices.append(price)
                    except:
                        continue
            
            # Contar keywords económicas
            economic_mentions = 0
            for keyword in economic_keywords:
                economic_mentions += len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE))
            
            # Buscar términos de valor agregado
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
        
        # Análisis comparativo
        price1 = economic_analysis['doc1_analysis']['estimated_total_price']
        price2 = economic_analysis['doc2_analysis']['estimated_total_price']
        
        comparative_analysis = {}
        
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
        
        # Comparar completitud económica
        econ1 = economic_analysis['doc1_analysis']['economic_completeness']
        econ2 = economic_analysis['doc2_analysis']['economic_completeness']
        
        comparative_analysis['economic_completeness_comparison'] = {
            'more_complete': doc1_id if econ1 > econ2 else doc2_id,
            'completeness_difference': abs(econ1 - econ2),
            doc1_id: econ1,
            doc2_id: econ2
        }
        
        economic_analysis['comparative_analysis'] = comparative_analysis
        
        return economic_analysis
    
    def comprehensive_comparison(self, doc1_id: str, doc2_id: str, 
                                weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Realiza una comparación comprehensiva entre dos documentos
        
        Args:
            doc1_id: ID del primer documento
            doc2_id: ID del segundo documento
            weights: Pesos personalizados para las dimensiones de comparación
            
        Returns:
            Análisis comparativo completo
        """
        
        if doc1_id not in self.documents or doc2_id not in self.documents:
            raise ValueError("Uno o ambos documentos no encontrados")
        
        if not weights:
            weights = {dim: info['weight'] for dim, info in self.COMPARISON_DIMENSIONS.items()}
        
        logger.info(f"Iniciando comparación comprehensiva entre {doc1_id} y {doc2_id}")
        
        comprehensive_comparison = {
            'comparison_id': f"{doc1_id}_vs_{doc2_id}_{int(datetime.now().timestamp())}",
            'doc1_id': doc1_id,
            'doc2_id': doc2_id,
            'comparison_timestamp': datetime.now().isoformat(),
            'weights_used': weights,
            'dimension_analyses': {},
            'overall_scores': {},
            'winner': None,
            'summary': {},
            'recommendations': []
        }
        
        total_score_doc1 = 0
        total_score_doc2 = 0
        
        # Ejecutar análisis por dimensión
        try:
            # Similitud de contenido
            content_analysis = self.analyze_content_similarity(doc1_id, doc2_id)
            comprehensive_comparison['dimension_analyses']['content_similarity'] = content_analysis
            
            similarity_score = content_analysis['overall_similarity_score']
            doc1_content_score = similarity_score
            doc2_content_score = 100 - similarity_score  # Inverso para el otro documento
            
            total_score_doc1 += doc1_content_score * weights.get('CONTENT_SIMILARITY', 0.2)
            total_score_doc2 += doc2_content_score * weights.get('CONTENT_SIMILARITY', 0.2)
        
        except Exception as e:
            logger.error(f"Error en análisis de similitud de contenido: {e}")
        
        try:
            # Cumplimiento estructural
            structural_analysis = self.analyze_structural_compliance(doc1_id, doc2_id)
            comprehensive_comparison['dimension_analyses']['structural_compliance'] = structural_analysis
            
            struct1 = structural_analysis['doc1_analysis']['compliance_percentage']
            struct2 = structural_analysis['doc2_analysis']['compliance_percentage']
            
            total_score_doc1 += struct1 * weights.get('STRUCTURAL_COMPLIANCE', 0.25)
            total_score_doc2 += struct2 * weights.get('STRUCTURAL_COMPLIANCE', 0.25)
        
        except Exception as e:
            logger.error(f"Error en análisis estructural: {e}")
        
        try:
            # Completitud técnica
            technical_analysis = self.analyze_technical_completeness(doc1_id, doc2_id)
            comprehensive_comparison['dimension_analyses']['technical_completeness'] = technical_analysis
            
            tech1 = technical_analysis['doc1_analysis']['technical_completeness_score']
            tech2 = technical_analysis['doc2_analysis']['technical_completeness_score']
            
            total_score_doc1 += tech1 * weights.get('TECHNICAL_COMPLETENESS', 0.2)
            total_score_doc2 += tech2 * weights.get('TECHNICAL_COMPLETENESS', 0.2)
        
        except Exception as e:
            logger.error(f"Error en análisis técnico: {e}")
        
        try:
            # Competitividad económica
            economic_analysis = self.analyze_economic_competitiveness(doc1_id, doc2_id)
            comprehensive_comparison['dimension_analyses']['economic_competitiveness'] = economic_analysis
            
            econ1 = economic_analysis['doc1_analysis']['economic_completeness']
            econ2 = economic_analysis['doc2_analysis']['economic_completeness']
            
            # Ajustar por precio si está disponible
            price1 = economic_analysis['doc1_analysis']['estimated_total_price']
            price2 = economic_analysis['doc2_analysis']['estimated_total_price']
            
            if price1 and price2:
                # El precio más bajo obtiene mayor score
                if price1 < price2:
                    econ1 += 20  # Bonus por mejor precio
                else:
                    econ2 += 20
            
            total_score_doc1 += econ1 * weights.get('ECONOMIC_COMPETITIVENESS', 0.2)
            total_score_doc2 += econ2 * weights.get('ECONOMIC_COMPETITIVENESS', 0.2)
        
        except Exception as e:
            logger.error(f"Error en análisis económico: {e}")
        
        # Scores finales
        comprehensive_comparison['overall_scores'] = {
            doc1_id: round(total_score_doc1, 2),
            doc2_id: round(total_score_doc2, 2)
        }
        
        # Determinar ganador
        if total_score_doc1 > total_score_doc2:
            comprehensive_comparison['winner'] = doc1_id
            score_difference = total_score_doc1 - total_score_doc2
        else:
            comprehensive_comparison['winner'] = doc2_id
            score_difference = total_score_doc2 - total_score_doc1
        
        # Resumen
        comprehensive_comparison['summary'] = {
            'winner': comprehensive_comparison['winner'],
            'score_difference': round(score_difference, 2),
            'close_competition': score_difference < 10,
            'decisive_winner': score_difference > 20,
            'analysis_completeness': len(comprehensive_comparison['dimension_analyses'])
        }
        
        # Generar recomendaciones
        comprehensive_comparison['recommendations'] = self._generate_comparison_recommendations(
            comprehensive_comparison
        )
        
        self.comparison_results[comprehensive_comparison['comparison_id']] = comprehensive_comparison
        logger.info(f"Comparación completada. Ganador: {comprehensive_comparison['winner']}")
        
        return comprehensive_comparison
    
    def compare_multiple_documents(self, doc_ids: List[str], 
                                 comparison_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Compara múltiples documentos usando matriz de comparación
        
        Args:
            doc_ids: Lista de IDs de documentos a comparar
            comparison_type: Tipo de comparación a realizar
            
        Returns:
            Matriz de comparación multi-dimensional
        """
        
        if len(doc_ids) < 2:
            raise ValueError("Se necesitan al menos 2 documentos para comparar")
        
        logger.info(f"Comparando {len(doc_ids)} documentos: {doc_ids}")
        
        multi_comparison = {
            'comparison_id': f"multi_{int(datetime.now().timestamp())}",
            'document_ids': doc_ids,
            'comparison_type': comparison_type,
            'comparison_timestamp': datetime.now().isoformat(),
            'pairwise_comparisons': {},
            'ranking': [],
            'similarity_matrix': {},
            'cluster_analysis': {},
            'summary_statistics': {}
        }
        
        # Realizar comparaciones por pares
        comparison_scores = defaultdict(list)
        
        for i, doc1_id in enumerate(doc_ids):
            for j, doc2_id in enumerate(doc_ids):
                if i < j:  # Evitar duplicados
                    comparison_key = f"{doc1_id}_vs_{doc2_id}"
                    
                    try:
                        if comparison_type == "comprehensive":
                            pairwise_result = self.comprehensive_comparison(doc1_id, doc2_id)
                        else:
                            pairwise_result = self.analyze_content_similarity(doc1_id, doc2_id)
                        
                        multi_comparison['pairwise_comparisons'][comparison_key] = pairwise_result
                        
                        # Acumular scores para ranking
                        if comparison_type == "comprehensive":
                            scores = pairwise_result['overall_scores']
                            comparison_scores[doc1_id].append(scores[doc1_id])
                            comparison_scores[doc2_id].append(scores[doc2_id])
                        
                    except Exception as e:
                        logger.error(f"Error en comparación {comparison_key}: {e}")
        
        # Calcular ranking basado en scores promedio
        if comparison_scores:
            avg_scores = {}
            for doc_id, scores in comparison_scores.items():
                avg_scores[doc_id] = sum(scores) / len(scores)
            
            ranking = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)
            multi_comparison['ranking'] = [
                {'rank': i+1, 'document_id': doc_id, 'average_score': score}
                for i, (doc_id, score) in enumerate(ranking)
            ]
        
        # Análisis de clustering (simplificado)
        if len(doc_ids) >= 3:
            multi_comparison['cluster_analysis'] = self._analyze_document_clusters(doc_ids)
        
        # Estadísticas resumen
        multi_comparison['summary_statistics'] = self._calculate_multi_comparison_stats(
            multi_comparison
        )
        
        return multi_comparison
    
    def _generate_comparison_recommendations(self, comparison_result: Dict) -> List[str]:
        """Genera recomendaciones basadas en los resultados de comparación"""
        
        recommendations = []
        
        winner = comparison_result.get('winner')
        score_diff = comparison_result.get('summary', {}).get('score_difference', 0)
        
        if winner:
            recommendations.append(f"Se recomienda seleccionar el documento {winner}")
        
        if score_diff < 5:
            recommendations.append("Diferencia mínima entre documentos. Considerar evaluación adicional.")
        elif score_diff > 30:
            recommendations.append("Diferencia significativa detectada. Decisión clara.")
        
        # Recomendaciones por dimensión
        dimension_analyses = comparison_result.get('dimension_analyses', {})
        
        if 'structural_compliance' in dimension_analyses:
            struct_analysis = dimension_analyses['structural_compliance']['comparative_analysis']
            if not struct_analysis.get('both_complete', False):
                recommendations.append("Verificar completitud documental antes de proceder.")
        
        if 'economic_competitiveness' in dimension_analyses:
            econ_analysis = dimension_analyses['economic_competitiveness']['comparative_analysis']
            price_comp = econ_analysis.get('price_comparison', {})
            if price_comp.get('both_prices_found', False):
                price_diff_pct = price_comp.get('price_difference_percentage', 0)
                if price_diff_pct > 20:
                    recommendations.append(f"Diferencia de precio significativa ({price_diff_pct:.1f}%). Considerar negociación.")
        
        return recommendations[:5]  # Máximo 5 recomendaciones
    
    def _analyze_document_clusters(self, doc_ids: List[str]) -> Dict[str, Any]:
        """Análisis simplificado de clustering de documentos"""
        
        # Análisis básico basado en similaridad de contenido
        clusters = {'similar_documents': [], 'outliers': []}
        
        try:
            # Calcular similitudes promedio para cada documento
            doc_similarities = {}
            
            for doc_id in doc_ids:
                similarities = []
                for other_doc_id in doc_ids:
                    if doc_id != other_doc_id:
                        # Usar comparación de contenido existente si está disponible
                        comparison_key = f"{doc_id}_vs_{other_doc_id}"
                        reverse_key = f"{other_doc_id}_vs_{doc_id}"
                        
                        # Buscar en resultados de comparaciones existentes
                        similarity_score = 50  # Default
                        
                        similarities.append(similarity_score)
                
                avg_similarity = sum(similarities) / len(similarities) if similarities else 0
                doc_similarities[doc_id] = avg_similarity
            
            # Identificar clusters basado en similitud promedio
            similarity_threshold = 60
            
            similar_docs = [doc_id for doc_id, sim in doc_similarities.items() if sim >= similarity_threshold]
            outlier_docs = [doc_id for doc_id, sim in doc_similarities.items() if sim < similarity_threshold]
            
            clusters['similar_documents'] = similar_docs
            clusters['outliers'] = outlier_docs
            clusters['similarity_scores'] = doc_similarities
            
        except Exception as e:
            logger.error(f"Error en análisis de clustering: {e}")
            clusters['error'] = str(e)
        
        return clusters
    
    def _calculate_multi_comparison_stats(self, multi_comparison: Dict) -> Dict[str, Any]:
        """Calcula estadísticas resumen para comparación múltiple"""
        
        stats = {
            'total_documents': len(multi_comparison['document_ids']),
            'total_comparisons': len(multi_comparison['pairwise_comparisons']),
            'successful_comparisons': 0,
            'failed_comparisons': 0,
            'average_score_range': 0
        }
        
        # Contar comparaciones exitosas
        for comparison in multi_comparison['pairwise_comparisons'].values():
            if 'error' not in comparison:
                stats['successful_comparisons'] += 1
            else:
                stats['failed_comparisons'] += 1
        
        # Calcular rango de scores si hay ranking
        if multi_comparison['ranking']:
            scores = [item['average_score'] for item in multi_comparison['ranking']]
            if scores:
                stats['highest_score'] = max(scores)
                stats['lowest_score'] = min(scores)
                stats['average_score'] = sum(scores) / len(scores)
                stats['score_range'] = max(scores) - min(scores)
        
        return stats
    
    def export_comparison_results(self, comparison_id: str, 
                                output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Exporta resultados de comparación a archivo JSON
        
        Args:
            comparison_id: ID de la comparación a exportar
            output_path: Ruta donde guardar el archivo
            
        Returns:
            Resultados de la comparación
        """
        
        if comparison_id not in self.comparison_results:
            raise ValueError(f"Comparación {comparison_id} no encontrada")
        
        results = self.comparison_results[comparison_id]
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Resultados de comparación guardados en: {output_path}")
        
        return results
    
    def clear_documents(self):
        """Limpia todos los documentos y comparaciones cargadas"""
        self.documents = {}
        self.comparison_results = {}
        logger.info("Todos los documentos y comparaciones han sido limpiados")
    
    def get_comparison_summary(self, comparison_id: str) -> Dict[str, Any]:
        """Obtiene un resumen ejecutivo de una comparación específica"""
        
        if comparison_id not in self.comparison_results:
            raise ValueError(f"Comparación {comparison_id} no encontrada")
        
        comparison = self.comparison_results[comparison_id]
        
        summary = {
            'comparison_id': comparison_id,
            'documents_compared': [comparison.get('doc1_id'), comparison.get('doc2_id')],
            'winner': comparison.get('winner'),
            'score_difference': comparison.get('summary', {}).get('score_difference', 0),
            'analysis_completeness': len(comparison.get('dimension_analyses', {})),
            'key_recommendations': comparison.get('recommendations', [])[:3],
            'timestamp': comparison.get('comparison_timestamp')
        }
        
        return summary