from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory

OPEN_AI_API_KEY = "# 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"

class TenderingChatbot:
    """
    Chatbot para la extracción de información de documentos de licitación.
    Utiliza un modelo de lenguaje para procesar y extraer datos relevantes.
    """

    def __init__(self):
        # Inicialización del modelo de lenguaje y memoria
        self.llm = ChatOpenAI(
            model="gpt-4.1",
            openai_api_key=OPEN_AI_API_KEY,
            temperature=0.2,
        )
        self.llm_context = """
    Eres un analista experto en documentos de licitación para proyectos de construcción.
    Tu tarea es extraer información de documentos PDF relacionados con licitaciones
    manteniendo la estructura jerárquica del documento.
    """
        self.memory = ConversationBufferMemory(
            memory_key="history",
            return_messages=True,
            input_key="input",
            output_key="output",
        )
