"""
Test para verificar RUC validation con archivo PDF real
"""

import sys
import os
from pathlib import Path
import logging

# Configurar path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

root_dir = os.path.dirname(backend_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_ruc_with_existing_document():
    """Test usando un documento existente en el sistema"""
    
    logger.info("🧪 Testing RUC validation con documento existente...")
    
    try:
        from backend.utils.bidding import BiddingAnalysisSystem
        
        # Crear sistema
        system = BiddingAnalysisSystem()
        logger.info("✅ BiddingAnalysisSystem creado")
        
        # Buscar documentos existentes
        lawdata_dir = Path("LawData")
        pdf_files = list(lawdata_dir.glob("*.pdf")) if lawdata_dir.exists() else []
        
        if not pdf_files:
            # Buscar en otros directorios
            for search_dir in ["uploads", "temp", "."]:
                search_path = Path(search_dir)
                if search_path.exists():
                    pdf_files.extend(search_path.glob("*.pdf"))
                    if pdf_files:
                        break
        
        if not pdf_files:
            logger.info("📄 No se encontraron PDFs. Creando contenido directo...")
            
            # Test directo con RUCValidationAgent
            content_with_ruc = """
            PROPUESTA TÉCNICA - CONSTRUCCIÓN EDIFICIO CORPORATIVO
            
            DATOS DE LA EMPRESA CONTRATISTA:
            Razón Social: CONSTRUCTORA QUITO MODERNO S.A.
            RUC: 1790123456001
            Dirección: Av. 6 de Diciembre N24-253, Quito - Ecuador
            Teléfono: (02) 2234567
            Email: info@quito-moderno.com
            
            REPRESENTANTE LEGAL:
            Nombre: Ing. María Elena Vásquez Torres
            Cédula de Ciudadanía: 1712345678
            RUC Personal: 1712345678001
            
            DATOS FINANCIEROS:
            Capital Social: $750,000.00
            Patrimonio: $2,500,000.00
            
            SUBCONTRATISTAS PROPUESTOS:
            
            1. ESTRUCTURAS ANDINAS CIA. LTDA.
               RUC: 1791234567001
               Especialidad: Diseño y construcción estructural
               
            2. INSTALACIONES MODERNAS DEL ECUADOR S.A.
               RUC: 1792345678001
               Especialidad: Instalaciones eléctricas y sanitarias
            
            ACTIVIDADES ECONÓMICAS REGISTRADAS:
            F4100.01 - Construcción de edificios residenciales
            F4100.02 - Construcción de edificios no residenciales
            F4290.01 - Construcción de obras de ingeniería civil
            
            El presente documento constituye nuestra propuesta formal
            para la ejecución del proyecto de construcción.
            """
            
            # Test directo del RUCValidationAgent
            ruc_result = system.ruc_validator.comprehensive_ruc_validation(
                content=content_with_ruc,
                work_type="CONSTRUCCION"
            )
            
            logger.info("🎯 RESULTADO RUC VALIDATION DIRECTO:")
            logger.info(f"   📊 Total RUCs: {ruc_result['validation_summary']['total_rucs']}")
            logger.info(f"   ✅ Formato válido: {ruc_result['validation_summary']['valid_format']}")
            logger.info(f"   🌐 Verificados online: {ruc_result['validation_summary']['verified_online']}")
            logger.info(f"   🔗 Compatibles: {ruc_result['validation_summary']['compatible_entities']}")
            logger.info(f"   📈 Score general: {ruc_result['overall_score']}%")
            logger.info(f"   🎯 Nivel: {ruc_result['validation_level']}")
            
            # Verificar que encontró RUCs
            if ruc_result['validation_summary']['total_rucs'] > 0:
                logger.info("✅ RUC VALIDATION ESTÁ FUNCIONANDO CORRECTAMENTE!")
                
                # Mostrar detalles de RUCs encontrados
                logger.info("📋 DETALLES DE RUCs DETECTADOS:")
                for i, ruc_detail in enumerate(ruc_result['detailed_results'], 1):
                    ruc_num = ruc_detail['ruc_number']
                    format_valid = ruc_detail['format_validation']['is_valid']
                    online_verified = ruc_detail['online_verification']['verified']
                    compatibility = ruc_detail['entity_compatibility']['compatible']
                    
                    logger.info(f"   {i}. RUC: {ruc_num}")
                    logger.info(f"      - Formato: {'✅' if format_valid else '❌'}")
                    logger.info(f"      - Online: {'✅' if online_verified else '❌'}")
                    logger.info(f"      - Compatible: {'✅' if compatibility else '❌'}")
                
                return True
            else:
                logger.error("❌ No se detectaron RUCs en el contenido")
                return False
        else:
            # Usar archivo PDF existente
            pdf_file = pdf_files[0]
            logger.info(f"📄 Usando archivo existente: {pdf_file}")
            
            # Ejecutar análisis comprehensive
            result = system.analyze_document(
                document_path=str(pdf_file),
                document_type="proposal",
                analysis_level="comprehensive"
            )
            
            logger.info(f"📊 Estado del análisis: {result.get('overall_status', 'unknown')}")
            
            # Verificar RUC validation
            stages = result.get('stages', {})
            if 'ruc_validation' in stages:
                ruc_stage = stages['ruc_validation']
                if ruc_stage.get('status') == 'completed':
                    ruc_data = ruc_stage.get('data', {})
                    logger.info("🎯 RUC VALIDATION EN ANÁLISIS COMPLETO:")
                    logger.info(f"   📊 Total RUCs: {ruc_data['validation_summary']['total_rucs']}")
                    logger.info(f"   📈 Score: {ruc_data['overall_score']}%")
                    return True
                else:
                    logger.info(f"⚠️ RUC validation status: {ruc_stage.get('status')}")
                    if 'error' in ruc_stage:
                        logger.info(f"   Error: {ruc_stage['error']}")
            else:
                logger.info("ℹ️ RUC validation no encontrado en stages")
                logger.info(f"   Stages disponibles: {list(stages.keys())}")
            
            return False
        
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_ruc_in_api_response():
    """Verificar si RUC aparece en las respuestas API recientes"""
    
    logger.info("🔍 Verificando si RUC aparece en análisis recientes...")
    
    try:
        # Buscar archivos de análisis recientes
        analysis_dir = Path("../analysis_databases")
        if not analysis_dir.exists():
            analysis_dir = Path("analysis_databases")
        
        if analysis_dir.exists():
            # Buscar directorios de análisis más recientes
            analysis_dirs = [d for d in analysis_dir.iterdir() if d.is_dir()]
            analysis_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for analysis_path in analysis_dirs[:3]:  # Revisar los 3 más recientes
                analysis_file = analysis_path / "analysis_result.json"
                if analysis_file.exists():
                    logger.info(f"📄 Revisando: {analysis_path.name}")
                    
                    import json
                    with open(analysis_file, 'r', encoding='utf-8') as f:
                        analysis_data = json.load(f)
                    
                    # Verificar si tiene RUC validation
                    stages = analysis_data.get('stages', {})
                    if 'ruc_validation' in stages:
                        logger.info("✅ ¡Encontrado RUC validation en análisis existente!")
                        ruc_data = stages['ruc_validation'].get('data', {})
                        if ruc_data:
                            logger.info(f"   📊 RUCs: {ruc_data.get('validation_summary', {}).get('total_rucs', 0)}")
                            logger.info(f"   📈 Score: {ruc_data.get('overall_score', 0)}%")
                        return True
                    else:
                        logger.info(f"   No RUC validation en {analysis_path.name}")
                        logger.info(f"   Stages: {list(stages.keys())}")
        else:
            logger.info("📁 No se encontró directorio analysis_databases")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Error verificando análisis: {e}")
        return False


def main():
    """Ejecutar verificaciones"""
    logger.info("🚀 Verificando estado de RUC validation...")
    
    # Test 1: Funcionalidad directa
    logger.info("\n" + "="*50)
    logger.info("TEST 1: Funcionalidad directa de RUC validation")
    logger.info("="*50)
    
    test1_ok = test_ruc_with_existing_document()
    
    # Test 2: Buscar en análisis existentes
    logger.info("\n" + "="*50)
    logger.info("TEST 2: RUC en análisis existentes")
    logger.info("="*50)
    
    test2_ok = check_ruc_in_api_response()
    
    # Resultado final
    logger.info("\n" + "="*50)
    logger.info("RESUMEN FINAL")
    logger.info("="*50)
    
    if test1_ok:
        logger.info("✅ RUC Validation Agent: FUNCIONANDO")
    else:
        logger.info("❌ RUC Validation Agent: PROBLEMA")
    
    if test2_ok:
        logger.info("✅ RUC en análisis previos: ENCONTRADO")
    else:
        logger.info("ℹ️ RUC en análisis previos: NO ENCONTRADO")
    
    if test1_ok:
        logger.info("\n🎉 CONCLUSIÓN: RUC VALIDATION ESTÁ FUNCIONANDO")
        logger.info("💡 Para que aparezca en frontend, el análisis debe ser 'comprehensive'")
        logger.info("🔗 Verificar que el servidor remoto tenga la última versión")
    else:
        logger.info("\n⚠️ CONCLUSIÓN: Revisar configuración de RUC validation")
    
    return test1_ok


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
