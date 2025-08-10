"""
Comprehensive Tendering Analysis API
Integrates all agents and systems for complete bidding document analysis
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends, Query, Form
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pathlib import Path
import os
import tempfile
import logging
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any, List
from datetime import datetime
import zipfile
import io
from pydantic import BaseModel, Field

# Importar sistemas y agentes
import sys
import os
# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Add root project directory to Python path for utils
root_dir = os.path.dirname(backend_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from utils.bidding import BiddingAnalysisSystem, RFPAnalyzer

# Importar database manager
from utils.db_manager import get_analysis_path, db_manager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear instancia de FastAPI
app = FastAPI(
    title="Tendering Analysis API",
    description="API completa para análisis inteligente de documentos de licitación",
    version="1.0.0",
    contact={
        "name": "Team draAIgon",
    }
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración global
UPLOAD_DIR = Path("./uploads")
ANALYSIS_DB_DIR = Path("./analysis_databases")
REPORTS_DIR = Path("./reports")
TEMP_DIR = Path("./temp")

# Crear directorios
for directory in [UPLOAD_DIR, ANALYSIS_DB_DIR, REPORTS_DIR, TEMP_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# Pool de threads para procesamiento en background
executor = ThreadPoolExecutor(max_workers=4)

# Cache de sistemas y agentes
system_cache: Dict[str, BiddingAnalysisSystem] = {}
rfp_analyzer_cache: Dict[str, RFPAnalyzer] = {}

# Security (básico)
security = HTTPBearer(auto_error=False)

# Modelos de datos para requests
class AnalysisRequest(BaseModel):
    document_type: str = Field(default="unknown", description="Tipo de documento")
    analysis_level: str = Field(default="comprehensive", description="Nivel de análisis")
    provider: str = Field(default="auto", description="Proveedor de embeddings")
    force_rebuild: bool = Field(default=False, description="Forzar reconstrucción")

class ComparisonRequest(BaseModel):
    comparison_criteria: Optional[Dict] = Field(default=None, description="Criterios de comparación")
    weights: Optional[Dict[str, float]] = Field(default=None, description="Pesos personalizados")

class ReportRequest(BaseModel):
    report_type: str = Field(default="comprehensive", description="Tipo de reporte")
    include_charts: bool = Field(default=True, description="Incluir gráficos")
    format: str = Field(default="json", description="Formato de salida")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Consulta de búsqueda")
    section_filter: Optional[str] = Field(default=None, description="Filtro por sección")
    top_k: int = Field(default=5, description="Número máximo de resultados")

# ===================== ENDPOINTS PRINCIPALES =====================

@app.get("/")
async def root():
    """Información general de la API"""
    return {
        "name": "Tendering Analysis API",
        "version": "1.0.0",
        "description": "API completa para análisis inteligente de documentos de licitación",
        "features": [
            "Análisis completo de documentos",
            "Clasificación automática",
            "Comparación de propuestas",
            "Análisis de riesgo",
            "Generación de reportes",
            "Validación de cumplimiento",
            "Búsqueda semántica"
        ],
        "supported_formats": [".pdf", ".doc", ".docx"],
        "embedding_providers": ["auto", "openai", "ollama"],
        "endpoints": {
            "analysis": "/api/v1/analysis/",
            "comparison": "/api/v1/comparison/",
            "reports": "/api/v1/reports/",
            "search": "/api/v1/search/",
            "rfp": "/api/v1/rfp/",
            "documents": "/api/v1/documents/"
        }
    }

@app.get("/health")
async def health_check():
    """Health check básico"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/health")
async def api_health_check():
    """Health check de la API"""
    try:
        # Verificar que los directorios existen
        for directory in [UPLOAD_DIR, ANALYSIS_DB_DIR, REPORTS_DIR, TEMP_DIR]:
            if not directory.exists():
                directory.mkdir(exist_ok=True, parents=True)
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "analysis_available": True,
            "cache_size": len(system_cache),
            "directories_ok": True
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy", 
            "error": str(e),
            "analysis_available": False,
            "timestamp": datetime.now().isoformat()
        }

# ===================== ANÁLISIS DE DOCUMENTOS =====================

