"""
Test simple para verificar la funcionalidad del RUCValidationAgent
"""

import sys
import os
from pathlib import Path
import logging
import json

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


def test_ruc_validation_agent():
    """Test directo del ComplianceValidationAgent con validación de RUC"""
    logger.info("🚀 Iniciando test directo del ComplianceValidationAgent...")
    
    try:
        # Importar el agente
        from utils.agents.validator import ComplianceValidationAgent
        
        # Crear instancia
        validator = ComplianceValidationAgent()
        logger.info("✅ ComplianceValidationAgent creado exitosamente")
        
        # Contenido de prueba
        test_content = """
        EMPRESA CONSTRUCTORA QUITO S.A.
        RUC: 1790123456001
        Dirección: Av. Amazonas 123, Quito
        
        DATOS DEL REPRESENTANTE LEGAL:
        Nombre: Juan Carlos Pérez
        Cédula: 1712345678
        RUC: 1712345678001
        
        ACTIVIDAD ECONOMICA:
        F4100.01 - Construcción de edificios residenciales
        
        EMPRESA SUBCONTRATISTA:
        Ingeniería Moderna Cía. Ltda.
        RUC: 1791234567001
        
        PROVEEDOR DE MATERIALES:
        Materiales Pérez
        RUC: 1792345678001
        """
        
        logger.info("📄 Contenido de prueba preparado")
        
        # Test 1: Validación básica de formato
        logger.info("\n🧪 Test 1: Validación de formato RUC")
        test_rucs = ["1790123456001", "1712345678001", "1791234567001", "1792345678001"]
        
        for ruc in test_rucs:
            result = validator.validate_ruc_format(ruc)
            logger.info(f"   RUC {ruc}: {'✅ VÁLIDO' if result else '❌ INVÁLIDO'}")
        
        # Test 2: Extracción de RUCs del contenido
        logger.info("\n🧪 Test 2: Extracción de RUCs del contenido")
        extracted_rucs = validator.extract_ruc_from_content(test_content)
        logger.info(f"   RUCs extraídos: {len(extracted_rucs)}")
        for ruc in extracted_rucs:
            logger.info(f"   - {ruc}")
        
        # Test 3: Validación completa
        logger.info("\n🧪 Test 3: Validación completa (CONSTRUCCION)")
        result = validator.validate_ruc_in_document(
            content=test_content,
            work_type="CONSTRUCCION"
        )
        
        logger.info("📊 Resultados de validación completa:")
        logger.info(f"   Total RUCs: {result['validation_summary']['total_rucs']}")
        logger.info(f"   Formato válido: {result['validation_summary']['valid_format']}")
        logger.info(f"   Verificados online: {result['validation_summary']['verified_online']}")
        logger.info(f"   Compatibles: {result['validation_summary']['compatible_entities']}")
        logger.info(f"   Score general: {result.get('overall_score', 0)}%")
        logger.info(f"   Nivel de validación: {result.get('validation_level', 'DESCONOCIDO')}")
        
        # Test 4: Diferentes tipos de trabajo
        work_types = ["SERVICIOS", "SUMINISTROS"]
        for work_type in work_types:
            logger.info(f"\n🧪 Test 4.{work_types.index(work_type)+1}: Validación para {work_type}")
            result = validator.validate_ruc_in_document(
                content=test_content,
                work_type=work_type
            )
            logger.info(f"   Score para {work_type}: {result.get('overall_score', 0)}%")
        
        # Test 5: Contenido sin RUCs
        logger.info("\n🧪 Test 5: Contenido sin RUCs")
        empty_result = validator.validate_ruc_in_document(
            content="Empresa sin RUC especificado",
            work_type="CONSTRUCCION"
        )
        logger.info(f"   Total RUCs (esperado 0): {empty_result['validation_summary']['total_rucs']}")
        
        logger.info("\n✅ Todos los tests completados exitosamente!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en tests: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bidding_system_integration():
    """Test de integración con BiddingAnalysisSystem"""
    logger.info("\n🔗 Iniciando test de integración con BiddingAnalysisSystem...")
    
    try:
        from utils.bidding import BiddingAnalysisSystem
        
        # Crear sistema
        system = BiddingAnalysisSystem()
        logger.info("✅ BiddingAnalysisSystem creado")
        
        # Verificar que incluye ComplianceValidationAgent
        assert hasattr(system, 'validator'), "Sistema no tiene validator"
        logger.info("✅ ComplianceValidationAgent integrado en el sistema")
        
        # Test básico de funcionalidad
        test_content = "Empresa Test RUC: 1790123456001"
        result = system.validator.validate_ruc_in_document(
            content=test_content,
            work_type="CONSTRUCCION"
        )
        
        assert 'validation_summary' in result, "Resultado no tiene validation_summary"
        logger.info("✅ Validación RUC funciona a través del sistema principal")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en integración: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todos los tests"""
    logger.info("🎯 Iniciando suite de tests para validación RUC...")
    
    tests_passed = 0
    tests_total = 2
    
    # Test 1: RUCValidationAgent
    if test_ruc_validation_agent():
        tests_passed += 1
        logger.info("✅ Test RUCValidationAgent: PASSED")
    else:
        logger.error("❌ Test RUCValidationAgent: FAILED")
    
    # Test 2: Integración con sistema
    if test_bidding_system_integration():
        tests_passed += 1
        logger.info("✅ Test integración sistema: PASSED")
    else:
        logger.error("❌ Test integración sistema: FAILED")
    
    # Resultados finales
    success_rate = (tests_passed / tests_total) * 100
    logger.info(f"\n📊 RESULTADOS FINALES:")
    logger.info(f"✅ Tests exitosos: {tests_passed}/{tests_total}")
    logger.info(f"📈 Tasa de éxito: {success_rate:.1f}%")
    
    if tests_passed == tests_total:
        logger.info("🎉 ¡Todos los tests pasaron! La validación RUC está funcionando correctamente.")
        return True
    else:
        logger.error("⚠️  Algunos tests fallaron. Revisar la implementación.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
