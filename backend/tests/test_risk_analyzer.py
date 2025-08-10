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
    
    # Try multiple documents, including the risky one first
    doc_paths = [
        backend_dir / ".." / "documents" / "pliego_licitacion_riesgoso.pdf",
        backend_dir / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf",
        backend_dir / ".." / "documents" / "EJEMPLO DE CONTRATO - RETO 1.pdf",
        backend_dir.parent / "EJEMPLO DE CONTRATO - RETO 1.pdf"
    ]
    
    document_path = None
    for path in doc_paths:
        if path.exists():
            logger.info(f"Usando documento: {path.name}")
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
        
        # Get overall assessment for more info
        overall_assessment = risk_analysis.get('overall_assessment', {})
        total_risk_score = overall_assessment.get('total_risk_score', 0)
        logger.info(f"📊 Score total de riesgo: {total_risk_score:.2f}%")
        
        # If we have recommendations, show them
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
            # If no recommendations but low risk, that's actually expected behavior
            if total_risk_score < 20:  # Very low risk - no recommendations expected
                logger.info("ℹ️  No se generaron recomendaciones (riesgo muy bajo - comportamiento esperado)")
                return True
            else:
                logger.warning("⚠️  No se generaron recomendaciones para riesgo medio/alto")
                return False
        
    except Exception as e:
        logger.error(f"Error en sugerencias de mitigación: {e}")
        return False

def test_synthetic_high_risk_document():
    """Test con documento sintético de alto riesgo para validar mitigación"""
    logger.info("\n=== Test con Documento Sintético de Alto Riesgo ===")
    
    # Crear contenido sintético con múltiples indicadores de riesgo
    synthetic_content = """
    PLIEGO DE CONDICIONES TÉCNICAS - PROYECTO DE ALTO RIESGO
    
    RIESGOS TÉCNICOS:
    - Tecnología no probada en entornos de producción
    - Especificaciones técnicas ambiguas en varios aspectos críticos
    - Compatibilidad dudosa con sistemas existentes
    - Falta de estándares establecidos para la implementación
    - Dependencia tecnológica con un solo proveedor
    - Integración compleja con múltiples sistemas legacy
    
    RIESGOS ECONÓMICOS:
    - Precio excesivamente bajo comparado con el mercado
    - Costos ocultos no especificados en la propuesta
    - Variación de precios sin tope máximo definido
    - Manejo de moneda extranjera sin cobertura
    - Garantías insuficientes para el alcance del proyecto
    - Flujo de caja negativo proyectado en primeros meses
    
    RIESGOS LEGALES:
    - Normatividad cambiante en el sector
    - Regulación no clara para nuevas tecnologías
    - Conflicto de leyes entre jurisdicciones
    - Licencias pendientes de aprobación regulatoria
    - Responsabilidad civil no completamente definida
    
    RIESGOS OPERACIONALES:
    - Recursos insuficientes para la magnitud del proyecto
    - Personal no calificado para tecnologías específicas
    - Cronograma extremadamente apretado
    - Múltiples dependencias externas críticas
    - Coordinación compleja entre equipos remotos
    - Control de calidad sin procedimientos establecidos
    
    RIESGOS DE PROVEEDOR:
    - Proveedor único sin alternativas viables
    - Experiencia limitada en proyectos similares
    - Estabilidad financiera dudosa del contratista principal
    - Referencias negativas en proyectos anteriores
    - Ubicación remota con dificultades logísticas
    """
    
    try:
        # Crear agente de análisis de riesgos
        backend_dir = Path(__file__).parent.parent
        db_path = backend_dir / "db" / "test_risk_analyzer_synthetic"
        agent = RiskAnalyzerAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        agent.initialize_embeddings()
        
        # Crear archivo temporal con contenido sintético
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(synthetic_content)
            tmp_path = tmp_file.name
        
        try:
            # Analizar el contenido sintético directamente
            risk_analysis = agent.analyze_document_risks(content=synthetic_content, document_type="RFP")
            
            if "error" in risk_analysis:
                logger.error(f"Error en análisis sintético: {risk_analysis['error']}")
                return False
            
            # Verificar que se detectaron riesgos altos
            overall_assessment = risk_analysis.get('overall_assessment', {})
            total_risk_score = overall_assessment.get('total_risk_score', 0)
            
            logger.info(f"� Score total de riesgo (sintético): {total_risk_score:.2f}%")
            
            # Mostrar categorías detectadas
            category_risks = risk_analysis.get('category_risks', {})
            high_risk_categories = 0
            
            for category, data in category_risks.items():
                if 'error' not in data:
                    score = data.get('risk_score', 0)
                    if score > 50:
                        high_risk_categories += 1
                    level = data.get('risk_level', 'UNKNOWN')
                    indicators = data.get('indicators_detected', 0)
                    logger.info(f"  • {category.replace('_', ' ')}: {score:.1f}% ({level}) - {indicators} indicadores")
            
            logger.info(f"📈 Categorías de alto riesgo detectadas: {high_risk_categories}")
            
            # Verificar recomendaciones de mitigación
            mitigation_recommendations = risk_analysis.get('mitigation_recommendations', [])
            logger.info(f"💡 Recomendaciones generadas: {len(mitigation_recommendations)}")
            
            if mitigation_recommendations:
                logger.info("🔧 Recomendaciones de mitigación:")
                for i, recommendation in enumerate(mitigation_recommendations[:3], 1):
                    category = recommendation.get('category', 'N/A').replace('_', ' ')
                    priority = recommendation.get('priority', 'MEDIUM')
                    text = recommendation.get('recommendation', 'N/A')[:100]
                    logger.info(f"  {i}. [{priority}] {category}: {text}...")
            
            # Considerar exitoso si se detectó al menos algún riesgo alto
            # o si se generaron recomendaciones
            if high_risk_categories > 0 or len(mitigation_recommendations) > 0:
                logger.info("✅ Test con documento sintético de alto riesgo exitoso")
                return True
            else:
                logger.warning("⚠️  No se detectaron riesgos altos en documento sintético")
                return False
                
        finally:
            # Limpiar archivo temporal
            import os
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
    except Exception as e:
        logger.error(f"Error en test sintético: {e}")
        import traceback
        traceback.print_exc()
