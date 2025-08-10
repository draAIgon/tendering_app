#!/usr/bin/env python3
"""
Test script for ReportGenerationAgent
Tests report generation capabilities for different types and formats
"""

import sys
from pathlib import Path

# Agregar paths necesarios
current_dir = Path(__file__).parent
backend_dir = current_dir.parent  # Go up one level to backend directory
sys.path.append(str(backend_dir))
sys.path.append(str(backend_dir / "utils" / "agents"))

from utils.agents.reporter import ReportGenerationAgent
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_report_generation():
    """Test básico de generación de reportes"""
    logger.info("=== Test Básico de Generación de Reportes ===")
    
    try:
        # Crear directorio de reportes
        reports_dir = backend_dir / "reports" / "test"
        agent = ReportGenerationAgent(output_directory=reports_dir)
        
        # Datos de ejemplo para generar reporte
        sample_data = {
            'classification': {
                'sections': {
                    'PLIEGO_GENERAL': {
                        'section_name': 'PLIEGO_GENERAL',
                        'document_count': 5,
                        'total_characters': 2500,
                        'content_preview': 'Información general del proyecto...',
                        'sources': ['document1.pdf'],
                        'taxonomy_info': {'priority': 1}
                    },
                    'REQUISITOS_TECNICOS': {
                        'section_name': 'REQUISITOS_TECNICOS',
                        'document_count': 8,
                        'total_characters': 4200,
                        'content_preview': 'Especificaciones técnicas del proyecto...',
                        'sources': ['document1.pdf'],
                        'taxonomy_info': {'priority': 2}
                    }
                },
                'document_info': {
                    'total_sections': 2,
                    'total_fragments': 13,
                    'source': 'test_document.pdf'
                },
                'confidence_scores': {'PLIEGO_GENERAL': 0.85, 'REQUISITOS_TECNICOS': 0.92},
                'key_requirements': {}
            },
            'validation': {
                'overall_score': 92.0, 
                'missing_docs': [],
                'summary': {'total_issues': 2}
            },
            'risk_analysis': {
                'overall_assessment': {
                    'total_risk_score': 25.0, 
                    'risk_level': 'LOW'
                },
                'critical_risks': [
                    {'category': 'TECHNICAL', 'description': 'Complejidad baja', 'impact': 'LOW'}
                ],
                'mitigation_recommendations': [
                    {'category': 'TECHNICAL', 'recommendation': 'Continuar con monitoreo estándar'}
                ]
            },
            'comparison': {
                'total_proposals': 2,
                'summary_statistics': {
                    'winner': 'Propuesta A'
                },
                'best_proposal': 'Propuesta A', 
                'score': 88.0
            },
            'extraction': {'pages': 10, 'text_length': 15000}
        }
        
        # Recopilar datos
        data_id = agent.collect_analysis_data(
            classification_results=sample_data['classification'],
            validation_results=sample_data['validation'],
            risk_analysis=sample_data['risk_analysis'],
            comparison_results=sample_data['comparison'],
            extraction_results=sample_data['extraction']
        )
        
        logger.info(f"✅ Datos recopilados con ID: {data_id}")
        
        # Generar reporte ejecutivo
        report_result = agent.generate_executive_summary(data_id)
        
        if 'error' not in report_result:
            logger.info("✅ Reporte ejecutivo generado exitosamente")
            logger.info(f"📄 Tipo de reporte: {report_result.get('report_type', 'N/A')}")
            
            # Verificar estructura básica del reporte ejecutivo
            expected_fields = ['key_findings', 'critical_issues', 'top_recommendations']
            found_fields = 0
            for field in expected_fields:
                if field in report_result:
                    found_fields += 1
                    logger.info(f"  ✓ {field}: {len(report_result[field]) if isinstance(report_result[field], list) else 'Presente'}")
            
            logger.info(f"📊 Campos encontrados: {found_fields}/{len(expected_fields)}")
            
            # También verificar datos de métricas
            if 'summary_metrics' in report_result:
                metrics = report_result['summary_metrics']
                logger.info(f"  ✓ Métricas: completeness={metrics.get('analysis_completeness', 0):.1f}%, confidence={metrics.get('confidence_level', 0):.1f}%")
                found_fields += 1
            
            if found_fields >= 2:
                logger.info("✅ Estructura de reporte válida")
                return True
            else:
                logger.warning("⚠️  Pocas secciones en el reporte")
                return False
        else:
            logger.error(f"Error en generación de reporte: {report_result['error']}")
            return False
        
    except Exception as e:
        logger.error(f"Error durante la generación de reporte: {e}")
        return False

