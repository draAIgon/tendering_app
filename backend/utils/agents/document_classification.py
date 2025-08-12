import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict
import json

# DSPy imports
import dspy
from dspy import Retrieve, Predict, Module, Signature, InputField, OutputField

# Importar funciones del sistema de embeddings y DSPy
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.dspy_service import initialize_dspy_and_embeddings, get_embeddings_instance, get_provider_info
from utils.embedding import txt_to_documents
from .document_extraction import DocumentExtractionAgent
from langchain_chroma import Chroma

# Importar database manager para ubicaciones estandarizadas
from ..db_manager import get_standard_db_path
from langchain.schema import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DSPy Signatures for document classification
class DocumentClassificationSignature(Signature):
    """Classify document sections based on tender/contract document taxonomy"""
    
    document_content: str = InputField(desc="Content of document section to classify")
    available_sections: str = InputField(desc="List of available section types for classification")
    
    section_type: str = OutputField(desc="The most appropriate section type from the taxonomy")
    confidence: float = OutputField(desc="Confidence score between 0.0 and 1.0")
    reasoning: str = OutputField(desc="Brief explanation for the classification decision")

class SectionClassificationSignature(Signature):
    """Classify individual document sections based on content and structure.
    
    CRITICAL CLASSIFICATION RULES (Spanish documents):
    - If content contains 'PLAZO DE EJECUCIÓN', 'plazo', 'ejecutará', 'meses', 'días' → PLAZOS
    - If content contains 'OBJETO DEL CONTRATO', 'objeto', 'antecedentes' → PLIEGO_GENERAL  
    - If content contains 'MONTO', 'PRECIO', 'PRESUPUESTO', 'PAGO' → CONDICIONES_ECONOMICAS
    - If content contains 'GARANTÍAS', 'FIANZAS', 'CAUCIONES' → GARANTIAS
    - If content contains technical specifications → REQUISITOS_TECNICOS
    - If content contains forms, annexes, 'RECEPCIÓN' → FORMULARIOS
    - If content contains invitation, bidding process → CONVOCATORIA
    - General/specific contractual conditions → CONDICIONES_GENERALES/CONDICIONES_PARTICULARES
    
    Available types: PLIEGO_GENERAL, REQUISITOS_TECNICOS, CONDICIONES_ECONOMICAS, PLAZOS, GARANTIAS, CONDICIONES_GENERALES, CONDICIONES_PARTICULARES, FORMULARIOS, CONVOCATORIA
    """
    
    section_content: str = InputField(desc="Content of the specific document section")
    section_position: int = InputField(desc="Position/order of section in document")
    available_types: str = InputField(desc="Available section types for classification")
    
    section_type: str = OutputField(desc="EXACT section type from available_types based on classification rules")
    confidence: float = OutputField(desc="Classification confidence (0.0-1.0)")
    key_indicators: str = OutputField(desc="Key words/phrases that influenced classification")
    summary: str = OutputField(desc="Brief summary of section content")

class RequirementExtractionSignature(Signature):
    """Extract key requirements from document sections"""
    
    section_content: str = InputField(desc="Content of document section")
    section_type: str = InputField(desc="Type of section being analyzed")
    
    requirements: List[str] = OutputField(desc="List of key requirements found in the section")
    priority_level: str = OutputField(desc="Priority level: HIGH, MEDIUM, or LOW")

