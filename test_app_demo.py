"""
Demo completo del sistema de análisis de licitaciones
Prueba todas las funcionalidades principales
"""

import sys
sys.path.append('./backend')

from utils.bidding import BiddingAnalysisSystem
import json
import time
from pathlib import Path

def main():
    print("🚀 DEMO COMPLETO - SISTEMA DE ANÁLISIS DE LICITACIONES")
    print("=" * 70)
    
    # 1. Inicializar sistema
    print("\n📊 1. Inicializando sistema...")
    system = BiddingAnalysisSystem()
    
    try:
        system.initialize_system(provider="auto")
        print("✅ Sistema inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando sistema: {e}")
        return
    
    # 2. Verificar documentos disponibles
    print("\n📁 2. Verificando documentos disponibles...")
    law_data_dir = Path("./LawData")
    if law_data_dir.exists():
        documents = list(law_data_dir.glob("*.pdf")) + list(law_data_dir.glob("*.txt"))
        print(f"✅ Encontrados {len(documents)} documentos:")
        for doc in documents[:3]:  # Mostrar solo los primeros 3
            print(f"   📄 {doc.name}")
    else:
        print("❌ Directorio LawData no encontrado")
        return
    
    # 3. Analizar un documento
    if documents:
        test_doc = documents[0]  # Usar el primer documento
        print(f"\n🔍 3. Analizando documento: {test_doc.name}")
        
        try:
            start_time = time.time()
            
            # Análisis completo
            result = system.analyze_document(
                document_path=str(test_doc),
                document_type="pliego",
                analysis_level="comprehensive"
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            print(f"✅ Análisis completado en {processing_time:.2f} segundos")
            
            # Mostrar resultados
            print("\n📊 Resultados del análisis:")
            print(f"   📄 Documento ID: {result.get('document_id', 'N/A')}")
            print(f"   🔍 Etapas completadas: {len([k for k, v in result.get('stages', {}).items() if v.get('status') == 'completed'])}")
            print(f"   ⚠️ Errores: {len(result.get('errors', []))}")
            
            # Mostrar detalles de cada etapa
            for stage_name, stage_data in result.get('stages', {}).items():
                status = stage_data.get('status', 'unknown')
                emoji = "✅" if status == "completed" else "❌" if status == "failed" else "⏳"
                print(f"   {emoji} {stage_name.title()}: {status}")
            
            # 4. Mostrar clasificación si está disponible
            if 'classification' in result.get('stages', {}) and result['stages']['classification'].get('status') == 'completed':
                print("\n📋 4. Clasificación del documento:")
                classification_data = result['stages']['classification']['data']
                
                print(f"   📂 Tipo detectado: {classification_data.get('document_type', 'N/A')}")
                print(f"   🎯 Confianza: {classification_data.get('confidence', 0):.2f}")
                
                sections = classification_data.get('sections', {})
                if sections:
                    print(f"   📑 Secciones identificadas: {len(sections)}")
                    for section_name, section_content in list(sections.items())[:3]:
                        print(f"      • {section_name}: {len(section_content)} elementos")
            
            # 5. Mostrar validación RUC si está disponible
            if 'ruc_validation' in result.get('stages', {}) and result['stages']['ruc_validation'].get('status') == 'completed':
                print("\n🏢 5. Validación de RUC:")
                ruc_data = result['stages']['ruc_validation']['data']
                
                rucs_found = ruc_data.get('rucs_found', [])
                print(f"   🔍 RUCs encontrados: {len(rucs_found)}")
                
                for ruc_info in rucs_found[:2]:  # Mostrar primeros 2
                    ruc = ruc_info.get('ruc', 'N/A')
                    validation = ruc_info.get('validation_result', {})
                    print(f"   📋 RUC: {ruc}")
                    print(f"      ✅ Válido: {validation.get('is_valid', False)}")
                    print(f"      🏢 Razón Social: {validation.get('entity_data', {}).get('razon_social', 'N/A')}")
            
            # 6. Mostrar análisis de riesgo si está disponible
            if 'risk_analysis' in result.get('stages', {}) and result['stages']['risk_analysis'].get('status') == 'completed':
                print("\n⚠️ 6. Análisis de riesgo:")
                risk_data = result['stages']['risk_analysis']['data']
                
                overall_score = risk_data.get('overall_risk_score', 0)
                risk_level = risk_data.get('overall_risk_level', 'N/A')
                
                print(f"   📊 Puntuación de riesgo: {overall_score:.2f}")
                print(f"   ⚠️ Nivel de riesgo: {risk_level}")
                
                risks = risk_data.get('identified_risks', [])
                if risks:
                    print(f"   🚨 Riesgos identificados: {len(risks)}")
                    for risk in risks[:2]:  # Mostrar primeros 2
                        print(f"      • {risk.get('type', 'N/A')}: {risk.get('description', 'N/A')}")
        
        except Exception as e:
            print(f"❌ Error en análisis: {e}")
            import traceback
            traceback.print_exc()
    
    # 7. Probar análisis de RFP específico
    print(f"\n📋 7. Probando análisis especializado de RFP...")
    rfp_files = [f for f in documents if 'pliego' in f.name.lower()]
    
    if rfp_files:
        try:
            rfp_result = system.analyze_rfp_requirements(str(rfp_files[0]))
            print("✅ Análisis de RFP completado")
            
            # Mostrar requisitos extraídos
            requirements = rfp_result.get('extracted_requirements', [])
            if requirements:
                print(f"   📝 Requisitos extraídos: {len(requirements)}")
                for req in requirements[:3]:  # Mostrar primeros 3
                    print(f"      • {req[:100]}...")
            
        except Exception as e:
            print(f"❌ Error en análisis RFP: {e}")
    
    print(f"\n🎉 Demo completado exitosamente!")
    print("=" * 70)

if __name__ == "__main__":
    main()
