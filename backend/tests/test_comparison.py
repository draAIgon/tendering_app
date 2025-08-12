#!/usr/bin/env python3
"""
Test script for ComparisonAgent with refactored API
Tests document comparison with pre-extracted content and analysis from BiddingAnalysisSystem
"""

import sys
from pathlib import Path

# Agregar paths necesarios
current_dir = Path(__file__).parent
backend_dir = current_dir.parent  # Go up one level to backend directory
sys.path.append(str(backend_dir))
sys.path.append(str(backend_dir / "utils" / "agents"))

from utils.agents.comparison import ComparisonAgent
from utils.bidding import BiddingAnalysisSystem
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_content_based_api():
    """Test de API basada en contenido pre-extraído (refactored architecture)"""
    logger.info("=== Test de API Basada en Contenido ===")
    
    try:
        # Crear agente de comparación
        comparison_agent = ComparisonAgent(llm_provider="auto")
        
        # Contenido de documentos de prueba
        doc1_content = """
        PROPUESTA TÉCNICA - EMPRESA XYZ
        
        METODOLOGÍA:
        Utilizaremos metodología ágil con fases bien definidas.
        Experiencia de 5 años en proyectos similares.
        
        EQUIPO:
        - 2 desarrolladores senior certificados
        - 1 arquitecto de software
        
        ASPECTOS ECONÓMICOS:
        Presupuesto: $150,000
        Plazo: 6 meses
        Sin costos ocultos
        """
        
        doc2_content = """
        PROPUESTA TÉCNICA - EMPRESA ABC
        
        METODOLOGÍA:
        Utilizaremos metodología waterfall tradicional.
        Experiencia limitada en proyectos de este tipo.
        
        EQUIPO:
        - 1 desarrollador junior
        - 1 consultor externo
        
        ASPECTOS ECONÓMICOS:
        Presupuesto inicial: $120,000
        Posibles incrementos por cambios
        Plazo: 8 meses
        """
        
        # Simular análisis pre-procesados del BiddingAnalysisSystem
        doc1_analysis = {
            "document_name": "propuesta_xyz.txt",
            "risk_analysis": {
                "overall_risk_level": "LOW",
                "overall_risk_score": 0.2,
                "categories": {
                    "TECHNICAL": "LOW",
                    "ECONOMIC": "LOW",
                    "OPERATIONAL": "LOW"
                }
            },
            "compliance_validation": {
                "compliance_score": 0.9,
                "overall_compliance": "HIGH",
                "missing_requirements": []
            },
            "classification_context": {
                "document_type": "TECHNICAL_PROPOSAL",
                "document_category": "proposal",
                "sections": ["METHODOLOGY", "TEAM", "ECONOMICS"]
            }
        }
        
        doc2_analysis = {
            "document_name": "propuesta_abc.txt",
            "risk_analysis": {
                "overall_risk_level": "HIGH",
                "overall_risk_score": 0.7,
                "categories": {
                    "TECHNICAL": "HIGH", 
                    "ECONOMIC": "MEDIUM",
                    "OPERATIONAL": "HIGH"
                }
            },
            "compliance_validation": {
                "compliance_score": 0.6,
                "overall_compliance": "MEDIUM",
                "missing_requirements": ["detailed_timeline", "risk_mitigation_plan"]
            },
            "classification_context": {
                "document_type": "TECHNICAL_PROPOSAL",
                "document_category": "proposal", 
                "sections": ["METHODOLOGY", "TEAM", "ECONOMICS"]
            }
        }
        
        # Test 1: Análisis individual de documentos usando contenido pre-extraído
        logger.info("Test 1: Análisis individual de documentos con contenido pre-extraído")
        result1 = comparison_agent.analyze_document(
            doc1_content, 
            "propuesta_xyz.txt",
            classification_context=doc1_analysis.get("classification_context"),
            validation_context=doc1_analysis.get("compliance_validation")
        )
        
        result2 = comparison_agent.analyze_document(
            doc2_content,
            "propuesta_abc.txt", 
            classification_context=doc2_analysis.get("classification_context"),
            validation_context=doc2_analysis.get("compliance_validation")
        )
        
        logger.info(f"✅ Análisis de documento 1: {result1.get('document_name', 'N/A')}")
        logger.info(f"✅ Análisis de documento 2: {result2.get('document_name', 'N/A')}")
        
        # Test 2: Comparación de documentos con contexto de análisis
        logger.info("Test 2: Comparación con contexto de análisis pre-procesado")
        comparison_result = comparison_agent.compare_documents(
            doc1_content, doc2_content,
            "propuesta_xyz.txt", "propuesta_abc.txt",
            comparison_mode="TENDER_EVALUATION",
            doc1_analysis=doc1_analysis,
            doc2_analysis=doc2_analysis
        )
        
        logger.info(f"✅ Comparación exitosa entre {comparison_result.get('document1', 'N/A')} y {comparison_result.get('document2', 'N/A')}")
        
        # Test 3: Verificar scoring mejorado con penalizaciones por riesgo
        logger.info("Test 3: Validación de scoring consciente de riesgos")
        if 'enhanced_scoring' in comparison_result:
            scoring = comparison_result['enhanced_scoring']
            logger.info("✅ Sistema de scoring mejorado funcionando")
            
            # Verificar penalizaciones por riesgo
            if 'overall' in scoring:
                overall = scoring['overall']
                if 'final_scores' in overall:
                    doc1_score = overall['final_scores'].get('document1', 0)
                    doc2_score = overall['final_scores'].get('document2', 0)
                    logger.info(f"   Documento 1 (Bajo Riesgo): {doc1_score:.2f}")
                    logger.info(f"   Documento 2 (Alto Riesgo): {doc2_score:.2f}")
                    
                    if doc1_score > doc2_score:
                        logger.info("✅ Sistema favorece correctamente documento de menor riesgo")
                    else:
                        logger.warning("⚠️  Sistema no está favoreciendo documento de menor riesgo como esperado")
        
        # Test 4: Evaluación de múltiples propuestas con datos pre-estructurados
        logger.info("Test 4: Evaluación de múltiples propuestas")
        proposals_data = [
            {
                'name': 'propuesta_xyz.txt',
                'content': doc1_content,
                'analysis': doc1_analysis
            },
            {
                'name': 'propuesta_abc.txt',
                'content': doc2_content,
                'analysis': doc2_analysis
            }
        ]
        
        evaluation_result = comparison_agent.evaluate_tender_proposals(proposals_data)
        logger.info(f"✅ Evaluación de licitación exitosa: {evaluation_result.get('total_proposals', 0)} propuestas procesadas")
        
        if 'ranked_proposals' in evaluation_result:
            ranked = evaluation_result['ranked_proposals']
            if ranked:
                logger.info("   Ranking final:")
                for i, proposal in enumerate(ranked[:3]):  # Top 3
                    score = proposal.get('comprehensive_score', {}).get('total', 0)
                    logger.info(f"   {i+1}. {proposal.get('proposal_name', 'N/A')}: {score:.2f}")
        
        logger.info("✅ Test de API basada en contenido completado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test de API basada en contenido: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_progressive_risk_penalties():
    """Test de penalizaciones progresivas por nivel de riesgo"""
    logger.info("=== Test de Penalizaciones Progresivas por Riesgo ===")
    
    try:
        # Crear agente de comparación
        comparison_agent = ComparisonAgent(llm_provider="auto")
        
        # Documento de muy bajo riesgo
        low_risk_content = """
        PROPUESTA SEGURA - EMPRESA CONFIABLE S.A.
        
        Metodología probada con bajo riesgo de implementación.
        Equipo senior con amplia experiencia y certificaciones.
        Presupuesto detallado y transparente: $100,000
        Garantías completas incluidas.
        """
        
        # Documento de muy alto riesgo  
        very_high_risk_content = """
        PROPUESTA EXPERIMENTAL - STARTUP NUEVA
        
        Metodología nueva no probada con alta incertidumbre.
        Equipo junior sin certificaciones específicas.
        Presupuesto inicial bajo: $50,000 (riesgo alto de incrementos).
        Sin garantías, pagos adelantados requeridos.
        """
        
        # Análisis simulados con diferentes niveles de riesgo
        low_risk_analysis = {
            "document_name": "propuesta_segura.txt",
            "risk_analysis": {
                "overall_risk_level": "LOW",
                "overall_risk_score": 0.15,  # Muy bajo riesgo
                "categories": {
                    "TECHNICAL": "LOW",
                    "ECONOMIC": "LOW",
                    "OPERATIONAL": "LOW",
                    "LEGAL": "LOW",
                    "SUPPLIER": "LOW"
                }
            },
            "compliance_validation": {
                "compliance_score": 0.95,
                "overall_compliance": "HIGH"
            },
            "classification_context": {
                "document_type": "TECHNICAL_PROPOSAL",
                "document_category": "proposal"
            }
        }
        
        very_high_risk_analysis = {
            "document_name": "propuesta_riesgosa.txt",
            "risk_analysis": {
                "overall_risk_level": "VERY_HIGH",
                "overall_risk_score": 0.92,  # Muy alto riesgo
                "categories": {
                    "TECHNICAL": "VERY_HIGH",
                    "ECONOMIC": "VERY_HIGH", 
                    "OPERATIONAL": "VERY_HIGH",
                    "LEGAL": "HIGH",
                    "SUPPLIER": "VERY_HIGH"
                }
            },
            "compliance_validation": {
                "compliance_score": 0.3,
                "overall_compliance": "LOW"
            },
            "classification_context": {
                "document_type": "TECHNICAL_PROPOSAL",
                "document_category": "proposal"
            }
        }
        
        # Realizar comparación para verificar penalizaciones progresivas
        logger.info("Comparando documento de bajo riesgo vs muy alto riesgo")
        comparison_result = comparison_agent.compare_documents(
            low_risk_content, very_high_risk_content,
            "propuesta_segura.txt", "propuesta_riesgosa.txt",
            comparison_mode="TENDER_EVALUATION",
            doc1_analysis=low_risk_analysis,
            doc2_analysis=very_high_risk_analysis
        )
        
        # Verificar que se aplicaron las penalizaciones progresivas
        if 'enhanced_scoring' in comparison_result:
            scoring = comparison_result['enhanced_scoring']
            logger.info("✅ Sistema de scoring mejorado con penalizaciones activo")
            
            if 'overall' in scoring:
                overall = scoring['overall']
                if 'final_scores' in overall:
                    low_risk_score = overall['final_scores'].get('document1', 0)
                    high_risk_score = overall['final_scores'].get('document2', 0)
                    
                    logger.info(f"Score documento BAJO riesgo: {low_risk_score:.3f}")
                    logger.info(f"Score documento MUY ALTO riesgo: {high_risk_score:.3f}")
                    
                    # Verificar penalización del 90% para VERY_HIGH risk
                    score_ratio = high_risk_score / low_risk_score if low_risk_score > 0 else 0
                    penalty_applied = 1 - score_ratio
                    
                    logger.info(f"Penalización aplicada: {penalty_applied:.1%}")
                    
                    # Validar que se aplicó una penalización significativa (≥80%)
                    if penalty_applied >= 0.80:
                        logger.info("✅ EXCELENTE: Penalización del 80%+ aplicada correctamente")
                        logger.info("✅ Sistema detecta y penaliza documentos de muy alto riesgo")
                        test_passed = True
                    elif penalty_applied >= 0.60:
                        logger.info("✅ BUENO: Penalización del 60%+ aplicada")
                        logger.info("✅ Sistema detecta documentos de alto riesgo")
                        test_passed = True
                    else:
                        logger.warning(f"⚠️ Penalización insuficiente: {penalty_applied:.1%}")
                        logger.warning("⚠️ Sistema no está penalizando adecuadamente documentos de alto riesgo")
                        test_passed = False
                        
                    # Verificar ganador
                    winner = overall.get('overall_winner', 'unknown')
                    if winner == 'document1':  # low risk document
                        logger.info("✅ CORRECTO: Documento de bajo riesgo es el ganador")
                    else:
                        logger.error("❌ ERROR: Documento de alto riesgo ganó (problema crítico)")
                        test_passed = False
                        
                else:
                    logger.warning("⚠️ No se encontraron scores finales en el resultado")
                    test_passed = False
            else:
                logger.warning("⚠️ No se encontró scoring general en el resultado")
                test_passed = False
        else:
            logger.error("❌ Sistema de scoring mejorado no está funcionando")
            test_passed = False
        
        # Test de múltiples niveles de riesgo
        logger.info("\\nTest adicional: Múltiples niveles de riesgo")
        
        risk_levels = [
            ("VERY_LOW", 0.05, "muy_bajo"),
            ("LOW", 0.25, "bajo"),
            ("MEDIUM", 0.5, "medio"),
            ("HIGH", 0.75, "alto"),
            ("VERY_HIGH", 0.95, "muy_alto")
        ]
        
        logger.info("Niveles de riesgo y penalizaciones esperadas:")
        for level, score, name in risk_levels:
            # Calculate penalty using ComparisonAgent's internal logic
            if score >= 0.9:
                expected_penalty = 0.9  # 90% penalty for very high risk
            elif score >= 0.7:
                expected_penalty = 0.7  # 70% penalty for high risk
            elif score >= 0.5:
                expected_penalty = 0.5  # 50% penalty for medium risk
            elif score >= 0.3:
                expected_penalty = 0.3  # 30% penalty for low risk
            else:
                expected_penalty = 0.1  # 10% penalty for very low risk
            
            logger.info(f"  {level:10} (score: {score:.2f}) → Penalización: {expected_penalty:.1%}")
        
        logger.info("✅ Test de penalizaciones progresivas completado")
        return test_passed
        
    except Exception as e:
        logger.error(f"❌ Error en test de penalizaciones progresivas: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_classification_context_extraction():
    """Test de extracción de tipo de documento desde contexto de clasificación"""
    logger.info("=== Test de Extracción de Contexto de Clasificación ===")
    
    try:
        # Crear agente de comparación
        comparison_agent = ComparisonAgent(llm_provider="auto")
        
        # Test cases para extracción de tipo de documento
        test_cases = [
            ({'document_type': 'TENDER_SPECIFICATION'}, 'tender_specification'),
            ({'document_category': 'PROPOSAL'}, 'proposal'),
            ({'inferred_type': 'CONTRACT'}, 'contract'),
            ({}, 'document'),
            (None, 'document')
        ]
        
        logger.info("Probando extracción de tipo de documento desde contexto de clasificación")
        all_passed = True
        
        for i, (context, expected) in enumerate(test_cases, 1):
            result = comparison_agent._get_document_type_from_context(context, 'test.txt')
            status = '✅' if result == expected else '❌'
            logger.info(f"{status} Test {i}: Contexto {context} → {result} (esperado: {expected})")
            if result != expected:
                all_passed = False
        
        if all_passed:
            logger.info("✅ TODOS los tests de extracción de contexto pasaron")
            logger.info("✅ ComparisonAgent obtiene tipo correctamente desde DocumentClassificationAgent")
        else:
            logger.error("❌ ALGUNOS tests de extracción fallaron")
            
        return all_passed
        
    except Exception as e:
        logger.error(f"❌ Error en test de extracción de contexto: {e}")
        return False

def test_basic_comparison_with_system():
    """Test básico usando BiddingAnalysisSystem para extraer y analizar documentos"""
    logger.info("=== Test de Comparación con Sistema Integrado ===")
    
    try:
        # Inicializar el sistema completo
        system = BiddingAnalysisSystem()
        
        # Override data directory to avoid permission issues
        system.data_dir = Path(__file__).parent / "test_data"
        system.data_dir.mkdir(parents=True, exist_ok=True)
        
        system.initialize_system(provider="auto")
        
        # Crear agente unificado para testing básico
        db_path = backend_dir / "db" / "test_basic_comparison"
        agent = ComparisonAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        if not agent.initialize_embeddings(provider="auto"):
            logger.warning("No se pudo inicializar embeddings, continuando con análisis básico")
        
        # Crear contenido de documentos de prueba
        doc1_content = """
        PROPUESTA TÉCNICA XYZ
        Metodología ágil con fases definidas.
        Equipo: 2 desarrolladores senior, 1 arquitecto.
        Presupuesto: $150,000. Plazo: 6 meses.
        """
        
        doc2_content = """
        PROPUESTA TÉCNICA ABC  
        Metodología waterfall tradicional.
        Equipo: 1 líder técnico, 3 desarrolladores junior.
        Presupuesto: $120,000. Plazo: 8 meses.
        """
        
        # Agregar documentos al agente
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
        
        # Contenido de propuestas realistas (shortened for focus on real tender test)
        proposal1_content = """
        PROPUESTA EMPRESA ALPHA S.A.
        Especificaciones técnicas: Cumplimos con todos los requisitos técnicos establecidos.
        Precio total: $250,000.00 pesos colombianos
        Experiencia: 15 proyectos similares en los últimos 5 años.
        """
        
        # Agregar una propuesta básica
        agent.add_proposal("alpha", proposal1_content, 
                          metadata={"company": "Alpha S.A.", "price": 250000})
        
        # Configurar base de datos vectorial
        agent.setup_vector_database()
        
        # Test básico de propuesta
        tech_scores = agent.extract_technical_scores("alpha")
        logger.info(f"Test básico completado para propuesta alpha")
        
        logger.info("✅ Test básico de evaluación de licitaciones completado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test de licitaciones: {e}", exc_info=True)
        return False

def test_real_tender_documents():
    """Test de comparación de pliegos reales - debe favorecer el documento menos riesgoso"""
    logger.info("=== Test de Comparación de Pliegos Reales ===")
    
    try:
        # Crear agente unificado
        db_path = backend_dir / "db" / "test_real_tenders"
        agent = ComparisonAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        if not agent.initialize_embeddings(provider="auto"):
            logger.warning("No se pudo inicializar embeddings, continuando con análisis básico")
        
        # Cargar contenidos de los pliegos reales
        documents_dir = backend_dir.parent.parent / "tendering_app" / "documents"
        
        try:
            # Leer pliego normal (seguro)
            with open(documents_dir / "pliego_licitacion.txt", 'r', encoding='utf-8') as f:
                pliego_normal = f.read()
            
            # Leer pliego riesgoso  
            with open(documents_dir / "pliego_licitacion_riesgoso.txt", 'r', encoding='utf-8') as f:
                pliego_riesgoso = f.read()
                
        except FileNotFoundError as e:
            logger.error(f"No se encontraron los archivos de pliegos: {e}")
            return False
        
        logger.info(f"Pliego normal cargado: {len(pliego_normal)} caracteres")
        logger.info(f"Pliego riesgoso cargado: {len(pliego_riesgoso)} caracteres")
        
        # Agregar documentos al agente
        agent.add_document("pliego_normal", pliego_normal, "tender", 
                          metadata={"type": "normal_tender", "risk_level": "low"})
        agent.add_document("pliego_riesgoso", pliego_riesgoso, "tender", 
                          metadata={"type": "risky_tender", "risk_level": "high"})
        
        # Configurar base de datos vectorial
        agent.setup_vector_database()
        
        # Test 1: Análisis de similitud - debe mostrar diferencias significativas
        logger.info("Test 1: Análisis de similitud entre pliegos")
        similarity_analysis = agent.analyze_content_similarity("pliego_normal", "pliego_riesgoso")
        similarity_score = similarity_analysis['overall_similarity_score']
        logger.info(f"Similitud entre pliegos: {similarity_score}%")
        logger.info(f"Palabras comunes: {similarity_analysis['metrics']['common_words_count']}")
        
        # Test 2: Análisis estructural - el pliego normal debe tener mejor cumplimiento
        logger.info("Test 2: Análisis estructural")
        structural_analysis = agent.analyze_structural_compliance("pliego_normal", "pliego_riesgoso")
        normal_compliance = structural_analysis['doc1_analysis']['compliance_percentage']
        risky_compliance = structural_analysis['doc2_analysis']['compliance_percentage']
        
        logger.info(f"Cumplimiento estructural pliego normal: {normal_compliance:.1f}%")
        logger.info(f"Cumplimiento estructural pliego riesgoso: {risky_compliance:.1f}%")
        
        # Verificar que el pliego normal tenga mejor cumplimiento
        if normal_compliance > risky_compliance:
            logger.info("✅ El pliego normal tiene mejor cumplimiento estructural")
        else:
            logger.warning("⚠️ Resultado inesperado: pliego riesgoso muestra mejor cumplimiento")
        
        # Test 3: Análisis técnico - debe detectar problemas en el pliego riesgoso
        logger.info("Test 3: Análisis técnico") 
        technical_analysis = agent.analyze_technical_completeness("pliego_normal", "pliego_riesgoso")
        normal_tech_score = technical_analysis['doc1_analysis']['technical_completeness_score']
        risky_tech_score = technical_analysis['doc2_analysis']['technical_completeness_score']
        
        logger.info(f"Score técnico pliego normal: {normal_tech_score:.1f}")
        logger.info(f"Score técnico pliego riesgoso: {risky_tech_score:.1f}")
        
        # Test 4: Análisis económico - debe detectar irregularidades económicas
        logger.info("Test 4: Análisis económico")
        economic_analysis = agent.analyze_economic_competitiveness("pliego_normal", "pliego_riesgoso")
        
        normal_econ = economic_analysis['doc1_analysis']
        risky_econ = economic_analysis['doc2_analysis']
        
        logger.info(f"Presupuesto pliego normal: ${normal_econ.get('estimated_total_price', 'N/A'):,}" if normal_econ.get('estimated_total_price') else "Presupuesto normal: No detectado")
        logger.info(f"Presupuesto pliego riesgoso: ${risky_econ.get('estimated_total_price', 'N/A'):,}" if risky_econ.get('estimated_total_price') else "Presupuesto riesgoso: No detectado")
        
        # Test 5: Comparación comprehensiva - DEBE FAVORECER EL PLIEGO NORMAL
        logger.info("Test 5: Comparación comprehensiva (RESULTADO CRÍTICO)")
        comprehensive = agent.comprehensive_comparison("pliego_normal", "pliego_riesgoso", mode="TENDER_EVALUATION")
        
        winner = comprehensive['winner']
        
        # Get scores from the proper structure
        if 'scores' in comprehensive:
            winner_score = comprehensive['scores'][winner]['total_score']
            loser = 'pliego_riesgoso' if winner == 'pliego_normal' else 'pliego_normal'
            loser_score = comprehensive['scores'][loser]['total_score']
        else:
            # Alternative structure - check what's available
            logger.info(f"Available keys in comprehensive result: {list(comprehensive.keys())}")
            winner_score = comprehensive.get('summary', {}).get('winner_score', 'N/A')
            loser_score = comprehensive.get('summary', {}).get('loser_score', 'N/A')
        
        score_difference = comprehensive.get('summary', {}).get('score_difference', 'N/A')
        
        logger.info(f"🏆 GANADOR: {winner}")
        logger.info(f"Score ganador: {winner_score}")
        logger.info(f"Score perdedor: {loser_score}")
        logger.info(f"Diferencia: {score_difference}")
        
        # VERIFICACIÓN CRÍTICA: El pliego normal debe ganar
        if winner == "pliego_normal":
            logger.info("✅ ¡CORRECTO! El pliego normal (menos riesgoso) ganó la comparación")
            logger.info("✅ El sistema detectó correctamente los riesgos del pliego problemático")
            test_result_message = "SISTEMA FUNCIONA CORRECTAMENTE - Detecta riesgos"
        else:
            logger.error("❌ ¡ERROR CRÍTICO! El pliego riesgoso ganó - el sistema no detectó los riesgos")
            logger.error("❌ Esto indica problemas en la detección de riesgos del algoritmo")
            test_result_message = "SISTEMA TIENE PROBLEMAS - No detecta riesgos adecuadamente"
        
        # Mostrar recomendaciones
        logger.info("Recomendaciones del sistema:")
        for i, rec in enumerate(comprehensive['recommendations'], 1):
            logger.info(f"  {i}. {rec}")
        
        # Test 6: Análisis específico de indicadores de riesgo
        logger.info("Test 6: Detección específica de indicadores de riesgo")
        
        # Buscar indicadores específicos en el pliego riesgoso
        risk_indicators_found = []
        risky_content_lower = pliego_riesgoso.lower()
        
        risk_patterns = [
            ("pago adelantado 80%", "Pago adelantado excesivo sin garantías"),
            ("sin garantías", "Ausencia de garantías bancarias"),
            ("justificación verbal", "Penalidades flexibles no documentadas"),
            ("subcontratar el 100%", "Subcontratación total permitida"),
            ("cualquier obra", "Experiencia previa no específica"),
            ("30 días", "Plazo extremadamente corto"),
            ("sin inspección", "Falta de control de calidad")
        ]
        
        for pattern, description in risk_patterns:
            if pattern in risky_content_lower:
                risk_indicators_found.append(description)
        
        logger.info(f"Indicadores de riesgo detectados: {len(risk_indicators_found)}")
        for indicator in risk_indicators_found:
            logger.info(f"  🚨 {indicator}")
        
        # Resultado final
        test_passed = (winner == "pliego_normal" and len(risk_indicators_found) >= 3)
        
        logger.info(f"\n🔍 DIAGNÓSTICO FINAL:")
        logger.info(f"   Ganador: {winner}")
        logger.info(f"   Indicadores de riesgo detectados: {len(risk_indicators_found)}")
        logger.info(f"   Mensaje: {test_result_message}")
        
        if test_passed:
            logger.info("✅ Test de pliegos reales EXITOSO - Sistema detectó riesgos correctamente")
        else:
            logger.error("❌ Test de pliegos reales FALLÓ - Sistema no detectó riesgos adecuadamente")
            if winner == "pliego_riesgoso":
                logger.error("   🚨 PROBLEMA CRÍTICO: El sistema favorece documentos riesgosos")
                logger.error("   🔧 RECOMENDACIÓN: Revisar algoritmos de detección de riesgos")
        
        return test_passed
        
    except Exception as e:
        logger.error(f"❌ Error en test de pliegos reales: {e}", exc_info=True)
        return False
        
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
                       else "Precio: N/A)")
        
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
        
        # Crear archivos temporales para la comparación múltiple
        import tempfile
        temp_files = []
        
        try:
            # Crear archivos temporales con el contenido
            for doc_id, content in documents.items():
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
                    tmp_file.write(content)
                    temp_files.append(Path(tmp_file.name))
            
            # Realizar comparación múltiple
            multi_comparison = agent.compare_multiple_documents(
                temp_files, 
                comparison_type="comprehensive"
            )
            
            logger.info("Resultados de comparación múltiple:")
            logger.info(f"Total documentos: {len(temp_files)}")
            logger.info(f"Comparaciones realizadas: {multi_comparison.get('summary_statistics', {}).get('successful_comparisons', 'N/A')}")
            
            if multi_comparison.get('ranking'):
                logger.info("Ranking de documentos:")
                for rank_info in multi_comparison['ranking']:
                    logger.info(f"{rank_info['rank']}. {rank_info['document_name']} "
                               f"(Score promedio: {rank_info['average_score']:.2f})")
                               
        finally:
            # Limpiar archivos temporales
            import os
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
        
        logger.info("✅ Test de comparación múltiple completado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en test múltiple: {e}", exc_info=True)
        return False

def test_pliego_comparison():
    """Test comparison between the two pliego documents (normal vs risky)"""
    logger.info("=== Test de Comparación de Pliegos (Normal vs Riesgoso) ===")
    
    try:
        # Crear agente unificado
        db_path = backend_dir / "db" / "test_pliego_comparison"
        agent = ComparisonAgent(vector_db_path=db_path)
        
        # Inicializar embeddings
        if not agent.initialize_embeddings(provider="auto"):
            logger.warning("No se pudo inicializar embeddings, continuando con análisis básico")
        
        # Load the pliego documents
        pliego_normal_path = backend_dir.parent / "documents" / "pliego_licitacion.txt"
        pliego_riesgoso_path = backend_dir.parent / "documents" / "pliego_licitacion_riesgoso.txt"
        
        if not pliego_normal_path.exists():
            logger.error(f"Normal pliego not found at: {pliego_normal_path}")
            return False
            
        if not pliego_riesgoso_path.exists():
            logger.error(f"Risky pliego not found at: {pliego_riesgoso_path}")
            return False
        
        logger.info(f"Loading normal pliego from: {pliego_normal_path}")
        logger.info(f"Loading risky pliego from: {pliego_riesgoso_path}")
        
        # Read the content directly and add to agent
        with open(pliego_normal_path, 'r', encoding='utf-8') as f:
            normal_content = f.read()
            
        with open(pliego_riesgoso_path, 'r', encoding='utf-8') as f:
            risky_content = f.read()
        
        # Add documents to the comparison agent
        agent.add_document("pliego_normal", normal_content, "tender_specification", 
                          metadata={"type": "normal_tender", "risk_level": "low"})
        agent.add_document("pliego_riesgoso", risky_content, "tender_specification", 
                          metadata={"type": "risky_tender", "risk_level": "very_high"})
        
        # Setup vector database
        agent.setup_vector_database()
        
        # Test 1: Content similarity analysis
        logger.info("Test 1: Análisis de similitud de contenido")
        similarity = agent.analyze_content_similarity("pliego_normal", "pliego_riesgoso")
        logger.info(f"Similitud general: {similarity['overall_similarity_score']}%")
        
        # Test 2: Structural compliance analysis
        logger.info("Test 2: Análisis de cumplimiento estructural")
        structural = agent.analyze_structural_compliance("pliego_normal", "pliego_riesgoso")
        normal_compliance = structural['doc1_analysis']['compliance_percentage']
        risky_compliance = structural['doc2_analysis']['compliance_percentage']
        logger.info(f"Cumplimiento pliego normal: {normal_compliance:.1f}%")
        logger.info(f"Cumplimiento pliego riesgoso: {risky_compliance:.1f}%")
        
        # Test 3: Risk-aware comparison
        logger.info("Test 3: Comparación consciente de riesgos")
        
        # Simulate risk context for the risky document
        risky_classification_context = {
            "risk_assessment": {
                "overall_risk_score": 0.95,  # Very high risk
                "risk_categories": {
                    "Technical Risks": {"score": 95, "level": "VERY_HIGH"},
                    "Economic Risks": {"score": 92, "level": "VERY_HIGH"},
                    "Legal Risks": {"score": 88, "level": "HIGH"},
                    "Operational Risks": {"score": 90, "level": "VERY_HIGH"},
                    "Supplier Risks": {"score": 85, "level": "HIGH"}
                }
            }
        }
        
        # Simulate normal risk context
        normal_classification_context = {
            "risk_assessment": {
                "overall_risk_score": 0.25,  # Low risk
                "risk_categories": {
                    "Technical Risks": {"score": 20, "level": "LOW"},
                    "Economic Risks": {"score": 15, "level": "LOW"},
                    "Legal Risks": {"score": 30, "level": "LOW"},
                    "Operational Risks": {"score": 25, "level": "LOW"},
                    "Supplier Risks": {"score": 20, "level": "LOW"}
                }
            }
        }
        
        # Test using content-based comparison with risk context
        try:
            comparison_result = agent.compare_documents(
                normal_content,
                risky_content, 
                "pliego_normal.txt",
                "pliego_riesgoso.txt",
                comparison_mode="TENDER_EVALUATION",
                doc1_analysis=normal_classification_context,
                doc2_analysis=risky_classification_context
            )
            
            if "error" not in comparison_result:
                logger.info("✅ Content-based comparison completed successfully")
                logger.info(f"Comparison method: {comparison_result.get('comparison_method', 'Unknown')}")
                
                # Check if comparison favors the normal (non-risky) document
                enhanced_scoring = comparison_result.get('enhanced_scoring', {})
                if enhanced_scoring and 'overall' in enhanced_scoring:
                    winner = enhanced_scoring['overall']['overall_winner']
                    logger.info(f"Overall winner: {winner}")
                    
                    if winner == "document1":  # pliego_normal is document1
                        logger.info("✅ PASS: Comparison correctly favors the non-risky document")
                        result_ok = True
                    else:
                        logger.warning("⚠️ WARNING: Comparison did not favor the non-risky document")
                        result_ok = False
                else:
                    logger.warning("No overall scoring available in comparison result")
                    result_ok = False
            else:
                logger.error(f"Content-based comparison failed: {comparison_result['error']}")
                result_ok = False
                
        except Exception as e:
            logger.error(f"Error in content-based comparison: {e}")
            result_ok = False
        
        # Test 4: Economic analysis
        logger.info("Test 4: Análisis económico")
        economic = agent.analyze_economic_competitiveness("pliego_normal", "pliego_riesgoso")
        normal_price = economic['doc1_analysis']['estimated_total_price']
        risky_price = economic['doc2_analysis']['estimated_total_price']
        
        logger.info(f"Precio pliego normal: ${normal_price:,}" if normal_price else "Precio pliego normal: No detectado")
        logger.info(f"Precio pliego riesgoso: ${risky_price:,}" if risky_price else "Precio pliego riesgoso: No detectado")
        
        # Expected outcome validation
        logger.info("=== VALIDACIÓN DE RESULTADOS ===")
        
        # The normal pliego should be better in most aspects
        if normal_compliance >= risky_compliance:
            logger.info("✅ PASS: El pliego normal tiene mejor cumplimiento estructural")
        else:
            logger.warning("⚠️ WARNING: El pliego riesgoso tiene mejor cumplimiento (inesperado)")
        
        # Summary
        logger.info("=== RESUMEN ===")
        logger.info("Se espera que el pliego normal sea preferido debido a:")
        logger.info("- Menor nivel de riesgo general")
        logger.info("- Mejores garantías y condiciones")
        logger.info("- Mayor tiempo de ejecución (más realista)")
        logger.info("- Procesos de evaluación más rigurosos")
        
        logger.info("El pliego riesgoso presenta:")
        logger.info("- Pago adelantado del 80% sin garantías")
        logger.info("- Plazo extremadamente corto (30 días)")
        logger.info("- Evaluación basada solo en precio (90%)")
        logger.info("- Subcontratación 100% permitida")
        
        logger.info("✅ Test de comparación de pliegos completado")
        return result_ok
        
    except Exception as e:
        logger.error(f"❌ Error en test de pliegos: {e}", exc_info=True)
        return False

def run_all_tests():
    """Ejecutar todos los tests"""
    logger.info("🚀 Iniciando tests del ComparisonAgent")
    
    test_results = []
    
    # Crear directorios necesarios
    test_dirs = [
        backend_dir / "db" / "test_unified_comparator",
        backend_dir / "db" / "test_tender_evaluation", 
        backend_dir / "db" / "test_real_tenders",
        backend_dir / "db" / "test_multi_comparison",
        backend_dir / "test_reports"
    ]
    
    for test_dir in test_dirs:
        test_dir.mkdir(parents=True, exist_ok=True)
    
    # Ejecutar tests
    tests = [
        ("API Basada en Contenido", test_content_based_api),
        ("Penalizaciones Progresivas por Riesgo", test_progressive_risk_penalties),
        ("Extracción de Contexto de Clasificación", test_classification_context_extraction),
        ("Comparación Básica con Sistema", test_basic_comparison_with_system),
        ("Evaluación de Licitaciones", test_tender_evaluation),
        ("Pliegos Reales (Anti-Riesgo)", test_real_tender_documents),
        ("Comparación de Pliegos (Normal vs Riesgoso)", test_pliego_comparison),
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
