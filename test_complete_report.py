#!/usr/bin/env python3
"""
Script de prueba para generar tanto HTML como PDF del reporte mejorado
"""

import json
from pathlib import Path
from backend.utils.report_generator import generate_html_from_report_data, generate_pdf_report

def create_sample_report_data():
    """Crear datos de ejemplo más completos para el reporte"""
    return {
        "executive_summary": {
            "total_score": 8.7,
            "recommendation": "RECOMENDADO PARA PARTICIPACIÓN",
            "risk_level": "MEDIO",
            "estimated_win_probability": 75.5,
            "key_advantages": [
                "Presupuesto competitivo dentro del rango esperado",
                "Requisitos técnicos alcanzables con capacidad actual",
                "Experiencia previa en proyectos similares"
            ],
            "main_challenges": [
                "Plazo de ejecución ajustado",
                "Competencia estimada alta (8+ participantes)"
            ]
        },
        "document_analysis": {
            "document_type": "Pliego de Condiciones Técnicas",
            "total_pages": 67,
            "word_count": 18420,
            "extraction_confidence": 0.94,
            "language_detected": "Spanish (ES)",
            "creation_date": "2024-01-15T09:30:00",
            "last_modified": "2024-01-18T14:22:00",
            "file_size_mb": 3.7,
            "structure_validation": True,
            "digital_signature_present": True
        },
        "financial_analysis": {
            "estimated_budget": 285750.00,
            "currency": "USD",
            "budget_range_min": 250000.00,
            "budget_range_max": 320000.00,
            "advance_payment": 15.0,
            "performance_guarantee": 10.0,
            "warranty_period_months": 12,
            "payment_terms": "Net 30 days",
            "tax_regime": "IVA incluido",
            "contract_type": "Precio fijo",
            "price_adjustment_allowed": False,
            "cost_breakdown_provided": True
        },
        "risk_analysis": {
            "overall_risk_score": 6.8,
            "technical_risk": 7.2,
            "financial_risk": 5.9,
            "legal_risk": 6.1,
            "operational_risk": 7.5,
            "market_risk": 6.4,
            "high_risk_factors": [
                "Plazo de ejecución muy ajustado (45 días calendario)",
                "Penalizaciones por retraso elevadas (2% diario)",
                "Requisitos de personal especializado específicos",
                "Localización geográfica compleja (zona rural)"
            ],
            "medium_risk_factors": [
                "Garantía de cumplimiento del 10%",
                "Experiencia mínima requerida de 5 años",
                "Certificaciones específicas obligatorias"
            ],
            "mitigation_strategies": [
                "Asignar equipo dedicado al proyecto",
                "Establecer plan de contingencia para plazos",
                "Verificar disponibilidad de personal certificado"
            ]
        },
        "technical_requirements": [
            "Certificación ISO 9001:2015 vigente",
            "Personal técnico con mínimo 5 años de experiencia",
            "Equipos especializados de última generación",
            "Cumplimiento de normas de seguridad OHSAS 18001",
            "Software de gestión de proyectos certificado",
            "Plan de calidad detallado y aprobado",
            "Protocolos de seguridad informática implementados",
            "Sistema de respaldo y recuperación de datos",
            "Capacitación específica del personal asignado",
            "Documentación técnica en español e inglés"
        ],
        "timeline_analysis": {
            "publication_date": "2024-01-10",
            "clarification_period": "2024-01-10 al 2024-01-25",
            "proposal_submission_deadline": "2024-02-05 15:00:00",
            "technical_evaluation": "2024-02-06 al 2024-02-15",
            "economic_evaluation": "2024-02-16 al 2024-02-20",
            "award_notification": "2024-02-22",
            "contract_signing": "2024-02-28",
            "project_start_date": "2024-03-05",
            "project_duration_days": 45,
            "project_end_date": "2024-04-19",
            "warranty_start": "2024-04-19",
            "warranty_end": "2025-04-19",
            "total_timeline_days": 99,
            "critical_path_identified": True
        },
        "competition_analysis": {
            "estimated_participants": 12,
            "market_concentration": "Alta",
            "known_competitors": [
                "TechSolutions Corp",
                "InnovateIT Ltd",
                "GlobalServices SA"
            ],
            "competitive_advantages": [
                "Experiencia local comprobada",
                "Equipo técnico especializado disponible",
                "Precios competitivos en el mercado",
                "Referencias sólidas en el sector"
            ],
            "market_position": "Fuerte",
            "win_probability": 0.755,
            "differentiation_factors": [
                "Metodología propia certificada",
                "Soporte post-implementación extendido",
                "Equipo bilingüe español-inglés"
            ]
        },
        "legal_compliance": {
            "regulatory_framework": "Ley de Contratación Pública 2023",
            "compliance_score": 0.92,
            "required_licenses": [
                "Licencia municipal vigente",
                "Registro en cámara de comercio",
                "Certificado de antecedentes judiciales",
                "Póliza de responsabilidad civil"
            ],
            "legal_risks_identified": [
                "Cláusulas de penalización estrictas",
                "Jurisdicción específica para controversias"
            ],
            "contract_terms_analysis": {
                "favorable_terms": 8,
                "neutral_terms": 15,
                "unfavorable_terms": 3
            },
            "recommendations": [
                "Revisar cláusulas de fuerza mayor",
                "Negociar términos de penalización",
                "Clarificar criterios de aceptación"
            ]
        },
        "scoring_criteria": {
            "technical_evaluation": {
                "weight_percentage": 70,
                "max_points": 70,
                "subcriteria": {
                    "methodology": 25,
                    "team_experience": 20,
                    "technical_proposal": 15,
                    "innovation": 10
                }
            },
            "economic_evaluation": {
                "weight_percentage": 30,
                "max_points": 30,
                "evaluation_method": "Menor precio"
            },
            "minimum_technical_score": 50,
            "total_max_score": 100,
            "award_criteria": "Mejor relación calidad-precio"
        }
    }

