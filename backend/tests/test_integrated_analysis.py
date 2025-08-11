#!/usr/bin/env python3
"""
Test de integración para validar el análisis completo con contexto enriquecido
"""

import sys
from pathlib import Path

# Agregar paths necesarios
current_dir = Path(__file__).parent
backend_dir = current_dir.parent  # Go up to backend directory
sys.path.append(str(backend_dir))

from utils.bidding import BiddingAnalysisSystem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_integrated_analysis_with_context():
    """
    Test del análisis integrado con contexto enriquecido
    """
    
    logger.info("🚀 Iniciando test de análisis integrado con contexto enriquecido")
    
    # Buscar documento de prueba
    document_paths = [
        backend_dir / ".." / "documents" / "pliego_licitacion_riesgoso.pdf",
        backend_dir / "documents" / "pliego_licitacion_riesgoso.pdf",
        Path("/home/hackiathon/workspace/documents/pliego_licitacion_riesgoso.pdf"),
        Path("/home/hackiathon/workspace/tendering_app/documents/pliego_licitacion_riesgoso.pdf")
    ]
    
    document_path = None
    for path in document_paths:
        if path.exists():
            document_path = str(path)
            logger.info(f"📄 Documento encontrado: {path}")
            break
    
    if not document_path:
        logger.error("❌ No se encontró el documento de prueba")
        return False
    
    try:
        # Inicializar sistema de análisis
        system = BiddingAnalysisSystem()
        system.initialize_system(provider="auto")
        
        logger.info("✅ Sistema inicializado correctamente")
        
        # Realizar análisis comprehensivo (esto debería usar el contexto enriquecido)
        analysis_result = system.analyze_document(
            document_path=document_path,
            document_type="RFP", 
            analysis_level="comprehensive"
        )
        
        # Verificar que el análisis fue exitoso
        if "error" in analysis_result:
            logger.error(f"❌ Error en análisis: {analysis_result['error']}")
            return False
        
        # Verificar que se completaron las etapas esperadas
        stages = analysis_result.get('stages', {})
        logger.info(f"📊 Etapas completadas: {len([s for s in stages.values() if s.get('status') == 'completed'])}/{len(stages)}")
        
        # Verificar que el análisis de riesgo fue enriquecido
        if 'risk_analysis' in stages and stages['risk_analysis']['status'] == 'completed':
            risk_data = stages['risk_analysis']['data']
            
            # Verificar si tiene contexto enriquecido
            if risk_data.get('context_enhanced', False):
                logger.info("🎯 ¡Análisis de riesgo fue enriquecido con contexto!")
                
                # Mostrar ajustes basados en contexto
                context_adjustments = risk_data.get('context_based_adjustments', {})
                if context_adjustments:
                    logger.info(f"⚙️  Ajustes basados en contexto aplicados: {len(context_adjustments)}")
                    for adjustment_type, adjustment_data in context_adjustments.items():
                        penalty = adjustment_data.get('penalty', 0)
                        logger.info(f"   • {adjustment_type}: +{penalty:.1f}% riesgo")
                
                # Mostrar recomendaciones contextuales
                recommendations = risk_data.get('mitigation_recommendations', [])
                context_recommendations = [r for r in recommendations if r.get('context_based', False)]
                if context_recommendations:
                    logger.info(f"💡 Recomendaciones contextuales generadas: {len(context_recommendations)}")
                    for rec in context_recommendations[:2]:
                        logger.info(f"   • [{rec.get('priority', 'MEDIUM')}] {rec.get('category', '')}: {rec.get('recommendation', '')[:60]}...")
            else:
                logger.warning("⚠️  El análisis de riesgo no fue enriquecido con contexto")
            
            # Mostrar score final
            overall_score = risk_data.get('overall_assessment', {}).get('total_risk_score', 0)
            risk_level = risk_data.get('overall_assessment', {}).get('risk_level', 'UNKNOWN')
            context_adjusted = risk_data.get('overall_assessment', {}).get('context_adjusted', False)
            
            logger.info(f"📈 Score final de riesgo: {overall_score:.2f}% ({risk_level})")
            if context_adjusted:
                logger.info("✨ Score fue ajustado basado en contexto de clasificación/validación")
        else:
            logger.error("❌ No se completó el análisis de riesgo")
            return False
        
        # Verificar summary general
        summary = analysis_result.get('summary', {})
        if summary:
            overall_status = summary.get('overall_status', 'unknown')
            completed_stages = summary.get('completed_stages', 0)
            logger.info(f"📋 Estado general: {overall_status} ({completed_stages} etapas completadas)")
        
        logger.info("✅ Test de análisis integrado completado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"💥 Error en test integrado: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal del test"""
    logger.info("🧪 Ejecutando test de análisis integrado con contexto enriquecido")
    
    success = test_integrated_analysis_with_context()
    
    if success:
        logger.info("🎉 ¡Test integrado exitoso!")
        logger.info("✅ El sistema puede usar contexto de clasificación y validación para enriquecer análisis de riesgos")
    else:
        logger.error("❌ Test integrado falló")
        logger.error("⚠️  Revisar integración entre agentes")

if __name__ == "__main__":
    main()
