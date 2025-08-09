from pathlib import Path
import re
import subprocess
import fitz
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import os
import logging
from collections import defaultdict
import hashlib
import requests
from io import BytesIO
from typing import List, Tuple, Optional
import unicodedata

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

def to_pdf_if_needed(path: Path) -> Path:
    """
    Acepta .pdf/.doc/.docx. Convierte DOC/DOCX a PDF con LibreOffice (soffice).
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"El archivo {path} no existe")

    if path.suffix.lower() == ".pdf":
        logger.info(f"Archivo PDF importado: {path.name}")
        return path

    if path.suffix.lower() in [".doc", ".docx"]:
        try:
            out_dir = path.parent
            soffice_bin = os.getenv("SOFFICE_BIN", "soffice")
            cmd = [soffice_bin, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(path)]
            logger.info(f"Convirtiendo {path.name} a PDF...")
            subprocess.run(cmd, check=True, capture_output=True, text=True)

            pdf_path = path.with_suffix(".pdf")
            if not pdf_path.exists():
                raise FileNotFoundError(f"No se pudo convertir {path.name} a PDF")

            logger.info(f"Conversión exitosa: {path.name} -> {pdf_path.name}")
            return pdf_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Error al convertir {path.name}: {e}")
            raise

    raise ValueError(f"Formato no soportado: {path.suffix}. Use .pdf, .doc o .docx")

def _normalize_text(text: str) -> str:
    """
    Normaliza unicode, corrige guiones por salto de línea y espacios múltiples.
    Mantiene los marcadores '=== PÁGINA i ==='.
    """
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text

def _ocr_page(pagina) -> str:
    import pytesseract
    from PIL import Image
    pix = pagina.get_pixmap(dpi=300, alpha=False)
    img = Image.open(BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img, lang="spa+eng")

def pdf_to_txt(pdf_path: Path, ocr_char_threshold: int = 30) -> Path:
    logger.info(f"Extrayendo texto de: {pdf_path.name}")
    texto = []
    try:
        import pytesseract  # opcional
        ocr_enabled = True
        try:
            pytesseract.get_tesseract_version()
        except Exception:
            ocr_enabled = False
    except ImportError:
        ocr_enabled = False

    with fitz.open(pdf_path) as pdf:
        total_pages = len(pdf)
        logger.info(f"Total de páginas: {total_pages}")
        for i, pagina in enumerate(pdf, 1):
            page_text = pagina.get_text() or ""
            page_text = page_text.strip()
            if not page_text or len(page_text) < ocr_char_threshold:
                if ocr_enabled:
                    try:
                        page_text = _ocr_page(pagina).strip()
                        if page_text:
                            texto.append(f"\n=== PÁGINA {i} (OCR) ===\n{page_text}")
                            continue
                    except Exception as e:
                        logger.warning(f"OCR falló en página {i}: {e}")
            if page_text:
                texto.append(f"\n=== PÁGINA {i} ===\n{page_text}")
            else:
                texto.append(f"\n=== PÁGINA {i} ===\n")
    contenido = _normalize_text("\n".join(texto))
    txt_path = pdf_path.with_suffix(".txt")
    txt_path.write_text(contenido, encoding="utf-8")
    return txt_path

SEPARADORES = [
    r"\nSECCIÓN\s+[IVXLC]+\b",
    r"\nCAPÍTULO\s+[IVXLC]+\b",
    r"\n\d+\.\s*[A-ZÁÉÍÓÚÑ]",
    r"\n\d+\.\d+(\.\d+)?\s",
    r"\n[A-ZÁÉÍÓÚÑ ]{10,}\n",
    r"\nCONVOCATORIA\b",
    r"\nOBJETO\s+DE\s+LA\s+CONTRATACI[ÓO]N\b",
    r"\nCONDICIONES\s+GENERALES\b",
    r"\nCONDICIONES\s+PARTICULARES\b",
    r"\nREQUISITOS\s+TÉCNICOS\b",
    r"\nESPECIFICACIONES\s+TÉCNICAS\b",
    r"\nCONDICIONES\s+ECON[ÓO]MICAS\b",
    r"\nGARANT[IÍ]AS\b",
    r"\nPLAZOS\b",
    r"\nCRONOGRAMA\b",
    r"\nFORMULARIO\s+ÚNICO\s+DE\s+LA\s+OFERTA\b",
]


def make_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=1800,
        chunk_overlap=200,
        separators=SEPARADORES + ["\n\n", "\n", ". ", " "],
        length_function=len,
        is_separator_regex=True,
    )


section_pattern = re.compile(
    r"(SECCIÓN\s+[IVXLC]+|FORMULARIO\s+ÚNICO\s+DE\s+LA\s+OFERTA|CONVOCATORIA|CONDICIONES\s+GENERALES|CONDICIONES\s+PARTICULARES|REQUISITOS\s+TÉCNICOS|ESPECIFICACIONES\s+TÉCNICAS|CONDICIONES\s+ECON[ÓO]MICAS|GARANT[IÍ]AS|PLAZOS|CRONOGRAMA)",
    re.I,
)


def txt_to_documents(txt_path: Path, source_name: str) -> List[Document]:
    text = txt_path.read_text(encoding="utf-8")
    splitter = make_splitter()
    chunks = splitter.split_text(text)

    docs: List[Document] = []
    for ch in chunks:
        m_sec = section_pattern.search(ch)
        section = m_sec.group(1).upper() if m_sec else "GENERAL"

        m_page = re.search(r"=== PÁGINA\s+(\d+)", ch)
        page = int(m_page.group(1)) if m_page else None

        docs.append(
            Document(
                page_content=ch.strip(),
                metadata={"source": source_name, "section": section, "page": page},
            )
        )
    return docs

def make_id(doc: Document) -> str:
    """
    ID determinista con baja probabilidad de colisión.
    Incluye source | section | todo el contenido del chunk.
    """
    base = f"{doc.metadata.get('source','')}|{doc.metadata.get('section','')}|{doc.page_content}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def _derive_collection_name(base_name: Optional[str], provider: str, model: str) -> str:
    if base_name:
        return base_name
    safe_model = model.replace(":", "_")
    return f"Licitaciones-{provider}-{safe_model}"

def build_embeddings(
    carpeta_lawdata: str,
    ruta_db: str,
    collection_name: Optional[str] = None,
    provider: str = "auto",
    model: Optional[str] = None,
    batch_size: int = 100,
    reset_db: bool = False,
):
    """
    1) Convierte DOC/DOCX a PDF (si hace falta)
    2) Extrae texto / OCR
    3) Split + metadatos
    4) Embeddings y persistencia en Chroma
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
                pdf = to_pdf_if_needed(p)
                txt = pdf.with_suffix(".txt")
                if not txt.exists():
                    txt = pdf_to_txt(pdf)
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
            all_docs.extend(txt_to_documents(txt, source_name=txt.stem))
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

    db.persist()

    sections_by_doc = defaultdict(set)
    for d in all_docs:
        sections_by_doc[d.metadata["source"]].add(d.metadata["section"])
    for src, secs in sections_by_doc.items():
        logger.info(f"{src}: {sorted(secs)}")

    logger.info(f"Archivos procesados: {len(archivos_procesados)} | Errores: {len(archivos_con_error)}")
    logger.info(f"Chunks totales: {len(all_docs)}")
    logger.info(f"Colección: {final_collection_name} | Proveedor: {used_provider} | Modelo: {used_model}")
    return db

def test_document_processing(archivo_pdf: str) -> List[Document]:
    pdf_path = Path(archivo_pdf)
    pdf_final = to_pdf_if_needed(pdf_path)
    txt_path = pdf_to_txt(pdf_final)
    docs = txt_to_documents(txt_path, pdf_path.stem)
    logger.info(f"Chunks: {len(docs)} | Secciones: {sorted(set(d.metadata['section'] for d in docs))}")
    return docs

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

