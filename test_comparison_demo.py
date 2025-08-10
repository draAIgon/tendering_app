"""
Demo de comparación de documentos
Prueba la funcionalidad de comparar múltiples propuestas
"""

import sys
sys.path.append('./backend')

from utils.bidding import BiddingAnalysisSystem
import json
from pathlib import Path

def main():
    print("🔄 DEMO COMPARACIÓN DE DOCUMENTOS")
    print("=" * 50)
    
    # Inicializar sistema
    print("📊 Inicializando sistema...")
    system = BiddingAnalysisSystem()
    system.initialize_system(provider="auto")
    print("✅ Sistema listo")
    
    # Obtener documentos para comparar
    law_data_dir = Path("./LawData")
    documents = list(law_data_dir.glob("*.pdf")) + list(law_data_dir.glob("*.txt"))
    
    if len(documents) >= 2:
        # Tomar los primeros 2 documentos para comparar
        doc1 = str(documents[0])
        doc2 = str(documents[1])
        
        print(f"\n🔍 Comparando documentos:")
        print(f"   📄 Documento 1: {Path(doc1).name}")
        print(f"   📄 Documento 2: {Path(doc2).name}")
        
        try:
            # Realizar comparación
            comparison_result = system.compare_proposals(
                proposal_paths=[doc1, doc2],
                comparison_criteria={
                    "structural_weight": 0.3,
                    "content_weight": 0.4,
                    "compliance_weight": 0.3
                }
            )
            
            print("✅ Comparación completada")
            
            # Mostrar resultados
            print("\n📊 Resultados de la comparación:")
            
            # Resumen general
            if 'summary' in comparison_result:
                summary = comparison_result['summary']
                print(f"   📈 Total documentos comparados: {summary.get('total_proposals', 0)}")
                print(f"   ✅ Comparaciones exitosas: {summary.get('successful_comparisons', 0)}")
            
            # Análisis individuales
            individual = comparison_result.get('individual_analyses', {})
            print(f"\n📋 Análisis individuales:")
            for prop_id, analysis in individual.items():
                doc_id = analysis.get('document_id', 'N/A')
                print(f"   {prop_id}: {doc_id}")
                
                # Mostrar puntuaciones si están disponibles
                summary = analysis.get('summary', {})
                if summary:
                    compliance_score = summary.get('compliance_score', 0)
                    risk_score = summary.get('risk_score', 0)
                    print(f"      📊 Cumplimiento: {compliance_score:.1f}%")
                    print(f"      ⚠️ Riesgo: {risk_score:.1f}")
            
            # Recomendación
            if 'recommendation' in comparison_result:
                rec = comparison_result['recommendation']
                print(f"\n🎯 Recomendación:")
                print(f"   🏆 Propuesta recomendada: {rec.get('recommended_proposal', 'N/A')}")
                print(f"   📊 Puntuación: {rec.get('score', 0):.2f}")
                print(f"   💡 Razón: {rec.get('reason', 'N/A')}")
            
            # Errores si los hay
            errors = comparison_result.get('errors', [])
            if errors:
                print(f"\n⚠️ Advertencias:")
                for error in errors:
                    print(f"   • {error}")
            
        except Exception as e:
            print(f"❌ Error en comparación: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print("❌ Se necesitan al menos 2 documentos para comparar")
    
    print(f"\n🎉 Demo de comparación completado!")

if __name__ == "__main__":
    main()
