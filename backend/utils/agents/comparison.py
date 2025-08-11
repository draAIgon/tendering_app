#!/usr/bin/env python3
"""
Unified Comparison Agent - Consolidates document and proposal comparison functionality
Combines the capabilities of ComparatorAgent and ProposalComparisonAgent into a single,
more powerful and maintainable agent.
"""

import re
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from collections import defaultdict

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Importar utilidades del paquete (rutas relativas consistentes con validator)
from ..db_manager import get_standard_db_path
from ..embedding import get_embeddings_provider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComparisonAgent:
    """
    Unified agent for document and proposal comparison.
    Supports both general document analysis and specialized tender evaluation.
    Combines functionality from ComparatorAgent and ProposalComparisonAgent.
    """

    # Comparison modes and criteria
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
    }

    def __init__(self, vector_db_path: Optional[Path] = None):
        self.vector_db_path = vector_db_path or get_standard_db_path('comparison', 'global')
        self.embeddings_provider = None
        self.vector_db = None
        self.documents: Dict[str, Any] = {}
        self.comparison_results: Dict[str, Any] = {}
        self.cached_embeddings: Dict[str, Any] = {}
        logger.info(f"ComparisonAgent iniciado con DB: {self.vector_db_path}")

    def initialize_embeddings(self, provider: str = "auto", model: Optional[str] = None) -> bool:
        """Inicializa embeddings para comparaciones semánticas."""
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
                self.vector_db.persist()
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

    def compare_multiple_documents(self, doc_ids: List[str],
                                   comparison_type: str = "comprehensive") -> Dict[str, Any]:
        """Compara múltiples documentos con matriz de comparaciones."""
        if len(doc_ids) < 2:
            raise ValueError("Se necesitan al menos 2 documentos para comparar")

        logger.info(f"Comparando {len(doc_ids)} documentos: {doc_ids}")

        multi_comparison: Dict[str, Any] = {
            'comparison_id': f"multi_{int(datetime.now().timestamp())}",
            'document_ids': doc_ids,
            'total_documents': len(doc_ids),
            'comparison_type': comparison_type,
            'comparison_timestamp': datetime.now().isoformat(),
            'pairwise_comparisons': {},
            'ranking': [],
            'similarity_matrix': {},
            'cluster_analysis': {},
            'summary_statistics': {}
        }

        comparison_scores: Dict[str, List[float]] = defaultdict(list)

        for i, doc1_id in enumerate(doc_ids):
            for j, doc2_id in enumerate(doc_ids):
                if i < j:
                    try:
                        comparison = self.comprehensive_comparison(doc1_id, doc2_id)
                        key = f"{doc1_id}_vs_{doc2_id}"
                        multi_comparison['pairwise_comparisons'][key] = comparison
                        scores = comparison['overall_scores']
                        comparison_scores[doc1_id].append(scores[doc1_id])
                        comparison_scores[doc2_id].append(scores[doc2_id])
                    except Exception as e:
                        logger.error(f"Error comparando {doc1_id} vs {doc2_id}: {e}")

        if comparison_scores:
            avg_scores: List[tuple] = []
            for doc_id in doc_ids:
                if comparison_scores.get(doc_id):
                    avg_scores.append((doc_id, sum(comparison_scores[doc_id]) / len(comparison_scores[doc_id])))
                else:
                    avg_scores.append((doc_id, 0.0))

            avg_scores.sort(key=lambda x: x[1], reverse=True)
            multi_comparison['ranking'] = [
                {'rank': i + 1, 'document_id': doc_id, 'average_score': round(score, 2),
                 'metadata': self.documents[doc_id]['metadata']}
                for i, (doc_id, score) in enumerate(avg_scores)
            ]

        if len(doc_ids) >= 3:
            multi_comparison['cluster_analysis'] = self._analyze_document_clusters(doc_ids)

        multi_comparison['summary_statistics'] = self._calculate_multi_comparison_stats(multi_comparison)
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