@app.post("/api/v1/analysis/upload")
async def upload_and_analyze_document(
    file: UploadFile = File(..., description="Documento a analizar"),
    request: AnalysisRequest = Depends(),
    background_tasks: BackgroundTasks = None
):
    """
    Subir y analizar un documento completo usando todos los agentes
    """
    # Validar tipo de archivo
    allowed_extensions = {".pdf", ".doc", ".docx"}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado: {file_extension}. "
                   f"Tipos permitidos: {allowed_extensions}"
        )
    
    try:
        # Guardar archivo temporal
        timestamp = int(datetime.now().timestamp())
        document_name = f"{Path(file.filename).stem}_{timestamp}"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            temp_path = tmp_file.name
        
        # Crear sistema de análisis
        system = BiddingAnalysisSystem(data_dir=str(ANALYSIS_DB_DIR / document_name))
        
        # Inicializar sistema
        system.initialize_system(provider=request.provider)
        
        logger.info(f"Iniciando análisis de {file.filename}")
        
        # Ejecutar análisis en thread pool
        loop = asyncio.get_event_loop()
        analysis_result = await loop.run_in_executor(
            executor,
            lambda: system.analyze_document(
                temp_path, 
                document_type=request.document_type,
                analysis_level=request.analysis_level
            )
        )
        
        # Limpiar archivo temporal
        os.unlink(temp_path)
        
        # Usar el document_id devuelto por el análisis para caching consistente
        actual_document_id = analysis_result.get('document_id', document_name)
        
        # Cachear sistema usando el ID correcto
        system_cache[actual_document_id] = system
        
        logger.info(f"Sistema cacheado con ID: {actual_document_id}")
        logger.info(f"Cache ahora contiene: {list(system_cache.keys())}")
        
        if analysis_result.get('errors'):
            logger.warning(f"Análisis completado con errores: {analysis_result['errors']}")
        
        # Respuesta de la API
        api_response = {
            "status": "success",
            "document_id": actual_document_id,  # Usar ID consistente
            "filename": file.filename,
            "analysis_level": request.analysis_level,
            "provider_used": request.provider,
            "analysis_result": analysis_result,
            "processing_time": datetime.now().isoformat(),
            "api_version": "1.0.0"
        }
        
        logger.info(f"Análisis completado para {file.filename}")
        return JSONResponse(content=api_response)
        
    except Exception as e:
        logger.error(f"Error analizando documento: {e}")
        if 'temp_path' in locals() and Path(temp_path).exists():
            os.unlink(temp_path)
        
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analysis/status")
async def get_analysis_status():
    """Obtener estado general del análisis"""
    try:
        # Verificar dependencias críticas
        from utils.embedding import verificar_dependencias
        dependencies_ok = verificar_dependencias()
        
        analysis_available = dependencies_ok and len(system_cache) >= 0
        
        return {
            "status": "operational" if analysis_available else "limited",
            "analysis_available": analysis_available,
            "dependencies_ok": dependencies_ok,
            "active_analyses": len(system_cache),
            "cached_systems": list(system_cache.keys()),
            "timestamp": datetime.now().isoformat(),
            "message": "Sistema de análisis operativo" if analysis_available else "Análisis limitado - verifica dependencias"
        }
    except Exception as e:
        logger.error(f"Error verificando estado del análisis: {e}")
        return {
            "status": "error",
            "analysis_available": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "message": "Error verificando estado del análisis"
        }
    
def load_analysis_from_disk(document_id: str) -> Optional[Dict[str, Any]]:
    """
    Cargar resultados de análisis desde disco si existen
    
    Args:
        document_id: ID del documento
        
    Returns:
        Resultados del análisis o None si no se encuentran
    """
    try:
        # Usar path estandarizado para análisis
        analysis_db_path = get_analysis_path(document_id)
        
        # Verificar si existe la base de datos de análisis
        if analysis_db_path.exists():
            # Buscar archivos de resultados JSON
            for json_file in analysis_db_path.glob("*.json"):
                if "analysis_result" in json_file.name or "summary" in json_file.name:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                        logger.info(f"Análisis cargado desde disco: {json_file}")
                        return result
            
            # Si no hay archivos JSON, buscar bases de datos vectoriales estandarizadas
            logger.info(f"Buscando bases de datos vectoriales estandarizadas para {document_id}...")
            
            # Buscar en las ubicaciones estandarizadas
            db_info = db_manager.get_database_info()
            available_dbs = []
            
            for db_type, info in db_info['databases'].items():
                if info['exists'] and info['count'] > 0:
                    available_dbs.append(f"{db_type} ({info['count']} databases)")
            
            # Crear respuesta más informativa
            return {
                "status": "reconstructible",
                "message": f"Análisis parcial disponible. Base de datos encontrada pero sin resultados JSON guardados.",
                "document_id": document_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "available_data": {
                    "database_directory": str(analysis_db_path),
                    "standardized_dbs": available_dbs,
                    "total_vector_dbs": db_info.get('total_databases', 0)
                },
                "reconstruction_info": {
                    "can_rebuild": len(available_dbs) > 0,
                    "rebuild_endpoint": f"/api/v1/analysis/{document_id}/rebuild",
                    "note": "Use el endpoint de rebuild para intentar reconstruir el análisis desde las bases de datos vectoriales estandarizadas"
                },
                "stages": {
                    "extraction": {"status": "unknown", "message": "Requiere reconstrucción"},
                    "classification": {"status": "possible" if available_dbs else "unknown", "message": f"Bases de datos estandarizadas disponibles: {len(available_dbs)}"},
                    "validation": {"status": "unknown", "message": "Requiere reconstrucción"},
                    "risk_analysis": {"status": "unknown", "message": "Requiere reconstrucción"}
                }
            }
                
        logger.warning(f"No se encontró análisis en disco para {document_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error cargando análisis desde disco: {e}")
        return None

