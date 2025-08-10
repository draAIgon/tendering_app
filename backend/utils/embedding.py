from pathlib import Path
import re
import subprocess
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import os
import logging
from collections import defaultdict
import hashlib
import requests
from typing import List, Optional

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

# Separadores simplificados - comentados para usar método más simple
# SEPARATORS = [
#     r"\nSECCIÓN\s+[IVXLC]+\b",
#     r"\nCAPÍTULO\s+[IVXLC]+\b",
#     r"\n\d+\.\s*[A-ZÁÉÍÓÚÑ]",
#     r"\n\d+\.\d+(\.\d+)?\s",
#     r"\n[A-ZÁÉÍÓÚÑ ]{10,}\n",
#     r"\nCONVOCATORIA\b",
#     r"\nOBJETO\s+DE\s+LA\s+CONTRATACI[ÓO]N\b",
#     r"\nCONDICIONES\s+GENERALES\b",
#     r"\nCONDICIONES\s+PARTICULARES\b",
#     r"\nREQUISITOS\s+TÉCNICOS\b",
#     r"\nESPECIFICACIONES\s+TÉCNICAS\b",
#     r"\nCONDICIONES\s+ECON[ÓO]MICAS\b",
#     r"\nGARANT[IÍ]AS\b",
#     r"\nPLAZOS\b",
#     r"\nCRONOGRAMA\b",
#     r"\nFORMULARIO\s+ÚNICO\s+DE\s+LA\s+OFERTA\b",
# ]

# Función regex compleja comentada - ya no se usa en el sistema simplificado
# def _custom_regex_split(text: str, separators: List[str]) -> List[str]:
#     """
#     Custom regex splitting that handles None values properly.
#     Splits text using regex patterns in order of preference.
#     """
#     if not text:
#         return []
#     
#     # Start with the full text
#     chunks = [text]
#     
#     # Apply each separator in order
#     for separator in separators:
#         new_chunks = []
#         for chunk in chunks:
#             if not chunk or not chunk.strip():
#                 continue
#             
#             try:
#                 # Split using the regex pattern
#                 parts = re.split(separator, chunk)
#                 # Filter out None and empty parts
#                 parts = [str(part).strip() for part in parts if part is not None and str(part).strip()]
#                 new_chunks.extend(parts)
#             except Exception:
#                 # If regex fails, keep the original chunk
#                 new_chunks.append(chunk)
#         
#         chunks = new_chunks
#         
#         # Stop if we have enough small chunks
#         if len(chunks) > 10 and all(len(chunk) < 2000 for chunk in chunks):
#             break
#     
#     # Final cleanup - remove empty chunks and ensure reasonable size
#     final_chunks = []
#     for chunk in chunks:
#         if chunk and len(chunk.strip()) > 10:  # Minimum chunk size
#             # If chunk is too large, split it manually
#             if len(chunk) > 2500:
#                 # Split large chunks into smaller pieces
#                 for i in range(0, len(chunk), 1800):
#                     sub_chunk = chunk[i:i+1800]
#                     if sub_chunk.strip():
#                         final_chunks.append(sub_chunk)
#             else:
#                 final_chunks.append(chunk)
#     
#     return final_chunks

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


# Pattern simplificado para detectar secciones (opcional)
section_pattern = re.compile(
    r"(SECCIÓN\s+[IVXLC]+|FORMULARIO\s+ÚNICO\s+DE\s+LA\s+OFERTA|CONVOCATORIA|CONDICIONES\s+GENERALES|CONDICIONES\s+PARTICULARES|REQUISITOS\s+TÉCNICOS|ESPECIFICACIONES\s+TÉCNICAS|CONDICIONES\s+ECON[ÓO]MICAS|GARANT[IÍ]AS|PLAZOS|CRONOGRAMA)",
    re.I,
)

# Convierte texto de un archivo .txt a una lista de Documentos
def txt_to_documents(txt_path: Path, source_name: str, chunk_size: int = 2000, chunk_overlap: int = 1000) -> List[Document]:
    """
    Convierte un archivo txt a documentos usando chunking simplificado.
    Ya no usa separadores regex complejos, solo chunks configurables con overlap.
    
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
        # Usar solo RecursiveCharacterTextSplitter simplificado
        logger.info(f"Using simplified RecursiveCharacterTextSplitter ({chunk_size}/{chunk_overlap})...")
        splitter = make_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = splitter.split_text(text)
        logger.info(f"Splitter successful: {len(chunks)} chunks created")
    except Exception as e:
        logger.error(f"Splitter failed: {e}")
        # Last resort - manual chunking with same parameters
        logger.info("Using manual chunking as fallback")
        step_size = max(1, chunk_size - chunk_overlap)
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), step_size)]
    
    # Filter out empty or None chunks
    chunks = [str(ch).strip() for ch in chunks if ch is not None and str(ch).strip()]
    
    if not chunks:
        logger.warning(f"No valid chunks created from {txt_path}")
        return []

    docs: List[Document] = []
    for ch in chunks:
        if not ch or not ch.strip():
            continue
            
        try:
            m_sec = section_pattern.search(ch)
            section = m_sec.group(1).upper() if m_sec else "GENERAL"
        except Exception:
            section = "GENERAL"

        try:
            m_page = re.search(r"=== PÁGINA\s+(\d+)", ch)
            page = int(m_page.group(1)) if m_page else None
        except Exception:
            page = None

        docs.append(
            Document(
                page_content=ch.strip(),
                metadata={"source": source_name, "section": section, "page": page},
            )
        )
    
    logger.info(f"Created {len(docs)} document chunks from {source_name}")
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
