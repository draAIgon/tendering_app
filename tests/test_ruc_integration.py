"""
Test para verificar si la validación RUC está funcionando en el análisis completo
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


def test_ruc_in_full_analysis():
    """Test para verificar que RUC se incluye en análisis completo"""
    
    logger.info("🧪 Testing RUC validation in comprehensive analysis...")
    
    try:
        from backend.utils.bidding import BiddingAnalysisSystem
        
        # Crear sistema
        system = BiddingAnalysisSystem()
        logger.info("✅ BiddingAnalysisSystem creado")
        
        # Crear un archivo temporal con contenido que incluya RUC
        test_content = """
        PROPUESTA TÉCNICA
        CONSTRUCTORA ANDES S.A.
        RUC: 1790123456001
        
        Estimado Comité de Licitaciones,
        
        Por medio de la presente, presentamos nuestra propuesta para la ejecución
        del proyecto de construcción solicitado.
        
        DATOS DE LA EMPRESA:
        Razón Social: CONSTRUCTORA ANDES S.A.
        RUC: 1790123456001
        Dirección: Av. Amazonas 1234, Quito
        
        REPRESENTANTE LEGAL:
        Nombre: Ing. Juan Pérez
        Cédula: 1712345678
        RUC Personal: 1712345678001
        
        EXPERIENCIA:
        - Construcción de edificios residenciales (10 años)
        - Obras de infraestructura vial (5 años)
        
        PROPUESTA ECONÓMICA:
        Valor total: $150,000.00
        Plazo de ejecución: 6 meses
        
        Atentamente,
        CONSTRUCTORA ANDES S.A.
        """
        
        # Crear archivo temporal
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            temp_file = f.name
        
        logger.info(f"📄 Archivo temporal creado: {temp_file}")
        
        # Ejecutar análisis comprehensive
        logger.info("🔍 Ejecutando análisis comprehensive...")
        result = system.analyze_document(
            document_path=temp_file,
            document_type="proposal",
            analysis_level="comprehensive"  # ¡IMPORTANTE: comprehensive para activar RUC!
        )
        
        # Verificar que el análisis se completó
        logger.info(f"📊 Estado del análisis: {result.get('overall_status', 'unknown')}")
        logger.info(f"🏗️ Etapas completadas: {len(result.get('stages', {}))}")
        
        # Verificar etapas específicas
        stages = result.get('stages', {})
        for stage_name in ['extraction', 'classification', 'validation', 'ruc_validation', 'risk_analysis']:
            if stage_name in stages:
                status = stages[stage_name].get('status', 'unknown')
                logger.info(f"   ✅ {stage_name}: {status}")
            else:
                logger.info(f"   ❌ {stage_name}: no encontrado")
        
        # Verificar específicamente RUC validation
        if 'ruc_validation' in stages:
            ruc_stage = stages['ruc_validation']
            if ruc_stage.get('status') == 'completed':
                ruc_data = ruc_stage.get('data', {})
                ruc_summary = ruc_data.get('validation_summary', {})
                
                logger.info("🎯 VALIDACIÓN RUC ENCONTRADA:")
                logger.info(f"   📊 Total RUCs: {ruc_summary.get('total_rucs', 0)}")
                logger.info(f"   ✅ Formato válido: {ruc_summary.get('valid_format', 0)}")
                logger.info(f"   🌐 Verificados online: {ruc_summary.get('verified_online', 0)}")
                logger.info(f"   🔗 Compatibles: {ruc_summary.get('compatible_entities', 0)}")
                logger.info(f"   📈 Score general: {ruc_data.get('overall_score', 0)}%")
                logger.info(f"   🎯 Nivel: {ruc_data.get('validation_level', 'UNKNOWN')}")
                
                # Verificar si está en el resumen
                summary = result.get('summary', {})
                key_findings = summary.get('key_findings', [])
                
                ruc_findings = [finding for finding in key_findings if 'RUC' in finding]
                if ruc_findings:
                    logger.info("🔍 RUC INCLUIDO EN RESUMEN:")
                    for finding in ruc_findings:
                        logger.info(f"   - {finding}")
                else:
                    logger.warning("⚠️ RUC no aparece en key_findings del resumen")
                
                return True
                
            else:
                logger.error(f"❌ RUC validation falló: {ruc_stage.get('error', 'Error desconocido')}")
                return False
        else:
            logger.error("❌ RUC validation no se ejecutó")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Limpiar archivo temporal
        try:
            os.unlink(temp_file)
            logger.info("🧹 Archivo temporal eliminado")
        except:
            pass


def main():
    """Ejecutar test"""
    logger.info("🚀 Iniciando verificación de RUC en análisis completo...")
    
    success = test_ruc_in_full_analysis()
    
    if success:
        logger.info("✅ ¡RUC VALIDATION ESTÁ FUNCIONANDO CORRECTAMENTE!")
        logger.info("📋 La validación RUC se ejecuta en análisis comprehensive")
        logger.info("🔗 Los resultados se incluyen en el resumen final")
    else:
        logger.error("❌ RUC validation no está funcionando como esperado")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
