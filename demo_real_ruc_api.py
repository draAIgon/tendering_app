"""
Demo: Integración Real con API del SRI para Validación de RUC
Este script demuestra la nueva funcionalidad de validación real de RUC usando la API del SRI
"""

import sys
sys.path.append('./backend')

from utils.bidding import BiddingAnalysisSystem
from utils.agents.ruc_validator import RUCValidationAgent
import time
import json
from datetime import datetime

def demo_ruc_validation():
    """Demostración de validación de RUC con API real vs simulación"""
    
    print("🚀 DEMO: VALIDACIÓN RUC CON API REAL DEL SRI")
    print("=" * 60)
    
    # RUCs de prueba (algunos válidos conocidos de Ecuador)
    test_rucs = [
        "1790016919001",  # RUC conocido válido
        "1234567890001",  # RUC con formato válido pero probablemente no existe
        "0992398117001",  # Otro RUC de prueba
        "1717171717001"   # RUC de formato válido para prueba
    ]
    
    print(f"\n📝 RUCs a validar: {test_rucs}")
    
    # 1. Crear validador en modo simulación
    print("\n" + "="*60)
    print("🎭 MODO SIMULACIÓN (Por defecto)")
    print("="*60)
    
    validator_sim = RUCValidationAgent(use_real_api=False)
    
    for ruc in test_rucs:
        print(f"\n🔍 Validando RUC: {ruc}")
        result = validator_sim.verify_ruc_online(ruc)
        
        print(f"   ✅ Estado: {result.get('status', 'N/A')}")
        print(f"   🏢 Razón Social: {result.get('razon_social', 'N/A')}")
        print(f"   📊 Fuente: {result.get('source', 'N/A')}")
        print(f"   🎭 Modo Simulación: {result.get('simulation_mode', False)}")
    
    # 2. Crear validador en modo API real
    print("\n" + "="*60)
    print("🌐 MODO API REAL DEL SRI")
    print("="*60)
    print("⚠️  NOTA: Requiere conexión a internet y API del SRI disponible")
    
    validator_real = RUCValidationAgent(use_real_api=True)
    
    for ruc in test_rucs:
        print(f"\n🔍 Validando RUC con API real: {ruc}")
        start_time = time.time()
        
        result = validator_real.verify_ruc_online(ruc)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"   ⏱️  Tiempo: {duration:.2f}s")
        print(f"   ✅ Estado: {result.get('status', 'N/A')}")
        print(f"   🌐 Online: {result.get('online_validation', False)}")
        print(f"   📊 Fuente: {result.get('source', 'N/A')}")
        
        if result.get('found'):
            print(f"   🏢 Razón Social: {result.get('razon_social', 'N/A')}")
            print(f"   📋 Tipo: {result.get('tipo_contribuyente', 'N/A')}")
            print(f"   📍 Estado: {result.get('estado_contribuyente', 'N/A')}")
        elif result.get('fallback_mode'):
            print(f"   ⚠️  Fallback: {result.get('error', 'Error de conexión')}")
        
        # Pausar entre requests para no sobrecargar el SRI
        time.sleep(1)
    
    # 3. Demostrar cache
    print("\n" + "="*60)
    print("💾 DEMO DE CACHE")
    print("="*60)
    
    test_ruc = test_rucs[0]
    print(f"🔍 Validando RUC {test_ruc} por segunda vez...")
    
    start_time = time.time()
    cached_result = validator_real.verify_ruc_online(test_ruc)
    end_time = time.time()
    
    print(f"   ⏱️  Tiempo (cached): {end_time - start_time:.3f}s")
    print(f"   💾 Desde cache: {cached_result.get('from_cache', False)}")
    
    # 4. Integración con BiddingAnalysisSystem
    print("\n" + "="*60)
    print("🏗️  INTEGRACIÓN CON SISTEMA PRINCIPAL")
    print("="*60)
    
    system = BiddingAnalysisSystem()
    system.initialize_system()
    
    print("📊 Estado inicial:")
    status = system.get_ruc_api_status()
    print(f"   🌐 API Real: {status['real_api_enabled']}")
    print(f"   💾 Cache: {status['cache_size']} entradas")
    
    # Habilitar API real
    print("\n🔄 Habilitando API real...")
    system.enable_real_ruc_api(True)
    
    status = system.get_ruc_api_status()
    print(f"   ✅ API Real habilitada: {status['real_api_enabled']}")
    
    # Deshabilitar API real
    print("\n🔄 Deshabilitando API real...")
    system.enable_real_ruc_api(False)
    
    status = system.get_ruc_api_status()
    print(f"   🎭 Modo simulación: {not status['real_api_enabled']}")
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETADO")
    print("="*60)
    print("📝 Funcionalidades demostradas:")
    print("   • Validación RUC con API real del SRI")
    print("   • Fallback automático a simulación")
    print("   • Cache inteligente para evitar llamadas repetitivas")
    print("   • Control dinámico de modo API/simulación")
    print("   • Integración con BiddingAnalysisSystem")
    print("   • Manejo robusto de errores y timeouts")

def demo_api_endpoints():
    """Demostración de cómo usar los nuevos endpoints de la API"""
    
    print("\n🌐 ENDPOINTS DE API DISPONIBLES:")
    print("="*50)
    
    endpoints = [
        {
            "method": "POST",
            "url": "/api/v1/ruc-config/enable-real-api",
            "description": "Habilitar API real del SRI"
        },
        {
            "method": "POST", 
            "url": "/api/v1/ruc-config/disable-real-api",
            "description": "Deshabilitar API real (usar simulación)"
        },
        {
            "method": "GET",
            "url": "/api/v1/ruc-config/status", 
            "description": "Obtener estado de configuración RUC"
        },
        {
            "method": "POST",
            "url": "/api/v1/ruc-config/clear-cache",
            "description": "Limpiar cache de validaciones"
        },
        {
            "method": "POST",
            "url": "/api/v1/ruc-config/test-real-api/{ruc}",
            "description": "Probar API real con RUC específico"
        }
    ]
    
    for endpoint in endpoints:
        print(f"   {endpoint['method']} {endpoint['url']}")
        print(f"      {endpoint['description']}")
        print()
    
    print("📋 Ejemplo de uso con curl:")
    print("   # Habilitar API real")
    print("   curl -X POST http://localhost:8000/api/v1/ruc-config/enable-real-api")
    print()
    print("   # Ver estado")
    print("   curl http://localhost:8000/api/v1/ruc-config/status")
    print()
    print("   # Probar RUC")
    print("   curl -X POST http://localhost:8000/api/v1/ruc-config/test-real-api/1790016919001")

if __name__ == "__main__":
    try:
        demo_ruc_validation()
        demo_api_endpoints()
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error en demo: {e}")
        import traceback
        traceback.print_exc()
