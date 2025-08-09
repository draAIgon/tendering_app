import fitz

class DocumentExtractionAgent:
    """
    Agent para extraer texto, imagenes, tablas y metadata de los documentos.
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

    def extract_text(self):
        # Check both attribute names for compatibility
        document_path = getattr(self, 'document', None) or self.document_path
        
        document_text = ""
        with fitz.open(document_path) as pdf:
            for page in pdf:
                page_text = page.get_text()
                document_text += page_text + " "
        return document_text.strip()

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
            "content": document_text,  # Change from "text" to "content" 
            "text": document_text,     # Keep for backward compatibility
            # "metadata": metadata
        }