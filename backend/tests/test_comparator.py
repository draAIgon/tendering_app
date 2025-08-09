#!/usr/bin/env python3
"""
Test script for ComparatorAgent
Tests document comparison and similarity analysis capabilities
"""

import sys
import os
from pathlib import Path

# Agregar paths necesarios
current_dir = Path(__file__).parent
backend_dir = current_dir.parent  # Go up one level to backend directory
sys.path.append(str(backend_dir))
sys.path.append(str(backend_dir / "utils" / "agents"))

from utils.agents.comparator import ComparatorAgent
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_comparison():
    """Test básico de comparación de documentos"""
    logger.info("=== Test Básico de Comparación ===")
    
    # Buscar el documento de prueba
    backend_dir = current_dir.parent
    doc_paths = [
        backend_dir / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf",
        backend_dir / ".." / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf",
        backend_dir.parent / "EJEMPLO DE CONTRATO - RETO 1.pdf"
    ]
    
    document_path = None
    for path in doc_paths:
        if path.exists():
            logger.info(f"Documento encontrado en: {path}")
            document_path = str(path)
            break
    
    if not document_path:
        logger.warning("No se encontró documento para comparación")
        return False
    
    try:
        # Crear agente comparador
        db_path = backend_dir / "db" / "test_comparator"
        agent = ComparatorAgent(vector_db_path=db_path)
        
        # Inicializar sistema de embeddings
        if agent.initialize_embeddings():
            logger.info("✅ Sistema de embeddings inicializado")
        
        # Leer contenido del documento
        with open(document_path, 'rb') as f:
            # Para un test básico, añadimos el mismo documento dos veces
            # En una implementación real, tendríamos documentos diferentes
            logger.info("Usando el mismo documento para auto-comparación")
            
            # Simulamos tener contenido de texto (normalmente extraído del PDF)
            content = "Contrato de obra pública entre PREFECTURA DEL GUAYAS y EDIFIKA S.A. Proyecto: Ampliación de la Vía Samborondón"
            
            # Añadir documentos al sistema
            agent.add_document("doc1", content, "contract", {"source": "test1"})
            agent.add_document("doc2", content, "contract", {"source": "test2"})
            
            # Realizar comparación de similitud de contenido
            comparison_result = agent.analyze_content_similarity("doc1", "doc2")
            
            logger.info("✅ Comparación de contenido exitosa")
            logger.info(f"📊 Similitud semántica: {comparison_result.get('semantic_similarity', 0):.2f}")
            
            # Verificar estructura del resultado
            required_keys = ['semantic_similarity', 'comparison_timestamp']
            for key in required_keys:
                if key in comparison_result:
                    logger.info(f"✅ Clave encontrada: {key}")
                else:
                    logger.warning(f"⚠️  Clave faltante: {key}")
            
            return True
        
    except Exception as e:
        logger.error(f"Error durante la comparación: {e}")
        return False

def test_multiple_comparison():
    """Test de comparación múltiple"""
    logger.info("\n=== Test de Comparación Múltiple ===")
    
    backend_dir = current_dir.parent
    
    try:
        # Crear agente comparador
        db_path = backend_dir / "db" / "test_comparator"
        agent = ComparatorAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        agent.initialize_embeddings()
        
        # Simular múltiples documentos
        documents = [
            ("doc1", "Contrato de obra pública para construcción de carretera", "contract"),
            ("doc2", "Propuesta técnica para pavimentación de vías", "proposal"),
            ("doc3", "Especificaciones técnicas para asfaltado", "specification")
        ]
        
        # Añadir documentos
        for doc_id, content, doc_type in documents:
            agent.add_document(doc_id, content, doc_type)
        
        # Realizar comparación múltiple
        doc_ids = [doc[0] for doc in documents]
        comparison_result = agent.compare_multiple_documents(doc_ids)
        
        logger.info("✅ Comparación múltiple exitosa")
        logger.info(f"📊 Documentos comparados: {len(doc_ids)}")
        
        # Verificar resultados
        if 'pairwise_comparisons' in comparison_result:
            comparisons = comparison_result['pairwise_comparisons']
            logger.info(f"🔍 Comparaciones pareadas: {len(comparisons)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en comparación múltiple: {e}")
        return False