@app.post("/api/v1/analysis/{document_id}/rebuild")
async def rebuild_analysis_from_disk(document_id: str, background_tasks: BackgroundTasks):
    """
    Intentar reconstruir análisis desde bases de datos vectoriales estandarizadas
    """
    try:
        # Verificar si ya existe en caché
        if document_id in system_cache:
            system = system_cache[document_id]
            if document_id in system.analysis_results:
                return JSONResponse(content={
                    "status": "success",
                    "message": "El análisis ya está disponible en memoria",
                    "document_id": document_id
                })
        
        # Verificar si existe base de datos de análisis usando path estandarizado
        analysis_db_path = get_analysis_path(document_id)
        if not analysis_db_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró base de datos de análisis para {document_id}"
            )
        
        # Obtener información de bases de datos estandarizadas
        db_info = db_manager.get_database_info()
        available_dbs = [db_type for db_type, info in db_info['databases'].items() 
                        if info['exists'] and info['count'] > 0]
        
        if not available_dbs:
            return JSONResponse(
                status_code=202,
                content={
                    "status": "partial_failure",
                    "message": "No se encontraron bases de datos vectoriales estandarizadas para reconstruir el análisis",
                    "document_id": document_id,
                    "database_info": db_info,
                    "available_actions": [
                        "Re-upload el documento original para análisis completo",
                        "Verificar que las bases de datos vectoriales existan en ubicaciones estandarizadas"
                    ]
                }
            )
        
        # Intentar reconstrucción básica con información estandarizada
        reconstructed_analysis = {
            "document_id": document_id,
            "status": "reconstructed",
            "analysis_timestamp": datetime.now().isoformat(),
            "reconstruction_timestamp": datetime.now().isoformat(),
            "message": "Análisis reconstruido desde bases de datos vectoriales estandarizadas",
            "source": "standardized_reconstruction",
            "database_info": db_info,
            "available_databases": available_dbs,
            "stages": {
                "extraction": {
                    "status": "reconstructed",
                    "message": "Estado desconocido - reconstruido desde metadatos"
                },
                "classification": {
                    "status": "available" if "classification" in available_dbs else "unavailable",
                    "message": f"Base de datos estandarizada: {'disponible' if 'classification' in available_dbs else 'no disponible'}"
                },
                "validation": {
                    "status": "available" if "validation" in available_dbs else "unavailable",
                    "message": f"Base de datos estandarizada: {'disponible' if 'validation' in available_dbs else 'no disponible'}"
                },
                "risk_analysis": {
                    "status": "available" if "risk_analysis" in available_dbs else "unavailable",
                    "message": f"Base de datos estandarizada: {'disponible' if 'risk_analysis' in available_dbs else 'no disponible'}"
                }
            },
            "summary": {
                "reconstruction_note": "Este análisis fue reconstruido desde bases de datos vectoriales estandarizadas. Los datos pueden estar incompletos.",
                "standardized_databases": len(available_dbs),
                "total_database_size_mb": db_info.get('total_size_mb', 0),
                "recommendation": "Para análisis completo, re-procese el documento original"
            }
        }
        
        # Guardar el análisis reconstruido
        try:
            result_file = analysis_db_path / "analysis_result_reconstructed.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(reconstructed_analysis, f, ensure_ascii=False, indent=2)
            logger.info(f"Análisis reconstruido guardado en {result_file}")
        except Exception as save_error:
            logger.warning(f"No se pudo guardar análisis reconstruido: {save_error}")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Análisis reconstruido exitosamente desde bases de datos vectoriales estandarizadas",
            "document_id": document_id,
            "reconstruction_info": {
                "standardized_databases": len(available_dbs),
                "databases_available": available_dbs,
                "total_size_mb": db_info.get('total_size_mb', 0)
            },
            "analysis": reconstructed_analysis
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reconstruyendo análisis: {e}")
        raise HTTPException(status_code=500, detail=f"Error en reconstrucción: {str(e)}")

