#!/usr/bin/env python3
"""
Test script for ReportGenerationAgent
Tests report generation capabilities for different types and formats
"""

import sys
import os
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
            'classification': {'sections': 5, 'fragments': 50, 'confidence': 85.0},
            'validation': {'compliance_score': 92.0, 'missing_docs': []},
            'risk_analysis': {'total_risk_score': 25.0, 'risk_level': 'LOW'},
            'comparison': {'best_proposal': 'Propuesta A', 'score': 88.0},
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
            logger.info(f"📄 Secciones del reporte: {len(report_result.get('sections', {}))}")
            
            # Verificar estructura básica
            expected_sections = ['overview', 'key_findings', 'recommendations']
            found_sections = 0
            for section in expected_sections:
                if section in report_result.get('sections', {}):
                    found_sections += 1
            
            logger.info(f"📊 Secciones encontradas: {found_sections}/{len(expected_sections)}")
            
            if found_sections >= 2:
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
                'sections': 8, 
                'fragments': 120, 
                'confidence': 87.5,
                'categories': ['TECHNICAL', 'ECONOMIC', 'LEGAL']
            },
            'risk_analysis': {
                'total_risk_score': 35.0, 
                'risk_level': 'MEDIUM',
                'critical_risks': 2,
                'recommendations': ['Implementar controles adicionales', 'Revisar especificaciones']
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
                'project_name': 'Proyecto Especial de Infraestructura',
                'sections': 12, 
                'confidence': 95.0
            },
            'risk_analysis': {
                'total_risk_score': 15.0, 
                'risk_level': 'LOW',
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
            include_charts=True,
            detailed_analysis=True
        )
        
        if 'error' not in report_result:
            logger.info("✅ Reporte personalizado generado")
            
            # Verificar personalización
            if 'metadata' in report_result:
                metadata = report_result['metadata']
                logger.info(f"📋 Incluye gráficos: {metadata.get('includes_charts', False)}")
                logger.info(f"📊 Análisis detallado: {metadata.get('detailed_analysis', False)}")
            
            # Verificar contenido comprensivo
            sections = report_result.get('sections', {})
            if len(sections) >= 4:
                logger.info(f"✅ Reporte comprensivo con {len(sections)} secciones")
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
            'classification': {'sections': 5, 'confidence': 90.0}
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
                export_path = reports_dir / f"test_report.{format_type}"
                export_result = agent.export_report(
                    report_data=report,
                    output_path=export_path,
                    format_type=format_type
                )
                
                if export_result.get('success', False) and export_path.exists():
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