def test_similarity_analysis():
    """Test de análisis de similitud"""
    logger.info("\n=== Test de Análisis de Similitud ===")
    
    backend_dir = current_dir.parent
    
    try:
        # Crear agente comparador
        db_path = backend_dir / "db" / "test_comparator"
        agent = ComparatorAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        if agent.initialize_embeddings():
            logger.info("✅ Sistema de embeddings inicializado")
        
        # Añadir documentos de prueba
        doc1_content = "Contrato para construcción de infraestructura vial con especificaciones técnicas detalladas"
        doc2_content = "Propuesta de pavimentación de carreteras con materiales de alta calidad"
        
        agent.add_document("test_doc1", doc1_content, "contract")
        agent.add_document("test_doc2", doc2_content, "proposal")
        
        # Realizar análisis de similitud semántica
        similarity_result = agent.analyze_content_similarity("test_doc1", "test_doc2")
        
        logger.info("✅ Análisis de similitud completado")
        
        # Verificar resultado
        if 'semantic_similarity' in similarity_result:
            similarity = similarity_result['semantic_similarity']
            logger.info(f"📊 Similitud semántica: {similarity:.3f}")
            
            if 0 <= similarity <= 1:
                logger.info("✅ Valor de similitud en rango válido")
                return True
            else:
                logger.warning(f"⚠️  Valor de similitud fuera de rango: {similarity}")
                return False
        else:
            logger.error("❌ No se encontró valor de similitud semántica")
            return False
        
    except Exception as e:
        logger.error(f"Error en análisis de similitud: {e}")
        return False

def test_custom_criteria():
    """Test de criterios de comparación personalizados"""
    logger.info("\n=== Test de Criterios de Comparación ===")
    
    backend_dir = current_dir.parent
    
    try:
        # Crear agente comparador
        db_path = backend_dir / "db" / "test_comparator"
        agent = ComparatorAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        agent.initialize_embeddings()
        
        # Añadir documentos de prueba
        doc1_content = "Especificaciones técnicas: Utilizar concreto de 250 kg/cm². Plazo de ejecución: 12 meses. Garantía: 24 meses."
        doc2_content = "Propuesta técnica: Concreto de 300 kg/cm². Tiempo de entrega: 10 meses. Garantía extendida: 36 meses."
        
        agent.add_document("spec_doc", doc1_content, "specification")
        agent.add_document("prop_doc", doc2_content, "proposal")
        
        # Realizar análisis de completitud técnica
        technical_analysis = agent.analyze_technical_completeness("spec_doc", "prop_doc")
        
        logger.info("✅ Análisis técnico completado")
        
        # Verificar resultado
        if technical_analysis and 'technical_score' in technical_analysis:
            tech_score = technical_analysis['technical_score']
            logger.info(f"📊 Score técnico: {tech_score:.2f}")
            
            # Realizar análisis económico
            economic_analysis = agent.analyze_economic_competitiveness("spec_doc", "prop_doc")
            
            if economic_analysis:
                logger.info("✅ Análisis económico completado")
                logger.info("✅ Criterios personalizados funcionando correctamente")
                return True
            else:
                logger.warning("⚠️  Análisis económico incompleto")
                return False
        else:
            logger.error("❌ Análisis técnico falló")
            return False
        
    except Exception as e:
        logger.error(f"Error en criterios personalizados: {e}")
        return False

def main():
    """Función principal del test"""
    logger.info("🚀 Iniciando tests del ComparatorAgent")
    
    tests = [
        ("Comparación Básica", test_basic_comparison),
        ("Comparación Múltiple", test_multiple_comparison),
        ("Análisis de Similitud", test_similarity_analysis),
        ("Criterios Personalizados", test_custom_criteria)
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
