from pathlib import Path
import re
import subprocess
import fitz
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import os
import logging
from collections import defaultdict
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def to_pdf_if_needed(path: Path) -> Path:
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
            cmd = [
                soffice_bin, "--headless", "--convert-to", "pdf", "--outdir",
                str(out_dir), str(path)
            ]
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

def pdf_to_txt(pdf_path: Path) -> Path:
    try:
        logger.info(f"Extrayendo texto de: {pdf_path.name}")
        texto = []
        with fitz.open(pdf_path) as pdf:
            total_pages = len(pdf)
            logger.info(f"Total de páginas: {total_pages}")

            for i, pagina in enumerate(pdf, 1):
                page_text = pagina.get_text()
                if page_text.strip():
                    texto.append(f"\n=== PÁGINA {i} ===\n{page_text}")
                else:
                    logger.warning(f"Página {i} sin texto (posible escaneo)")

        if not any(t.strip() for t in texto):
            try:
                import pytesseract
                from PIL import Image
                logger.warning(f"Documento sin texto detectado. Intentando OCR en {pdf_path.name}...")
                
                # Verificar que tesseract esté disponible
                try:
                    pytesseract.get_tesseract_version()
                except pytesseract.TesseractNotFoundError:
                    logger.error("Tesseract no encontrado. Instala tesseract-ocr en tu sistema.")
                    raise
                
                ocr_text = []
                with fitz.open(pdf_path) as pdf:
                    for i, pagina in enumerate(pdf, 1):
                        pix = pagina.get_pixmap(dpi=300)
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        page_ocr = pytesseract.image_to_string(img, lang="spa")
                        if page_ocr.strip():
                            ocr_text.append(f"\n=== PÁGINA {i} (OCR) ===\n{page_ocr}")
                        else:
                            logger.warning(f"OCR: Página {i} sin texto reconocible")
                            
                if ocr_text:
                    texto = ocr_text
                    logger.info(f"OCR exitoso: {len(ocr_text)} páginas procesadas")
                else:
                    logger.warning(f"OCR no pudo extraer texto de {pdf_path.name}")
                    
            except ImportError:
                logger.error("OCR no disponible. Para PDFs escaneados instala: pip install pytesseract pillow")
                logger.error("Y también instala tesseract-ocr en tu sistema operativo.")

        txt_path = pdf_path.with_suffix(".txt")
        txt_path.write_text("\n".join(texto), encoding="utf-8")
        return txt_path

    except Exception as e:
        logger.error(f"Error extrayendo texto de {pdf_path.name}: {e}")
        raise

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

def make_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=SEPARADORES + ["\n\n", "\n", ". ", " "],
        length_function=len,
        is_separator_regex=True
    )

def txt_to_documents(txt_path: Path, source_name: str):
    text = txt_path.read_text(encoding="utf-8")
    splitter = make_splitter()
    chunks = splitter.split_text(text)

    docs = []
    for ch in chunks:
        m = re.search(r"(SECCIÓN\s+[IVXLC]+|FORMULARIO\s+ÚNICO\s+DE\s+LA\s+OFERTA|CONVOCATORIA)", ch, flags=re.I)
        section = m.group(1).upper() if m else "GENERAL"
        docs.append(Document(
            page_content=ch.strip(),
            metadata={"source": source_name, "section": section}
        ))
    return docs

def make_id(doc: Document) -> str:
    base = f"{doc.metadata['source']}_{doc.metadata['section']}_{doc.page_content[:100]}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()

def build_embeddings(carpeta_lawdata, ruta_db, collection_name="Licitaciones"):
    carpeta = Path(carpeta_lawdata)
    ruta_db = Path(ruta_db)

    if not carpeta.exists():
        raise FileNotFoundError(f"Carpeta no encontrada: {carpeta}")

    ruta_db.mkdir(parents=True, exist_ok=True)
    logger.info(f"Iniciando procesamiento en: {carpeta}")

    txt_paths = []
    archivos_procesados = []
    archivos_con_error = []

    for p in carpeta.iterdir():
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

    all_docs = []
    for txt in txt_paths:
        try:
            all_docs.extend(txt_to_documents(txt, source_name=txt.stem))
        except Exception as e:
            logger.error(f"Error creando docs de {txt.name}: {e}")

    if not all_docs:
        logger.error("No se crearon documentos")
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Configura la variable OPENAI_API_KEY")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)

    ids = [make_id(doc) for doc in all_docs]
    db = Chroma(collection_name=collection_name, persist_directory=str(ruta_db), embedding=embeddings)
    db.add_documents(all_docs, ids=ids)
    db.persist()

    sections_by_doc = defaultdict(set)
    for d in all_docs:
        sections_by_doc[d.metadata["source"]].add(d.metadata["section"])
    for src, secs in sections_by_doc.items():
        logger.info(f"{src}: {sorted(secs)}")

    logger.info(f"Archivos procesados: {len(archivos_procesados)} | Errores: {len(archivos_con_error)}")
    logger.info(f"Chunks totales: {len(all_docs)}")
    return db

def test_document_processing(archivo_pdf: str):
    pdf_path = Path(archivo_pdf)
    pdf_final = to_pdf_if_needed(pdf_path)
    txt_path = pdf_to_txt(pdf_final)
    docs = txt_to_documents(txt_path, pdf_path.stem)
    logger.info(f"Chunks: {len(docs)} | Secciones: {set(d.metadata['section'] for d in docs)}")
    return docs

def verificar_dependencias():
    """
    Verifica que todas las dependencias estén instaladas y configuradas.
    """
    logger.info("🔍 Verificando dependencias...")
    
    dependencias_ok = True
    
    # 1. Verificar OpenAI API Key
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY no configurada")
        logger.info("Configura: export OPENAI_API_KEY='tu-api-key'")
        dependencias_ok = False
    else:
        logger.info("OPENAI_API_KEY configurada")
    
    # 2. Verificar LibreOffice
    soffice_bin = os.getenv("SOFFICE_BIN", "soffice")
    try:
        subprocess.run([soffice_bin, "--version"], 
                      capture_output=True, check=True, timeout=10)
        logger.info("LibreOffice disponible")
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        logger.error(f"LibreOffice no encontrado en: {soffice_bin}")
        logger.info("Instala LibreOffice o configura SOFFICE_BIN")
        dependencias_ok = False
    
    # 3. Verificar OCR (opcional)
    try:
        import pytesseract
        from PIL import Image
        pytesseract.get_tesseract_version()
        logger.info("OCR (tesseract) disponible")
    except ImportError:
        logger.warning("OCR no disponible (opcional para PDFs escaneados)")
        logger.info("Para OCR: pip install pytesseract pillow")
    except pytesseract.TesseractNotFoundError:
        logger.warning("Tesseract no encontrado (opcional)")
        logger.info("Instala tesseract-ocr en tu sistema")
    
    if dependencias_ok:
        logger.info("Todas las dependencias principales están OK")
    else:
        logger.error("Faltan dependencias críticas")
    
    return dependencias_ok