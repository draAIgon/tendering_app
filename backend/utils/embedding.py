from pathlib import Path
import re
import subprocess
from typing import List, Dict, Optional, Union, Tuple
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import os
import logging
from collections import defaultdict
import hashlib
import requests
from typing import List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from langchain_ollama import OllamaEmbeddings
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.warning("OllamaEmbeddings no disponible. Instala: pip install langchain-ollama")

try:
    import tiktoken  
    _ENC = tiktoken.get_encoding("cl100k_base")
except Exception:
    _ENC = None

#Verifica Ollama
def verificar_ollama() -> bool:
    """Verifica si OLLAMA está disponible y funcionando."""
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            version_info = response.json()
            logger.info(f"OLLAMA disponible - Versión: {version_info.get('version', 'desconocida')}")
            return True
    except requests.exceptions.RequestException:
        pass

    logger.warning("OLLAMA no está ejecutándose en http://localhost:11434")
    logger.info("Instalación rápida OLLAMA:")
    logger.info("1) https://ollama.ai/download")
    logger.info("2) ollama serve")
    logger.info("3) ollama pull nomic-embed-text")
    return False

#Modelo de OLLAMA       
def listar_modelos_ollama() -> List[str]:
    """Lista los modelos disponibles en OLLAMA."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            modelos = response.json()
            modelos_disponibles = [modelo["name"] for modelo in modelos.get("models", [])]
            logger.info(f"Modelos OLLAMA disponibles: {modelos_disponibles}")
            return modelos_disponibles
    except requests.exceptions.RequestException as e:
        logger.error(f"Error obteniendo modelos OLLAMA: {e}")
    return []

#Permite usar OpenAI si OLLAMA no está disponible
def get_embeddings_provider(provider: str = "auto", model: Optional[str] = None):
    """
    Devuelve (embeddings, provider_usado, model_usado).
    Prioriza OLLAMA si está disponible cuando provider='auto'.
    """
    chosen_provider = provider
    chosen_model = model

    if provider == "auto":
        if OLLAMA_AVAILABLE and verificar_ollama():
            chosen_provider = "ollama"
        else:
            chosen_provider = "openai"

    if chosen_provider == "ollama":
        if not OLLAMA_AVAILABLE:
            raise ImportError("OLLAMA no está instalado. pip install langchain-ollama")
        if not verificar_ollama():
            raise ConnectionError("OLLAMA no está ejecutándose")

        if not chosen_model:
            modelos = listar_modelos_ollama()
            if "nomic-embed-text:latest" in modelos:
                chosen_model = "nomic-embed-text"
            elif any("embed" in m for m in modelos):
                chosen_model = next(m for m in modelos if "embed" in m)
            else:
                logger.warning("No se encontró modelo de embeddings. Descargando nomic-embed-text...")
                subprocess.run(["ollama", "pull", "nomic-embed-text"], check=True)
                chosen_model = "nomic-embed-text"

        logger.info(f"Usando OLLAMA con modelo: {chosen_model}")
        return OllamaEmbeddings(model=chosen_model), "ollama", chosen_model

    elif chosen_provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("Configura la variable de entorno OPENAI_API_KEY para usar OpenAI.")
        chosen_model = chosen_model or "text-embedding-3-small"
        logger.info(f"Usando OpenAI con modelo: {chosen_model}")
        return OpenAIEmbeddings(model=chosen_model), "openai", chosen_model

    else:
        raise ValueError(f"Proveedor no soportado: {chosen_provider}. Use 'openai', 'ollama' o 'auto'.")

#Crea un splitter para dividir el texto en chunks simples
def make_splitter(chunk_size: int = 2000, chunk_overlap: int = 1000) -> RecursiveCharacterTextSplitter:
    """
    Crea un splitter simplificado con parámetros configurables.
    Usa solo separadores naturales del texto sin regex complejos.
    
    Args:
        chunk_size: Tamaño de cada chunk en caracteres
        chunk_overlap: Overlap entre chunks en caracteres
    """
    # Separadores naturales simples - sin regex complejos
    simple_separators = ["\n\n", "\n", ". ", " ", ""]
    
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=simple_separators,
        length_function=len,
        is_separator_regex=False,
    )

def detect_section_boundaries_semantic(text: str) -> List[Tuple[int, str, float]]:
    """
    Detect section boundaries using semantic cues and text analysis.
    Returns list of (position, section_name, confidence) tuples.
    """
    import re
    
    def get_ordinal_position(line_text: str) -> Optional[int]:
        """Extract ordinal position from clause headers (primera=1, segunda=2, etc.)"""
        line_lower = line_text.lower()
        
        # Spanish ordinal mapping
        ordinal_map = {
            'primera': 1, 'primero': 1, 'primer': 1,
            'segunda': 2, 'segundo': 2, 
            'tercera': 3, 'tercero': 3,
            'cuarta': 4, 'cuarto': 4,
            'quinta': 5, 'quinto': 5,
            'sexta': 6, 'sexto': 6,
            'séptima': 7, 'septima': 7, 'séptimo': 7, 'septimo': 7,
            'octava': 8, 'octavo': 8,
            'novena': 9, 'noveno': 9,
            'décima': 10, 'decima': 10, 'décimo': 10, 'decimo': 10
        }
        
        # Check for Spanish ordinals
        for ordinal, position in ordinal_map.items():
            if ordinal in line_lower:
                return position
        
        # Check for Arabic numerals (1., 2., etc.)
        arabic_match = re.match(r'^(\d+)\.?\s', line_text.strip())
        if arabic_match:
            return int(arabic_match.group(1))
            
        # Check for Roman numerals (I., II., etc.)
        roman_match = re.match(r'^([IVXLCDM]+)\.?\s', line_text.strip())
        if roman_match:
            roman_to_int = {
                'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
                'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10
            }
            return roman_to_int.get(roman_match.group(1), None)
        
        return None
    
    def map_position_to_section(position: int, line_content: str) -> Optional[str]:
        """Map ordinal position to most likely section type based on common contract structure"""
        line_lower = line_content.lower()
        
        # Position-based mapping with content validation
        position_mapping = {
            1: [('objeto', ['objeto', 'contrato', 'denominada', 'encarga', 'ejecución']), 
                ('convocatoria', ['convocatoria', 'proceso', 'licitación'])],
            2: [('condiciones_economicas', ['monto', 'valor', 'precio', 'asciende', 'total']),
                ('objeto', ['objeto', 'alcance', 'descripción'])],
            3: [('plazos', ['plazo', 'tiempo', 'ejecutará', 'meses', 'días']),
                ('requisitos_tecnicos', ['requisitos', 'especificaciones'])],
            4: [('garantias', ['garantía', 'garantías', 'póliza', 'fianza', 'cumplimiento']),
                ('condiciones_economicas', ['condiciones', 'económicas'])],
            5: [('condiciones_generales', ['anticipo', 'entregará', 'amortizable']),
                ('garantias', ['garantía', 'seguros'])],
            6: [('condiciones_generales', ['multas', 'penalizaciones', 'sanciones']),
                ('plazos', ['cronograma', 'fechas'])],
            7: [('formularios', ['recepción', 'entrega', 'documentos']),
                ('condiciones_generales', ['multas', 'terminación'])],
            8: [('condiciones_particulares', ['controversias', 'resolución', 'jurisdicción']),
                ('formularios', ['documentación'])],
            9: [('condiciones_particulares', ['legislación', 'normativa', 'aplicable']),
                ('condiciones_generales', ['disposiciones'])]
        }
        
        if position in position_mapping:
            for section_name, keywords in position_mapping[position]:
                if any(keyword in line_lower for keyword in keywords):
                    return section_name.upper()
                    
        # Default fallback based on position
        if position == 1:
            return 'OBJETO'
        elif position == 2:
            return 'CONDICIONES_ECONOMICAS'
        elif position == 3:
            return 'PLAZOS'
        elif position == 4:
            return 'GARANTIAS'
        else:
            return 'CONDICIONES_GENERALES'
    
    boundaries = []
    lines = text.split('\n')
    
    # Define semantic patterns for different section types (updated for contracts and RFPs)
    semantic_patterns = {
        'CONVOCATORIA': {
            'keywords': ['convocatoria', 'llamado', 'invitación', 'proceso', 'licitación', 'concurso', 'información', 'general'],
            'context_words': ['pública', 'privada', 'internacional', 'nacional', 'abierta', 'participar'],
            'structure_cues': ['proceso de', 'número', 'fecha de publicación', 'tiene por objeto', 'se rige por', 'cláusulas contractuales'],
            'priority': 1
        },
        'OBJETO': {
            'keywords': ['objeto', 'finalidad', 'propósito', 'alcance', 'descripción'],
            'context_words': ['contrato', 'contratación', 'servicio', 'obra', 'suministro', 'contractual', 'ejecución'],
            'structure_cues': ['del contrato', 'de la contratación', 'duración', 'valor estimado', 'se requiere', 'encarga', 'objeto del contrato', 'denominada'],
            'priority': 2
        },
        'REQUISITOS_TECNICOS': {
            'keywords': ['requisitos', 'especificaciones', 'requerimientos', 'capacidades', 'mínimos'],
            'context_words': ['técnicos', 'tecnológicos', 'especializado', 'profesional', 'proponentes', 'interesados'],
            'structure_cues': ['experiencia', 'certificaciones', 'personal', 'equipo', 'infraestructura', 'acreditar', 'especificaciones técnicas'],
            'priority': 3
        },
        'CONDICIONES_ECONOMICAS': {
            'keywords': ['condiciones', 'aspectos', 'términos', 'económicos', 'presupuesto', 'monto', 'valor'],
            'context_words': ['económicas', 'financieras', 'monetarias', 'precio', 'valor', 'pago', 'contrato'],
            'structure_cues': ['forma de pago', 'anticipo', 'presupuesto', 'desembolsos', 'descuentos', 'asciende', 'total', 'monto del contrato', 'valor total'],
            'priority': 4
        },
        'GARANTIAS': {
            'keywords': ['garantías', 'pólizas', 'seguros', 'fianzas', 'respaldos', 'requeridas'],
            'context_words': ['seriedad', 'cumplimiento', 'responsabilidad', 'civil', 'manejo', 'fiel'],
            'structure_cues': ['equivalente', 'vigencia', 'constituir', 'mantener', 'por el', 'smmlv', 'deberá presentar', 'garantía de fiel', 'garantía por vicios'],
            'priority': 5
        },
        'PLAZOS': {
            'keywords': ['cronograma', 'plazos', 'fechas', 'calendario', 'programación', 'proceso', 'ejecución'],
            'context_words': ['proceso', 'selección', 'evaluación', 'adjudicación', 'ejecutará', 'meses'],
            'structure_cues': ['apertura', 'recepción', 'hasta', 'enero', 'febrero', 'marzo', 'contados desde', 'plazo de ejecución', 'se ejecutará'],
            'priority': 6
        },
        'FORMULARIOS': {
            'keywords': ['documentos', 'formularios', 'anexos', 'formatos', 'certificados', 'documentación'],
            'context_words': ['propuesta', 'presentar', 'requeridos', 'integral', 'entregar'],
            'structure_cues': ['deberán presentar', 'carta de', 'estados financieros', 'sobre separado', 'recepción', 'controversias'],
            'priority': 7
        },
        'CONDICIONES_GENERALES': {
            'keywords': ['condiciones', 'disposiciones', 'normas', 'términos', 'multas', 'penalizaciones'],
            'context_words': ['generales', 'aplicables', 'marco', 'normativo', 'terminación', 'resolución'],
            'structure_cues': ['según', 'conforme', 'de acuerdo', 'vigentes', 'causales', 'jurisdicción', 'anticipo', 'multas'],
            'priority': 8
        },
        'CONDICIONES_PARTICULARES': {
            'keywords': ['condiciones', 'disposiciones', 'normas', 'anticipo', 'recepción'],
            'context_words': ['particulares', 'específicas', 'especiales', 'propias', 'provisional', 'definitiva'],
            'structure_cues': ['en particular', 'específicamente', 'adicionalmente', 'concluir', 'vicios ocultos'],
            'priority': 9
        }
    }
    
    current_pos = 0
    
    for i, line in enumerate(lines):
        line_clean = line.strip()
        if not line_clean or len(line_clean) < 5:
            current_pos += len(line) + 1
            continue
            
        line_lower = line_clean.lower()
        
        # Check if line could be a section header based on semantic cues
        is_potential_header = False
        header_confidence = 0.0
        detected_section = None
        
        # Analyze line characteristics with improved numeric detection
        line_characteristics = {
            'is_short': len(line_clean) < 150,  # Headers are usually shorter
            'is_uppercase': line_clean.isupper(),  # Many headers are uppercase
            'has_numbers': bool(re.search(r'\b[IVXLC]+\b|\b\d+\.?\s*[A-ZÁÉÍÓÚÑ]|^\d+\.|^[a-z]\)', line_clean)),  # Roman/Arabic numerals
            'ends_with_colon': line_clean.endswith(':'),
            'is_standalone': i > 0 and i < len(lines) - 1 and (not lines[i-1].strip() or lines[i-1].strip() == '') and lines[i+1].strip(),
            'has_title_case': any(word[0].isupper() for word in line_clean.split() if len(word) > 3),
            'starts_with_number': bool(re.match(r'^\d+\.?\s', line_clean)),
            'has_header_words': any(hw in line_lower for hw in ['información', 'descripción', 'requisitos', 'aspectos', 'garantías', 'programación', 'documentación']),
            # Enhanced numeric patterns for contract clauses
            'has_ordinal_pattern': bool(re.search(r'(primera|segunda|tercera|cuarta|quinta|sexta|séptima|octava|novena|décima)', line_lower)),
            'has_clause_number': bool(re.search(r'^(cláusula\s+)?(primera|segunda|tercera|cuarta|quinta|sexta|séptima|octava|novena|décima|\d+[°ª]?\.?)[\s–-]', line_lower)),
            'has_section_dash': bool(re.search(r'[–-]\s*[A-ZÁÉÍÓÚÑ]', line_clean)),
            'starts_with_roman': bool(re.match(r'^[IVXLCDM]+\.?\s', line_clean))
        }
        
        # Calculate base header probability with improved scoring
        header_score = 0
        if line_characteristics['is_short']: header_score += 0.2
        if line_characteristics['is_uppercase']: header_score += 0.3
        if line_characteristics['has_numbers']: header_score += 0.3
        if line_characteristics['ends_with_colon']: header_score += 0.2
        if line_characteristics['is_standalone']: header_score += 0.3
        if line_characteristics['has_title_case']: header_score += 0.2
        if line_characteristics['starts_with_number']: header_score += 0.4
        if line_characteristics['has_header_words']: header_score += 0.3
        # Enhanced scoring for contract patterns
        if line_characteristics['has_ordinal_pattern']: header_score += 0.5
        if line_characteristics['has_clause_number']: header_score += 0.6  # Very strong indicator
        if line_characteristics['has_section_dash']: header_score += 0.4
        if line_characteristics['starts_with_roman']: header_score += 0.4
        
        # Minimum header score to be considered
        if header_score < 0.3:
            current_pos += len(line) + 1
            continue
        
        # First check for ordinal-based contract clauses (priority approach)
        ordinal_position = get_ordinal_position(line_clean)
        if ordinal_position and line_characteristics['has_clause_number']:
            detected_section = map_position_to_section(ordinal_position, line_clean)
            if detected_section:
                header_confidence = 0.8  # High confidence for clear ordinal patterns
                is_potential_header = True
                logger.info(f"Detected ordinal clause {ordinal_position} -> {detected_section}: '{line_clean[:50]}...' (confidence: {header_confidence:.3f})")
        
        # If no ordinal match, fall back to semantic analysis
        if not is_potential_header:
            # Semantic analysis for each section type
            for section_name, pattern_info in semantic_patterns.items():
                section_score = 0
                total_possible = 0
                
                # Check keywords (most important)
                keyword_matches = sum(1 for kw in pattern_info['keywords'] if kw in line_lower)
                if keyword_matches > 0:
                    section_score += keyword_matches * 0.4
                total_possible += len(pattern_info['keywords']) * 0.4
                
                # Check context words
                context_matches = sum(1 for cw in pattern_info['context_words'] if cw in line_lower)
                if context_matches > 0:
                    section_score += context_matches * 0.3
                total_possible += len(pattern_info['context_words']) * 0.3
                
                # Check structure cues (look in next few lines too)
                structure_score = 0
                context_lines = lines[i:min(i+5, len(lines))]
                context_text = ' '.join(context_lines).lower()
                
                structure_matches = sum(1 for sc in pattern_info['structure_cues'] if sc in context_text)
                if structure_matches > 0:
                    structure_score = structure_matches * 0.4  # Increased weight since contract patterns are merged here
                section_score += structure_score
                total_possible += len(pattern_info['structure_cues']) * 0.4
                
                # Calculate confidence for this section
                if total_possible > 0:
                    section_confidence = (section_score / total_possible) * header_score
                    
                    # Boost confidence if multiple indicators align
                    if keyword_matches > 0 and context_matches > 0:
                        section_confidence *= 1.2
                    if keyword_matches > 0 and structure_matches > 0:
                        section_confidence *= 1.3  # Higher boost since structure cues now include contract patterns
                    
                    # Consider priority (earlier sections might appear first)
                    position_factor = 1.0 - (i / len(lines)) * 0.2
                    section_confidence *= position_factor
                    
                    if section_confidence > header_confidence and section_confidence > 0.15:  # Lower threshold
                        header_confidence = section_confidence
                        detected_section = section_name
                        is_potential_header = True
        
        # Add boundary if confident enough
        if is_potential_header and detected_section and header_confidence > 0.2:  # Lower threshold
            boundaries.append((current_pos, detected_section, header_confidence))
            logger.info(f"Detected section '{detected_section}' at line {i+1}: '{line_clean[:60]}...' (confidence: {header_confidence:.3f})")
        
        current_pos += len(line) + 1
    
    # Sort by position and remove duplicates/overlaps
    boundaries.sort()
    filtered_boundaries = []
    for pos, section, conf in boundaries:
        # Avoid very close boundaries (< 100 characters apart)
        if not filtered_boundaries or pos - filtered_boundaries[-1][0] > 100:
            filtered_boundaries.append((pos, section, conf))
    
    logger.info(f"Semantic analysis found {len(filtered_boundaries)} section boundaries")
    return filtered_boundaries

# Convierte texto de un archivo .txt a una lista de Documentos con detección semántica mejorada
def txt_to_documents(txt_path: Path, source_name: str, chunk_size: int = 2000, chunk_overlap: int = 1000) -> List[Document]:
    """
    Convierte un archivo txt a documentos usando detección semántica inteligente de secciones.
    Analiza el contenido semántico para identificar límites de secciones.
    
    Args:
        txt_path: Ruta al archivo txt
        source_name: Nombre del documento fuente
        chunk_size: Tamaño de cada chunk en caracteres
        chunk_overlap: Overlap entre chunks en caracteres
    """
    text = txt_path.read_text(encoding="utf-8")
    
    # Validate text content
    if not text or not text.strip():
        logger.warning(f"Empty or invalid text content in {txt_path}")
        return []
    
    # Ensure text doesn't have None values by cleaning it
    text = str(text).replace('\x00', '').strip()
    
    chunks = []
    
    try:
        # Use semantic boundary detection
        logger.info("Using semantic section boundary detection...")
        boundaries = detect_section_boundaries_semantic(text)
        
        if boundaries:
            logger.info(f"Found {len(boundaries)} semantic section boundaries")
            
            # Create chunks based on semantic boundaries
            for i, (start_pos, section_name, confidence) in enumerate(boundaries):
                # Determine end position
                if i + 1 < len(boundaries):
                    end_pos = boundaries[i + 1][0]
                else:
                    end_pos = len(text)
                
                # Extract section content
                section_content = text[start_pos:end_pos].strip()
                
                if len(section_content) > 20:  # Minimum content length
                    # If section is too large, split it but try to keep logical parts together
                    if len(section_content) > chunk_size:
                        logger.info(f"Section '{section_name}' is large ({len(section_content)} chars), intelligent splitting...")
                        
                        # Try to split on paragraph boundaries first
                        paragraphs = section_content.split('\n\n')
                        if len(paragraphs) > 1:
                            current_chunk = ""
                            for para in paragraphs:
                                if len(current_chunk + para) <= chunk_size:
                                    current_chunk += para + "\n\n"
                                else:
                                    if current_chunk.strip():
                                        chunks.append(current_chunk.strip())
                                    current_chunk = para + "\n\n"
                            if current_chunk.strip():
                                chunks.append(current_chunk.strip())
                        else:
                            # Fallback to regular splitting
                            splitter = make_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                            sub_chunks = splitter.split_text(section_content)
                            chunks.extend(sub_chunks)
                    else:
                        chunks.append(section_content)
        else:
            # Fallback to intelligent paragraph-based splitting
            logger.info("No semantic boundaries detected, using intelligent paragraph splitting...")
            
            # Split by double newlines (paragraphs) first
            paragraphs = text.split('\n\n')
            current_chunk = ""
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                    
                # Check if adding this paragraph exceeds chunk size
                if len(current_chunk + para) <= chunk_size:
                    current_chunk += para + "\n\n"
                else:
                    # Save current chunk if not empty
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    
                    # Start new chunk with current paragraph
                    if len(para) <= chunk_size:
                        current_chunk = para + "\n\n"
                    else:
                        # Paragraph itself is too large, split it
                        splitter = make_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                        para_chunks = splitter.split_text(para)
                        chunks.extend(para_chunks)
                        current_chunk = ""
            
            # Add final chunk if any
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
    except Exception as e:
        logger.error(f"Error in semantic splitting: {e}")
        # Last resort - regular splitter
        logger.info("Using regular splitter as fallback")
        splitter = make_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = splitter.split_text(text)
    
    # Filter out empty chunks
    chunks = [str(ch).strip() for ch in chunks if ch is not None and str(ch).strip()]
    
    if not chunks:
        logger.warning(f"No valid chunks created from {txt_path}")
        return []

    docs: List[Document] = []
    section_boundaries = detect_section_boundaries_semantic(text) if chunks else []
    
    for i, ch in enumerate(chunks):
        if not ch or not ch.strip():
            continue
            
        # Find which section this chunk belongs to using semantic analysis
        detected_section = "GENERAL"
        chunk_start_pos = text.find(ch[:50]) if len(ch) >= 50 else text.find(ch)
        
        if chunk_start_pos != -1 and section_boundaries:
            # Find the section boundary that this chunk falls under
            applicable_boundary = None
            for pos, section_name, confidence in section_boundaries:
                if pos <= chunk_start_pos:
                    applicable_boundary = (section_name, confidence)
                else:
                    break
            
            if applicable_boundary:
                detected_section = applicable_boundary[0]
        
        # Also use content-based semantic classification as backup
        if detected_section == "GENERAL":
            content_lower = ch.lower()
            
            # Use semantic keyword analysis
            section_scores = {}
            semantic_patterns = {
                'CONVOCATORIA': ['convocatoria', 'licitación', 'proceso', 'llamado', 'invitación'],
                'OBJETO': ['objeto', 'contrato', 'contratación', 'servicio', 'finalidad'],
                'REQUISITOS_TECNICOS': ['requisitos', 'técnicos', 'experiencia', 'certificaciones', 'personal'],
                'CONDICIONES_ECONOMICAS': ['económicas', 'pago', 'valor', 'precio', 'presupuesto', 'financieras'],
                'GARANTIAS': ['garantías', 'pólizas', 'seguros', 'seriedad', 'cumplimiento'],
                'PLAZOS': ['cronograma', 'fechas', 'plazos', 'publicación', 'cierre'],
                'FORMULARIOS': ['documentos', 'formularios', 'presentar', 'carta', 'certificado']
            }
            
            for section, keywords in semantic_patterns.items():
                score = sum(1 for keyword in keywords if keyword in content_lower)
                if score > 0:
                    section_scores[section] = score
            
            if section_scores:
                detected_section = max(section_scores.items(), key=lambda x: x[1])[0]
        
        # Extract page number if available
        try:
            m_page = re.search(r"=== PÁGINA\s+(\d+)", ch)
            page = int(m_page.group(1)) if m_page else None
        except Exception:
            page = None

        docs.append(
            Document(
                page_content=ch.strip(),
                metadata={
                    "source": source_name, 
                    "section": detected_section, 
                    "page": page,
                    "chunk_index": i,
                    "chunk_method": "semantic_aware"
                },
            )
        )
    
    logger.info(f"Created {len(docs)} document chunks from {source_name}")
    
    # Show section distribution
    section_counts = {}
    for doc in docs:
        section = doc.metadata.get('section', 'UNKNOWN')
        section_counts[section] = section_counts.get(section, 0) + 1
    
    logger.info(f"Semantic section distribution: {section_counts}")
    return docs

# ID determinista 
def make_id(doc: Document) -> str:
    """
    ID determinista con baja probabilidad de colisión.
    Incluye source | section | todo el contenido del chunk.
    """
    base = f"{doc.metadata.get('source','')}|{doc.metadata.get('section','')}|{doc.page_content}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()

# Deriva el nombre de la colección
def _derive_collection_name(base_name: Optional[str], provider: str, model: str) -> str:
    if base_name:
        return base_name
    safe_model = model.replace(":", "_")
    return f"Licitaciones-{provider}-{safe_model}"

# Construye embeddings y los guarda en Chroma
def build_embeddings(
    carpeta_lawdata: str,
    ruta_db: str,
    collection_name: Optional[str] = None,
    provider: str = "auto",
    model: Optional[str] = None,
    batch_size: int = 100,
    reset_db: bool = False,
    chunk_size: int = 2000,
    chunk_overlap: int = 1000,
):
    """
    1) Convierte DOC/DOCX a PDF (si hace falta)
    2) Extrae texto / OCR
    3) Split simplificado con chunks de 2000/1000 + metadatos
    4) Embeddings y persistencia en Chroma
    
    Parámetros nuevos:
    - chunk_size: Tamaño de cada chunk (por defecto 2000)
    - chunk_overlap: Overlap entre chunks (por defecto 1000)
    """

    if not carpeta_lawdata or not ruta_db:
        raise ValueError("carpeta_lawdata y ruta_db son requeridos")

    carpeta = Path(carpeta_lawdata)
    ruta_db = Path(ruta_db)

    if not carpeta.exists():
        raise FileNotFoundError(f"Carpeta no encontrada: {carpeta}")

    if reset_db and ruta_db.exists():
        import shutil

        logger.info(f"Reset de base vectorial: {ruta_db}")
        shutil.rmtree(ruta_db, ignore_errors=True)

    ruta_db.mkdir(parents=True, exist_ok=True)
    logger.info(f"Iniciando procesamiento en: {carpeta.resolve()}")

    txt_paths: List[Path] = []
    archivos_procesados: List[str] = []
    archivos_con_error: List[str] = []

    for p in sorted(carpeta.iterdir()):
        if p.suffix.lower() in [".pdf", ".doc", ".docx"]:
            try:
                from .agents.document_extraction import DocumentExtractionAgent
                pdf = DocumentExtractionAgent.to_pdf_if_needed(p)
                txt = pdf.with_suffix(".txt")
                if not txt.exists():
                    txt = DocumentExtractionAgent.pdf_to_txt(pdf)
                txt_paths.append(txt)
                archivos_procesados.append(p.name)
            except Exception as e:
                archivos_con_error.append(p.name)
                logger.error(f"Error con {p.name}: {e}")

    if not txt_paths:
        logger.error("No se procesaron archivos válidos")
        return None

    all_docs: List[Document] = []
    for txt in txt_paths:
        try:
            all_docs.extend(txt_to_documents(txt, source_name=txt.stem, chunk_size=chunk_size, chunk_overlap=chunk_overlap))
        except Exception as e:
            archivos_con_error.append(txt.name)
            logger.error(f"Error creando docs de {txt.name}: {e}")

    if not all_docs:
        logger.error("No se crearon documentos")
        return None

    embeddings, used_provider, used_model = get_embeddings_provider(provider=provider, model=model)
    final_collection_name = _derive_collection_name(collection_name, used_provider, used_model)
    db = Chroma(
        collection_name=final_collection_name,
        persist_directory=str(ruta_db),
        embedding_function=embeddings,
    )

    total = len(all_docs)
    for i in range(0, total, batch_size):
        batch_docs = all_docs[i : i + batch_size]
        batch_ids = [make_id(doc) for doc in batch_docs]
        try:
            db.add_documents(batch_docs, ids=batch_ids)
            logger.info(f"Lote {i//batch_size + 1}/{(total - 1)//batch_size + 1} indexado")
        except Exception as e:
            logger.warning(f"Fallo add_documents por lote, intentando inserción individual: {e}")
            for d, _id in zip(batch_docs, batch_ids):
                try:
                    db.add_documents([d], ids=[_id])
                except Exception:
                    logger.info(f"Documento duplicado (omitido): {d.metadata.get('source')}#{d.metadata.get('page')}")

    # Persistir base de datos (en versiones nuevas de ChromaDB no es necesario)
    try:
        db.persist()
        logger.info("Base de datos persistida correctamente")
    except AttributeError:
        # Las versiones nuevas de ChromaDB no requieren persist() explícito
        logger.info("Base de datos auto-persistida (ChromaDB nueva versión)")

    sections_by_doc = defaultdict(set)
    for d in all_docs:
        sections_by_doc[d.metadata["source"]].add(d.metadata["section"])
    for src, secs in sections_by_doc.items():
        logger.info(f"{src}: {sorted(secs)}")

    logger.info(f"Archivos procesados: {len(archivos_procesados)} | Errores: {len(archivos_con_error)}")
    logger.info(f"Chunks totales: {len(all_docs)}")
    logger.info(f"Colección: {final_collection_name} | Proveedor: {used_provider} | Modelo: {used_model}")
    return db

# Verifica dependencias críticas
def verificar_dependencias() -> bool:
    """
    Verifica que las dependencias críticas estén instaladas y configuradas.
    """
    logger.info("Verificando dependencias...")

    dependencias_ok = True

    logger.info("\nProveedores de Embeddings:")
    openai_ok = bool(os.getenv("OPENAI_API_KEY"))
    if openai_ok:
        logger.info("OpenAI API configurada")
    else:
        logger.warning("OpenAI API no configurada")
        logger.info("Configura: export OPENAI_API_KEY='tu-api-key'")

    ollama_ok = OLLAMA_AVAILABLE and verificar_ollama()
    if ollama_ok:
        modelos = listar_modelos_ollama()
        if any("embed" in m for m in modelos) or "nomic-embed-text:latest" in modelos:
            logger.info("OLLAMA con modelo de embeddings disponible")
        else:
            logger.warning("OLLAMA sin modelo de embeddings")
            logger.info("   Ejecuta: ollama pull nomic-embed-text")

    if not (openai_ok or ollama_ok):
        logger.error("Ningún proveedor de embeddings disponible")
        dependencias_ok = False
    else:
        provider_recomendado = "OLLAMA (gratis/local)" if ollama_ok else "OpenAI (hosted)"
        logger.info(f"Proveedor recomendado: {provider_recomendado}")

    logger.info("\nConversión de Documentos:")
    soffice_bin = os.getenv("SOFFICE_BIN", "soffice")
    try:
        subprocess.run([soffice_bin, "--version"], capture_output=True, check=True, timeout=10)
        logger.info("LibreOffice disponible")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.error(f"LibreOffice no encontrado en: {soffice_bin}")
        logger.info("Instala LibreOffice o configura SOFFICE_BIN")
        dependencias_ok = False

    logger.info("\nOCR (Opcional para PDFs escaneados):")
    try:
        import pytesseract  
        from PIL import Image  
        import pytesseract as pt
        pt.get_tesseract_version()
        logger.info("OCR (tesseract) disponible")
    except ImportError:
        logger.warning("OCR no disponible")
        logger.info("   pip install pytesseract pillow")
    except Exception:
        logger.warning("Tesseract no encontrado")
        logger.info("   Instala tesseract-ocr en tu sistema")

    if dependencias_ok:
        logger.info("\nDependencias principales: OK")
    else:
        logger.error("Faltan dependencias críticas")

    return dependencias_ok


def test_simplified_embeddings(db_path: str, query: str = "requisitos técnicos", k: int = 5):
    """
    Función de prueba para verificar que los embeddings simplificados funcionan correctamente.
    """
    try:
        from langchain_chroma import Chroma
        
        # Obtener proveedor de embeddings
        embeddings, provider, model = get_embeddings_provider()
        
        # Cargar base de datos existente
        db = Chroma(
            persist_directory=db_path,
            embedding_function=embeddings
        )
        
        logger.info(f"🔍 Probando búsqueda: '{query}'")
        
        # Verificar que la base de datos tenga contenido
        try:
            collection = db._collection
            count = collection.count()
            logger.info(f"📊 Base de datos contiene {count} documentos")
            
            if count == 0:
                logger.warning("⚠️ Base de datos vacía - no se pueden realizar búsquedas")
                return []
        except Exception as e:
            logger.warning(f"No se pudo verificar el conteo de documentos: {e}")
        
        # Realizar búsqueda semántica
        results = db.similarity_search(query, k=k)
        
        logger.info(f"📋 Encontrados {len(results)} resultados:")
        
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get('source', 'unknown')
            section = doc.metadata.get('section', 'unknown')
            page = doc.metadata.get('page', 'N/A')
            
            preview = doc.page_content[:200].replace('\n', ' ').strip()
            
            logger.info(f"   {i}. {source} (sección: {section}, página: {page})")
            logger.info(f"      Vista previa: {preview}...")
            logger.info("")
        
        return results
        
    except Exception as e:
        logger.error(f"Error en búsqueda de prueba: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    # Ejemplo de uso del sistema simplificado
    logging.basicConfig(level=logging.INFO)
    
    # Verificar dependencias
    verificar_dependencias()
    
    # Probar sistema simplificado
    logger.info("\n" + "="*60)
    logger.info("🔬 PROBANDO SISTEMA DE EMBEDDINGS SIMPLIFICADO")
    logger.info("="*60)
    
    # Configurar rutas
    carpeta_docs = "./LawData"
    ruta_db = "./db/chroma/simplified_embeddings"
    
    # Construir embeddings con el sistema simplificado
    try:
        db = build_embeddings(
            carpeta_lawdata=carpeta_docs,
            ruta_db=ruta_db,
            collection_name="simplified_docs",
            provider="auto",
            chunk_size=2000,  # Chunks de 2000 caracteres
            chunk_overlap=1000,  # Overlap de 1000 caracteres
            reset_db=True
        )
        
        if db:
            logger.info("✅ Base de datos creada exitosamente")
            
            # Probar búsquedas
            test_queries = [
                "requisitos técnicos",
                "garantías",
                "cronograma", 
                "objeto del contrato",
                "condiciones generales"
            ]
            
            for query in test_queries:
                logger.info(f"\n{'='*40}")
                test_simplified_embeddings(ruta_db, query, k=2)
        else:
            logger.error("❌ Error creando base de datos")
            
    except Exception as e:
        logger.error(f"❌ Error en el proceso: {e}")
        import traceback
        traceback.print_exc()