class DocumentClassificationModule(Module):
    """DSPy module for document classification with ChromaDB integration and individual section analysis"""
    
    def __init__(self, vector_db: Chroma, taxonomy: Dict[str, Dict]):
        super().__init__()
        self.vector_db = vector_db
        self.taxonomy = taxonomy
        
        # Initialize DSPy components
        self.classify = Predict(DocumentClassificationSignature)
        self.classify_section = Predict(SectionClassificationSignature)
        self.extract_requirements = Predict(RequirementExtractionSignature)
        
    def forward(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """Process query and classify relevant document sections"""
        
        # Retrieve relevant documents from ChromaDB
        try:
            docs_with_scores = self.vector_db.similarity_search_with_score(query, k=top_k)
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return {"error": f"Document retrieval failed: {e}"}
        
        if not docs_with_scores:
            return {"error": "No relevant documents found"}
        
        # Prepare available sections for classification
        available_sections = ", ".join(self.taxonomy.keys())
        
        classified_sections = {}
        
        for doc, score in docs_with_scores:
            content = doc.page_content
            
            # Classify using DSPy
            try:
                classification_result = self.classify(
                    document_content=content,
                    available_sections=available_sections
                )
                
                section_type = classification_result.section_type
                confidence = float(classification_result.confidence) if hasattr(classification_result, 'confidence') else 0.8
                reasoning = classification_result.reasoning if hasattr(classification_result, 'reasoning') else ""
                
                # Convert ChromaDB distance to similarity score
                similarity_score = 1.0 - score if score <= 1.0 else max(0.0, 2.0 - score)
                
                if section_type not in classified_sections:
                    classified_sections[section_type] = []
                
                classified_sections[section_type].append({
                    'document': doc,
                    'dspy_confidence': confidence,
                    'similarity_score': similarity_score,
                    'reasoning': reasoning,
                    'combined_confidence': (confidence + similarity_score) / 2
                })
                
            except Exception as e:
                logger.warning(f"Error classifying document section: {e}")
                # Fallback to original metadata if available
                original_section = doc.metadata.get('section', 'GENERAL')
                similarity_score = 1.0 - score if score <= 1.0 else max(0.0, 2.0 - score)
                
                if original_section not in classified_sections:
                    classified_sections[original_section] = []
                
                classified_sections[original_section].append({
                    'document': doc,
                    'dspy_confidence': 0.5,  # Default confidence
                    'similarity_score': similarity_score,
                    'reasoning': "Fallback classification",
                    'combined_confidence': similarity_score * 0.75
                })
        
        return classified_sections
    
    def classify_individual_sections(self, text_content: str) -> Dict[str, Any]:
        """Classify each individual section detected in the document"""
        from ..embedding import detect_section_boundaries_semantic
        
        # Detect semantic section boundaries
        section_boundaries = detect_section_boundaries_semantic(text_content)
        
        if not section_boundaries:
            logger.warning("No section boundaries detected, using full document")
            return self._classify_full_document_as_section(text_content)
        
        available_types = ", ".join(self.taxonomy.keys())
        classified_sections = {}
        
        logger.info(f"Classifying {len(section_boundaries)} individual sections...")
        
        for i, (start_pos, detected_section, boundary_confidence) in enumerate(section_boundaries):
            # Determine end position for this section
            if i + 1 < len(section_boundaries):
                end_pos = section_boundaries[i + 1][0]
            else:
                end_pos = len(text_content)
            
            # Extract section content
            section_content = text_content[start_pos:end_pos].strip()
            
            if len(section_content) < 50:  # Skip very short sections
                continue
            
            try:
                # Use DSPy to classify this individual section
                section_result = self.classify_section(
                    section_content=section_content[:3000],  # Limit content for DSPy
                    section_position=i + 1,
                    available_types=available_types
                )
                
                # Extract results - prioritize boundary detection for high-confidence matches
                detected_section_type = getattr(section_result, 'section_type', detected_section) or detected_section
                dspy_confidence = float(getattr(section_result, 'confidence', 0.7))
                key_indicators = getattr(section_result, 'key_indicators', '')
                summary = getattr(section_result, 'summary', section_content[:200] + '...')
                
                # CRITICAL: Use semantic boundary result if it has high confidence (>= 0.7)
                # This prioritizes ordinal clause detection over DSPy classification
                if boundary_confidence >= 0.7:
                    final_section_type = detected_section
                    logger.info(f"Section {i+1}: Using semantic boundary result '{detected_section}' (confidence: {boundary_confidence:.3f}) over DSPy '{detected_section_type}'")
                else:
                    final_section_type = detected_section_type
                
                # Combine boundary detection confidence with DSPy confidence
                combined_confidence = max(boundary_confidence, dspy_confidence * 0.8)  # Give boundary detection priority
                
                section_info = {
                    'section_type': final_section_type,
                    'content': section_content,
                    'position': i + 1,
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'boundary_confidence': boundary_confidence,
                    'dspy_confidence': dspy_confidence,
                    'combined_confidence': combined_confidence,
                    'key_indicators': key_indicators,
                    'summary': summary,
                    'content_length': len(section_content),
                    'detected_by': 'semantic_boundary' if boundary_confidence > 0.3 else 'dspy_classification'
                }
                
                if final_section_type not in classified_sections:
                    classified_sections[final_section_type] = []
                
                classified_sections[final_section_type].append(section_info)
                
                logger.info(f"Section {i+1}: {final_section_type} (boundary: {boundary_confidence:.3f}, DSPy: {dspy_confidence:.3f}, combined: {combined_confidence:.3f})")
                
            except Exception as e:
                logger.warning(f"Error classifying section {i+1}: {e}")
                # Fallback to boundary detection result
                section_info = {
                    'section_type': detected_section,
                    'content': section_content,
                    'position': i + 1,
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'boundary_confidence': boundary_confidence,
                    'dspy_confidence': 0.0,
                    'combined_confidence': boundary_confidence * 0.8,
                    'key_indicators': 'boundary_detection_fallback',
                    'summary': section_content[:200] + '...',
                    'content_length': len(section_content),
                    'detected_by': 'boundary_fallback'
                }
                
                if detected_section not in classified_sections:
                    classified_sections[detected_section] = []
                
                classified_sections[detected_section].append(section_info)
        
        return classified_sections
    
    def _classify_full_document_as_section(self, text_content: str) -> Dict[str, Any]:
        """Fallback method when no sections are detected"""
        try:
            available_types = ", ".join(self.taxonomy.keys())
            
            section_result = self.classify_section(
                section_content=text_content[:3000],
                section_position=1,
                available_types=available_types
            )
            
            section_type = getattr(section_result, 'section_type', 'GENERAL')
            confidence = float(getattr(section_result, 'confidence', 0.5))
            
            return {
                section_type: [{
                    'section_type': section_type,
                    'content': text_content,
                    'position': 1,
                    'start_pos': 0,
                    'end_pos': len(text_content),
                    'boundary_confidence': 0.0,
                    'dspy_confidence': confidence,
                    'combined_confidence': confidence * 0.7,
                    'key_indicators': getattr(section_result, 'key_indicators', ''),
                    'summary': getattr(section_result, 'summary', text_content[:200] + '...'),
                    'content_length': len(text_content),
                    'detected_by': 'full_document_classification'
                }]
            }
        except Exception as e:
            logger.error(f"Error in full document classification: {e}")
            return {
                'GENERAL': [{
                    'section_type': 'GENERAL',
                    'content': text_content,
                    'position': 1,
                    'start_pos': 0,
                    'end_pos': len(text_content),
                    'boundary_confidence': 0.0,
                    'dspy_confidence': 0.0,
                    'combined_confidence': 0.3,
                    'key_indicators': 'fallback_classification',
                    'summary': text_content[:200] + '...',
                    'content_length': len(text_content),
                    'detected_by': 'fallback'
                }]
            }

class DocumentClassificationAgent:
    """
    DSPy-based document classification agent that uses ChromaDB for semantic search
    and language models for intelligent section classification.
    """
    
    # Enhanced Taxonomía de secciones para documentos de licitación
    SECTION_TAXONOMY = {
        'CONVOCATORIA': {
            'keywords': ['convocatoria', 'llamado', 'invitación', 'proceso', 'licitación'],
            'priority': 1,
            'description': 'Información general de la convocatoria y términos del proceso'
        },
        'OBJETO': {
            'keywords': ['objeto', 'finalidad', 'propósito', 'contratación', 'servicio', 'obra'],
            'priority': 2,
            'description': 'Objeto del contrato y descripción detallada del servicio o obra'
        },
        'CONDICIONES_GENERALES': {
            'keywords': ['condiciones generales', 'disposiciones generales', 'normas generales', 'marco normativo'],
            'priority': 3,
            'description': 'Condiciones generales aplicables al proceso de contratación'
        },
        'CONDICIONES_PARTICULARES': {
            'keywords': ['condiciones particulares', 'disposiciones particulares', 'normas específicas', 'condiciones especiales'],
            'priority': 4,
            'description': 'Condiciones específicas y particulares del contrato'
        },
        'REQUISITOS_TECNICOS': {
            'keywords': ['requisitos técnicos', 'especificaciones técnicas', 'requerimientos técnicos', 'aspectos técnicos'],
            'priority': 5,
            'description': 'Requisitos y especificaciones técnicas detalladas'
        },
        'CONDICIONES_ECONOMICAS': {
            'keywords': ['condiciones económicas', 'aspectos económicos', 'precio', 'valor', 'presupuesto', 'pagos'],
            'priority': 6,
            'description': 'Condiciones económicas, precios y forma de pago'
        },
        'GARANTIAS': {
            'keywords': ['garantías', 'pólizas', 'seguros', 'fianzas', 'avales'],
            'priority': 7,
            'description': 'Garantías, seguros y respaldos financieros requeridos'
        },
        'PLAZOS': {
            'keywords': ['plazos', 'cronograma', 'fechas', 'tiempo', 'duración', 'calendario', 'plazo', 'ejecución', 'ejecutará', 'meses', 'días'],
            'priority': 8,
            'description': 'Plazos, cronograma y fechas importantes del proceso'
        },
        'FORMULARIOS': {
            'keywords': ['formulario', 'formato', 'anexo', 'plantilla', 'documentos requeridos'],
            'priority': 9,
            'description': 'Formularios, anexos y documentos que debe presentar el oferente'
        }
    }
    
    def __init__(self, document_path=None, vector_db_path=None, collection_name="DocumentClassification",
                 llm_provider="auto", llm_model=None):
        self.document_path = document_path
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        
        # Use standardized database path
        if vector_db_path:
            self.vector_db_path = Path(vector_db_path)
        else:
            # Generate document ID for standardized path
            if document_path:
                doc_name = Path(document_path).stem
                self.vector_db_path = get_standard_db_path('classification', doc_name)
            else:
                self.vector_db_path = get_standard_db_path('classification', 'global')
                
        self.collection_name = collection_name
        self.embeddings_provider = None
        self.vector_db = None
        self.dspy_module = None
        self.document_sections = {}
        self.classification_results = {}
        
        logger.info(f"DSPy DocumentClassificationAgent iniciado con DB: {self.vector_db_path}")
        
    def initialize_dspy_and_embeddings(self, provider="auto", model=None):
        """Inicializa DSPy con el modelo apropiado y los embeddings usando el servicio centralizado"""
        try:
            success, info = initialize_dspy_and_embeddings(
                provider=provider, 
                model=model, 
                llm_provider=self.llm_provider
            )
            
            if success:
                self.embeddings_provider = get_embeddings_instance()
                self.provider_info = info
                logger.info(f"DSPy y embeddings inicializados: {info}")
                return True
            else:
                logger.error(f"Error inicializando DSPy y embeddings: {info}")
                return False
                
        except Exception as e:
            logger.error(f"Error inicializando DSPy y embeddings: {e}")
            return False
    
    def load_or_create_vector_db(self, force_rebuild=False):
        """Carga o crea la base de datos vectorial con chunking estándar"""
        if not self.embeddings_provider:
            raise ValueError("Debe inicializar los embeddings primero")
        
        # Si existe la BD y no se fuerza reconstrucción, cargarla
        if self.vector_db_path.exists() and not force_rebuild:
            try:
                self.vector_db = Chroma(
                    collection_name=self.collection_name,
                    persist_directory=str(self.vector_db_path),
                    embedding_function=self.embeddings_provider
                )
                logger.info(f"Base de datos vectorial cargada desde {self.vector_db_path}")
                return True
            except Exception as e:
                logger.warning(f"Error cargando BD existente: {e}")
        
        # Crear nueva BD si no existe o hay error
        if self.document_path:
            return self._create_vector_db_from_document_tiktoken()
        else:
            logger.warning("No hay documento para procesar. BD vacía creada.")
            self.vector_db = Chroma(
                collection_name=self.collection_name,
                persist_directory=str(self.vector_db_path),
                embedding_function=self.embeddings_provider
            )
            return True
    
    def _create_vector_db_from_document_tiktoken(self):
        """Crea la BD vectorial usando chunking estándar para documentos completos"""
        try:
            # Validate document path
            if not self.document_path or not Path(self.document_path).exists():
                raise ValueError(f"Document path does not exist: {self.document_path}")
            
            doc_path = Path(self.document_path)
            
            # Check if it's already a text file
            if doc_path.suffix.lower() == '.txt':
                # If it's already a text file, use it directly
                txt_path = doc_path
                logger.info(f"Using existing text file: {txt_path}")
            else:
                # Convert document to PDF if needed
                pdf_path = DocumentExtractionAgent.to_pdf_if_needed(self.document_path)
                
                # Extract text
                txt_path = DocumentExtractionAgent.pdf_to_txt(pdf_path)
            
            # Create documents with standard chunking (2000 chars, 100 overlap)
            documents = txt_to_documents(
                txt_path, 
                source_name=doc_path.stem,
                chunk_size=2000,
                chunk_overlap=100
            )
            
            # Ensure we have valid documents
            if not documents:
                raise ValueError(f"No documents could be created from {txt_path}")
            
            # Create vector database
            self.vector_db = Chroma(
                collection_name=self.collection_name,
                persist_directory=str(self.vector_db_path),
                embedding_function=self.embeddings_provider
            )
            
            # Add documents
            self.vector_db.add_documents(documents)
            
            # Note: persist() is no longer needed in ChromaDB 0.4+
            # The database auto-persists
            try:
                self.vector_db.persist()
            except AttributeError:
                # persist() method doesn't exist in newer versions
                pass
            
            logger.info(f"BD vectorial creada con {len(documents)} fragmentos usando chunking estándar")
            return True
            
        except Exception as e:
            logger.error(f"Error creando BD vectorial: {e}")
            return False
    
    def classify_document_sections_dspy(self, query: str = "") -> Dict[str, List[Dict]]:
        """Clasifica las secciones del documento usando DSPy y ChromaDB"""
        if not self.vector_db:
            raise ValueError("Base de datos vectorial no inicializada")
        
        # Initialize DSPy module if not done yet
        if not self.dspy_module:
            self.dspy_module = DocumentClassificationModule(self.vector_db, self.SECTION_TAXONOMY)
        
        # If no specific query, use a general query that covers all sections
        if not query:
            all_keywords = []
            for section_info in self.SECTION_TAXONOMY.values():
                all_keywords.extend(section_info['keywords'])
            query = " ".join(all_keywords[:20])  # Use top 20 keywords
        
        # Use DSPy module to classify
        classification_results = self.dspy_module.forward(query, top_k=50)  # Get more documents for comprehensive classification
        
        if "error" in classification_results:
            logger.error(f"Error en clasificación DSPy: {classification_results['error']}")
            return {}
        
        # Process and organize results
        processed_results = {}
        
        for section_name, section_docs in classification_results.items():
            if section_name not in processed_results:
                processed_results[section_name] = []
            
            for doc_info in section_docs:
                processed_results[section_name].append({
                    'document': doc_info['document'],
                    'dspy_confidence': doc_info['dspy_confidence'],
                    'similarity_score': doc_info['similarity_score'],
                    'combined_confidence': doc_info['combined_confidence'],
                    'reasoning': doc_info['reasoning']
                })
        
        # Sort each section by combined confidence
        for section_name in processed_results:
            processed_results[section_name].sort(
                key=lambda x: x['combined_confidence'], 
                reverse=True
            )
        
        self.classification_results = processed_results
        
        # Convert to document-only format for compatibility
        self.document_sections = {}
        for section_name, section_docs in processed_results.items():
            self.document_sections[section_name] = [doc_info['document'] for doc_info in section_docs]
        
        logger.info(f"Documento clasificado en {len(processed_results)} secciones usando DSPy")
        return processed_results
    
    def classify_individual_document_sections(self) -> Dict[str, Any]:
        """Classify each individual section of the document using semantic boundary detection + DSPy"""
        if not self.document_path:
            raise ValueError("Document path required for individual section classification")
        
        # Initialize DSPy module if not done yet
        if not self.dspy_module:
            if not self.initialize_dspy_and_embeddings():
                raise ValueError("Could not initialize DSPy system")
            self.dspy_module = DocumentClassificationModule(self.vector_db if self.vector_db else None, self.SECTION_TAXONOMY)
        
        # Get document text content
        doc_path = Path(self.document_path)
        
        # Convert to text if needed
        if doc_path.suffix.lower() == '.txt':
            txt_path = doc_path
        else:
            pdf_path = DocumentExtractionAgent.to_pdf_if_needed(self.document_path)
            txt_path = DocumentExtractionAgent.pdf_to_txt(pdf_path)
        
        # Read text content
        with open(txt_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Classify individual sections
        individual_sections = self.dspy_module.classify_individual_sections(text_content)
        
        # Store results
        self.individual_section_results = individual_sections
        
        logger.info(f"Document analyzed into {len(individual_sections)} distinct section types with {sum(len(sections) for sections in individual_sections.values())} total sections")
        
        return individual_sections
    
    def semantic_search_dspy(self, query: str, section_filter: Optional[str] = None, top_k: int = 5) -> List[Tuple[Document, float, str]]:
        """Búsqueda semántica mejorada con análisis DSPy"""
        if not self.vector_db:
            raise ValueError("Base de datos vectorial no inicializada")
        
        try:
            # Initialize DSPy module if not done yet
            if not self.dspy_module:
                self.dspy_module = DocumentClassificationModule(self.vector_db, self.SECTION_TAXONOMY)
            
            # Get classification for the query
            classification_results = self.dspy_module.forward(query, top_k=top_k * 2)
            
            if "error" in classification_results:
                # Fallback to basic similarity search
                results = self.vector_db.similarity_search_with_score(query, k=top_k)
                return [(doc, 1.0 - score if score <= 1.0 else max(0.0, 2.0 - score), "Basic similarity search") for doc, score in results]
            
            # Process and rank results
            all_results = []
            for section_name, section_docs in classification_results.items():
                if section_filter and section_filter != section_name:
                    continue
                    
                for doc_info in section_docs[:top_k]:  # Limit per section
                    all_results.append((
                        doc_info['document'],
                        doc_info['combined_confidence'],
                        f"DSPy: {doc_info['reasoning']}"
                    ))
            
            # Sort by combined confidence and limit to top_k
            all_results.sort(key=lambda x: x[1], reverse=True)
            final_results = all_results[:top_k]
            
            logger.info(f"DSPy semantic search: {len(final_results)} resultados para '{query}'")
            return final_results
            
        except Exception as e:
            logger.error(f"Error en búsqueda semántica DSPy: {e}")
            # Fallback to basic similarity search
            try:
                results = self.vector_db.similarity_search_with_score(query, k=top_k)
                return [(doc, 1.0 - score if score <= 1.0 else max(0.0, 2.0 - score), "Fallback similarity search") for doc, score in results]
            except Exception as e2:
                logger.error(f"Error en búsqueda de respaldo: {e2}")
                return []
    
    def extract_key_requirements_dspy(self, section_name: str) -> List[Dict[str, Any]]:
        """Extrae requisitos clave usando DSPy"""
        if section_name not in self.document_sections:
            return []
        
        if not self.dspy_module:
            self.dspy_module = DocumentClassificationModule(self.vector_db, self.SECTION_TAXONOMY)
        
        requirements_list = []
        docs = self.document_sections[section_name]
        
        for doc in docs[:5]:  # Analyze top 5 documents in section
            try:
                # Use DSPy to extract requirements
                requirements_result = self.dspy_module.extract_requirements(
                    section_content=doc.page_content,
                    section_type=section_name
                )
                
                if hasattr(requirements_result, 'requirements') and requirements_result.requirements:
                    priority = getattr(requirements_result, 'priority_level', 'MEDIUM')
                    
                    for req in requirements_result.requirements:
                        if req and len(req.strip()) > 10:  # Filter out short/empty requirements
                            requirements_list.append({
                                'requirement': req.strip(),
                                'priority': priority,
                                'source_section': section_name,
                                'source_document': doc.metadata.get('source', 'unknown')
                            })
                            
            except Exception as e:
                logger.warning(f"Error extracting requirements with DSPy: {e}")
                # Fallback to regex-based extraction
                requirement_patterns = [
                    r"(?:debe|deberá|requiere|necesario|obligatorio|indispensable)\s+([^.]+)",
                    r"(?:requisito|requerimiento|condición):\s*([^.]+)",
                    r"(?:el\s+(?:proveedor|contratista|oferente)\s+(?:debe|deberá))\s+([^.]+)"
                ]
                
                for pattern in requirement_patterns:
                    matches = re.findall(pattern, doc.page_content.lower(), re.IGNORECASE)
                    for match in matches:
                        if len(match.strip()) > 10:
                            requirements_list.append({
                                'requirement': match.strip(),
                                'priority': 'MEDIUM',
                                'source_section': section_name,
                                'source_document': doc.metadata.get('source', 'unknown'),
                                'extraction_method': 'regex_fallback'
                            })
        
        # Remove duplicates and sort by priority
        unique_requirements = []
        seen_requirements = set()
        
        for req in requirements_list:
            req_text = req['requirement'].lower()
            if req_text not in seen_requirements:
                seen_requirements.add(req_text)
                unique_requirements.append(req)
        
        # Sort by priority (HIGH, MEDIUM, LOW)
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        unique_requirements.sort(key=lambda x: priority_order.get(x['priority'], 1))
        
        return unique_requirements[:15]  # Return top 15 requirements
    
    def get_section_summary_dspy(self, section_name: str) -> Dict:
        """Obtiene resumen de una sección específica usando DSPy para mejorar la información"""
        if section_name not in self.document_sections:
            return {"error": f"Sección {section_name} no encontrada"}
        
        docs = self.document_sections[section_name]
        
        # Basic summary information
        summary = {
            "section_name": section_name,
            "document_count": len(docs),
            "total_characters": sum(len(doc.page_content) for doc in docs),
            "content_preview": docs[0].page_content[:200] + "..." if docs else "",
            "sources": list(set(doc.metadata.get('source', 'unknown') for doc in docs)),
            "taxonomy_info": self.SECTION_TAXONOMY.get(section_name, {}),
            "tiktoken_chunks": len([doc for doc in docs if doc.metadata.get('chunk_method') == 'standard'])
        }
        
        # Add DSPy classification confidence if available
        if hasattr(self, 'classification_results') and section_name in self.classification_results:
            section_results = self.classification_results[section_name]
            if section_results:
                avg_dspy_confidence = sum(doc_info['dspy_confidence'] for doc_info in section_results) / len(section_results)
                avg_similarity_score = sum(doc_info['similarity_score'] for doc_info in section_results) / len(section_results)
                avg_combined_confidence = sum(doc_info['combined_confidence'] for doc_info in section_results) / len(section_results)
                
                summary["dspy_analysis"] = {
                    "avg_dspy_confidence": avg_dspy_confidence,
                    "avg_similarity_score": avg_similarity_score,
                    "avg_combined_confidence": avg_combined_confidence,
                    "classification_reasoning": section_results[0]['reasoning'] if section_results else ""
                }
        
        return summary
    
    def get_document_structure_dspy(self) -> Dict:
        """Obtiene la estructura completa del documento con información DSPy"""
        if not self.document_sections:
            self.classify_document_sections_dspy()
        
        structure = {
            "total_sections": len(self.document_sections),
            "sections": {},
            "document_info": {
                "source": str(self.document_path) if self.document_path else "Unknown",
                "total_fragments": sum(len(docs) for docs in self.document_sections.values()),
                "embedding_approach": "standard_chunking",
                "chunk_size": 2000,
                "chunk_overlap": 100,
                "dspy_enabled": self.dspy_module is not None
            }
        }
        
        # Ordenar secciones por prioridad
        sorted_sections = sorted(
            self.document_sections.keys(),
            key=lambda x: self.SECTION_TAXONOMY.get(x, {}).get('priority', 999)
        )
        
        for section in sorted_sections:
            structure["sections"][section] = self.get_section_summary_dspy(section)
        
        return structure
    
    def export_classification_report_dspy(self, output_path: Optional[Path] = None) -> Dict:
        """Genera un reporte completo de clasificación con análisis DSPy"""
        if not self.document_sections:
            self.classify_document_sections_dspy()
        
        report = {
            "document_info": {
                "source": str(self.document_path) if self.document_path else "Unknown",
                "total_sections": len(self.document_sections),
                "total_fragments": sum(len(docs) for docs in self.document_sections.values()),
                "classification_timestamp": str(__import__('datetime').datetime.now()),
                "approach": "DSPy + ChromaDB + Standard Chunking",
                "embedding_provider": getattr(self, 'provider_info', {}),
                "dspy_enabled": self.dspy_module is not None
            },
            "sections": self.get_document_structure_dspy()["sections"],
            "dspy_requirements": {}
        }
        
        # Extraer requisitos clave para cada sección relevante usando DSPy
        for section in ["REQUISITOS_TECNICOS", "CONDICIONES_ECONOMICAS", "GARANTIAS"]:
            if section in self.document_sections:
                report["dspy_requirements"][section] = self.extract_key_requirements_dspy(section)
        
        # Guardar reporte si se especifica ruta
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Reporte de clasificación DSPy guardado en: {output_path}")
        
        return report
    
    def process_document_dspy(self, provider="auto", model=None, force_rebuild=False) -> Dict:
        """Procesa completamente un documento usando DSPy: embeddings, clasificación y análisis de secciones individuales"""
        logger.info(f"Iniciando procesamiento completo DSPy del documento: {self.document_path}")
        
        # 1. Inicializar DSPy y embeddings
        if not self.initialize_dspy_and_embeddings(provider, model):
            return {"error": "No se pudo inicializar DSPy y el sistema de embeddings"}
        
        # 2. Crear/cargar base de datos vectorial con chunking estándar
        if not self.load_or_create_vector_db(force_rebuild):
            return {"error": "No se pudo crear la base de datos vectorial"}
        
        # 3. Classify individual sections using semantic boundaries + DSPy
        try:
            individual_sections = self.classify_individual_document_sections()
        except Exception as e:
            logger.warning(f"Error in individual section classification: {e}")
            individual_sections = {}
        
        # 4. Clasificar secciones usando DSPy (método original para chunks)
        self.classify_document_sections_dspy()
        
        # 5. Generar reporte DSPy completo
        report = self.export_classification_report_dspy()
        
        # 6. Add individual section analysis to report
        report["individual_sections"] = {
            "section_count": len(individual_sections),
            "total_sections_detected": sum(len(sections) for sections in individual_sections.values()),
            "sections": individual_sections
        }
        
        # 7. Add section summaries
        section_summaries = {}
        for section_type, sections_list in individual_sections.items():
            if sections_list:
                # Calculate averages and stats for this section type
                avg_confidence = sum(s['combined_confidence'] for s in sections_list) / len(sections_list)
                total_content_length = sum(s['content_length'] for s in sections_list)
                
                section_summaries[section_type] = {
                    "instances": len(sections_list),
                    "average_confidence": avg_confidence,
                    "total_content_length": total_content_length,
                    "key_indicators": list(set(s['key_indicators'] for s in sections_list if s['key_indicators'])),
                    "detection_methods": list(set(s['detected_by'] for s in sections_list))
                }
        
        report["individual_sections"]["summary_by_type"] = section_summaries
        
        logger.info("Procesamiento completo DSPy finalizado exitosamente")
        return report

    def get_individual_sections(self, section_type: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed information about individual sections"""
        if not hasattr(self, 'individual_section_results'):
            logger.info("Individual sections not yet analyzed, running classification...")
            self.classify_individual_document_sections()
        
        if section_type:
            return self.individual_section_results.get(section_type, [])
        
        return self.individual_section_results
    
    def get_section_content(self, section_type: str, section_index: int = 0) -> Optional[str]:
        """Get the content of a specific section by type and index"""
        individual_sections = self.get_individual_sections(section_type)
        
        if individual_sections and section_index < len(individual_sections):
            return individual_sections[section_index]['content']
        
        return None
    
    def get_sections_summary(self) -> Dict[str, Any]:
        """Get a summary of all individual sections detected"""
        individual_sections = self.get_individual_sections()
        
        summary = {
            "total_section_types": len(individual_sections),
            "total_sections": sum(len(sections) for sections in individual_sections.values()),
            "section_breakdown": {}
        }
        
        for section_type, sections_list in individual_sections.items():
            if sections_list:
                confidences = [s['combined_confidence'] for s in sections_list]
                summary["section_breakdown"][section_type] = {
                    "count": len(sections_list),
                    "avg_confidence": sum(confidences) / len(confidences),
                    "min_confidence": min(confidences),
                    "max_confidence": max(confidences),
                    "total_content_length": sum(s['content_length'] for s in sections_list)
                }
        
        return summary

    # Backward compatibility methods (delegates to DSPy versions)
    def initialize_embeddings(self, provider="auto", model=None):
        """Compatibility method - delegates to DSPy version"""
        return self.initialize_dspy_and_embeddings(provider, model)
    
    def classify_document_sections(self) -> Dict[str, List[Document]]:
        """Compatibility method - delegates to DSPy version"""
        self.classify_document_sections_dspy()
        return self.document_sections
    
    def semantic_search(self, query: str, section_filter: Optional[str] = None, top_k: int = 5) -> List[Tuple[Document, float]]:
        """Compatibility method - delegates to DSPy version"""
        results = self.semantic_search_dspy(query, section_filter, top_k)
        return [(doc, confidence) for doc, confidence, reasoning in results]
    
    def extract_key_requirements(self, section_name: str = "REQUISITOS_TECNICOS") -> List[str]:
        """Compatibility method - delegates to DSPy version"""
        dspy_requirements = self.extract_key_requirements_dspy(section_name)
        return [req['requirement'] for req in dspy_requirements]
    
    def get_section_summary(self, section_name: str) -> Dict:
        """Compatibility method - delegates to DSPy version"""
        return self.get_section_summary_dspy(section_name)
    
    def get_document_structure(self) -> Dict:
        """Compatibility method - delegates to DSPy version"""
        return self.get_document_structure_dspy()
    
    def export_classification_report(self, output_path: Optional[Path] = None) -> Dict:
        """Compatibility method - delegates to DSPy version"""
        return self.export_classification_report_dspy(output_path)
    
    def process_document(self, provider="auto", model=None, force_rebuild=False) -> Dict:
        """Compatibility method - delegates to DSPy version"""
        return self.process_document_dspy(provider, model, force_rebuild)