@app.get("/api/v1/database/info")
async def get_database_info():
    """Obtener información completa de las bases de datos"""
    try:
        db_info = db_manager.get_database_info()
        db_list = db_manager.list_databases()
        
        return JSONResponse(content={
            "status": "success",
            "database_manager": {
                "base_directory": db_info['base_directory'],
                "analysis_directory": db_info['analysis_directory'],
                "total_databases": db_info['total_databases'],
                "total_size_mb": db_info['total_size_mb']
            },
            "databases_by_type": db_list,
            "detailed_info": db_info['databases']
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo información de base de datos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/database/migrate")
async def migrate_old_databases():
    """Migrar bases de datos de ubicaciones antiguas a estandarizadas"""
    try:
        migration_stats = db_manager.migrate_old_databases()
        
        return JSONResponse(content={
            "status": "success",
            "message": "Migración de bases de datos completada",
            "migration_stats": migration_stats
        })
        
    except Exception as e:
        logger.error(f"Error migrando bases de datos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/database/cleanup")
async def cleanup_old_databases(days_old: int = Query(30, description="Remove databases older than this many days")):
    """Limpiar bases de datos antiguas"""
    try:
        cleanup_stats = db_manager.cleanup_old_databases(days_old)
        
        return JSONResponse(content={
            "status": "success", 
            "message": f"Limpieza completada - removidas bases de datos con más de {days_old} días",
            "cleanup_stats": cleanup_stats
        })
        
    except Exception as e:
        logger.error(f"Error limpiando bases de datos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analysis/list")
async def list_available_analyses():
    """Listar todos los análisis disponibles (en caché y en disco)"""
    
    try:
        available_analyses = []
        
        # 1. Análisis en caché (memoria)
        for doc_id in system_cache:
            system = system_cache[doc_id]
            if doc_id in system.analysis_results:
                available_analyses.append({
                    "document_id": doc_id,
                    "status": "active",
                    "source": "memory",
                    "timestamp": system.analysis_results[doc_id].get("analysis_timestamp", "unknown")
                })
        
        # 2. Análisis en disco usando path estandarizado
        analysis_base_path = db_manager.ANALYSIS_DB_DIR
        if analysis_base_path.exists():
            for db_dir in analysis_base_path.iterdir():
                if db_dir.is_dir():
                    doc_id = db_dir.name
                    
                    # Skip if already in memory
                    if doc_id in system_cache:
                        continue
                    
                    # Check for analysis files
                    result_file = db_dir / "analysis_result.json"
                    summary_file = db_dir / "analysis_summary.json"
                    reconstructed_file = db_dir / "analysis_result_reconstructed.json"
                    
                    if result_file.exists() or summary_file.exists() or reconstructed_file.exists():
                        timestamp = "unknown"
                        status = "stored"
                        
                        # Check reconstructed file first
                        if reconstructed_file.exists():
                            status = "reconstructed"
                            try:
                                with open(reconstructed_file, 'r', encoding='utf-8') as f:
                                    recon_data = json.load(f)
                                    timestamp = recon_data.get("reconstruction_timestamp", "unknown")
                            except:
                                pass
                        elif summary_file.exists():
                            try:
                                with open(summary_file, 'r', encoding='utf-8') as f:
                                    summary_data = json.load(f)
                                    timestamp = summary_data.get("timestamp", "unknown")
                            except:
                                pass
                        
                        available_analyses.append({
                            "document_id": doc_id,
                            "status": status,
                            "source": "disk",
                            "timestamp": timestamp,
                            "has_results": result_file.exists(),
                            "has_summary": summary_file.exists(),
                            "has_reconstructed": reconstructed_file.exists()
                        })
                    else:
                        # Database exists but no saved results
                        available_analyses.append({
                            "document_id": doc_id,
                            "status": "reconstructible",
                            "source": "disk",
                            "timestamp": "unknown",
                            "has_results": False,
                            "has_summary": False,
                            "has_reconstructed": False,
                            "actions": ["rebuild"],
                            "message": "Analysis database exists - can attempt reconstruction"
                        })
        
        # Add database information
        db_info = db_manager.get_database_info()
        
        return JSONResponse(content={
            "status": "success",
            "total_analyses": len(available_analyses),
            "analyses": available_analyses,
            "database_info": {
                "total_vector_dbs": db_info['total_databases'],
                "total_size_mb": db_info['total_size_mb'],
                "standardized_location": db_info['base_directory']
            }
        })
        
    except Exception as e:
        logger.error(f"Error listando análisis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analysis/{document_id}")
async def get_analysis_result(document_id: str):
    """Obtener resultados de análisis de un documento"""
    
    try:
        # Primero verificar si está en caché
        if document_id in system_cache:
            system = system_cache[document_id]
            
            if document_id in system.analysis_results:
                result = system.analysis_results[document_id]
                return JSONResponse(content={
                    "status": "success",
                    "document_id": document_id,
                    "analysis": result,
                    "source": "memory"
                })
        
        # Si no está en caché, intentar cargar desde disco
        disk_result = load_analysis_from_disk(document_id)
        if disk_result:
            status_map = {
                "reconstructible": "partial",
                "partial": "partial",
                "reconstructed": "success"
            }
            
            response_status = status_map.get(disk_result.get("status"), "success")
            
            response_data = {
                "status": response_status,
                "document_id": document_id,
                "analysis": disk_result,
                "source": "disk"
            }
            
            # Add helpful actions for reconstructible analyses
            if disk_result.get("status") == "reconstructible":
                response_data["available_actions"] = [
                    {
                        "action": "rebuild",
                        "method": "POST",
                        "endpoint": f"/api/v1/analysis/{document_id}/rebuild",
                        "description": "Attempt to reconstruct analysis from vector databases"
                    },
                    {
                        "action": "re_upload",
                        "method": "POST", 
                        "endpoint": "/api/v1/analysis/upload",
                        "description": "Upload original document for complete fresh analysis"
                    }
                ]
            
            return JSONResponse(content=response_data)
        
        # Si no se encuentra en ningún lado
        raise HTTPException(
            status_code=404,
            detail="Resultados de análisis no disponibles"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo análisis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analysis/{document_id}/search")
async def semantic_search_document(
    document_id: str,
    search_request: SearchRequest
):
    """Realizar búsqueda semántica en un documento analizado"""
    
    if document_id not in system_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Documento '{document_id}' no encontrado"
        )
    
    try:
        system = system_cache[document_id]
        
        # Usar el clasificador para búsqueda semántica
        results = system.classifier.semantic_search(
            search_request.query,
            section_filter=search_request.section_filter,
            top_k=search_request.top_k
        )
        
        # Formatear resultados
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "score": float(score),
                "section": doc.metadata.get("section", "GENERAL"),
                "source": doc.metadata.get("source", "unknown"),
                "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            })
        
        return JSONResponse(content={
            "status": "success",
            "document_id": document_id,
            "query": search_request.query,
            "results_count": len(formatted_results),
            "results": formatted_results
        })
        
    except Exception as e:
        logger.error(f"Error en búsqueda semántica: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== COMPARACIÓN DE PROPUESTAS =====================

@app.post("/api/v1/comparison/upload-multiple")
async def upload_and_compare_proposals(
    files: List[UploadFile] = File(..., description="Propuestas a comparar"),
    comparison_request: ComparisonRequest = Depends()
):
    """Subir múltiples propuestas y realizar comparación completa"""
    
    if len(files) < 2:
        raise HTTPException(
            status_code=400,
            detail="Se requieren al menos 2 archivos para comparación"
        )
    
    try:
        timestamp = int(datetime.now().timestamp())
        comparison_id = f"comparison_{timestamp}"
        
        # Guardar archivos temporales
        temp_files = []
        file_names = []
        
        for i, file in enumerate(files):
            # Validar extensión
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in {".pdf", ".doc", ".docx"}:
                raise HTTPException(
                    status_code=400,
                    detail=f"Archivo {file.filename}: tipo no soportado {file_extension}"
                )
            
            # Guardar temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                temp_files.append(tmp_file.name)
                file_names.append(file.filename)
        
        # Crear sistema de análisis
        system = BiddingAnalysisSystem(data_dir=str(ANALYSIS_DB_DIR / comparison_id))
        system.initialize_system()
        
        logger.info(f"Iniciando comparación de {len(files)} propuestas")
        
        # Ejecutar comparación en thread pool
        loop = asyncio.get_event_loop()
        comparison_result = await loop.run_in_executor(
            executor,
            lambda: system.compare_proposals(
                temp_files,
                comparison_criteria=comparison_request.comparison_criteria
            )
        )
        
        # Limpiar archivos temporales
        for temp_file in temp_files:
            os.unlink(temp_file)
        
        # Cachear sistema
        system_cache[comparison_id] = system
        
        # Respuesta de la API
        api_response = {
            "status": "success",
            "comparison_id": comparison_id,
            "files_compared": file_names,
            "comparison_result": comparison_result,
            "processing_time": datetime.now().isoformat()
        }
        
        logger.info(f"Comparación completada: {comparison_id}")
        return JSONResponse(content=api_response)
        
    except Exception as e:
        logger.error(f"Error en comparación: {e}")
        # Limpiar archivos temporales
        if 'temp_files' in locals():
            for temp_file in temp_files:
                if Path(temp_file).exists():
                    os.unlink(temp_file)
        
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/comparison/{comparison_id}")
async def get_comparison_result(comparison_id: str):
    """Obtener resultados de comparación"""
    
    if comparison_id not in system_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Comparación '{comparison_id}' no encontrada"
        )
    
    try:
        system = system_cache[comparison_id]
        
        # Obtener todos los resultados de comparación disponibles
        comparison_data = {
            "comparison_id": comparison_id,
            "system_status": system.get_system_status(),
            "analysis_results": system.analysis_results
        }
        
        return JSONResponse(content={
            "status": "success",
            "comparison": comparison_data
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo comparación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== GENERACIÓN DE REPORTES =====================

@app.post("/api/v1/reports/generate/{document_id}")
async def generate_document_report(
    document_id: str,
    report_request: ReportRequest
):
    """Generar reporte completo de un documento analizado"""
    
    if document_id not in system_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Documento '{document_id}' no encontrado"
        )
    
    try:
        system = system_cache[document_id]
        
        logger.info(f"Generando reporte {report_request.report_type} para {document_id}")
        
        # Generar reporte
        report = system.generate_comprehensive_report(
            document_ids=[document_id],
            report_type=report_request.report_type
        )
        
        if report.get('error'):
            raise HTTPException(status_code=500, detail=report['error'])
        
        # Guardar reporte si es necesario
        report_filename = f"report_{document_id}_{report_request.report_type}_{int(datetime.now().timestamp())}"
        
        if report_request.format == "html" and report.get('html_content'):
            # Guardar como HTML
            report_path = REPORTS_DIR / f"{report_filename}.html"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report['html_content'])
            
            return FileResponse(
                path=report_path,
                media_type='text/html',
                filename=f"{report_filename}.html"
            )
        
        elif report_request.format == "json":
            # Respuesta JSON
            return JSONResponse(content={
                "status": "success",
                "document_id": document_id,
                "report_type": report_request.report_type,
                "report": report,
                "generated_at": datetime.now().isoformat()
            })
        
        else:
            # Formato por defecto
            return JSONResponse(content=report)
        
    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/reports/comparison/{comparison_id}")
async def generate_comparison_report(
    comparison_id: str,
    report_request: ReportRequest
):
    """Generar reporte de comparación de propuestas"""
    
    if comparison_id not in system_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Comparación '{comparison_id}' no encontrada"
        )
    
    try:
        system = system_cache[comparison_id]
        
        # Obtener todos los document_ids del análisis
        document_ids = list(system.analysis_results.keys())
        
        if not document_ids:
            raise HTTPException(
                status_code=404,
                detail="No hay documentos analizados disponibles para el reporte"
            )
        
        logger.info(f"Generando reporte de comparación para {len(document_ids)} documentos")
        
        # Generar reporte
        report = system.generate_comprehensive_report(
            document_ids=document_ids,
            report_type="comparison"
        )
        
        return JSONResponse(content={
            "status": "success",
            "comparison_id": comparison_id,
            "documents_included": len(document_ids),
            "report": report,
            "generated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generando reporte de comparación: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== ANÁLISIS DE RFP =====================

@app.post("/api/v1/rfp/analyze")
async def analyze_rfp_document(
    file: UploadFile = File(..., description="Documento RFP/Pliego"),
    provider: str = Query(default="auto", description="Proveedor de embeddings")
):
    """Análisis especializado de documentos RFP/Pliegos"""
    
    # Validar archivo
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in {".pdf", ".doc", ".docx"}:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado: {file_extension}"
        )
    
    try:
        timestamp = int(datetime.now().timestamp())
        rfp_id = f"rfp_{Path(file.filename).stem}_{timestamp}"
        
        # Guardar archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            temp_path = tmp_file.name
        
        # Crear analizador RFP
        rfp_analyzer = RFPAnalyzer(data_dir=str(ANALYSIS_DB_DIR / rfp_id))
        rfp_analyzer.bidding_system.initialize_system(provider=provider)
        
        logger.info(f"Iniciando análisis RFP de {file.filename}")
        
        # Ejecutar análisis en thread pool
        loop = asyncio.get_event_loop()
        rfp_analysis = await loop.run_in_executor(
            executor,
            lambda: rfp_analyzer.analyze_rfp(temp_path)
        )
        
        # Extraer resumen de requisitos
        requirements_summary = rfp_analyzer.extract_requirements_summary(rfp_analysis)
        
        # Limpiar archivo temporal
        os.unlink(temp_path)
        
        # Cachear analizador
        rfp_analyzer_cache[rfp_id] = rfp_analyzer
        
        # Respuesta de la API
        api_response = {
            "status": "success",
            "rfp_id": rfp_id,
            "filename": file.filename,
            "provider_used": provider,
            "rfp_analysis": rfp_analysis,
            "requirements_summary": requirements_summary,
            "analyzed_at": datetime.now().isoformat()
        }
        
        logger.info(f"Análisis RFP completado: {rfp_id}")
        return JSONResponse(content=api_response)
        
    except Exception as e:
        logger.error(f"Error analizando RFP: {e}")
        if 'temp_path' in locals() and Path(temp_path).exists():
            os.unlink(temp_path)
        
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/rfp/compare")
async def compare_rfp_with_previous(
    current_rfp: UploadFile = File(..., description="RFP actual"),
    previous_rfps: List[UploadFile] = File(..., description="RFPs anteriores para comparar")
):
    """Comparar RFP actual con RFPs anteriores"""
    
    try:
        timestamp = int(datetime.now().timestamp())
        comparison_id = f"rfp_comparison_{timestamp}"
        
        # Guardar archivos temporales
        current_temp_path = None
        previous_temp_paths = []
        
        # RFP actual
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(current_rfp.filename).suffix) as tmp_file:
            content = await current_rfp.read()
            tmp_file.write(content)
            current_temp_path = tmp_file.name
        
        # RFPs anteriores
        for rfp_file in previous_rfps:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(rfp_file.filename).suffix) as tmp_file:
                content = await rfp_file.read()
                tmp_file.write(content)
                previous_temp_paths.append(tmp_file.name)
        
        # Crear analizador
        rfp_analyzer = RFPAnalyzer(data_dir=str(ANALYSIS_DB_DIR / comparison_id))
        rfp_analyzer.bidding_system.initialize_system()
        
        logger.info(f"Comparando RFP con {len(previous_rfps)} RFPs anteriores")
        
        # Ejecutar comparación
        loop = asyncio.get_event_loop()
        comparison_result = await loop.run_in_executor(
            executor,
            lambda: rfp_analyzer.compare_with_previous_rfps(
                current_temp_path,
                previous_temp_paths
            )
        )
        
        # Limpiar archivos temporales
        os.unlink(current_temp_path)
        for temp_path in previous_temp_paths:
            os.unlink(temp_path)
        
        # Cachear analizador
        rfp_analyzer_cache[comparison_id] = rfp_analyzer
        
        return JSONResponse(content={
            "status": "success",
            "comparison_id": comparison_id,
            "current_rfp": current_rfp.filename,
            "previous_rfps_count": len(previous_rfps),
            "comparison_result": comparison_result,
            "compared_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en comparación RFP: {e}")
        # Limpiar archivos temporales
        if 'current_temp_path' in locals() and current_temp_path and Path(current_temp_path).exists():
            os.unlink(current_temp_path)
        if 'previous_temp_paths' in locals():
            for temp_path in previous_temp_paths:
                if Path(temp_path).exists():
                    os.unlink(temp_path)
        
        raise HTTPException(status_code=500, detail=str(e))

# ===================== GESTIÓN DE DOCUMENTOS =====================

@app.get("/api/v1/documents/list")
async def list_processed_documents():
    """Listar todos los documentos procesados"""
    
    documents = []
    
    # Documentos individuales
    for doc_id, system in system_cache.items():
        if doc_id.startswith("doc_") or not doc_id.startswith(("comparison_", "rfp_")):
            status = system.get_system_status()
            documents.append({
                "id": doc_id,
                "type": "document",
                "status": status,
                "processed_at": status.get("timestamp")
            })
    
    # Comparaciones
    for comp_id, system in system_cache.items():
        if comp_id.startswith("comparison_"):
            status = system.get_system_status()
            documents.append({
                "id": comp_id,
                "type": "comparison",
                "status": status,
                "processed_at": status.get("timestamp")
            })
    
    # RFPs
    for rfp_id, analyzer in rfp_analyzer_cache.items():
        documents.append({
            "id": rfp_id,
            "type": "rfp",
            "status": "analyzed",
            "processed_at": datetime.now().isoformat()
        })
    
    return JSONResponse(content={
        "status": "success",
        "total_documents": len(documents),
        "documents": documents
    })

@app.delete("/api/v1/documents/{document_id}")
async def delete_document(document_id: str):
    """Eliminar documento del cache y limpiar recursos"""
    
    deleted_items = []
    
    # Buscar en cache de sistemas
    if document_id in system_cache:
        del system_cache[document_id]
        deleted_items.append("system_cache")
    
    # Buscar en cache de RFP
    if document_id in rfp_analyzer_cache:
        del rfp_analyzer_cache[document_id]
        deleted_items.append("rfp_cache")
    
    # Intentar eliminar directorio de base de datos
    db_path = ANALYSIS_DB_DIR / document_id
    if db_path.exists():
        import shutil
        shutil.rmtree(db_path)
        deleted_items.append("database")
    
    if not deleted_items:
        raise HTTPException(
            status_code=404,
            detail=f"Documento '{document_id}' no encontrado"
        )
    
    return JSONResponse(content={
        "status": "success",
        "document_id": document_id,
        "deleted_items": deleted_items,
        "deleted_at": datetime.now().isoformat()
    })

@app.post("/api/v1/documents/export/{document_id}")
async def export_document_results(document_id: str):
    """Exportar todos los resultados de un documento"""
    
    if document_id not in system_cache:
        raise HTTPException(
            status_code=404,
            detail=f"Documento '{document_id}' no encontrado"
        )
    
    try:
        system = system_cache[document_id]
        
        # Crear archivo temporal para exportación
        export_data = {
            "document_id": document_id,
            "system_status": system.get_system_status(),
            "analysis_results": system.analysis_results,
            "processed_documents": system.processed_documents,
            "exported_at": datetime.now().isoformat()
        }
        
        # Crear archivo JSON
        export_filename = f"export_{document_id}_{int(datetime.now().timestamp())}.json"
        export_path = TEMP_DIR / export_filename
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return FileResponse(
            path=export_path,
            media_type='application/json',
            filename=export_filename,
            headers={"Content-Disposition": f"attachment; filename={export_filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error exportando documento: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== UTILIDADES =====================

@app.post("/api/v1/utils/generate-synthetic")
async def generate_synthetic_documents(
    source_pdf: UploadFile = File(..., description="PDF fuente para generar documentos sintéticos"),
    count: int = Query(default=5, ge=1, le=20, description="Número de documentos a generar"),
    model: str = Query(default="gpt-4", description="Modelo OpenAI a usar")
):
    """Generar documentos sintéticos basados en un PDF fuente - TEMPORALMENTE DESHABILITADO"""
    
    raise HTTPException(
        status_code=501,
        detail="Generación de documentos sintéticos temporalmente deshabilitada. "
               "Funcionalidad en desarrollo."
    )

def generate_synthetic_docs_sync(pdf_path: str, output_dir: str, count: int, model: str):
    """Función síncrona para generar documentos sintéticos - DESHABILITADA"""
    return {
        "status": "error", 
        "error": "Generación de documentos sintéticos temporalmente deshabilitada"
    }

@app.get("/api/v1/utils/system-status")
async def get_system_status():
    """Obtener estado general del sistema"""
    
    return JSONResponse(content={
        "status": "operational",
        "version": "1.0.0",
        "cache_stats": {
            "systems_cached": len(system_cache),
            "rfp_analyzers_cached": len(rfp_analyzer_cache)
        },
        "directories": {
            "uploads": str(UPLOAD_DIR),
            "analysis_db": str(ANALYSIS_DB_DIR),
            "reports": str(REPORTS_DIR),
            "temp": str(TEMP_DIR)
        },
        "supported_features": [
            "document_analysis",
            "proposal_comparison", 
            "rfp_analysis",
            "report_generation",
            "semantic_search",
            "synthetic_generation"
        ],
        "timestamp": datetime.now().isoformat()
    })

@app.get("/api/v1/utils/debug-cache")
async def debug_cache():
    """Obtener información detallada del cache para debugging"""
    
    cache_details = []
    for doc_id, system in system_cache.items():
        system_info = {
            "document_id": doc_id,
            "analysis_results_count": len(system.analysis_results) if hasattr(system, 'analysis_results') else 0,
            "analysis_results_keys": list(system.analysis_results.keys()) if hasattr(system, 'analysis_results') else [],
            "processed_documents": list(system.processed_documents.keys()) if hasattr(system, 'processed_documents') else [],
            "system_initialized": getattr(system, 'system_initialized', False),
            "data_dir": str(system.data_dir) if hasattr(system, 'data_dir') else None
        }
        cache_details.append(system_info)
    
    return JSONResponse(content={
        "status": "success",
        "cache_summary": {
            "total_systems": len(system_cache),
            "system_cache_keys": list(system_cache.keys()),
            "rfp_cache_keys": list(rfp_analyzer_cache.keys())
        },
        "detailed_cache": cache_details,
        "timestamp": datetime.now().isoformat()
    })

@app.post("/api/v1/utils/clear-cache")
async def clear_system_cache():
    """Limpiar cache del sistema"""
    
    cache_counts = {
        "systems_cleared": len(system_cache),
        "rfp_analyzers_cleared": len(rfp_analyzer_cache)
    }
    
    system_cache.clear()
    rfp_analyzer_cache.clear()
    
    return JSONResponse(content={
        "status": "success",
        "message": "Cache del sistema limpiado",
        "cleared_items": cache_counts,
        "cleared_at": datetime.now().isoformat()
    })

# ===================== MANEJO DE ERRORES =====================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Recurso no encontrado",
            "detail": str(exc.detail) if hasattr(exc, 'detail') else "Endpoint no existe",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "detail": "Ha ocurrido un error inesperado",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
