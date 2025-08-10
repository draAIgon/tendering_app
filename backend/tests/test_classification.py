#!/usr/bin/env python3
"""
Test script for DocumentClassificationAgent
Demuestra las capacidades de clasificación y organización de contenido
"""

import sys
from pathlib import Path

# Agregar paths necesarios
current_dir = Path(__file__).parent
backend_dir = current_dir.parent  # Go up one level to backend directory
sys.path.append(str(backend_dir))
sys.path.append(str(backend_dir / "utils" / "agents"))

from utils.agents.document_classification import DocumentClassificationAgent
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_classification():
    """Test básico de clasificación de documentos"""
    logger.info("=== Test Básico de Clasificación ===")
    
    # Usar el documento de ejemplo
    backend_dir = current_dir.parent  # Go up to backend
    document_path = backend_dir / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf"
    
    if not document_path.exists():
        logger.warning(f"Documento no encontrado: {document_path}")
        # Buscar en otras ubicaciones
        alt_paths = [
            backend_dir.parent / "EJEMPLO DE CONTRATO - RETO 1.pdf",
            backend_dir / ".." / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf"
        ]
        
        for alt_path in alt_paths:
            if Path(alt_path).exists():
                document_path = Path(alt_path)
                logger.info(f"Documento encontrado en: {document_path}")
                break
        else:
            logger.error("No se encontró el documento de prueba")
            return False
    
    # Crear agente de clasificación
    db_dir = backend_dir / "db"
    agent = DocumentClassificationAgent(
        document_path=document_path,
        vector_db_path=db_dir / "test_classification"
    )
    
    try:
        # Procesar documento completo
        report = agent.process_document(provider="auto", force_rebuild=True)
        
        if "error" in report:
            logger.error(f"Error en procesamiento: {report['error']}")
            return False
        
        # Mostrar resultados
        logger.info("✅ Documento procesado exitosamente")
        logger.info(f"📄 Total de secciones: {report['document_info']['total_sections']}")
        logger.info(f"📝 Total de fragmentos: {report['document_info']['total_fragments']}")
        
        # Mostrar secciones encontradas
        logger.info("\n📋 Secciones clasificadas:")
        for section_name, section_info in report['sections'].items():
            confidence = report['confidence_scores'].get(section_name, 0)
            logger.info(f"  • {section_name}: {section_info['document_count']} fragmentos (Confianza: {confidence:.1f}%)")
        
        # Mostrar requisitos clave encontrados
        if report['key_requirements']:
            logger.info("\n🔍 Requisitos clave encontrados:")
            for section, requirements in report['key_requirements'].items():
                if requirements:
                    logger.info(f"  {section}:")
                    for req in requirements[:3]:  # Mostrar solo los primeros 3
                        logger.info(f"    - {req[:80]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Error durante el test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_semantic_search():
    """Test de búsqueda semántica"""
    logger.info("\n=== Test de Búsqueda Semántica ===")
    
    backend_dir = Path(__file__).parent.parent  # Go up to backend
    document_path = backend_dir / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf"
    
    # Buscar documento alternativo si no existe
    if not document_path.exists():
        alt_paths = [
            backend_dir.parent / "EJEMPLO DE CONTRATO - RETO 1.pdf",
            backend_dir / ".." / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf"
        ]
        for alt_path in alt_paths:
            if Path(alt_path).exists():
                document_path = Path(alt_path)
                break
        else:
            logger.warning("Documento no disponible para test semántico")
            return False
    
    db_dir = backend_dir / "db"
    agent = DocumentClassificationAgent(
        document_path=document_path,
        vector_db_path=db_dir / "test_classification"
    )
    
    try:
        # Inicializar (reutilizar BD existente)
        agent.initialize_embeddings()
        agent.load_or_create_vector_db()
        
        # Queries de prueba
        test_queries = [
            "requisitos técnicos del sistema",
            "condiciones económicas y precios",
            "garantías y seguros requeridos",
            "plazos de entrega y cronograma"
        ]
        
        for query in test_queries:
            logger.info(f"\n🔍 Buscando: '{query}'")
            results = agent.semantic_search(query, top_k=3)
            
            for i, (doc, score) in enumerate(results, 1):
                preview = doc.page_content[:100].replace('\n', ' ')
                section = doc.metadata.get('section', 'GENERAL')
                logger.info(f"  {i}. [Score: {score:.3f}] [{section}] {preview}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en búsqueda semántica: {e}")
        return False

def test_requirement_extraction():
    """Test de extracción de requisitos"""
    logger.info("\n=== Test de Extracción de Requisitos ===")
    
    backend_dir = Path(__file__).parent.parent  # Go up to backend
    document_path = backend_dir / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf"
    
    if not document_path.exists():
        alt_paths = [
            backend_dir.parent / "EJEMPLO DE CONTRATO - RETO 1.pdf",
            backend_dir / ".." / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf"
        ]
        for alt_path in alt_paths:
            if Path(alt_path).exists():
                document_path = Path(alt_path)
                break
        else:
            logger.warning("Documento no disponible para extracción")
            return False
    
    db_dir = backend_dir / "db"
    agent = DocumentClassificationAgent(
        document_path=document_path,
        vector_db_path=db_dir / "test_classification"
    )
    
    try:
        agent.initialize_embeddings()
        agent.load_or_create_vector_db()
        agent.classify_document_sections()
        
        # Buscar requisitos en diferentes secciones
        sections_to_check = ["REQUISITOS_TECNICOS", "CONDICIONES_ECONOMICAS", "GARANTIAS"]
        
        for section in sections_to_check:
            requirements = agent.extract_key_requirements(section)
            if requirements:
                logger.info(f"\n📋 Requisitos en {section}:")
                for i, req in enumerate(requirements[:5], 1):  # Top 5
                    logger.info(f"  {i}. {req[:120]}...")
            else:
                logger.info(f"\n📋 {section}: No se encontraron requisitos específicos")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en extracción de requisitos: {e}")
        return False

def main():
    """Función principal del test"""
    logger.info("🚀 Iniciando tests del DocumentClassificationAgent")
    
    # Verificar dependencias primero
    try:
        from utils.embedding import verificar_dependencias
        if not verificar_dependencias():
            logger.error("❌ Dependencias no satisfechas")
            return
    except Exception as e:
        logger.warning(f"No se pudo verificar dependencias: {e}")
    
    tests = [
        ("Clasificación Básica", test_basic_classification),
        ("Búsqueda Semántica", test_semantic_search),
        ("Extracción de Requisitos", test_requirement_extraction)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 Ejecutando: {test_name}")
        logger.info('='*50)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                logger.info(f"✅ {test_name} completado exitosamente")
            else:
                logger.error(f"❌ {test_name} falló")
                
        except Exception as e:
            logger.error(f"💥 Error crítico en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen final
    logger.info(f"\n{'='*50}")
    logger.info("📊 RESUMEN DE TESTS")
    logger.info('='*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"  {status} {test_name}")
    
    logger.info(f"\n🏆 Resultado final: {passed}/{total} tests exitosos")
    
    if passed == total:
        logger.info("🎉 ¡Todos los tests pasaron!")
    else:
        logger.warning(f"⚠️  {total - passed} tests fallaron")

if __name__ == "__main__":
    main()
