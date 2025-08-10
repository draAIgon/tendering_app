import fitz
import re
import subprocess
import logging
import unicodedata
from pathlib import Path
from typing import List
from io import BytesIO
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentExtractionAgent:
    """
    Agent para extraer texto, imagenes, tablas y metadata de los documentos.
    
    This class provides comprehensive document extraction capabilities including:
    - PDF text extraction with OCR support
    - DOC/DOCX to PDF conversion
    - Text normalization and processing
    - Document chunking and metadata extraction
    
    Key Methods:
    - extract_text(): Basic text extraction from document
    - process_document(): Complete document processing with metadata
    - process_pdf_to_documents(): Convert PDF to Document objects with metadata (recommended)
    
    Static Methods:
    - to_pdf_if_needed(): Convert DOC/DOCX to PDF
    - pdf_to_txt(): Extract text from PDF with OCR support
    - _normalize_text(): Text normalization utility
    - _ocr_page(): OCR processing utility
    """
    def __init__(self, document_path=None):
        self.document_path = document_path
        self.document = document_path  # Support both attribute names

    @property  
    def document(self):
        return self._document if hasattr(self, '_document') else self.document_path
    
    @document.setter
    def document(self, value):
        self._document = value
        self.document_path = value

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def _ocr_page(pagina) -> str:
        """
        Performs OCR on a PDF page using pytesseract.
        """
        import pytesseract
        from PIL import Image
        pix = pagina.get_pixmap(dpi=300, alpha=False)
        img = Image.open(BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img, lang="spa+eng")

    @staticmethod
    def pdf_to_txt(pdf_path: Path, ocr_char_threshold: int = 30) -> Path:
        """
        Extrae texto de un PDF con soporte para OCR cuando es necesario.
        """
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
                            page_text = DocumentExtractionAgent._ocr_page(pagina).strip()
                            if page_text:
                                texto.append(f"\n=== PÁGINA {i} (OCR) ===\n{page_text}")
                                continue
                        except Exception as e:
                            logger.warning(f"OCR falló en página {i}: {e}")
                if page_text:
                    texto.append(f"\n=== PÁGINA {i} ===\n{page_text}")
                else:
                    texto.append(f"\n=== PÁGINA {i} ===\n")
        
        contenido = DocumentExtractionAgent._normalize_text("\n".join(texto))
        txt_path = pdf_path.with_suffix(".txt")
        txt_path.write_text(contenido, encoding="utf-8")
        return txt_path

    def extract_text(self):
        # Check both attribute names for compatibility
        document_path = getattr(self, 'document', None) or self.document_path
        
        if document_path is None:
            raise ValueError("No document provided for extraction.")
        
        document_path = Path(document_path)
        
        # Convert to PDF if needed (DOC/DOCX support)
        pdf_path = self.to_pdf_if_needed(document_path)
        
        # Extract text using the enhanced PDF text extraction
        txt_path = self.pdf_to_txt(pdf_path)
        
        # Read the extracted text
        return txt_path.read_text(encoding="utf-8")

    @staticmethod
    def process_pdf_to_documents(pdf_file_path: str, source_name: str = None) -> List:
        """
        Processes a PDF file and converts it to a list of Document objects with metadata.
        
        Args:
            pdf_file_path: Path to the PDF file to process
            source_name: Optional name for the document source (defaults to filename stem)
            
        Returns:
            List of Document objects with extracted text and metadata
        """
        from pathlib import Path
        
        # Import here to avoid circular imports
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        sys.path.append(parent_dir)
        from utils.embedding import txt_to_documents
        
        pdf_path = Path(pdf_file_path)
        if source_name is None:
            source_name = pdf_path.stem
            
        # Convert to PDF if needed (handles DOC/DOCX)
        pdf_final = DocumentExtractionAgent.to_pdf_if_needed(pdf_path)
        
        # Extract text to temporary .txt file
        txt_path = DocumentExtractionAgent.pdf_to_txt(pdf_final)
        
        # Convert to Document objects with metadata
        docs = txt_to_documents(txt_path, source_name)
        
        logger.info(f"Processed {pdf_file_path}: {len(docs)} chunks | Sections: {sorted(set(d.metadata['section'] for d in docs))}")
        return docs

    def extract_metadata(self):
        # TODO: Implement metadata extraction logic
        return {"title": "", "document_type": ""}

    def process_document(self):
        # Check both attribute names for compatibility
        document_path = getattr(self, 'document', None) or self.document_path
        
        if document_path is None:
            raise ValueError("No document provided for extraction.")
        
        document_text = self.extract_text()
        # metadata = self.extract_metadata()
        return {
            "content": document_text
            # "metadata": metadata
        }