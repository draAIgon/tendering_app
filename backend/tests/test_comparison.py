#!/usr/bin/env python3
"""
Test script for ComparisonAgent
Tests both general document comparison and specialized tender evaluation capabilities
"""

import sys
import os
from pathlib import Path

# Agregar paths necesarios
current_dir = Path(__file__).parent
backend_dir = current_dir.parent  # Go up one level to backend directory
sys.path.append(str(backend_dir))
sys.path.append(str(backend_dir / "utils" / "agents"))

from utils.agents.comparison import ComparisonAgent
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_comparison():
    """Test básico de comparación de documentos"""
    logger.info("=== Test Básico de Comparación ===")
    
    try:
        # Crear agente unificado
        db_path = backend_dir / "db" / "test_unified_comparator"
        agent = ComparisonAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        if not agent.initialize_embeddings(provider="auto"):
            logger.warning("No se pudo inicializar embeddings, continuando con análisis básico")
        
        # Contenido de prueba
        doc1_content = """
        PROPUESTA TÉCNICA
        
        Nuestra empresa XYZ propone una solución integral para el desarrollo del sistema de gestión.
        
        METODOLOGÍA:
        Utilizaremos una metodología ágil con las siguientes fases:
        1. Análisis y diseño
        2. Desarrollo iterativo
        3. Pruebas y validación
        4. Implementación
        
        EQUIPO:
        - 2 desarrolladores senior con más de 5 años de experiencia
        - 1 arquitecto de software certificado
        - 1 tester especializado
        
        TECNOLOGÍAS:
        - Java 11, Spring Boot
        - PostgreSQL
        - Docker, Kubernetes
        
        PRESUPUESTO:
        Valor total: $150,000 USD
        Forma de pago: 30% anticipo, 70% contra entrega
        
        CRONOGRAMA:
        Duración total: 6 meses
        """
        
        doc2_content = """
        OFERTA COMERCIAL
        
        La empresa ABC presenta su propuesta para el proyecto de sistema de gestión.
        
        APPROACH TÉCNICO:
        Proponemos usar metodología waterfall con estas etapas:
        1. Requerimientos
        2. Diseño detallado
        3. Codificación
        4. Testing
        5. Deployment
        
        RECURSOS HUMANOS:
        - 1 líder técnico con 8 años de experiencia
        - 3 desarrolladores junior
        - 1 analista QA
        
        STACK TECNOLÓGICO:
        - Python, Django
        - MySQL
        - AWS Cloud
        
        ASPECTOS ECONÓMICOS:
        Costo total: $120,000 USD
        Términos de pago: 50% al inicio, 50% al final
        
        TIMELINE:
        Tiempo estimado: 8 meses
        """
        
        # Agregar documentos
        agent.add_document("propuesta_xyz", doc1_content, "proposal", 
                          metadata={"company": "XYZ", "price": 150000})
        agent.add_document("propuesta_abc", doc2_content, "proposal", 
                          metadata={"company": "ABC", "price": 120000})
        
        # Configurar base de datos vectorial
        agent.setup_vector_database()
        
        # Test 1: Análisis de similitud de contenido
        logger.info("Test 1: Análisis de similitud de contenido")
        similarity_analysis = agent.analyze_content_similarity("propuesta_xyz", "propuesta_abc")
        logger.info(f"Similitud general: {similarity_analysis['overall_similarity_score']}%")
        logger.info(f"Palabras comunes: {similarity_analysis['metrics']['common_words_count']}")
        
        # Test 2: Análisis estructural
        logger.info("Test 2: Análisis estructural")
        structural_analysis = agent.analyze_structural_compliance("propuesta_xyz", "propuesta_abc")
        logger.info(f"Cumplimiento XYZ: {structural_analysis['doc1_analysis']['compliance_percentage']:.1f}%")
        logger.info(f"Cumplimiento ABC: {structural_analysis['doc2_analysis']['compliance_percentage']:.1f}%")
        
        # Test 3: Análisis técnico
        logger.info("Test 3: Análisis técnico")
        technical_analysis = agent.analyze_technical_completeness("propuesta_xyz", "propuesta_abc")
        score_xyz = technical_analysis['doc1_analysis']['technical_completeness_score']
        score_abc = technical_analysis['doc2_analysis']['technical_completeness_score']
        logger.info(f"Score técnico XYZ: {score_xyz:.1f}")
        logger.info(f"Score técnico ABC: {score_abc:.1f}")
        
        # Test 4: Análisis económico
        logger.info("Test 4: Análisis económico")
        economic_analysis = agent.analyze_economic_competitiveness("propuesta_xyz", "propuesta_abc")
        price_xyz = economic_analysis['doc1_analysis']['estimated_total_price']
        price_abc = economic_analysis['doc2_analysis']['estimated_total_price']
        logger.info(f"Precio XYZ: ${price_xyz:,}" if price_xyz else "Precio XYZ: No detectado")
        logger.info(f"Precio ABC: ${price_abc:,}" if price_abc else "Precio ABC: No detectado")
        
        # Test 5: Comparación comprehensiva
        logger.info("Test 5: Comparación comprehensiva")
        comprehensive = agent.comprehensive_comparison("propuesta_xyz", "propuesta_abc", mode="GENERAL")
        winner = comprehensive['winner']
        score_diff = comprehensive['summary']['score_difference']
        logger.info(f"Ganador: {winner}")
        logger.info(f"Diferencia de score: {score_diff:.2f}")
        logger.info("Recomendaciones:")
        for rec in comprehensive['recommendations']:
            logger.info(f"  - {rec}")
        
        logger.info("✅ Test básico de comparación completado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test básico: {e}", exc_info=True)
        return False