def main():
    """Función principal para generar reportes HTML y PDF"""
    print("🎨 Generando reportes de prueba con diseño mejorado...")
    
    # Crear datos de ejemplo más completos
    report_data = create_sample_report_data()
    document_id = "LICO-V-2024-INFRAESTRUCTURA-001"
    report_type = "Análisis Integral de Licitación"
    
    # === GENERAR REPORTE HTML ===
    print("\n📄 Generando reporte HTML...")
    html_content = generate_html_from_report_data(
        report_data=report_data,
        document_id=document_id,
        report_type=report_type
    )
    
    # Guardar HTML
    html_path = Path("reporte_completo.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Reporte HTML generado: {html_path.absolute()}")
    
    # === GENERAR REPORTE PDF ===
    print("\n📋 Generando reporte PDF...")
    pdf_path = Path("reporte_completo.pdf")
    
    try:
        pdf_success = generate_pdf_report(
            report_data=report_data,
            document_id=document_id,
            report_type=report_type,
            output_path=pdf_path
        )
        
        if pdf_success:
            print(f"✅ Reporte PDF generado: {pdf_path.absolute()}")
        else:
            print("⚠️ No se pudo generar el PDF (dependencias faltantes)")
            
    except Exception as e:
        print(f"⚠️ Error generando PDF: {e}")
        print("💡 Instala ReportLab o WeasyPrint para generar PDFs")
    
    # === ESTADÍSTICAS DEL REPORTE ===
    print(f"\n📊 Estadísticas del reporte:")
    print(f"   📑 Secciones principales: {len([k for k in report_data.keys() if not k.startswith('_')])}")
    print(f"   💾 Tamaño del HTML: {len(html_content):,} caracteres")
    print(f"   🎯 Puntuación de riesgo: {report_data.get('risk_analysis', {}).get('overall_risk_score', 'N/A')}")
    print(f"   💰 Presupuesto estimado: ${report_data.get('financial_analysis', {}).get('estimated_budget', 0):,.2f}")
    print(f"   📈 Probabilidad de éxito: {report_data.get('competition_analysis', {}).get('win_probability', 0)*100:.1f}%")
    print(f"   ⚖️ Cumplimiento legal: {report_data.get('legal_compliance', {}).get('compliance_score', 0)*100:.1f}%")
    
    print(f"\n🌐 Para ver el reporte HTML, abre: {html_path.absolute()}")
    if pdf_path.exists():
        print(f"📄 Para ver el reporte PDF, abre: {pdf_path.absolute()}")

if __name__ == "__main__":
    main()
