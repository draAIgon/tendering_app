import fitz

class DocumentClassificationAgent:
    """
    Identifica las secciones clave del documento.
    Utiliza embedding semanticos y LLM para clasificar y organizar el contenido.
    """
    def __init__(self, document_path=None):
        self.document_path = document_path
        

    