def test_tender_evaluation():
    """Test especializado de evaluación de licitaciones"""
    logger.info("=== Test de Evaluación de Licitaciones ===")
    
    try:
        # Crear agente unificado
        db_path = backend_dir / "db" / "test_tender_evaluation"
        agent = ComparisonAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        if not agent.initialize_embeddings(provider="auto"):
            logger.warning("No se pudo inicializar embeddings, continuando con análisis básico")
        
        # Contenido de propuestas realistas
        proposal1_content = """
        PROPUESTA EMPRESA ALPHA S.A.
        
        1. PROPUESTA TÉCNICA
        Especificaciones técnicas: Cumplimos con todos los requisitos técnicos establecidos.
        Nuestra experiencia incluye 15 proyectos similares en los últimos 5 años.
        
        Metodología de trabajo: Implementaremos metodología PMBOK con enfoque ágil.
        El plan de trabajo incluye 4 fases principales con entregables específicos.
        
        Equipo de trabajo:
        - Project Manager certificado PMP con 10 años experiencia
        - 3 Ingenieros senior con certificaciones específicas
        - 2 Técnicos especializados
        
        2. PROPUESTA ECONÓMICA
        Precio total: $250,000.00 pesos colombianos
        Forma de pago: 20% anticipo, 40% avance 50%, 40% contra entrega final
        Desglose de costos incluido en anexo técnico
        
        3. CUMPLIMIENTO LEGAL
        Cumplimiento normatividad vigente, certificaciones ISO 9001 e ISO 27001
        Todos los documentos requeridos están anexos
        Cronograma detallado con plazos de entrega específicos
        """
        
        proposal2_content = """
        OFERTA COMERCIAL BETA LTDA
        
        ASPECTOS TÉCNICOS
        Especificaciones técnicas: Proponemos mejoras adicionales a los requisitos.
        Experiencia comprobada: 8 proyectos exitosos en sector público.
        
        Metodología: Aplicaremos metodología propia basada en mejores prácticas internacionales.
        Plan de trabajo estructurado en 5 etapas con validaciones intermedias.
        
        Personal asignado:
        - Coordinador general con 7 años experiencia
        - 2 Especialistas técnicos
        - 1 Consultor externo
        
        PROPUESTA ECONÓMICA
        Valor ofertado: $180,000.00 pesos colombianos
        Condiciones de pago: 30% inicial, 70% contra entrega
        Incluye valor agregado sin costo adicional
        
        ASPECTOS LEGALES Y DE CUMPLIMIENTO
        Cumplimiento total de normatividad aplicable
        Documentos de habilitación jurídica completos
        Plazos de entrega: Según cronograma establecido en términos de referencia
        """
        
        proposal3_content = """
        PROPUESTA GAMMA CONSULTORES
        
        COMPONENTE TÉCNICO
        Requisitos técnicos: Superamos especificaciones mínimas requeridas.
        Trayectoria: 20 años en el mercado con más de 30 proyectos ejecutados.
        
        Enfoque metodológico: Combinamos metodologías tradicionales y ágiles.
        Estrategia de implementación en 3 fases con hitos de control.
        
        Recursos humanos:
        - Director de proyecto MBA con 15 años experiencia
        - 4 Consultores senior especializados
        - Equipo de soporte técnico 24/7
        
        COMPONENTE ECONÓMICO  
        Precio propuesto: $220,000.00 pesos colombianos
        Forma de pago: 25% anticipo, 25% avance 30%, 50% entrega final
        Garantías extendidas incluidas
        
        ASPECTOS REGULATORIOS
        Cumplimiento integral de marco legal vigente
        Certificaciones de calidad actualizadas
        Cronograma optimizado con margen de contingencia
        """
        
        # Cargar propuestas
        agent.add_proposal("alpha", proposal1_content, 
                          metadata={"company": "Alpha S.A.", "price": 250000})
        agent.add_proposal("beta", proposal2_content, 
                          metadata={"company": "Beta Ltda", "price": 180000})
        agent.add_proposal("gamma", proposal3_content, 
                          metadata={"company": "Gamma Consultores", "price": 220000})
        
        # Configurar base de datos vectorial
        agent.setup_vector_database()
        
        # Test 1: Extraer scores técnicos
        logger.info("Test 1: Análisis técnico por propuesta")
        for prop_id in ["alpha", "beta", "gamma"]:
            tech_scores = agent.extract_technical_scores(prop_id)
            logger.info(f"Scores técnicos {prop_id}:")
            for criterion, score in tech_scores.items():
                logger.info(f"  {criterion}: {score:.1f}")
        
        # Test 2: Extraer datos económicos
        logger.info("Test 2: Análisis económico por propuesta")
        for prop_id in ["alpha", "beta", "gamma"]:
            econ_data = agent.extract_economic_data(prop_id)
            price = econ_data['total_price']
            logger.info(f"Datos económicos {prop_id}:")
            logger.info(f"  Precio: ${price:,}" if price else "  Precio: No detectado")
            logger.info(f"  Términos de pago: {len(econ_data['payment_terms'])} encontrados")
        
        # Test 3: Calcular compliance scores
        logger.info("Test 3: Análisis de cumplimiento")
        for prop_id in ["alpha", "beta", "gamma"]:
            compliance = agent.calculate_compliance_score(prop_id)
            logger.info(f"Compliance {prop_id}:")
            for criterion, score in compliance.items():
                logger.info(f"  {criterion}: {score:.1f}%")
        
        # Test 4: Comparación completa de propuestas
        logger.info("Test 4: Comparación completa de propuestas")
        comparison_results = agent.compare_proposals()
        
        logger.info("Ranking final:")
        for rank_data in comparison_results['ranking']:
            logger.info(f"{rank_data['rank']}. {rank_data['proposal_id']} "
                       f"(Score: {rank_data['total_score']:.1f}, "
                       f"Empresa: {rank_data['company']}, "
                       f"Precio: ${rank_data['price']:,})" if rank_data['price'] != 'N/A' 
                       else f"Precio: N/A)")
        
        # Test 5: Análisis de similaridad semántica
        logger.info("Test 5: Análisis de similaridad semántica")
        similarity = agent.semantic_similarity_analysis("alpha", "beta", "metodología técnica")
        if 'error' not in similarity:
            logger.info(f"Similaridad Alpha vs Beta: {similarity['similarity_percentage']:.1f}%")
            logger.info(f"Temas comunes: {len(similarity['common_themes'])}")
        
        # Test 6: Generar reporte
        logger.info("Test 6: Generación de reporte")
        report_path = backend_dir / "test_reports" / "tender_evaluation_report.json"
        report = agent.generate_comparison_report(report_path)
        logger.info(f"Reporte generado: {report_path}")
        
        logger.info("✅ Test de evaluación de licitaciones completado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test de licitaciones: {e}", exc_info=True)
        return False