def test_multiple_report_types():
    """Test de múltiples tipos de reportes"""
    logger.info("\n=== Test de Múltiples Tipos de Reportes ===")
    
    try:
        # Crear agente
        reports_dir = backend_dir / "reports" / "test"
        agent = ReportGenerationAgent(output_directory=reports_dir)
        
        # Datos más completos
        comprehensive_data = {
            'classification': {
                'sections': {
                    'PLIEGO_GENERAL': {
                        'section_name': 'PLIEGO_GENERAL',
                        'document_count': 3,
                        'total_characters': 1800
                    },
                    'REQUISITOS_TECNICOS': {
                        'section_name': 'REQUISITOS_TECNICOS', 
                        'document_count': 5,
                        'total_characters': 3200
                    }
                },
                'document_info': {'total_sections': 8, 'total_fragments': 120},
                'confidence_scores': {'overall': 87.5},
                'key_requirements': {}
            },
            'risk_analysis': {
                'overall_assessment': {
                    'total_risk_score': 35.0, 
                    'risk_level': 'MEDIUM',
                    'risk_distribution': {'TECHNICAL': 15.0, 'ECONOMIC': 20.0},
                    'assessment_summary': 'Riesgo moderado identificado en el proyecto'
                },
                'critical_risks': [
                    {'category': 'TECHNICAL', 'description': 'Complejidad técnica alta', 'impact': 'HIGH'},
                    {'category': 'ECONOMIC', 'description': 'Presupuesto ajustado', 'impact': 'MEDIUM'}
                ],
                'mitigation_recommendations': [
                    {'category': 'TECHNICAL', 'recommendation': 'Implementar controles adicionales'},
                    {'category': 'ECONOMIC', 'recommendation': 'Revisar especificaciones'}
                ],
                'category_risks': {
                    'TECHNICAL': {'risk_score': 15.0, 'weight': 0.25},
                    'ECONOMIC': {'risk_score': 20.0, 'weight': 0.20}
                }
            }
        }
        
        # Recopilar datos
        data_id = agent.collect_analysis_data(
            classification_results=comprehensive_data['classification'],
            risk_analysis=comprehensive_data['risk_analysis']
        )
        
        # Tipos de reporte a probar
        report_types = [
            ('EXECUTIVE_SUMMARY', 'generate_executive_summary'),
            ('RISK_ASSESSMENT', 'generate_risk_assessment_report'),
            ('TECHNICAL_ANALYSIS', 'generate_technical_analysis')
        ]
        
        successful_reports = 0
        
        for report_type, method_name in report_types:
            logger.info(f"🔄 Generando reporte: {report_type}")
            
            try:
                method = getattr(agent, method_name)
                report_result = method(data_id)
                
                if 'error' not in report_result and report_result.get('report_type') == report_type:
                    logger.info(f"  ✅ {report_type} generado exitosamente")
                    successful_reports += 1
                else:
                    logger.warning(f"  ⚠️  {report_type} con problemas")
                    
            except Exception as e:
                logger.warning(f"  ❌ Error en {report_type}: {str(e)[:50]}...")
        
        logger.info(f"📊 Reportes generados exitosamente: {successful_reports}/{len(report_types)}")
        
        if successful_reports >= 2:
            logger.info("✅ Generación múltiple exitosa")
            return True
        else:
            logger.warning("⚠️  Pocos reportes generados exitosamente")
            return False
        
    except Exception as e:
        logger.error(f"Error en generación múltiple de reportes: {e}")
        return False

