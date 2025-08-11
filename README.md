# Hackiathon 2025 - Team draAIgon
## Reto 1 - Optimización Inteligente de Procesos de Licitación en Construcción

## Stack Tecnológico

### Backend
- **Python 3.10+** - Lenguaje principal
- **FastAPI** - Framework web para APIs REST
- **LangChain** - Framework para aplicaciones con LLM
- **ChromaDB** - Base de datos vectorial
- **PyMuPDF** - Procesamiento de documentos PDF
- **OpenAI GPT-4** - Modelos de lenguaje
- **OLLAMA** - Modelos locales alternativos
- **Pydantic** - Validación de datos
- **LibreOffice** - Conversión de documentos

### Frontend
- **Next.js 15** - Framework React de producción
- **React 19** - Biblioteca de interfaces de usuario
- **TypeScript** - Tipado estático para JavaScript
- **Tailwind CSS 4** - Framework de estilos utility-first
- **Node.js** - Runtime de JavaScript

### AI/ML Stack
- **OpenAI Embeddings** (text-embedding-3-small)
- **RecursiveCharacterTextSplitter** - Chunking de documentos
- **Vector Similarity Search** - Búsqueda semántica
- **Multi-Agent Architecture** - Sistema distribuido de agentes especializados

### Herramientas de Desarrollo
- **ESLint** - Linter para JavaScript/TypeScript
- **Pytest** - Framework de testing para Python
- **Git** - Control de versiones
- **Docker** - Contenedorización (opcional)

## Arquitectura

```mermaid
graph TB
    %% Frontend Layer
    subgraph "Frontend"
        NextJS[Next.js App<br/>React 19 + TypeScript]
        UI[UI Components<br/>Tailwind CSS]
    end

    %% API Gateway
    subgraph "API Gateway"
        FastAPI[FastAPI Main<br/>REST API]
        Auth[Authentication<br/>HTTPBearer]
    end

    %% Core System
    subgraph "Core Analysis System"
        BiddingSystem[BiddingAnalysisSystem<br/>Orchestrator]
        RFPAnalyzer[RFPAnalyzer<br/>Specialized Analysis]
    end

    %% Specialized Agents
    subgraph "Specialized Agents"
        DocExtraction[DocumentExtraction<br/>PDF/DOC Processing]
        DocClassification[DocumentClassification<br/>9-Category Taxonomy]
        RiskAnalyzer[RiskAnalyzer<br/>5-Dimension Risk]
        Validator[ComplianceValidation<br/>Regulatory Rules]
        Comparator[ComparisonAgent<br/>Multi-dimensional]
        Reporter[ReportGeneration<br/>6 Report Types]
    end

    %% Data Layer
    subgraph "Data & Storage"
        ChromaDB[(ChromaDB<br/>Vector Database)]
        DBManager[DatabaseManager<br/>Collections Manager]
        VectorStore[(Vector Storage<br/>Persistent)]
    end

    %% Embedding Layer
    subgraph "Embedding Services"
        EmbedProvider[EmbeddingProvider<br/>Dual Provider]
        OpenAIEmbed[OpenAI Embeddings<br/>text-embedding-3-small]
        OllamaEmbed[OLLAMA Embeddings<br/>Local Alternative]
    end

    %% Document Processing
    subgraph "Document Processing"
        PyMuPDF[PyMuPDF<br/>PDF Processing]
        LibreOffice[LibreOffice<br/>DOC Conversion]
        TextSplitter[RecursiveTextSplitter<br/>Smart Chunking]
    end

    %% External Services
    subgraph "External Services"
        OpenAIAPI[OpenAI API<br/>GPT Models]
        OllamaLocal[OLLAMA Local<br/>Self-hosted]
    end

    %% Frontend Connections
    NextJS --> FastAPI
    UI --> Auth

    %% API Gateway Connections
    FastAPI --> BiddingSystem
    FastAPI --> RFPAnalyzer

    %% Core System to Agents
    BiddingSystem --> DocExtraction
    BiddingSystem --> DocClassification
    BiddingSystem --> RiskAnalyzer
    BiddingSystem --> Validator
    BiddingSystem --> Comparator
    BiddingSystem --> Reporter

    %% Agents to Data Layer
    DocClassification --> ChromaDB
    RiskAnalyzer --> ChromaDB
    Validator --> ChromaDB
    Comparator --> ChromaDB

    %% Database Management
    DBManager --> ChromaDB
    DBManager --> VectorStore

    %% Embedding Connections
    DocClassification --> EmbedProvider
    RiskAnalyzer --> EmbedProvider
    Validator --> EmbedProvider
    Comparator --> EmbedProvider

    EmbedProvider --> OpenAIEmbed
    EmbedProvider --> OllamaEmbed

    %% External Service Connections
    OpenAIEmbed --> OpenAIAPI
    OllamaEmbed --> OllamaLocal

    %% Document Processing Connections
    DocExtraction --> PyMuPDF
    DocExtraction --> LibreOffice
    DocExtraction --> TextSplitter

    %% Styling
    classDef frontend fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef core fill:#e8f5e8
    classDef agents fill:#fff3e0
    classDef data fill:#fce4ec
    classDef embedding fill:#f1f8e9
    classDef processing fill:#e0f2f1
    classDef external fill:#fafafa

    class NextJS,UI frontend
    class FastAPI,Auth api
    class BiddingSystem,RFPAnalyzer core
    class DocExtraction,DocClassification,RiskAnalyzer,Validator,Comparator,Reporter agents
    class ChromaDB,DBManager,VectorStore data
    class EmbedProvider,OpenAIEmbed,OllamaEmbed embedding
    class PyMuPDF,LibreOffice,TextSplitter processing
    class OpenAIAPI,OllamaLocal external
```

