import sys
sys.path.insert(0, 'backend')
from utils.bidding import BiddingAnalysisSystem
import os

# Buscar documentos PDF disponibles
pdf_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.pdf'):
            pdf_files.append(os.path.join(root, file))

print('PDFs encontrados:')
for pdf in pdf_files[:3]:  # Mostrar solo los primeros 3
    print(f'  - {pdf}')

if pdf_files:
    # Usar el primer PDF encontrado
    test_pdf = pdf_files[0]
    print(f'\nUsando: {test_pdf}')
    
    # Analizar
    system = BiddingAnalysisSystem('test_success_calc_pdf')
    system.initialize_system(provider='ollama')
    result = system.analyze_document(test_pdf, document_type='RFP', analysis_level='complete')
    
    print('\nAnálisis completado!')
    stages = result.get('stages', {})
    print(f'Stages: {list(stages.keys())}')
    
    summary = result.get('summary', {})
    print(f'Status: {summary.get("overall_status", "N/A")}')
    
    # Mostrar datos para cálculo de éxito
    print('\n=== DATOS PARA CÁLCULO DE ÉXITO ===')
    
    if 'risk_analysis' in stages and stages['risk_analysis'].get('data'):
        risk_data = stages['risk_analysis']['data']
        if 'overall_assessment' in risk_data:
            risk_score = risk_data['overall_assessment'].get('total_risk_score', 'N/A')
            print(f'Risk Score: {risk_score}')
    
    if 'validation' in stages and stages['validation'].get('data'):
        val_score = stages['validation']['data'].get('overall_score', 'N/A')
        print(f'Validation Score: {val_score}')
        
    if 'classification' in stages and stages['classification'].get('data'):
        sections = stages['classification']['data'].get('sections', {})
        print(f'Sections Count: {len(sections)}')
        
    # Calcular éxito estimado manualmente
    print('\n=== CÁLCULO MANUAL DE ÉXITO ===')
    success_score = 0
    
    # Factor 1: Estado general (30%)
    if summary.get('overall_status') == 'success':
        success_score += 30
        print('✅ Estado: success (+30 puntos)')
    elif summary.get('overall_status') == 'partial_success':
        success_score += 15
        print('⚠️ Estado: partial_success (+15 puntos)')
    else:
        print('❌ Estado: failed (+0 puntos)')
    
    # Factor 2: Riesgos (25%)
    if 'risk_analysis' in stages and stages['risk_analysis'].get('data', {}).get('overall_assessment'):
        risk_score = stages['risk_analysis']['data']['overall_assessment'].get('total_risk_score', 0)
        risk_contribution = max(0, 25 - (risk_score * 0.25))
        success_score += risk_contribution
        print(f'🔍 Riesgos: {risk_score}% (+{risk_contribution:.1f} puntos)')
    
    # Factor 3: Validación (25%)
    if 'validation' in stages and stages['validation'].get('data'):
        val_score = stages['validation']['data'].get('overall_score', 0)
        val_contribution = (val_score / 100) * 25
        success_score += val_contribution
        print(f'✅ Validación: {val_score}% (+{val_contribution:.1f} puntos)')
    
    # Factor 4: Clasificación (20%)
    if 'classification' in stages and stages['classification'].get('data', {}).get('sections'):
        sections_count = len(stages['classification']['data']['sections'])
        class_contribution = min(1, sections_count / 5) * 20
        success_score += class_contribution
        print(f'📋 Clasificación: {sections_count} secciones (+{class_contribution:.1f} puntos)')
    
    print(f'\n🎯 ÉXITO ESTIMADO TOTAL: {round(success_score)}%')
    
else:
    print('No se encontraron archivos PDF')