def test_multi_document_comparison():
    """Test de comparación múltiple de documentos"""
    logger.info("=== Test de Comparación Múltiple ===")
    
    try:
        # Crear agente unificado
        db_path = backend_dir / "db" / "test_multi_comparison"
        agent = ComparisonAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        if not agent.initialize_embeddings(provider="auto"):
            logger.warning("No se pudo inicializar embeddings, continuando con análisis básico")
        
        # Contenido de múltiples documentos
        documents = {
            "doc1": "Contrato de servicios de consultoría con metodología ágil y equipo especializado.",
            "doc2": "Propuesta técnica con enfoque tradicional y recursos humanos certificados.",
            "doc3": "Oferta comercial competitiva con valor agregado y garantías extendidas.",
            "doc4": "Licitación pública para desarrollo de software con especificaciones técnicas detalladas."
        }
        
        # Cargar documentos
        for doc_id, content in documents.items():
            agent.add_document(doc_id, content, "document", 
                              metadata={"type": "test", "length": len(content)})
        
        # Configurar base de datos vectorial
        agent.setup_vector_database()
        
        # Realizar comparación múltiple
        multi_comparison = agent.compare_multiple_documents(
            list(documents.keys()), 
            comparison_type="comprehensive"
        )
        
        logger.info("Resultados de comparación múltiple:")
        logger.info(f"Total documentos: {len(multi_comparison['document_ids'])}")
        logger.info(f"Comparaciones realizadas: {multi_comparison['summary_statistics']['successful_comparisons']}")
        
        if multi_comparison['ranking']:
            logger.info("Ranking de documentos:")
            for rank_info in multi_comparison['ranking']:
                logger.info(f"{rank_info['rank']}. {rank_info['document_id']} "
                           f"(Score promedio: {rank_info['average_score']:.2f})")
        
        logger.info("✅ Test de comparación múltiple completado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test múltiple: {e}", exc_info=True)
        return False