def test_report_customization():
    """Test de personalización de reportes"""
    logger.info("\n=== Test de Personalización de Reportes ===")
    
    try:
        # Crear agente
        reports_dir = backend_dir / "reports" / "test"
        agent = ReportGenerationAgent(output_directory=reports_dir)
        
        # Datos personalizados
        custom_data = {
            'classification': {
                'sections': {
                    'PLIEGO_GENERAL': {'section_name': 'PLIEGO_GENERAL', 'document_count': 4},
                    'REQUISITOS_TECNICOS': {'section_name': 'REQUISITOS_TECNICOS', 'document_count': 6},
                    'CONDICIONES_ECONOMICAS': {'section_name': 'CONDICIONES_ECONOMICAS', 'document_count': 2}
                },
                'document_info': {'total_sections': 12, 'source': 'Proyecto Especial de Infraestructura'},
                'confidence_scores': {'overall': 95.0},
                'key_requirements': {}
            },
            'risk_analysis': {
                'overall_assessment': {
                    'total_risk_score': 15.0, 
                    'risk_level': 'LOW'
                },
                'critical_risks': [],
                'mitigation_recommendations': [
                    {'category': 'GENERAL', 'recommendation': 'Mantener controles estándar'}
                ],
                'assessment_date': '2025-01-15'
            }
        }
        
        # Recopilar datos
        data_id = agent.collect_analysis_data(
            classification_results=custom_data['classification'],
            risk_analysis=custom_data['risk_analysis']
        )
        
        # Generar reporte comprensivo personalizado
        report_result = agent.generate_comprehensive_report(
            data_id, 
            include_charts=True
        )
        
        if 'error' not in report_result:
            logger.info("✅ Reporte personalizado generado")
            
            # Verificar personalización
            if 'metadata' in report_result:
                metadata = report_result['metadata']
                logger.info(f"📋 Incluye gráficos: {'chart_data' in report_result}")
                logger.info(f"📊 Análisis detallado: {metadata.get('analysis_completeness', 0) > 0}")
            
            # Verificar contenido comprensivo - verificar secciones principales del reporte integral
            main_sections = ['executive_summary', 'technical_analysis', 'risk_assessment', 'recommendations']
            found_sections = 0
            for section in main_sections:
                if section in report_result and report_result[section]:
                    found_sections += 1
            
            logger.info(f"📊 Secciones principales encontradas: {found_sections}/{len(main_sections)}")
            
            if found_sections >= 2:  # Al menos 2 secciones principales deben estar presentes
                logger.info(f"✅ Reporte comprensivo con {found_sections} secciones")
                return True
            else:
                logger.warning("⚠️  Reporte incompleto")
                return False
        else:
            logger.error(f"Error en personalización: {report_result['error']}")
            return False
        
    except Exception as e:
        logger.error(f"Error en personalización de reporte: {e}")
        return False

def test_export_formats():
    """Test de formatos de exportación"""
    logger.info("\n=== Test de Formatos de Exportación ===")
    
    try:
        # Crear agente
        reports_dir = backend_dir / "reports" / "test"
        agent = ReportGenerationAgent(output_directory=reports_dir)
        
        # Datos simples para exportar
        export_data = {
            'classification': {
                'sections': {
                    'PLIEGO_GENERAL': {'section_name': 'PLIEGO_GENERAL', 'document_count': 2},
                    'REQUISITOS_TECNICOS': {'section_name': 'REQUISITOS_TECNICOS', 'document_count': 3}
                },
                'document_info': {'total_sections': 5},
                'confidence_scores': {'overall': 90.0},
                'key_requirements': {}
            }
        }
        
        data_id = agent.collect_analysis_data(
            classification_results=export_data['classification']
        )
        
        # Generar reporte para exportar
        report = agent.generate_executive_summary(data_id)
        
        if 'error' in report:
            logger.error("No se pudo generar reporte para exportar")
            return False
        
        # Formatos de exportación a probar
        export_formats = ['json', 'html']
        successful_exports = 0
        
        for format_type in export_formats:
            logger.info(f"🔄 Exportando a formato: {format_type}")
            
            try:
                export_filename = f"test_report.{format_type}"
                export_result = agent.export_report(
                    report_data=report,
                    output_format=format_type,
                    filename=export_filename
                )
                
                if export_result.exists():
                    logger.info(f"  ✅ {format_type.upper()}: Exportado exitosamente")
                    successful_exports += 1
                else:
                    logger.warning(f"  ❌ {format_type.upper()}: Error en exportación")
                    
            except Exception as e:
                logger.warning(f"  ❌ {format_type.upper()}: Error - {str(e)[:50]}...")
        
        logger.info(f"📊 Formatos exportados exitosamente: {successful_exports}/{len(export_formats)} ({(successful_exports/len(export_formats))*100:.1f}%)")
        
        if successful_exports >= 1:  # Al menos un formato debe funcionar
            logger.info("✅ Exportación exitosa")
            return True
        else:
            logger.error("❌ No se pudo exportar en ningún formato")
            return False
        
    except Exception as e:
        logger.error(f"Error en formatos de exportación: {e}")
        return False

def main():
    """Función principal del test"""
    logger.info("🚀 Iniciando tests del ReportGenerationAgent")
    
    tests = [
        ("Generación Básica de Reportes", test_basic_report_generation),
        ("Múltiples Tipos de Reportes", test_multiple_report_types),
        ("Personalización de Reportes", test_report_customization),
        ("Formatos de Exportación", test_export_formats)
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
