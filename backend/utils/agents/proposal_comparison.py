import logging
import re
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

class ProposalComparisonAgent:
    """
    Agente especializado en comparar múltiples propuestas de licitación
    usando análisis semántico y criterios técnicos, económicos y de cumplimiento.
    """
    
    # Criterios de comparación predefinidos
    COMPARISON_CRITERIA = {
        'TECHNICAL': {
            'weight': 0.4,
            'subcriteria': {
                'technical_specifications': {'weight': 0.3, 'keywords': ['especificaciones técnicas', 'requisitos técnicos', 'tecnología']},
                'experience': {'weight': 0.25, 'keywords': ['experiencia', 'proyectos anteriores', 'referencias']},
                'methodology': {'weight': 0.25, 'keywords': ['metodología', 'enfoque', 'plan de trabajo']},
                'team_qualifications': {'weight': 0.2, 'keywords': ['equipo', 'personal', 'certificaciones']}
            }
        },
        'ECONOMIC': {
            'weight': 0.35,
            'subcriteria': {
                'total_price': {'weight': 0.5, 'keywords': ['precio total', 'valor', 'costo']},
                'payment_terms': {'weight': 0.2, 'keywords': ['forma de pago', 'términos', 'anticipo']},
                'cost_breakdown': {'weight': 0.2, 'keywords': ['desglose', 'detalle de costos', 'presupuesto']},
                'value_for_money': {'weight': 0.1, 'keywords': ['relación precio-calidad', 'valor agregado']}
            }
        },
        'COMPLIANCE': {
            'weight': 0.25,
            'subcriteria': {
                'legal_compliance': {'weight': 0.4, 'keywords': ['cumplimiento legal', 'normatividad', 'regulaciones']},
                'document_completeness': {'weight': 0.3, 'keywords': ['documentos completos', 'requisitos', 'anexos']},
                'deadlines_compliance': {'weight': 0.3, 'keywords': ['plazos', 'cronograma', 'fechas de entrega']}
            }
        }
    }
    
    def __init__(self, vector_db_path: Optional[Path] = None):
        self.vector_db_path = vector_db_path or Path("./comparison_db")
        self.embeddings_provider = None
        self.vector_db = None
        self.proposals = {}
        self.comparison_results = {}
        
    def initialize_embeddings(self, provider="auto", model=None):
        """Inicializa el sistema de embeddings para comparación semántica"""
        try:
            self.embeddings_provider = get_embeddings_provider(provider=provider, model=model)
            logger.info("Sistema de embeddings inicializado para comparación")
            return True
        except Exception as e:
            logger.error(f"Error inicializando embeddings: {e}")
            return False
    
    def load_proposal(self, proposal_id: str, content: str, metadata: Optional[Dict] = None):
        """
        Carga una propuesta para comparación
        
        Args:
            proposal_id: Identificador único de la propuesta
            content: Contenido de la propuesta
            metadata: Metadatos adicionales (precio, empresa, etc.)
        """
        
        if not metadata:
            metadata = {}
        
        # Crear documentos para embeddings
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
                'proposal_id': proposal_id,
                'chunk_id': i,
                'content_type': 'proposal_text',
                **metadata
            }
            documents.append(Document(page_content=chunk, metadata=doc_metadata))
        
        self.proposals[proposal_id] = {
            'content': content,
            'metadata': metadata,
            'documents': documents,
            'loaded_at': datetime.now().isoformat()
        }
        
        logger.info(f"Propuesta {proposal_id} cargada con {len(documents)} chunks")
    
    def setup_vector_database(self):
        """Configura la base de datos vectorial con todas las propuestas"""
        if not self.embeddings_provider:
            raise ValueError("Debe inicializar los embeddings primero")
        
        if not self.proposals:
            raise ValueError("No hay propuestas cargadas")
        
        # Recopilar todos los documentos
        all_documents = []
        for proposal_id, proposal_data in self.proposals.items():
            all_documents.extend(proposal_data['documents'])
        
        # Crear base de datos vectorial
        self.vector_db = Chroma(
            collection_name="proposal_comparison",
            persist_directory=str(self.vector_db_path),
            embedding_function=self.embeddings_provider
        )
        
        self.vector_db.add_documents(all_documents)
        self.vector_db.persist()
        
        logger.info(f"Base de datos vectorial configurada con {len(all_documents)} documentos")
    
    def extract_technical_scores(self, proposal_id: str) -> Dict[str, float]:
        """Extrae scores técnicos de una propuesta específica"""
        
        if proposal_id not in self.proposals:
            raise ValueError(f"Propuesta {proposal_id} no encontrada")
        
        content = self.proposals[proposal_id]['content']
        technical_scores = {}
        
        for subcriterion, info in self.COMPARISON_CRITERIA['TECHNICAL']['subcriteria'].items():
            score = 0.0
            keyword_matches = 0
            
            for keyword in info['keywords']:
                # Contar menciones ponderadas por contexto
                matches = len(re.findall(rf'\b{re.escape(keyword)}\b', content, re.IGNORECASE))
                keyword_matches += matches
            
            # Búsqueda semántica si está disponible
            if self.vector_db:
                try:
                    query = ' '.join(info['keywords'])
                    results = self.vector_db.similarity_search(
                        query, 
                        k=5,
                        filter={'proposal_id': proposal_id}
                    )
                    semantic_relevance = len(results) * 10  # Score base por relevancia
                except:
                    semantic_relevance = 0
            else:
                semantic_relevance = 0
            
            # Calcular score combinado (0-100)
            raw_score = (keyword_matches * 5) + (semantic_relevance * 0.1)
            normalized_score = min(100, raw_score)
            
            technical_scores[subcriterion] = normalized_score
        
        return technical_scores
    
    def extract_economic_data(self, proposal_id: str) -> Dict[str, Any]:
        """Extrae datos económicos de una propuesta"""
        
        if proposal_id not in self.proposals:
            raise ValueError(f"Propuesta {proposal_id} no encontrada")
        
        content = self.proposals[proposal_id]['content']
        metadata = self.proposals[proposal_id]['metadata']
        
        economic_data = {
            'total_price': None,
            'currency': None,
            'payment_terms': [],
            'cost_breakdown': {},
            'value_added_services': []
        }
        
        # Extraer precio total
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
                except:
                    continue
        
        # Si no se encontró en contenido, usar metadata
        if economic_data['total_price'] is None and 'price' in metadata:
            economic_data['total_price'] = metadata['price']
        
        # Extraer términos de pago
        payment_patterns = [
            r'(anticipo\s+del?\s+\d+%)',
            r'(pago\s+contra\s+entrega)',
            r'(\d+%\s+al?\s+inicio)',
            r'(\d+\s+cuotas?)'
        ]
        
        for pattern in payment_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            economic_data['payment_terms'].extend(matches)
        
        return economic_data
    
    def calculate_compliance_score(self, proposal_id: str, rfp_requirements: Optional[List[str]] = None) -> Dict[str, float]:
        """Calcula score de cumplimiento de una propuesta"""
        
        if proposal_id not in self.proposals:
            raise ValueError(f"Propuesta {proposal_id} no encontrada")
        
        content = self.proposals[proposal_id]['content']
        compliance_scores = {}
        
        # Score de completitud documental
        required_sections = [
            'propuesta técnica', 'propuesta económica', 'experiencia',
            'certificaciones', 'cronograma', 'equipo de trabajo'
        ]
        
        found_sections = 0
        for section in required_sections:
            if re.search(rf'\b{re.escape(section)}\b', content, re.IGNORECASE):
                found_sections += 1
        
        compliance_scores['document_completeness'] = (found_sections / len(required_sections)) * 100
        
        # Score de cumplimiento legal
        legal_keywords = ['cumplimiento', 'normatividad', 'regulación', 'ley', 'decreto']
        legal_mentions = sum(len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE)) 
                           for keyword in legal_keywords)
        compliance_scores['legal_compliance'] = min(100, legal_mentions * 10)
        
        # Score de cumplimiento de plazos
        deadline_keywords = ['plazo', 'cronograma', 'entrega', 'fecha']
        deadline_mentions = sum(len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE)) 
                              for keyword in deadline_keywords)
        compliance_scores['deadlines_compliance'] = min(100, deadline_mentions * 15)
        
        return compliance_scores
    
    def semantic_similarity_analysis(self, proposal1_id: str, proposal2_id: str, 
                                   query: str = "propuesta técnica") -> Dict[str, Any]:
        """
        Analiza similaridad semántica entre dos propuestas
        
        Args:
            proposal1_id: ID de la primera propuesta
            proposal2_id: ID de la segunda propuesta  
            query: Query para enfocar la comparación
            
        Returns:
            Análisis de similaridad
        """
        
        if not self.vector_db:
            return {"error": "Base de datos vectorial no disponible"}
        
        try:
            # Obtener documentos relevantes para cada propuesta
            results1 = self.vector_db.similarity_search(
                query, k=5, filter={'proposal_id': proposal1_id}
            )
            results2 = self.vector_db.similarity_search(
                query, k=5, filter={'proposal_id': proposal2_id}
            )
            
            # Comparar contenido
            similarity_analysis = {
                'query': query,
                'proposal1_relevant_docs': len(results1),
                'proposal2_relevant_docs': len(results2),
                'common_themes': [],
                'unique_to_proposal1': [],
                'unique_to_proposal2': []
            }
            
            # Análisis básico de contenido común
            content1 = ' '.join([doc.page_content for doc in results1])
            content2 = ' '.join([doc.page_content for doc in results2])
            
            # Extraer conceptos clave (simplificado)
            keywords1 = set(re.findall(r'\b[a-záéíóúñ]{4,}\b', content1.lower()))
            keywords2 = set(re.findall(r'\b[a-záéíóúñ]{4,}\b', content2.lower()))
            
            common_keywords = keywords1.intersection(keywords2)
            unique1 = keywords1 - keywords2
            unique2 = keywords2 - keywords1
            
            similarity_analysis['common_themes'] = list(common_keywords)[:10]
            similarity_analysis['unique_to_proposal1'] = list(unique1)[:10]
            similarity_analysis['unique_to_proposal2'] = list(unique2)[:10]
            similarity_analysis['similarity_percentage'] = len(common_keywords) / max(len(keywords1), len(keywords2)) * 100
            
            return similarity_analysis
            
        except Exception as e:
            logger.error(f"Error en análisis de similaridad: {e}")
            return {"error": str(e)}
    
    def compare_proposals(self, rfp_requirements: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compara todas las propuestas cargadas usando criterios múltiples
        
        Args:
            rfp_requirements: Requisitos específicos del RFP
            
        Returns:
            Análisis comparativo completo
        """
        
        if len(self.proposals) < 2:
            raise ValueError("Se necesitan al menos 2 propuestas para comparar")
        
        logger.info(f"Comparando {len(self.proposals)} propuestas")
        
        comparison_results = {
            'comparison_timestamp': datetime.now().isoformat(),
            'total_proposals': len(self.proposals),
            'proposals': {},
            'ranking': [],
            'summary_statistics': {}
        }
        
        # Analizar cada propuesta individualmente
        for proposal_id in self.proposals.keys():
            logger.info(f"Analizando propuesta {proposal_id}")
            
            try:
                technical_scores = self.extract_technical_scores(proposal_id)
                economic_data = self.extract_economic_data(proposal_id)
                compliance_scores = self.calculate_compliance_score(proposal_id, rfp_requirements)
                
                # Calcular scores ponderados
                technical_weighted = sum(
                    score * self.COMPARISON_CRITERIA['TECHNICAL']['subcriteria'][sub]['weight']
                    for sub, score in technical_scores.items()
                )
                
                compliance_weighted = sum(
                    score * self.COMPARISON_CRITERIA['COMPLIANCE']['subcriteria'][sub]['weight']
                    for sub, score in compliance_scores.items()
                )
                
                # Score económico (simplificado - inverso del precio si está disponible)
                economic_score = 50  # Score neutral por defecto
                if economic_data['total_price']:
                    # Normalizar precio (el más bajo obtiene mayor score)
                    all_prices = [
                        self.extract_economic_data(pid).get('total_price', 0) 
                        for pid in self.proposals.keys()
                    ]
                    valid_prices = [p for p in all_prices if p > 0]
                    if valid_prices:
                        min_price = min(valid_prices)
                        max_price = max(valid_prices)
                        if max_price > min_price:
                            economic_score = 100 - ((economic_data['total_price'] - min_price) / 
                                                   (max_price - min_price)) * 100
                        else:
                            economic_score = 100
                
                # Score total ponderado
                total_score = (
                    technical_weighted * self.COMPARISON_CRITERIA['TECHNICAL']['weight'] +
                    economic_score * self.COMPARISON_CRITERIA['ECONOMIC']['weight'] +
                    compliance_weighted * self.COMPARISON_CRITERIA['COMPLIANCE']['weight']
                )
                
                proposal_analysis = {
                    'proposal_id': proposal_id,
                    'metadata': self.proposals[proposal_id]['metadata'],
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
                comparison_results['proposals'][proposal_id] = {
                    'error': str(e),
                    'scores': {'total_score': 0}
                }
        
        # Generar ranking
        valid_proposals = [
            (pid, data) for pid, data in comparison_results['proposals'].items() 
            if 'error' not in data
        ]
        
        ranking = sorted(
            valid_proposals,
            key=lambda x: x[1]['scores']['total_score'],
            reverse=True
        )
        
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
        
        # Estadísticas resumen
        scores = [data['scores']['total_score'] for _, data in valid_proposals]
        if scores:
            comparison_results['summary_statistics'] = {
                'average_score': sum(scores) / len(scores),
                'highest_score': max(scores),
                'lowest_score': min(scores),
                'score_spread': max(scores) - min(scores),
                'winner': ranking[0][0] if ranking else None
            }
        
        self.comparison_results = comparison_results
        logger.info("Comparación de propuestas completada")
        
        return comparison_results
    
    def _identify_strengths(self, technical: Dict, economic: float, compliance: Dict) -> List[str]:
        """Identifica fortalezas de una propuesta"""
        strengths = []
        
        # Fortalezas técnicas
        for criterion, score in technical.items():
            if score > 70:
                strengths.append(f"Excelente {criterion.replace('_', ' ')}")
        
        # Fortalezas económicas
        if economic > 80:
            strengths.append("Propuesta económica muy competitiva")
        
        # Fortalezas de cumplimiento
        for criterion, score in compliance.items():
            if score > 80:
                strengths.append(f"Alto cumplimiento en {criterion.replace('_', ' ')}")
        
        return strengths[:5]  # Máximo 5 fortalezas
    
    def _identify_weaknesses(self, technical: Dict, economic: float, compliance: Dict) -> List[str]:
        """Identifica debilidades de una propuesta"""
        weaknesses = []
        
        # Debilidades técnicas
        for criterion, score in technical.items():
            if score < 40:
                weaknesses.append(f"Deficiencia en {criterion.replace('_', ' ')}")
        
        # Debilidades económicas
        if economic < 30:
            weaknesses.append("Propuesta económica poco competitiva")
        
        # Debilidades de cumplimiento
        for criterion, score in compliance.items():
            if score < 50:
                weaknesses.append(f"Bajo cumplimiento en {criterion.replace('_', ' ')}")
        
        return weaknesses[:5]  # Máximo 5 debilidades
    
    def generate_comparison_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Genera reporte detallado de comparación
        
        Args:
            output_path: Ruta donde guardar el reporte
            
        Returns:
            Reporte de comparación
        """
        
        if not self.comparison_results:
            raise ValueError("No hay resultados de comparación disponibles")
        
        # Enriquecer reporte con análisis adicionales
        enhanced_report = self.comparison_results.copy()
        
        # Agregar comparaciones por pares para las top 3
        top_proposals = enhanced_report['ranking'][:3]
        pairwise_comparisons = []
        
        for i in range(len(top_proposals)):
            for j in range(i + 1, len(top_proposals)):
                prop1_id = top_proposals[i]['proposal_id']
                prop2_id = top_proposals[j]['proposal_id']
                
                similarity = self.semantic_similarity_analysis(prop1_id, prop2_id)
                pairwise_comparisons.append({
                    'proposal1': prop1_id,
                    'proposal2': prop2_id,
                    'similarity_analysis': similarity
                })
        
        enhanced_report['pairwise_comparisons'] = pairwise_comparisons
        
        # Recomendaciones
        enhanced_report['recommendations'] = self._generate_comparison_recommendations()
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Reporte de comparación guardado en: {output_path}")
        
        return enhanced_report
    
    def _generate_comparison_recommendations(self) -> List[str]:
        """Genera recomendaciones basadas en la comparación"""
        recommendations = []
        
        if not self.comparison_results or 'ranking' not in self.comparison_results:
            return recommendations
        
        ranking = self.comparison_results['ranking']
        
        if ranking:
            winner = ranking[0]
            recommendations.append(f"Se recomienda la propuesta {winner['proposal_id']} como ganadora con score {winner['total_score']:.1f}")
        
        if len(ranking) > 1:
            second = ranking[1]
            score_diff = ranking[0]['total_score'] - second['total_score']
            if score_diff < 10:
                recommendations.append(f"La diferencia con el segundo lugar es mínima ({score_diff:.1f} puntos). Considerar negociación.")
        
        # Recomendaciones por criterios
        proposals = self.comparison_results.get('proposals', {})
        
        # Mejor propuesta técnica
        technical_scores = {pid: data['scores']['technical_weighted'] 
                          for pid, data in proposals.items() 
                          if 'error' not in data}
        if technical_scores:
            best_technical = max(technical_scores.items(), key=lambda x: x[1])
            recommendations.append(f"Mejor propuesta técnica: {best_technical[0]} ({best_technical[1]:.1f} pts)")
        
        # Mejor propuesta económica
        economic_scores = {pid: data['scores']['economic'] 
                         for pid, data in proposals.items() 
                         if 'error' not in data}
        if economic_scores:
            best_economic = max(economic_scores.items(), key=lambda x: x[1])
            recommendations.append(f"Mejor propuesta económica: {best_economic[0]} ({best_economic[1]:.1f} pts)")
        
        return recommendations
    
    def clear_proposals(self):
        """Limpia todas las propuestas cargadas"""
        self.proposals = {}
        self.comparison_results = {}
        if self.vector_db:
            # Opcional: limpiar la base de datos vectorial
            pass
        logger.info("Todas las propuestas han sido limpiadas")