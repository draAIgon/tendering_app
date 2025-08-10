import fitz
import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from collections import defaultdict, Counter
import numpy as np

# Importar funciones del sistema de embeddings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.embedding import (
    get_embeddings_provider, 
    build_embeddings, 
    txt_to_documents
)
from .document_extraction import DocumentExtractionAgent
from langchain_chroma import Chroma

# Importar database manager para ubicaciones estandarizadas
from ..db_manager import get_standard_db_path
from langchain.schema import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentClassificationAgent:
    """
    Identifica las secciones clave del documento y organiza el contenido usando embeddings semánticos.
    Utiliza Chroma vector database para clasificación inteligente de contenido.
    """
    
    # Taxonomía de secciones para documentos de licitación
    SECTION_TAXONOMY = {
        'CONVOCATORIA': {
            'keywords': ['convocatoria', 'llamado', 'invitación', 'proceso', 'licitación'],
            'priority': 1,
            'description': 'Información general de la convocatoria'
        },
        'OBJETO': {
            'keywords': ['objeto', 'finalidad', 'propósito', 'contratación', 'servicio', 'obra'],
            'priority': 2,
            'description': 'Objeto del contrato y descripción del servicio'
        },
        'CONDICIONES_GENERALES': {
            'keywords': ['condiciones generales', 'disposiciones generales', 'normas generales'],
            'priority': 3,
            'description': 'Condiciones generales del proceso'
        },
        'CONDICIONES_PARTICULARES': {
            'keywords': ['condiciones particulares', 'disposiciones particulares', 'normas específicas'],
            'priority': 4,
            'description': 'Condiciones específicas del contrato'
        },
        'REQUISITOS_TECNICOS': {
            'keywords': ['requisitos técnicos', 'especificaciones técnicas', 'requerimientos técnicos'],
            'priority': 5,
            'description': 'Requisitos y especificaciones técnicas'
        },
        'CONDICIONES_ECONOMICAS': {
            'keywords': ['condiciones económicas', 'aspectos económicos', 'precio', 'valor', 'presupuesto'],
            'priority': 6,
            'description': 'Condiciones económicas y de precios'
        },
        'GARANTIAS': {
            'keywords': ['garantías', 'pólizas', 'seguros', 'fianzas'],
            'priority': 7,
            'description': 'Garantías y seguros requeridos'
        },
        'PLAZOS': {
            'keywords': ['plazos', 'cronograma', 'fechas', 'tiempo', 'duración'],
            'priority': 8,
            'description': 'Plazos y cronograma del proceso'
        },
        'FORMULARIOS': {
            'keywords': ['formulario', 'formato', 'anexo', 'plantilla'],
            'priority': 9,
            'description': 'Formularios y documentos requeridos'
        }
    }
    
    def __init__(self, document_path=None, vector_db_path=None, collection_name="DocumentClassification"):
        self.document_path = document_path
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
        self.document_sections = {}
        self.classified_content = {}
        
        logger.info(f"DocumentClassificationAgent iniciado con DB: {self.vector_db_path}")
        
    def initialize_embeddings(self, provider="auto", model=None):
        """Inicializa el proveedor de embeddings"""
        try:
            embeddings, used_provider, used_model = get_embeddings_provider(provider=provider, model=model)
            self.embeddings_provider = embeddings
            self.provider_info = {"provider": used_provider, "model": used_model}
            logger.info(f"Proveedor de embeddings inicializado: {used_provider} ({used_model})")
            return True
        except Exception as e:
            logger.error(f"Error inicializando embeddings: {e}")
            return False
    
    def load_or_create_vector_db(self, force_rebuild=False):
        """Carga o crea la base de datos vectorial"""
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
            return self._create_vector_db_from_document()
        else:
            logger.warning("No hay documento para procesar. BD vacía creada.")
            self.vector_db = Chroma(
                collection_name=self.collection_name,
                persist_directory=str(self.vector_db_path),
                embedding_function=self.embeddings_provider
            )
            return True
    
    def _create_vector_db_from_document(self):
        """Crea la BD vectorial desde el documento"""
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
            
            # Create documents with metadatas
            documents = txt_to_documents(txt_path, source_name=doc_path.stem)
            
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
            
            logger.info(f"BD vectorial creada con {len(documents)} fragmentos")
            return True
            
        except Exception as e:
            logger.error(f"Error creando BD vectorial: {e}")
            return False
    
    def classify_document_sections(self) -> Dict[str, List[Document]]:
        """Clasifica las secciones del documento usando similitud semántica"""
        if not self.vector_db:
            raise ValueError("Base de datos vectorial no inicializada")
        
        classified_sections = defaultdict(list)
        
        # Para cada sección en la taxonomía, buscar contenido relacionado
        for section_name, section_info in self.SECTION_TAXONOMY.items():
            # Crear query basada en keywords
            query = " ".join(section_info['keywords'])
            
            try:
                # Buscar documentos similares
                results = self.vector_db.similarity_search(
                    query, 
                    k=10,  # Top 10 resultados más similares
                    filter=None
                )
                
                # Filtrar por relevancia (score mínimo)
                for doc in results:
                    classified_sections[section_name].append(doc)
                
            except Exception as e:
                logger.warning(f"Error clasificando sección {section_name}: {e}")
        
        # También incluir secciones ya identificadas por el procesamiento inicial
        try:
            all_docs = self.vector_db.similarity_search("", k=1000)  # Obtener todos
            for doc in all_docs:
                if 'section' in doc.metadata:
                    original_section = doc.metadata['section']
                    if original_section not in classified_sections:
                        classified_sections[original_section].append(doc)
        except:
            pass
        
        self.document_sections = dict(classified_sections)
        logger.info(f"Documento clasificado en {len(classified_sections)} secciones")
        
        return self.document_sections
    
    def get_section_summary(self, section_name: str) -> Dict:
        """Obtiene resumen de una sección específica"""
        if section_name not in self.document_sections:
            return {"error": f"Sección {section_name} no encontrada"}
        
        docs = self.document_sections[section_name]
        
        summary = {
            "section_name": section_name,
            "document_count": len(docs),
            "total_characters": sum(len(doc.page_content) for doc in docs),
            "content_preview": docs[0].page_content[:200] + "..." if docs else "",
            "sources": list(set(doc.metadata.get('source', 'unknown') for doc in docs)),
            "taxonomy_info": self.SECTION_TAXONOMY.get(section_name, {})
        }
        
        return summary
    
    def get_document_structure(self) -> Dict:
        """Obtiene la estructura completa del documento"""
        if not self.document_sections:
            self.classify_document_sections()
        
        structure = {
            "total_sections": len(self.document_sections),
            "sections": {},
            "document_info": {
                "source": str(self.document_path) if self.document_path else "Unknown",
                "total_fragments": sum(len(docs) for docs in self.document_sections.values())
            }
        }
        
        # Ordenar secciones por prioridad
        sorted_sections = sorted(
            self.document_sections.keys(),
            key=lambda x: self.SECTION_TAXONOMY.get(x, {}).get('priority', 999)
        )
        
        for section in sorted_sections:
            structure["sections"][section] = self.get_section_summary(section)
        
        return structure
    
    def find_content_by_keywords(self, keywords: List[str], top_k: int = 5) -> List[Document]:
        """Busca contenido específico por palabras clave"""
        if not self.vector_db:
            raise ValueError("Base de datos vectorial no inicializada")
        
        query = " ".join(keywords)
        results = self.vector_db.similarity_search(query, k=top_k)
        
        logger.info(f"Encontrados {len(results)} documentos para keywords: {keywords}")
        return results
    
    def semantic_search(self, query: str, section_filter: Optional[str] = None, top_k: int = 5) -> List[Tuple[Document, float]]:
        """Búsqueda semántica en el contenido del documento"""
        if not self.vector_db:
            raise ValueError("Base de datos vectorial no inicializada")
        
        try:
            # Búsqueda con scores
            results = self.vector_db.similarity_search_with_score(query, k=top_k)
            
            # Filtrar por sección si se especifica
            if section_filter and section_filter in self.document_sections:
                section_content = set(doc.page_content for doc in self.document_sections[section_filter])
                results = [(doc, score) for doc, score in results if doc.page_content in section_content]
            
            logger.info(f"Búsqueda semántica: {len(results)} resultados para '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda semántica: {e}")
            return []
    
    def extract_key_requirements(self, section_name: str = "REQUISITOS_TECNICOS") -> List[str]:
        """Extrae requisitos clave de una sección específica"""
        if section_name not in self.document_sections:
            return []
        
        requirements = []
        docs = self.document_sections[section_name]
        
        # Patrones para identificar requisitos
        requirement_patterns = [
            r"(?:debe|deberá|requiere|necesario|obligatorio|indispensable)\s+([^.]+)",
            r"(?:requisito|requerimiento|condición):\s*([^.]+)",
            r"(?:el\s+(?:proveedor|contratista|oferente)\s+(?:debe|deberá))\s+([^.]+)"
        ]
        
        for doc in docs:
            text = doc.page_content.lower()
            for pattern in requirement_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                requirements.extend([match.strip() for match in matches if len(match.strip()) > 10])
        
        # Eliminar duplicados y ordenar por longitud
        unique_requirements = list(set(requirements))
        unique_requirements.sort(key=len, reverse=True)
        
        return unique_requirements[:10]  # Top 10 requisitos
    
    def get_classification_confidence(self) -> Dict[str, float]:
        """Calcula la confianza de la clasificación para cada sección"""
        confidence_scores = {}
        
        for section_name, docs in self.document_sections.items():
            if not docs:
                confidence_scores[section_name] = 0.0
                continue
            
            # Calcular confianza basada en coincidencia de keywords
            if section_name in self.SECTION_TAXONOMY:
                keywords = self.SECTION_TAXONOMY[section_name]['keywords']
                total_matches = 0
                total_possible = len(docs) * len(keywords)
                
                for doc in docs:
                    content_lower = doc.page_content.lower()
                    matches = sum(1 for keyword in keywords if keyword.lower() in content_lower)
                    total_matches += matches
                
                confidence_scores[section_name] = min(total_matches / total_possible * 100, 100.0)
            else:
                confidence_scores[section_name] = 50.0  # Confianza neutral para secciones no taxonomizadas
        
        return confidence_scores
    
    def export_classification_report(self, output_path: Optional[Path] = None) -> Dict:
        """Genera un reporte completo de clasificación"""
        if not self.document_sections:
            self.classify_document_sections()
        
        report = {
            "document_info": {
                "source": str(self.document_path) if self.document_path else "Unknown",
                "total_sections": len(self.document_sections),
                "total_fragments": sum(len(docs) for docs in self.document_sections.values()),
                "classification_timestamp": str(__import__('datetime').datetime.now())
            },
            "sections": self.get_document_structure()["sections"],
            "confidence_scores": self.get_classification_confidence(),
            "key_requirements": {}
        }
        
        # Extraer requisitos clave para cada sección relevante
        for section in ["REQUISITOS_TECNICOS", "CONDICIONES_ECONOMICAS", "GARANTIAS"]:
            if section in self.document_sections:
                report["key_requirements"][section] = self.extract_key_requirements(section)
        
        # Guardar reporte si se especifica ruta
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Reporte de clasificación guardado en: {output_path}")
        
        return report
    
    def process_document(self, provider="auto", model=None, force_rebuild=False) -> Dict:
        """Procesa completamente un documento: embeddings, clasificación y análisis"""
        logger.info(f"Iniciando procesamiento completo del documento: {self.document_path}")
        
        # 1. Inicializar embeddings
        if not self.initialize_embeddings(provider, model):
            return {"error": "No se pudo inicializar el sistema de embeddings"}
        
        # 2. Crear/cargar base de datos vectorial
        if not self.load_or_create_vector_db(force_rebuild):
            return {"error": "No se pudo crear la base de datos vectorial"}
        
        # 3. Clasificar secciones
        self.classify_document_sections()
        
        # 4. Generar reporte
        report = self.export_classification_report()
        
        logger.info("Procesamiento completo finalizado exitosamente")
        return report