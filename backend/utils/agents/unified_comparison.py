#!/usr/bin/env python3
"""
Unified Comparison Agent - Consolidates document and proposal comparison functionality
Combines the capabilities of ComparatorAgent and ProposalComparisonAgent into a single, 
more powerful and maintainable agent.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import json
import numpy as np
from collections import defaultdict

# Import embedding system functions
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.embedding import get_embeddings_provider, txt_to_documents
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Import database manager for standardized locations
from ..db_manager import get_standard_db_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedComparisonAgent:
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
        # Use standardized database path
        if vector_db_path:
            self.vector_db_path = vector_db_path
        else:
            self.vector_db_path = get_standard_db_path('unified_comparison', 'global')
            
        self.embeddings_provider = None
        self.vector_db = None
        self.documents = {}  # Unified storage for all documents/proposals
        self.comparison_results = {}
        self.cached_embeddings = {}
        
        logger.info(f"UnifiedComparisonAgent iniciado con DB: {self.vector_db_path}")
        
    def initialize_embeddings(self, provider="auto", model=None):
        """Initialize embedding system for semantic comparisons"""
        try:
            embeddings_result = get_embeddings_provider(provider=provider, model=model)
            # The function returns a tuple (embeddings, provider, model)
            if isinstance(embeddings_result, tuple):
                self.embeddings_provider = embeddings_result[0]
                self.provider_used = embeddings_result[1]
                self.model_used = embeddings_result[2]
            else:
                self.embeddings_provider = embeddings_result
                self.provider_used = provider
                self.model_used = model
                
            logger.info("Sistema de embeddings inicializado para comparaciones")
            return True
        except Exception as e:
            logger.error(f"Error inicializando embeddings: {e}")
            return False
    
    def add_document(self, doc_id: str, content: str, doc_type: str = "proposal", 
                    metadata: Optional[Dict] = None):
        """
        Add a document to the comparison system
        
        Args:
            doc_id: Unique document identifier
            content: Document content
            doc_type: Type of document (proposal, rfp, contract, etc.)
            metadata: Additional metadata
        """
        if not content or not content.strip():
            raise ValueError(f"Empty content for document {doc_id}")
            
        if not metadata:
            metadata = {}
        
        # Process content into chunks for detailed analysis
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " "]
        )
        
        chunks = splitter.split_text(content)
        documents = []
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) > 50:  # Only include meaningful chunks
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
    
    # Alias methods for backward compatibility with different naming conventions
    def load_proposal(self, proposal_id: str, content: str, metadata: Optional[Dict] = None):
        """Load a proposal (alias for add_document with doc_type='proposal')"""
        return self.add_document(proposal_id, content, doc_type='proposal', metadata=metadata)
    
    def add_proposal(self, proposal_id: str, content: str, metadata: Optional[Dict] = None):
        """Add a proposal (alias for add_document with doc_type='proposal')"""
        return self.add_document(proposal_id, content, doc_type='proposal', metadata=metadata)
    
    def setup_vector_database(self):
        """Set up vector database with all documents"""
        if not self.embeddings_provider:
            logger.warning("Embeddings no disponibles, comparación limitada a análisis textual")
            return True
            
        if not self.documents:
            raise ValueError("No hay documentos cargados")
        
        # Collect all documents
        all_documents = []
        for doc_id, doc_data in self.documents.items():
            all_documents.extend(doc_data['documents'])
        
        # Create vector database
        self.vector_db = Chroma(
            collection_name="unified_comparison",
            persist_directory=str(self.vector_db_path),
            embedding_function=self.embeddings_provider
        )
        
        self.vector_db.add_documents(all_documents)
        # Note: In newer versions of Chroma, persistence is automatic
        
        logger.info(f"Base de datos vectorial configurada con {len(all_documents)} documentos")
        return True
    
    def analyze_content_similarity(self, doc1_id: str, doc2_id: str) -> Dict[str, Any]:
        """
        Analyze content similarity between two documents
        
        Args:
            doc1_id: ID of first document
            doc2_id: ID of second document
            
        Returns:
            Content similarity analysis
        """
        if doc1_id not in self.documents or doc2_id not in self.documents:
            raise ValueError("Uno o ambos documentos no encontrados")
        
        content1 = self.documents[doc1_id]['content']
        content2 = self.documents[doc2_id]['content']
        
        similarity_analysis = {
            'comparison_type': 'content_similarity',
            'doc1_id': doc1_id,
            'doc2_id': doc2_id,
            'comparison_timestamp': datetime.now().isoformat(),
            'semantic_similarity': 0.0,
            'metrics': {}
        }
        
        # Basic text analysis
        words1 = set(re.findall(r'\b\w+\b', content1.lower()))
        words2 = set(re.findall(r'\b\w+\b', content2.lower()))
        
        common_words = words1.intersection(words2)
        all_words = words1.union(words2)
        
        jaccard_similarity = len(common_words) / len(all_words) if all_words else 0
        
        similarity_analysis['metrics']['jaccard_similarity'] = jaccard_similarity
        similarity_analysis['metrics']['common_words_count'] = len(common_words)
        similarity_analysis['metrics']['unique_words_doc1'] = len(words1 - words2)
        similarity_analysis['metrics']['unique_words_doc2'] = len(words2 - words1)
        
        # Use Jaccard similarity as semantic similarity for now
        similarity_analysis['semantic_similarity'] = jaccard_similarity
        
        # Semantic analysis if available
        if self.vector_db:
            try:
                # Get relevant documents for each proposal
                results1 = self.vector_db.similarity_search(
                    content1[:500], k=3, filter={'doc_id': doc1_id}
                )
                results2 = self.vector_db.similarity_search(
                    content2[:500], k=3, filter={'doc_id': doc2_id}
                )
                
                # Simple semantic similarity based on common themes
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
        
        # Combined similarity score (0-100)
        if 'semantic_similarity' in similarity_analysis['metrics']:
            combined_score = (
                jaccard_similarity * 0.3 + 
                similarity_analysis['metrics']['semantic_similarity'] * 0.7
            ) * 100
        else:
            combined_score = jaccard_similarity * 100
        
        similarity_analysis['overall_similarity_score'] = round(combined_score, 2)
        
        return similarity_analysis
    
    def analyze_structural_compliance(self, doc1_id: str, doc2_id: str, 
                                    required_sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compare structural compliance between documents
        
        Args:
            doc1_id: ID of first document
            doc2_id: ID of second document
            required_sections: Required sections to evaluate
            
        Returns:
            Comparative structural compliance analysis
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
        
        # Analyze each document
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
                'estimated_completeness': min(100, len(content) / 5000 * 100)
            }
        
        # Comparative analysis
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
        Compare technical completeness between documents
        
        Args:
            doc1_id: ID of first document
            doc2_id: ID of second document
            
        Returns:
            Comparative technical completeness analysis
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
        
        # Analyze each document
        for doc_id, analysis_key in [(doc1_id, 'doc1_analysis'), (doc2_id, 'doc2_analysis')]:
            content = self.documents[doc_id]['content'].lower()
            
            keyword_matches = {}
            total_matches = 0
            
            for keyword in technical_keywords:
                matches = len(re.findall(rf'\b{re.escape(keyword)}\b', content, re.IGNORECASE))
                keyword_matches[keyword] = matches
                total_matches += matches
            
            # Look for specific technical patterns
            technical_patterns = [
                r'\d+\s*(gb|mb|ghz|mhz)',
                r'iso\s*\d+',
                r'version\s*\d+\.\d+',
                r'(mysql|postgresql|oracle|mongodb)',
                r'(java|python|\.net|php|javascript)',
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
        
        # Comparative analysis
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
        
        # Add required test keys
        technical_analysis['technical_completeness'] = {
            doc1_id: score1,
            doc2_id: score2
        }
        technical_analysis['completeness_comparison'] = technical_analysis['comparative_analysis']['technical_coverage_comparison']
        
        return technical_analysis
    
    def analyze_economic_competitiveness(self, doc1_id: str, doc2_id: str) -> Dict[str, Any]:
        """
        Compare economic competitiveness between proposals
        
        Args:
            doc1_id: ID of first document
            doc2_id: ID of second document
            
        Returns:
            Comparative economic competitiveness analysis
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
        
        # Patterns to extract economic information
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
        
        # Analyze each document
        for doc_id, analysis_key in [(doc1_id, 'doc1_analysis'), (doc2_id, 'doc2_analysis')]:
            content = self.documents[doc_id]['content']
            
            # Extract prices
            found_prices = []
            for pattern in price_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    try:
                        price = float(match.replace(',', ''))
                        found_prices.append(price)
                    except:
                        continue
            
            # Count economic keywords
            economic_mentions = 0
            for keyword in economic_keywords:
                economic_mentions += len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE))
            
            # Look for value-added terms
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
        
        # Comparative analysis
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
        
        # Compare economic completeness
        econ1 = economic_analysis['doc1_analysis']['economic_completeness']
        econ2 = economic_analysis['doc2_analysis']['economic_completeness']
        
        comparative_analysis['economic_completeness_comparison'] = {
            'more_complete': doc1_id if econ1 > econ2 else doc2_id,
            'completeness_difference': abs(econ1 - econ2),
            doc1_id: econ1,
            doc2_id: econ2
        }
        
        economic_analysis['comparative_analysis'] = comparative_analysis
        
        # Add required test keys
        economic_analysis['economic_competitiveness'] = {
            doc1_id: econ1,
            doc2_id: econ2
        }
        economic_analysis['cost_analysis'] = {
            doc1_id: price1 or 0,
            doc2_id: price2 or 0
        }
        
        return economic_analysis
    
    def extract_technical_scores(self, proposal_id: str) -> Dict[str, float]:
        """Extract technical scores from a specific proposal (tender evaluation mode)"""
        if proposal_id not in self.documents:
            raise ValueError(f"Propuesta {proposal_id} no encontrada")
        
        content = self.documents[proposal_id]['content']
        technical_scores = {}
        
        for subcriterion, info in self.COMPARISON_MODES['TENDER_EVALUATION']['TECHNICAL']['subcriteria'].items():
            score = 0.0
            keyword_matches = 0
            
            for keyword in info['keywords']:
                matches = len(re.findall(rf'\b{re.escape(keyword)}\b', content, re.IGNORECASE))
                keyword_matches += matches
            
            # Semantic search if available
            if self.vector_db:
                try:
                    query = ' '.join(info['keywords'])
                    results = self.vector_db.similarity_search(
                        query, 
                        k=5,
                        filter={'doc_id': proposal_id}
                    )
                    semantic_relevance = len(results) * 10
                except:
                    semantic_relevance = 0
            else:
                semantic_relevance = 0
            
            # Calculate combined score (0-100)
            raw_score = (keyword_matches * 5) + (semantic_relevance * 0.1)
            normalized_score = min(100, raw_score)
            
            technical_scores[subcriterion] = normalized_score
        
        return technical_scores
    
    def extract_economic_data(self, proposal_id: str) -> Dict[str, Any]:
        """Extract economic data from a proposal (tender evaluation mode)"""
        if proposal_id not in self.documents:
            raise ValueError(f"Propuesta {proposal_id} no encontrada")
        
        content = self.documents[proposal_id]['content']
        metadata = self.documents[proposal_id]['metadata']
        
        economic_data = {
            'total_price': None,
            'currency': None,
            'payment_terms': [],
            'cost_breakdown': {},
            'value_added_services': []
        }
        
        # Extract total price
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
        
        # If not found in content, use metadata
        if economic_data['total_price'] is None and 'price' in metadata:
            economic_data['total_price'] = metadata['price']
        
        # Extract payment terms
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
        """Calculate compliance score for a proposal (tender evaluation mode)"""
        if proposal_id not in self.documents:
            raise ValueError(f"Propuesta {proposal_id} no encontrada")
        
        content = self.documents[proposal_id]['content']
        compliance_scores = {}
        
        # Document completeness score
        required_sections = [
            'propuesta técnica', 'propuesta económica', 'experiencia',
            'certificaciones', 'cronograma', 'equipo de trabajo'
        ]
        
        found_sections = 0
        for section in required_sections:
            if re.search(rf'\b{re.escape(section)}\b', content, re.IGNORECASE):
                found_sections += 1
        
        compliance_scores['document_completeness'] = (found_sections / len(required_sections)) * 100
        
        # Legal compliance score
        legal_keywords = ['cumplimiento', 'normatividad', 'regulación', 'ley', 'decreto']
        legal_mentions = sum(len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE)) 
                           for keyword in legal_keywords)
        compliance_scores['legal_compliance'] = min(100, legal_mentions * 10)
        
        # Deadline compliance score
        deadline_keywords = ['plazo', 'cronograma', 'entrega', 'fecha']
        deadline_mentions = sum(len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE)) 
                              for keyword in deadline_keywords)
        compliance_scores['deadlines_compliance'] = min(100, deadline_mentions * 15)
        
        return compliance_scores
    
    def semantic_similarity_analysis(self, proposal1_id: str, proposal2_id: str, 
                                   query: str = "propuesta técnica") -> Dict[str, Any]:
        """
        Analyze semantic similarity between two proposals
        
        Args:
            proposal1_id: ID of first proposal
            proposal2_id: ID of second proposal  
            query: Query to focus the comparison
            
        Returns:
            Similarity analysis
        """
        if not self.vector_db:
            return {"error": "Base de datos vectorial no disponible"}
        
        try:
            # Get relevant documents for each proposal
            results1 = self.vector_db.similarity_search(
                query, k=5, filter={'doc_id': proposal1_id}
            )
            results2 = self.vector_db.similarity_search(
                query, k=5, filter={'doc_id': proposal2_id}
            )
            
            # Compare content
            similarity_analysis = {
                'query': query,
                'proposal1_relevant_docs': len(results1),
                'proposal2_relevant_docs': len(results2),
                'common_themes': [],
                'unique_to_proposal1': [],
                'unique_to_proposal2': []
            }
            
            # Basic content analysis
            content1 = ' '.join([doc.page_content for doc in results1])
            content2 = ' '.join([doc.page_content for doc in results2])
            
            # Extract key concepts
            keywords1 = set(re.findall(r'\b[a-záéíóúñ]{4,}\b', content1.lower()))
            keywords2 = set(re.findall(r'\b[a-záéíóúñ]{4,}\b', content2.lower()))
            
            common_keywords = keywords1.intersection(keywords2)
            unique1 = keywords1 - keywords2
            unique2 = keywords2 - keywords1
            
            similarity_analysis['common_themes'] = list(common_keywords)[:10]
            similarity_analysis['unique_to_proposal1'] = list(unique1)[:10]
            similarity_analysis['unique_to_proposal2'] = list(unique2)[:10]
            similarity_analysis['similarity_percentage'] = len(common_keywords) / max(len(keywords1), len(keywords2)) * 100 if (keywords1 or keywords2) else 0
            
            return similarity_analysis
            
        except Exception as e:
            logger.error(f"Error en análisis de similaridad: {e}")
            return {"error": str(e)}
    
    def comprehensive_comparison(self, doc1_id: str, doc2_id: str, 
                                mode: str = "GENERAL",
                                weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive comparison between two documents
        
        Args:
            doc1_id: ID of first document
            doc2_id: ID of second document
            mode: Comparison mode ('GENERAL' or 'TENDER_EVALUATION')
            weights: Custom weights for comparison dimensions
            
        Returns:
            Complete comparative analysis
        """
        if doc1_id not in self.documents or doc2_id not in self.documents:
            raise ValueError("Uno o ambos documentos no encontrados")
        
        if mode not in self.COMPARISON_MODES:
            raise ValueError(f"Modo de comparación no válido: {mode}")
        
        if not weights:
            if mode == "GENERAL":
                weights = {dim: info['weight'] for dim, info in self.COMPARISON_MODES[mode].items()}
            else:
                weights = {dim: info['weight'] for dim, info in self.COMPARISON_MODES[mode].items()}
        
        logger.info(f"Iniciando comparación comprehensiva entre {doc1_id} y {doc2_id} en modo {mode}")
        
        comprehensive_comparison = {
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
        
        total_score_doc1 = 0
        total_score_doc2 = 0
        
        if mode == "GENERAL":
            # Execute dimension-by-dimension analysis for general mode
            try:
                # Content similarity
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
                # Structural compliance
                structural_analysis = self.analyze_structural_compliance(doc1_id, doc2_id)
                comprehensive_comparison['dimension_analyses']['structural_compliance'] = structural_analysis
                
                struct1 = structural_analysis['doc1_analysis']['compliance_percentage']
                struct2 = structural_analysis['doc2_analysis']['compliance_percentage']
                
                total_score_doc1 += struct1 * weights.get('STRUCTURAL_COMPLIANCE', 0.25)
                total_score_doc2 += struct2 * weights.get('STRUCTURAL_COMPLIANCE', 0.25)
            
            except Exception as e:
                logger.error(f"Error en análisis estructural: {e}")
            
            try:
                # Technical completeness
                technical_analysis = self.analyze_technical_completeness(doc1_id, doc2_id)
                comprehensive_comparison['dimension_analyses']['technical_completeness'] = technical_analysis
                
                tech1 = technical_analysis['doc1_analysis']['technical_completeness_score']
                tech2 = technical_analysis['doc2_analysis']['technical_completeness_score']
                
                total_score_doc1 += tech1 * weights.get('TECHNICAL_COMPLETENESS', 0.25)
                total_score_doc2 += tech2 * weights.get('TECHNICAL_COMPLETENESS', 0.25)
            
            except Exception as e:
                logger.error(f"Error en análisis técnico: {e}")
            
            try:
                # Economic competitiveness
                economic_analysis = self.analyze_economic_competitiveness(doc1_id, doc2_id)
                comprehensive_comparison['dimension_analyses']['economic_competitiveness'] = economic_analysis
                
                econ1 = economic_analysis['doc1_analysis']['economic_completeness']
                econ2 = economic_analysis['doc2_analysis']['economic_completeness']
                
                total_score_doc1 += econ1 * weights.get('ECONOMIC_COMPETITIVENESS', 0.25)
                total_score_doc2 += econ2 * weights.get('ECONOMIC_COMPETITIVENESS', 0.25)
            
            except Exception as e:
                logger.error(f"Error en análisis económico: {e}")
        
        # Final scores
        comprehensive_comparison['overall_scores'] = {
            doc1_id: round(total_score_doc1, 2),
            doc2_id: round(total_score_doc2, 2)
        }
        
        # Determine winner
        if total_score_doc1 > total_score_doc2:
            comprehensive_comparison['winner'] = doc1_id
            score_difference = total_score_doc1 - total_score_doc2
        else:
            comprehensive_comparison['winner'] = doc2_id
            score_difference = total_score_doc2 - total_score_doc1
        
        # Summary
        comprehensive_comparison['summary'] = {
            'winner': comprehensive_comparison['winner'],
            'score_difference': round(score_difference, 2),
            'close_competition': score_difference < 10,
            'decisive_winner': score_difference > 20,
            'analysis_completeness': len(comprehensive_comparison['dimension_analyses'])
        }
        
        # Generate recommendations
        comprehensive_comparison['recommendations'] = self._generate_comparison_recommendations(
            comprehensive_comparison
        )
        
        self.comparison_results[comprehensive_comparison['comparison_id']] = comprehensive_comparison
        logger.info(f"Comparación completada. Ganador: {comprehensive_comparison['winner']}")
        
        return comprehensive_comparison
    
    def compare_multiple_documents(self, doc_ids: List[str], 
                                 comparison_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Compare multiple documents using comparison matrix
        
        Args:
            doc_ids: List of document IDs to compare
            comparison_type: Type of comparison to perform
            
        Returns:
            Multi-dimensional comparison matrix
        """
        if len(doc_ids) < 2:
            raise ValueError("Se necesitan al menos 2 documentos para comparar")
        
        logger.info(f"Comparando {len(doc_ids)} documentos: {doc_ids}")
        
        multi_comparison = {
            'comparison_id': f"multi_{int(datetime.now().timestamp())}",
            'document_ids': doc_ids,
            'total_documents': len(doc_ids),  # Add this for backward compatibility
            'comparison_type': comparison_type,
            'comparison_timestamp': datetime.now().isoformat(),
            'pairwise_comparisons': {},
            'ranking': [],
            'similarity_matrix': {},
            'cluster_analysis': {},
            'summary_statistics': {}
        }
        
        # Perform pairwise comparisons
        comparison_scores = defaultdict(list)
        
        for i, doc1_id in enumerate(doc_ids):
            for j, doc2_id in enumerate(doc_ids):
                if i < j:  # Avoid duplicate comparisons
                    try:
                        comparison = self.comprehensive_comparison(doc1_id, doc2_id)
                        comparison_key = f"{doc1_id}_vs_{doc2_id}"
                        multi_comparison['pairwise_comparisons'][comparison_key] = comparison
                        
                        # Collect scores for ranking
                        scores = comparison['overall_scores']
                        comparison_scores[doc1_id].append(scores[doc1_id])
                        comparison_scores[doc2_id].append(scores[doc2_id])
                        
                    except Exception as e:
                        logger.error(f"Error comparando {doc1_id} vs {doc2_id}: {e}")
        
        # Calculate ranking based on average scores
        if comparison_scores:
            avg_scores = []
            for doc_id in doc_ids:
                if doc_id in comparison_scores and comparison_scores[doc_id]:
                    avg_score = sum(comparison_scores[doc_id]) / len(comparison_scores[doc_id])
                    avg_scores.append((doc_id, avg_score))
                else:
                    avg_scores.append((doc_id, 0))
            
            # Sort by average score (descending)
            avg_scores.sort(key=lambda x: x[1], reverse=True)
            
            multi_comparison['ranking'] = [
                {
                    'rank': i + 1,
                    'document_id': doc_id,
                    'average_score': round(score, 2),
                    'metadata': self.documents[doc_id]['metadata']
                }
                for i, (doc_id, score) in enumerate(avg_scores)
            ]
        
        # Cluster analysis (simplified)
        if len(doc_ids) >= 3:
            multi_comparison['cluster_analysis'] = self._analyze_document_clusters(doc_ids)
        
        # Summary statistics
        multi_comparison['summary_statistics'] = self._calculate_multi_comparison_stats(
            multi_comparison
        )
        
        return multi_comparison
    
    def compare_proposals(self, rfp_requirements: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compare all loaded proposals using tender evaluation criteria
        
        Args:
            rfp_requirements: Specific RFP requirements
            
        Returns:
            Complete proposal comparison analysis
        """
        proposal_docs = {doc_id: doc_data for doc_id, doc_data in self.documents.items() 
                        if doc_data['doc_type'] == 'proposal'}
        
        if len(proposal_docs) < 2:
            raise ValueError("Se necesitan al menos 2 propuestas para comparar")
        
        logger.info(f"Comparando {len(proposal_docs)} propuestas")
        
        comparison_results = {
            'comparison_timestamp': datetime.now().isoformat(),
            'total_proposals': len(proposal_docs),
            'proposals': {},
            'ranking': [],
            'summary_statistics': {}
        }
        
        # Analyze each proposal individually
        for proposal_id in proposal_docs.keys():
            logger.info(f"Analizando propuesta {proposal_id}")
            
            try:
                technical_scores = self.extract_technical_scores(proposal_id)
                economic_data = self.extract_economic_data(proposal_id)
                compliance_scores = self.calculate_compliance_score(proposal_id, rfp_requirements)
                
                # Calculate weighted scores
                technical_weighted = sum(
                    score * self.COMPARISON_MODES['TENDER_EVALUATION']['TECHNICAL']['subcriteria'][sub]['weight']
                    for sub, score in technical_scores.items()
                )
                
                compliance_weighted = sum(
                    score * self.COMPARISON_MODES['TENDER_EVALUATION']['COMPLIANCE']['subcriteria'][sub]['weight']
                    for sub, score in compliance_scores.items()
                )
                
                # Economic score (simplified - lowest price gets highest score)
                economic_score = 50  # Neutral default
                if economic_data['total_price']:
                    all_prices = [
                        self.extract_economic_data(pid).get('total_price', 0) 
                        for pid in proposal_docs.keys()
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
                
                # Total weighted score
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
                comparison_results['proposals'][proposal_id] = {
                    'error': str(e),
                    'scores': {'total_score': 0}
                }
        
        # Generate ranking
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
        
        # Summary statistics
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
        """Identify proposal strengths"""
        strengths = []
        
        # Technical strengths
        for criterion, score in technical.items():
            if score > 70:
                strengths.append(f"Excelente {criterion.replace('_', ' ')}")
        
        # Economic strengths
        if economic > 80:
            strengths.append("Propuesta económica muy competitiva")
        
        # Compliance strengths
        for criterion, score in compliance.items():
            if score > 80:
                strengths.append(f"Alto cumplimiento en {criterion.replace('_', ' ')}")
        
        return strengths[:5]  # Maximum 5 strengths
    
    def _identify_weaknesses(self, technical: Dict, economic: float, compliance: Dict) -> List[str]:
        """Identify proposal weaknesses"""
        weaknesses = []
        
        # Technical weaknesses
        for criterion, score in technical.items():
            if score < 40:
                weaknesses.append(f"Deficiencia en {criterion.replace('_', ' ')}")
        
        # Economic weaknesses
        if economic < 30:
            weaknesses.append("Propuesta económica poco competitiva")
        
        # Compliance weaknesses
        for criterion, score in compliance.items():
            if score < 50:
                weaknesses.append(f"Bajo cumplimiento en {criterion.replace('_', ' ')}")
        
        return weaknesses[:5]  # Maximum 5 weaknesses
    
    def _generate_comparison_recommendations(self, comparison_result: Dict) -> List[str]:
        """Generate recommendations based on comparison results"""
        recommendations = []
        
        winner = comparison_result.get('winner')
        score_diff = comparison_result.get('summary', {}).get('score_difference', 0)
        
        if winner:
            recommendations.append(f"Se recomienda el documento {winner} como superior")
        
        if score_diff < 5:
            recommendations.append("La diferencia es mínima, considerar criterios adicionales")
        elif score_diff > 30:
            recommendations.append("Diferencia decisiva en favor del ganador")
        
        # Dimension-specific recommendations
        dimension_analyses = comparison_result.get('dimension_analyses', {})
        
        if 'structural_compliance' in dimension_analyses:
            struct_analysis = dimension_analyses['structural_compliance']
            better_compliance = struct_analysis['comparative_analysis']['better_compliance']
            recommendations.append(f"Mejor cumplimiento estructural: {better_compliance}")
        
        if 'economic_competitiveness' in dimension_analyses:
            econ_analysis = dimension_analyses['economic_competitiveness']
            if 'price_comparison' in econ_analysis['comparative_analysis']:
                price_comp = econ_analysis['comparative_analysis']['price_comparison']
                if price_comp.get('both_prices_found'):
                    cheaper = price_comp['cheaper_option']
                    recommendations.append(f"Opción económicamente más competitiva: {cheaper}")
        
        return recommendations[:5]  # Maximum 5 recommendations
    
    def _analyze_document_clusters(self, doc_ids: List[str]) -> Dict[str, Any]:
        """Simplified document clustering analysis"""
        clusters = {'similar_documents': [], 'outliers': []}
        
        try:
            # Basic analysis based on content similarity
            similarity_threshold = 0.7
            similar_pairs = []
            
            for i, doc1_id in enumerate(doc_ids):
                for j, doc2_id in enumerate(doc_ids):
                    if i < j:
                        try:
                            similarity = self.analyze_content_similarity(doc1_id, doc2_id)
                            if similarity['overall_similarity_score'] > similarity_threshold:
                                similar_pairs.append((doc1_id, doc2_id, similarity['overall_similarity_score']))
                        except:
                            continue
            
            clusters['similar_pairs'] = similar_pairs
            clusters['similarity_threshold'] = similarity_threshold
            
        except Exception as e:
            logger.error(f"Error en análisis de clusters: {e}")
            clusters['error'] = str(e)
        
        return clusters
    
    def _calculate_multi_comparison_stats(self, multi_comparison: Dict) -> Dict[str, Any]:
        """Calculate summary statistics for multi-comparison"""
        stats = {
            'total_documents': len(multi_comparison['document_ids']),
            'total_comparisons': len(multi_comparison['pairwise_comparisons']),
            'successful_comparisons': 0,
            'failed_comparisons': 0,
            'average_score_range': 0
        }
        
        # Count successful comparisons
        for comparison in multi_comparison['pairwise_comparisons'].values():
            if 'error' not in comparison:
                stats['successful_comparisons'] += 1
            else:
                stats['failed_comparisons'] += 1
        
        # Calculate score range if ranking exists
        if multi_comparison['ranking']:
            scores = [item['average_score'] for item in multi_comparison['ranking']]
            stats['average_score_range'] = max(scores) - min(scores) if scores else 0
        
        return stats
    
    def generate_comparison_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Generate detailed comparison report
        
        Args:
            output_path: Path to save the report
            
        Returns:
            Comparison report
        """
        if not self.comparison_results:
            raise ValueError("No hay resultados de comparación disponibles")
        
        # Enrich report with additional analyses
        enhanced_report = self.comparison_results.copy()
        
        # Add pairwise comparisons for top 3 if available
        if 'ranking' in enhanced_report and len(enhanced_report['ranking']) >= 2:
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
        
        # Add recommendations
        enhanced_report['recommendations'] = self._generate_proposal_recommendations()
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Reporte de comparación guardado en: {output_path}")
        
        return enhanced_report
    
    def _generate_proposal_recommendations(self) -> List[str]:
        """Generate recommendations based on proposal comparison"""
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
        
        # Recommendations by criteria
        proposals = self.comparison_results.get('proposals', {})
        
        # Best technical proposal
        technical_scores = {pid: data['scores']['technical_weighted'] 
                          for pid, data in proposals.items() 
                          if 'error' not in data}
        if technical_scores:
            best_technical = max(technical_scores.items(), key=lambda x: x[1])
            recommendations.append(f"Mejor propuesta técnica: {best_technical[0]} ({best_technical[1]:.1f} pts)")
        
        # Best economic proposal
        economic_scores = {pid: data['scores']['economic'] 
                         for pid, data in proposals.items() 
                         if 'error' not in data}
        if economic_scores:
            best_economic = max(economic_scores.items(), key=lambda x: x[1])
            recommendations.append(f"Mejor propuesta económica: {best_economic[0]} ({best_economic[1]:.1f} pts)")
        
        return recommendations
    
    def export_comparison_results(self, comparison_id: str, 
                                output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Export comparison results to JSON file
        
        Args:
            comparison_id: ID of comparison to export
            output_path: Path to save the file
            
        Returns:
            Comparison results
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
        """Clear all loaded documents and comparisons"""
        self.documents = {}
        self.comparison_results = {}
        self.cached_embeddings = {}
        logger.info("Todos los documentos y comparaciones han sido limpiados")
    
    def clear_proposals(self):
        """Clear all loaded proposals (alias for clear_documents)"""
        self.clear_documents()
    
    def get_comparison_summary(self, comparison_id: str) -> Dict[str, Any]:
        """Get executive summary of a specific comparison"""
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
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'embeddings_initialized': self.embeddings_provider is not None,
            'vector_db_initialized': self.vector_db is not None,
            'documents_loaded': len(self.documents),
            'comparison_results': len(self.comparison_results),
            'vector_db_path': str(self.vector_db_path),
            'supported_modes': list(self.COMPARISON_MODES.keys())
        }