### Componentes de la Arquitectura

#### Frontend Layer
- **Next.js App**: Aplicación web moderna con React 19 y Tailwind CSS
- **UI Components**: Componentes reutilizables para análisis y visualización

#### API Gateway
- **FastAPI Main**: API REST principal con documentación automática (/docs)
- **Authentication**: Sistema de seguridad con HTTPBearer tokens

#### Core Analysis System  
- **BiddingAnalysisSystem**: Orquestador central que coordina todos los agentes
- **RFPAnalyzer**: Analizador especializado para Request for Proposals

#### Specialized Agents
- **DocumentExtraction**: Procesamiento de PDF/DOC con OCR
- **DocumentClassification**: Clasificación semántica en 9 categorías
- **RiskAnalyzer**: Análisis de riesgos en 5 dimensiones (técnico, económico, legal, operacional, proveedor)
- **ComplianceValidation**: Validación de cumplimiento normativo
- **ComparisonAgent**: Comparación multi-dimensional de propuestas
- **ReportGeneration**: Generación de 6 tipos de reportes (HTML/JSON/PDF)

#### Data & Storage Layer
- **ChromaDB**: Base de datos vectorial para embeddings
- **DatabaseManager**: Gestor centralizado de colecciones vectoriales
- **Vector Storage**: Almacenamiento persistente de embeddings

#### Embedding Layer
- **EmbeddingProvider**: Proveedor dual con fallback automático
- **OpenAI Embeddings**: text-embedding-3-small para análisis semántico
- **OLLAMA Embeddings**: Alternativa local/gratuita

#### Document Processing
- **PyMuPDF**: Procesamiento avanzado de archivos PDF
- **LibreOffice**: Conversión de documentos DOC/DOCX
- **RecursiveTextSplitter**: Chunking inteligente (1000 chars, 200 overlap)

#### External Services
- **OpenAI API**: Servicios de embeddings y procesamiento de lenguaje
- **OLLAMA Local**: Modelos de embeddings ejecutados localmente

## Guía de Ejecución

### Configuración del Entorno

1. **Configurar variables de entorno**:
```bash
cp .env.example .env
# Editar .env con tu OPENAI_API_KEY
```

2. **Instalar dependencias del backend**:
```bash
cd backend
pip install -r requirements_pdf.txt
```

3. **Instalar dependencias del frontend**:
```bash
cd frontend
npm install
```

### Ejecución de Servicios

#### Iniciar el Backend API
```bash
# Opción 1: Desarrollo con auto-reload
fastapi dev backend/api/main.py --host 0.0.0.0

# Opción 2: Puerto específico
fastapi dev backend/api/main.py --host 0.0.0.0 --port 8001
```

#### Iniciar el Frontend
```bash
# Desarrollo con Next.js
cd frontend
npm run dev
```

### Acceso a los Servicios

- **API Backend**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs (Swagger UI)
- **Frontend**: http://localhost:3000
- **API Alternative**: http://localhost:8001 (si se usa puerto alternativo)

### Endpoints Principales

- `POST /api/v1/analysis/upload` - Análisis completo de documentos
- `POST /api/v1/comparison/upload-multiple` - Comparación de propuestas
- `GET /api/v1/reports/generate/{document_id}` - Generación de reportes
- `POST /api/v1/rfp/analyze` - Análisis especializado de RFP
- `GET /api/v1/utils/system-status` - Estado del sistema

### Configuración Opcional

#### Para usar OLLAMA (alternativa gratuita):
```bash
# Instalar OLLAMA
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar modelo de embeddings
ollama pull nomic-embed-text
```

#### Para instalar LibreOffice (conversión de documentos):
```bash
# Ubuntu/Debian
sudo apt-get install libreoffice

# macOS
brew install --cask libreoffice

# Windows
# Descargar desde https://www.libreoffice.org/
```
