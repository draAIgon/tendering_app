#!/usr/bin/env python3
"""
Test script for RiskAnalyzerAgent
Tests risk identification, analysis, and scoring capabilities
"""

import sys
import os
from pathlib import Path

# Agregar paths necesarios
current_dir = Path(__file__).parent
backend_dir = current_dir.parent  # Go up one level to backend directory
sys.path.append(str(backend_dir))
sys.path.append(str(backend_dir / "utils" / "agents"))

from utils.agents.risk_analyzer import RiskAnalyzerAgent
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_risk_analysis():
    """Test básico de análisis de riesgos"""
    logger.info("=== Test Básico de Análisis de Riesgos ===")
    
    # Buscar el documento de prueba en múltiples ubicaciones
    backend_dir = current_dir.parent  # Go up to backend
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
        logger.warning(f"Documento no encontrado: {doc_paths[0]}")
        return False
    
    try:
        # Crear agente de análisis de riesgos con ruta correcta
        db_path = backend_dir / "db" / "test_risk_analyzer"
        agent = RiskAnalyzerAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        if agent.initialize_embeddings():
            logger.info("✅ Sistema de embeddings inicializado")
        
        # Realizar análisis de riesgos del documento
        risk_analysis = agent.analyze_document_risks(document_path=document_path)
        
        if "error" in risk_analysis:
            logger.error(f"Error en análisis: {risk_analysis['error']}")
            return False
        
        # Mostrar resultados
        logger.info("✅ Análisis de riesgos completado exitosamente")
        
        overall_score = risk_analysis.get('overall_assessment', {}).get('total_risk_score', 0)
        logger.info(f"📊 Score total de riesgo: {overall_score:.2f}%")
        
        # Mostrar categorías de riesgo encontradas
        category_risks = risk_analysis.get('category_risks', {})
        logger.info(f"\n🚨 Categorías de riesgo analizadas ({len(category_risks)}):")
        for category, data in category_risks.items():
            if 'error' not in data:
                score = data.get('risk_score', 0)
                indicators = data.get('indicators_detected', 0)
                level = data.get('risk_level', 'UNKNOWN')
                logger.info(f"  • {category.replace('_', ' ')}: {score:.1f}% ({level}) - {indicators} indicadores")
        
        # Mostrar riesgos críticos si los hay
        critical_risks = risk_analysis.get('critical_risks', [])
        if critical_risks:
            logger.info(f"\n⚠️  Riesgos críticos encontrados ({len(critical_risks)}):")
            for risk in critical_risks[:3]:  # Mostrar solo los primeros 3
                logger.info(f"    - {risk.get('category', 'N/A')}: Score {risk.get('score', 0):.1f}%")
        
        # Verificar estructura básica
        required_keys = ['category_risks', 'overall_assessment', 'mitigation_recommendations']
        for key in required_keys:
            if key not in risk_analysis:
                logger.error(f"❌ Clave requerida faltante: {key}")
                return False
        
        logger.info("✅ Estructura del análisis de riesgos válida")
        return True
        
    except Exception as e:
        logger.error(f"Error durante el análisis de riesgos: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_risk_categorization():
    """Test de categorización de riesgos"""
    logger.info("\n=== Test de Categorización de Riesgos ===")
    
    backend_dir = Path(__file__).parent.parent  # Go up to backend
    doc_paths = [
        backend_dir / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf",
        backend_dir / ".." / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf",
        backend_dir.parent / "EJEMPLO DE CONTRATO - RETO 1.pdf"
    ]
    
    document_path = None
    for path in doc_paths:
        if path.exists():
            document_path = str(path)
            break
    
    if not document_path:
        logger.warning("No se encontró documento para test de categorización")
        return False
    
    try:
        # Crear agente de análisis de riesgos
        db_path = backend_dir / "db" / "test_risk_analyzer"
        agent = RiskAnalyzerAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        agent.initialize_embeddings()
        
        # Realizar análisis de riesgos
        risk_analysis = agent.analyze_document_risks(document_path=document_path)
        
        if "error" in risk_analysis:
            logger.error(f"Error en análisis: {risk_analysis['error']}")
            return False
        
        # Verificar categorías específicas
        category_risks = risk_analysis.get('category_risks', {})
        expected_categories = ['TECHNICAL_RISKS', 'ECONOMIC_RISKS', 'LEGAL_RISKS', 'OPERATIONAL_RISKS', 'SUPPLIER_RISKS']
        
        found_categories = 0
        for category in expected_categories:
            if category in category_risks and 'error' not in category_risks[category]:
                found_categories += 1
                data = category_risks[category]
                logger.info(f"✅ {category.replace('_', ' ')}: Score {data.get('risk_score', 0):.1f}% - {data.get('indicators_detected', 0)} indicadores")
        
        logger.info(f"📊 Categorías analizadas exitosamente: {found_categories}/{len(expected_categories)}")
        
        # Verificar que al menos algunas categorías fueron analizadas
        if found_categories >= 3:
            logger.info("✅ Categorización de riesgos exitosa")
            return True
        else:
            logger.warning("⚠️  Pocas categorías analizadas exitosamente")
            return False
        
    except Exception as e:
        logger.error(f"Error en categorización de riesgos: {e}")
        return False

def test_risk_scoring():
    """Test de puntuación de riesgos"""
    logger.info("\n=== Test de Puntuación de Riesgos ===")
    
    backend_dir = Path(__file__).parent.parent  # Go up to backend
    doc_paths = [
        backend_dir / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf",
        backend_dir / ".." / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf",
        backend_dir.parent / "EJEMPLO DE CONTRATO - RETO 1.pdf"
    ]
    
    document_path = None
    for path in doc_paths:
        if path.exists():
            document_path = str(path)
            break
    
    if not document_path:
        logger.warning("No se encontró documento para test de puntuación")
        return False
    
    try:
        # Crear agente de análisis de riesgos
        db_path = backend_dir / "db" / "test_risk_analyzer"
        agent = RiskAnalyzerAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        agent.initialize_embeddings()
        
        # Realizar análisis de riesgos
        risk_analysis = agent.analyze_document_risks(document_path=document_path)
        
        if "error" in risk_analysis:
            logger.error(f"Error en análisis: {risk_analysis['error']}")
            return False
        
        # Verificar scores de riesgo
        overall_assessment = risk_analysis.get('overall_assessment', {})
        total_risk_score = overall_assessment.get('total_risk_score', 0)
        risk_level = overall_assessment.get('risk_level', 'UNKNOWN')
        
        logger.info(f"📊 Score total de riesgo: {total_risk_score:.2f}%")
        logger.info(f"🎯 Nivel de riesgo: {risk_level}")
        
        # Verificar distribución de riesgos
        risk_distribution = overall_assessment.get('risk_distribution', {})
        if risk_distribution:
            logger.info("📈 Distribución de riesgos por categoría:")
            for category, percentage in risk_distribution.items():
                logger.info(f"  • {category.replace('_', ' ')}: {percentage:.1f}%")
        
        # Verificar que el score está en rango válido
        if 0 <= total_risk_score <= 100:
            logger.info("✅ Score de riesgo en rango válido")
            return True
        else:
            logger.error(f"❌ Score de riesgo fuera de rango: {total_risk_score}")
            return False
        
    except Exception as e:
        logger.error(f"Error en puntuación de riesgos: {e}")
        return False

def test_mitigation_suggestions():
    """Test de sugerencias de mitigación"""
    logger.info("\n=== Test de Sugerencias de Mitigación ===")
    
    backend_dir = Path(__file__).parent.parent  # Go up to backend
    doc_paths = [
        backend_dir / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf",
        backend_dir / ".." / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf",
        backend_dir.parent / "EJEMPLO DE CONTRATO - RETO 1.pdf"
    ]
    
    document_path = None
    for path in doc_paths:
        if path.exists():
            document_path = str(path)
            break
    
    if not document_path:
        logger.warning("No se encontró documento para test de mitigación")
        return False
    
    try:
        # Crear agente de análisis de riesgos
        db_path = backend_dir / "db" / "test_risk_analyzer"
        agent = RiskAnalyzerAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        agent.initialize_embeddings()
        
        # Realizar análisis de riesgos
        risk_analysis = agent.analyze_document_risks(document_path=document_path)
        
        if "error" in risk_analysis:
            logger.error(f"Error en análisis: {risk_analysis['error']}")
            return False
        
        # Verificar recomendaciones de mitigación
        mitigation_recommendations = risk_analysis.get('mitigation_recommendations', [])
        
        logger.info(f"💡 Recomendaciones de mitigación generadas: {len(mitigation_recommendations)}")
        
        if mitigation_recommendations:
            logger.info("🔧 Principales recomendaciones:")
            for i, recommendation in enumerate(mitigation_recommendations[:3], 1):
                category = recommendation.get('category', 'N/A').replace('_', ' ')
                priority = recommendation.get('priority', 'MEDIUM')
                text = recommendation.get('recommendation', 'N/A')[:80] + "..."
                logger.info(f"  {i}. [{priority}] {category}: {text}")
            
            logger.info("✅ Sugerencias de mitigación generadas exitosamente")
            return True
        else:
            logger.warning("⚠️  No se generaron recomendaciones de mitigación")
            return False
        
    except Exception as e:
        logger.error(f"Error en sugerencias de mitigación: {e}")
        return False

def main():
    """Función principal del test"""
    logger.info("🚀 Iniciando tests del RiskAnalyzerAgent")
    
    tests = [
        ("Análisis Básico de Riesgos", test_basic_risk_analysis),
        ("Categorización de Riesgos", test_risk_categorization),
        ("Puntuación de Riesgos", test_risk_scoring),
        ("Sugerencias de Mitigación", test_mitigation_suggestions)
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
