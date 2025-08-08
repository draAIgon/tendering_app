import fitz

class DocumentExtractionAgent:
    """
    Agent para extraer texto, imagenes, tablas y metadata de los documentos.
    """
    def __init__(self, document_path=None):
        self.document_path = document_path

    def extract_text(self):
        document_text = ""
        with fitz.open(self.document_path) as pdf:
            for page in pdf:
                page_text = page.get_text()
                document_text += page_text + " "
        return document_text.strip()

    def extract_metadata(self):
        # TODO: Implement metadata extraction logic
        return {"title": "", "document_type": ""}

    def process_document(self):
        if self.document_path is None:
            raise ValueError("No document provided for extraction.")
        document_text = self.extract_text()
        # metadata = self.extract_metadata()
        return {
            "text": document_text,
            # "metadata": metadata
        }