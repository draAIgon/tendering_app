from pathlib import Path
import re
import subprocess
import fitz
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import logging
from collections import defaultdict
import hashlib
import requests
from typing import List, Optional

# Updated imports for newer LangChain versions
try:
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    from langchain.embeddings import OpenAIEmbeddings

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain.vectorstores import Chroma

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from langchain_ollama import OllamaEmbeddings
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

def get_embeddings_provider(provider: str = "auto", model: Optional[str] = None):
    """Get embeddings provider based on availability and configuration."""
    if provider not in ["auto", "openai", "ollama"]:
        raise ValueError(f"Invalid provider: {provider}. Must be 'auto', 'openai', or 'ollama'")
        
    if provider == "auto":
        if OLLAMA_AVAILABLE:
            try:
                response = requests.get("http://localhost:11434/api/version", timeout=3)
                provider = "ollama" if response.status_code == 200 else "openai"
            except Exception:
                provider = "openai"
        else:
            provider = "openai"
            
    if provider == "ollama":
        if not OLLAMA_AVAILABLE:
            raise ImportError("Ollama embeddings not available. Install langchain-ollama.")
        return OllamaEmbeddings(model=model or "nomic-embed-text")
        
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    return OpenAIEmbeddings(model=model or "text-embedding-3-small", openai_api_key=api_key)

def convert_to_pdf(file_path: Path) -> Path:
    """Convert document to PDF format if necessary."""
    if file_path.suffix.lower() == ".pdf":
        return file_path
        
    if file_path.suffix.lower() in [".doc", ".docx"]:
        soffice = os.getenv("SOFFICE_BIN", "soffice")
        
        # Check if LibreOffice is available
        try:
            subprocess.run([soffice, "--version"], check=True, capture_output=True, timeout=10)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise FileNotFoundError(f"LibreOffice not found or not working ('{soffice}'). Set SOFFICE_BIN environment variable. Error: {e}")
        
        # Convert to PDF
        try:
            cmd = [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(file_path.parent), str(file_path)]
            result = subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            pdf_path = file_path.with_suffix(".pdf")
            
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF conversion failed: {file_path.name}")
            return pdf_path
            
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"PDF conversion timed out for: {file_path.name}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"PDF conversion failed: {e.stderr.decode() if e.stderr else str(e)}")
    
    raise ValueError(f"Unsupported file format: {file_path.suffix}")

def extract_text(pdf_path: Path) -> str:
    parts = []
    try:
        import pytesseract
        from PIL import Image
        ocr_ok = True
    except ImportError:
        ocr_ok = False
    with fitz.open(pdf_path) as pdf:
        for i, page in enumerate(pdf, 1):
            txt = page.get_text()
            if txt.strip():
                parts.append(f"\n=== PÁGINA {i} ===\n{txt}")
                continue
            if ocr_ok:
                pix = page.get_pixmap(dpi=150, alpha=False)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr_txt = pytesseract.image_to_string(img, lang="spa").strip()
                if ocr_txt:
                    parts.append(f"\n=== PÁGINA {i} (OCR) ===\n{ocr_txt}")
                    continue
                logger.warning(f"OCR sin resultados en página {i}")
            else:
                logger.warning(f"Página {i} sin texto - OCR no disponible")
    return "\n".join(parts)

def create_documents(text: str, source_name: str) -> List[Document]:
    separators = [
        r"\nSECCIÓN\s+[IVXLC]+",
        r"\nCAPÍTULO\s+[IVXLC]+",
        r"\n\d+\.\d+(?:\.\d+)?\s",
        r"\n\d+\.\s*[A-ZÁÉÍÓÚÑ]",
        r"\n[A-ZÁÉÍÓÚÑ ]{10,}\n",
        r"\nFORMULARIO\s+ÚNICO\s+DE\s+LA\s+OFERTA",
        r"\nCONVOCATORIA",
        r"\nOBJETO\s+DE",
        r"\nCONDICIONES",
        r"\nREQUISITOS",
        "\n\n",
        "\n",
        ". ",
        " "
    ]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=separators,
        is_separator_regex=True
    )
    chunks = splitter.split_text(text)
    documents: List[Document] = []
    for chunk in chunks:
        m = re.search(r"(SECCIÓN\s+[IVXLC]+|CAPÍTULO\s+[IVXLC]+|FORMULARIO\s+ÚNICO\s+DE\s+LA\s+OFERTA|CONVOCATORIA)", chunk, re.I)
        section = m.group(1).upper() if m else "GENERAL"
        documents.append(Document(page_content=chunk.strip(), metadata={"source": source_name, "section": section}))
    return documents

def build_embeddings(
    input_folder: str, 
    output_db: str, 
    provider: str = "auto", 
    collection_name: str = "Licitaciones", 
    model: Optional[str] = None
):
    """Build embeddings database from documents in input folder."""
    # Validate inputs
    if not input_folder or not output_db:
        raise ValueError("input_folder and output_db cannot be empty")
    
    if provider not in ["auto", "openai", "ollama"]:
        raise ValueError(f"Invalid provider: {provider}. Must be 'auto', 'openai', or 'ollama'")
    
    input_path = Path(input_folder)
    output_path = Path(output_db)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input folder not found: {input_path}")
    
    if not input_path.is_dir():
        raise ValueError(f"Input path is not a directory: {input_path}")
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    all_documents: List[Document] = []
    processed_files = []
    supported_extensions = [".pdf", ".doc", ".docx"]
    
    for file_path in input_path.iterdir():
        if file_path.suffix.lower() in supported_extensions:
            try:
                logger.info(f"Processing: {file_path.name}")
                pdf_path = convert_to_pdf(file_path)
                text = extract_text(pdf_path)
                
                if text.strip():
                    docs = create_documents(text, pdf_path.stem)
                    all_documents.extend(docs)
                    processed_files.append(file_path.name)
                    logger.info(f"Created {len(docs)} chunks")
                else:
                    logger.warning(f"No extractable text: {file_path.name}")
                    
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
    
    if not all_documents:
        raise ValueError("No valid documents were processed")
    
    embeddings = get_embeddings_provider(provider=provider, model=model)
    ids = [f"doc_{i:06d}" for i in range(len(all_documents))]
    
    db = Chroma(
        collection_name=collection_name, 
        persist_directory=str(output_path), 
        embedding_function=embeddings
    )
    
    db.add_documents(all_documents, ids=ids)
    db.persist()
    
    # Log summary
    sections_by_doc = defaultdict(set)
    for doc in all_documents:
        sections_by_doc[doc.metadata["source"]].add(doc.metadata["section"])
    
    for source, sections in sections_by_doc.items():
        logger.info(f"{source}: {sorted(sections)}")
    
    logger.info(f"Completed: {len(processed_files)} files, {len(all_documents)} chunks")
    return db

def test_processing(file_path: str):
    path = Path(file_path)
    pdf_path = convert_to_pdf(path)
    text = extract_text(pdf_path)
    docs = create_documents(text, path.stem)
    sections = set(doc.metadata['section'] for doc in docs)
    logger.info(f"Archivo: {path.name}")
    logger.info(f"Chunks: {len(docs)}")
    logger.info(f"Secciones: {sorted(sections)}")
    return docs