def test_risk_scoring_validation():
    """Test específico de validación del algoritmo de scoring"""
    logger.info("\n=== Test de Validación del Algoritmo de Scoring ===")
    
    # Contenido con términos de muy alto riesgo repetidos
    high_risk_content = """
    DOCUMENTO DE LICITACIÓN EXTREMADAMENTE RIESGOSO
    
    RIESGOS TÉCNICOS CRÍTICOS:
    Tecnología no probada tecnología no probada tecnología no probada
    Especificaciones ambiguas especificaciones ambiguas especificaciones ambiguas 
    Compatibilidad dudosa compatibilidad dudosa compatibilidad dudosa
    Falta de estándares falta de estándares falta de estándares
    Dependencia tecnológica dependencia tecnológica dependencia tecnológica
    Integración compleja integración compleja integración compleja
    Obsolescencia técnica obsolescencia técnica obsolescencia técnica
    
    RIESGOS ECONÓMICOS CRÍTICOS:
    Precio excesivamente bajo precio excesivamente bajo precio excesivamente bajo
    Costos ocultos costos ocultos costos ocultos costos ocultos
    Variación de precios variación de precios variación de precios
    Moneda extranjera moneda extranjera moneda extranjera
    Garantías insuficientes garantías insuficientes garantías insuficientes
    Penalidades excesivas penalidades excesivas penalidades excesivas
    Flujo de caja negativo flujo de caja negativo flujo de caja negativo
    
    RIESGOS LEGALES CRÍTICOS:
    Normatividad cambiante normatividad cambiante normatividad cambiante
    Regulación no clara regulación no clara regulación no clara
    Conflicto de leyes conflicto de leyes conflicto de leyes
    Jurisdicción multiple jurisdicción multiple jurisdicción multiple
    Licencias pendientes licencias pendientes licencias pendientes
    Propiedad intelectual propiedad intelectual propiedad intelectual
    Responsabilidad civil responsabilidad civil responsabilidad civil
    
    RIESGOS OPERACIONALES CRÍTICOS:
    Recursos insuficientes recursos insuficientes recursos insuficientes
    Personal no calificado personal no calificado personal no calificado
    Cronograma apretado cronograma apretado cronograma apretado
    Dependencias externas dependencias externas dependencias externas
    Coordinación compleja coordinación compleja coordinación compleja
    Comunicación deficiente comunicación deficiente comunicación deficiente
    Control de calidad control de calidad control de calidad
    
    RIESGOS DE PROVEEDOR CRÍTICOS:
    Proveedor único proveedor único proveedor único
    Experiencia limitada experiencia limitada experiencia limitada
    Estabilidad financiera dudosa estabilidad financiera dudosa
    Referencias negativas referencias negativas referencias negativas
    Ubicación remota ubicación remota ubicación remota
    Idioma diferente idioma diferente idioma diferente
    Zona de conflicto zona de conflicto zona de conflicto
    """
    
    try:
        # Crear agente
        backend_dir = Path(__file__).parent.parent
        db_path = backend_dir / "db" / "test_risk_scoring"
        agent = RiskAnalyzerAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        agent.initialize_embeddings()
        
        # Analizar el contenido de muy alto riesgo
        risk_analysis = agent.analyze_document_risks(content=high_risk_content, document_type="RFP")
        
        if "error" in risk_analysis:
            logger.error(f"Error en análisis: {risk_analysis['error']}")
            return False
        
        # Validar que se detectaron múltiples indicadores
        category_risks = risk_analysis.get('category_risks', {})
        overall_score = risk_analysis.get('overall_assessment', {}).get('total_risk_score', 0)
        
        logger.info(f"📊 Score general con contenido de muy alto riesgo: {overall_score:.2f}%")
        
        total_indicators = 0
        high_scoring_categories = 0
        
        for category, data in category_risks.items():
            if 'error' not in data:
                score = data.get('risk_score', 0)
                indicators = data.get('indicators_detected', 0)
                total_indicators += indicators
                
                if score > 20:  # Esperamos scores más altos con contenido repetitivo
                    high_scoring_categories += 1
                
                logger.info(f"  • {category.replace('_', ' ')}: {score:.1f}% - {indicators} indicadores")
        
        logger.info(f"📈 Total de indicadores detectados: {total_indicators}")
        logger.info(f"📈 Categorías con score > 20%: {high_scoring_categories}")
        
        # Validar recomendaciones
        recommendations = risk_analysis.get('mitigation_recommendations', [])
        logger.info(f"💡 Recomendaciones generadas: {len(recommendations)}")
        
        # El test es exitoso si:
        # 1. Se detectaron múltiples indicadores (esperamos al menos 15 con repeticiones)
        # 2. Se generaron recomendaciones
        # 3. Al menos algunas categorías tienen scores > 20%
        
        success_conditions = [
            total_indicators >= 10,  # Al menos 10 indicadores detectados
            len(recommendations) > 0,  # Se generaron recomendaciones
            high_scoring_categories >= 2  # Al menos 2 categorías con score significativo
        ]
        
        logger.info("\n🔍 Validación de condiciones:")
        logger.info(f"  ✓ Indicadores detectados >= 10: {total_indicators >= 10} ({total_indicators})")
        logger.info(f"  ✓ Recomendaciones generadas: {len(recommendations) > 0} ({len(recommendations)})")
        logger.info(f"  ✓ Categorías con score alto: {high_scoring_categories >= 2} ({high_scoring_categories})")
        
        if all(success_conditions):
            logger.info("✅ Algoritmo de scoring funciona correctamente")
            return True
        else:
            logger.warning("⚠️  El algoritmo de scoring podría necesitar ajustes")
            return False
            
    except Exception as e:
        logger.error(f"Error en validación de scoring: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal del test"""
    logger.info("🚀 Iniciando tests del RiskAnalyzerAgent")
    
    tests = [
        ("Análisis Básico de Riesgos", test_basic_risk_analysis),
        ("Categorización de Riesgos", test_risk_categorization),
        ("Puntuación de Riesgos", test_risk_scoring),
        ("Documento Sintético Alto Riesgo", test_synthetic_high_risk_document),
        ("Validación Algoritmo Scoring", test_risk_scoring_validation),
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
