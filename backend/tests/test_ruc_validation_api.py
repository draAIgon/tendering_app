"""
Tests para los endpoints de validación RUC de la API
"""

import pytest
import json
import asyncio
from pathlib import Path
import logging
from fastapi.testclient import TestClient

# Configurar path
import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

root_dir = os.path.dirname(backend_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from api.main import app

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestRUCValidationAPI:
    """Suite de tests para validación RUC via API"""
    
    def setup_method(self):
        """Configuración para cada test"""
        self.client = TestClient(app)
        
        # Contenido de prueba con RUCs
        self.test_content = """
        EMPRESA CONSTRUCTORA QUITO S.A.
        RUC: 1790123456001
        Dirección: Av. Amazonas 123, Quito
        
        DATOS DEL REPRESENTANTE LEGAL:
        Nombre: Juan Carlos Pérez
        Cédula: 1712345678
        RUC: 1712345678001
        
        ACTIVIDAD ECONOMICA:
        F4100.01 - Construcción de edificios residenciales
        
        INFORMACIÓN BANCARIA:
        Banco del Pichincha
        Cuenta: 2200123456
        """
    
    def test_validate_ruc_content_basic(self):
        """Test validación RUC básica desde contenido"""
        logger.info("🧪 Test: Validación RUC básica desde contenido")
        
        response = self.client.post(
            "/api/validate-ruc-content",
            data={
                "content": self.test_content,
                "work_type": "CONSTRUCCION"
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["work_type"] == "CONSTRUCCION"
        assert "ruc_validation" in data
        
        ruc_validation = data["ruc_validation"]
        assert "validation_summary" in ruc_validation
        assert "detailed_results" in ruc_validation
        
        logger.info(f"✅ RUCs encontrados: {ruc_validation['validation_summary'].get('total_rucs', 0)}")
        logger.info(f"✅ Score general: {ruc_validation.get('overall_score', 0)}%")
    
    def test_validate_ruc_content_different_work_types(self):
        """Test validación con diferentes tipos de trabajo"""
        work_types = ["CONSTRUCCION", "SERVICIOS", "SUMINISTROS"]
        
        for work_type in work_types:
            logger.info(f"🧪 Test: Validación RUC para tipo {work_type}")
            
            response = self.client.post(
                "/api/validate-ruc-content",
                data={
                    "content": self.test_content,
                    "work_type": work_type
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["work_type"] == work_type
            
            logger.info(f"✅ Tipo {work_type} procesado correctamente")
    
    def test_validate_ruc_content_empty(self):
        """Test validación con contenido vacío"""
        logger.info("🧪 Test: Validación RUC con contenido vacío")
        
        response = self.client.post(
            "/api/validate-ruc-content",
            data={
                "content": "",
                "work_type": "CONSTRUCCION"
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        
        ruc_validation = data["ruc_validation"]
        assert ruc_validation["validation_summary"]["total_rucs"] == 0
        
        logger.info("✅ Contenido vacío manejado correctamente")
    
    def test_validate_ruc_content_no_rucs(self):
        """Test validación con contenido sin RUCs"""
        logger.info("🧪 Test: Validación contenido sin RUCs")
        
        content_no_rucs = """
        Empresa de Construcción ABC
        Dirección: Calle 123
        Teléfono: 02-2345678
        """
        
        response = self.client.post(
            "/api/validate-ruc-content",
            data={
                "content": content_no_rucs,
                "work_type": "CONSTRUCCION"
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        ruc_validation = data["ruc_validation"]
        assert ruc_validation["validation_summary"]["total_rucs"] == 0
        
        logger.info("✅ Contenido sin RUCs manejado correctamente")
    
    def test_ruc_validation_status_nonexistent(self):
        """Test estado de validación para documento inexistente"""
        logger.info("🧪 Test: Estado validación documento inexistente")
        
        response = self.client.get("/api/ruc-validation-status/documento_inexistente")
        
        assert response.status_code == 404
        
        logger.info("✅ Documento inexistente manejado correctamente")
    
    def test_validate_ruc_document_nonexistent(self):
        """Test validación RUC para documento inexistente"""
        logger.info("🧪 Test: Validación RUC documento inexistente")
        
        response = self.client.post(
            "/api/validate-ruc/documento_inexistente",
            json={"work_type": "CONSTRUCCION"}
        )
        
        assert response.status_code == 404
        
        logger.info("✅ Documento inexistente manejado correctamente")
    
    def test_api_health_check(self):
        """Test básico de salud de la API"""
        logger.info("🧪 Test: Health check API")
        
        response = self.client.get("/health")
        assert response.status_code == 200
        
        logger.info("✅ API funcionando correctamente")
    
    def test_ruc_validation_integration(self):
        """Test integración completa con análisis de contenido"""
        logger.info("🧪 Test: Integración completa validación RUC")
        
        # Contenido con múltiples RUCs
        multi_ruc_content = """
        PROPUESTA TÉCNICA
        
        EMPRESA PRINCIPAL:
        Constructora Quito S.A.
        RUC: 1790123456001
        
        EMPRESA SUBCONTRATISTA:
        Ingeniería Moderna Cía. Ltda.
        RUC: 1791234567001
        
        PROVEEDOR DE MATERIALES:
        Materiales Pérez
        RUC: 1792345678001
        """
        
        response = self.client.post(
            "/api/validate-ruc-content",
            data={
                "content": multi_ruc_content,
                "work_type": "CONSTRUCCION"
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        ruc_validation = data["ruc_validation"]
        
        # Verificar que se encontraron múltiples RUCs
        total_rucs = ruc_validation["validation_summary"]["total_rucs"]
        assert total_rucs >= 3, f"Se esperaban al menos 3 RUCs, se encontraron {total_rucs}"
        
        # Verificar detalles de validación
        assert "detailed_results" in ruc_validation
        assert len(ruc_validation["detailed_results"]) == total_rucs
        
        logger.info(f"✅ Procesados {total_rucs} RUCs exitosamente")
        logger.info(f"✅ Score general: {ruc_validation.get('overall_score', 0)}%")


def main():
    """Ejecutar tests de validación RUC API"""
    logger.info("🚀 Iniciando tests de validación RUC API...")
    
    test_suite = TestRUCValidationAPI()
    test_methods = [
        method for method in dir(test_suite) 
        if method.startswith('test_') and callable(getattr(test_suite, method))
    ]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            test_suite.setup_method()
            method = getattr(test_suite, test_method)
            method()
            passed += 1
            logger.info(f"✅ {test_method} - PASSED")
        except Exception as e:
            failed += 1
            logger.error(f"❌ {test_method} - FAILED: {e}")
    
    logger.info(f"\n📊 RESULTADOS FINALES:")
    logger.info(f"✅ Tests exitosos: {passed}")
    logger.info(f"❌ Tests fallidos: {failed}")
    logger.info(f"📈 Tasa de éxito: {(passed/(passed+failed)*100):.1f}%")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
