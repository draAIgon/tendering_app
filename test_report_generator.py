#!/usr/bin/env python3
"""
Script de prueba para el generador de reportes mejorado
"""

import json
from pathlib import Path
from backend.utils.report_generator import generate_html_from_report_data

def create_sample_report_data():
    """Crear datos de ejemplo para el reporte"""
    return {
        "document_analysis": {
            "document_type": "Pliego de Licitación",
            "pages_count": 45,
            "word_count": 12850,
            "confidence_score": 0.92,
            "extraction_successful": True,
            "language": "Spanish",
            "creation_date": "2024-01-15",
            "file_size_mb": 2.3
        },
        "risk_analysis": {
            "overall_risk_score": 7.2,
            "high_risk_items": [
                "Plazo de ejecución muy ajustado (30 días)",
                "Requisitos técnicos específicos no clarificados",
                "Penalizaciones elevadas por incumplimiento"
            ],
            "medium_risk_items": [
                "Experiencia mínima requerida de 5 años",
                "Garantía de cumplimiento del 10%"
            ],
            "risk_categories": {
                "technical": 8.1,
                "financial": 6.3,
                "legal": 7.8,
                "operational": 6.9
            },
            "compliance_percentage": 85.4
        },
        "financial_analysis": {
            "estimated_budget": 150000.50,
            "minimum_guarantee": 15000.00,
            "performance_bond_percentage": 10.0,
            "payment_terms": "30 días calendario",
            "currency": "USD",
            "tax_included": True,
            "advance_payment_allowed": False
        },
        "requirements": [
            "Experiencia mínima de 5 años en proyectos similares",
            "Certificación ISO 9001 vigente",
            "Personal técnico especializado disponible",
            "Capacidad financiera demostrable",
            "Referencias comerciales verificables",
            "Seguros de responsabilidad civil vigentes"
        ],
        "timeline": {
            "publication_date": "2024-01-10",
            "questions_deadline": "2024-01-20",
            "proposal_submission": "2024-02-01",
            "evaluation_period": "2024-02-15",
            "award_notification": "2024-02-20",
            "contract_signing": "2024-02-25",
            "project_start": "2024-03-01",
            "project_duration_days": 90
        },
        "validation": {
            "format_validation": True,
            "content_completeness": True,
            "legal_compliance": True,
            "technical_feasibility": True,
            "missing_sections": [],
            "warning_items": [
                "Algunos criterios de evaluación podrían ser más específicos"
            ]
        },
        "participants": {
            "contracting_entity": "Ministerio de Obras Públicas",
            "contact_person": "Ing. María González",
            "contact_email": "maria.gonzalez@mop.gov",
            "procurement_method": "Licitación Pública",
            "estimated_participants": 8,
            "participation_requirements": {
                "national_companies": True,
                "international_companies": True,
                "joint_ventures_allowed": True,
                "minimum_experience_years": 5
            }
        }
    }

def main():
    """Función principal para generar el reporte de prueba"""
    print("🎨 Generando reporte de prueba con el nuevo diseño...")
    
    # Crear datos de ejemplo
    report_data = create_sample_report_data()
    
    # Generar HTML
    html_content = generate_html_from_report_data(
        report_data=report_data,
        document_id="LICO-V-2024-001",
        report_type="Análisis Completo"
    )
    
    # Guardar archivo HTML
    output_path = Path("reporte_ejemplo.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Reporte generado exitosamente: {output_path.absolute()}")
    print("🌐 Puedes abrir el archivo en tu navegador para ver el resultado")
    
    # Mostrar algunas estadísticas del reporte
    print(f"\n📊 Estadísticas del reporte:")
    print(f"   • Secciones procesadas: {len([k for k in report_data.keys() if k not in ['error', 'status']])}")
    print(f"   • Tamaño del HTML: {len(html_content):,} caracteres")
    print(f"   • Elementos de riesgo alto: {len(report_data.get('risk_analysis', {}).get('high_risk_items', []))}")
    print(f"   • Requisitos identificados: {len(report_data.get('requirements', []))}")

if __name__ == "__main__":
    main()