def run_all_tests():
    """Ejecutar todos los tests"""
    logger.info("🚀 Iniciando tests del ComparisonAgent")
    
    test_results = []
    
    # Crear directorios necesarios
    test_dirs = [
        backend_dir / "db" / "test_unified_comparator",
        backend_dir / "db" / "test_tender_evaluation", 
        backend_dir / "db" / "test_multi_comparison",
        backend_dir / "test_reports"
    ]
    
    for test_dir in test_dirs:
        test_dir.mkdir(parents=True, exist_ok=True)
    
    # Ejecutar tests
    tests = [
        ("Comparación Básica", test_basic_comparison),
        ("Evaluación de Licitaciones", test_tender_evaluation),
        ("Comparación Múltiple", test_multi_document_comparison)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Ejecutando: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            logger.error(f"Error crítico en {test_name}: {e}")
            test_results.append((test_name, False))
    
    # Resumen final
    logger.info(f"\n{'='*50}")
    logger.info("RESUMEN DE TESTS")
    logger.info(f"{'='*50}")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if result:
            passed += 1
    
    logger.info(f"\nResultado final: {passed}/{total} tests exitosos")
    
    if passed == total:
        logger.info("🎉 Todos los tests del ComparisonAgent completados exitosamente!")
        return True
    else:
        logger.error(f"⚠️ {total - passed} tests fallaron")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
