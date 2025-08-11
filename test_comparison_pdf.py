#!/usr/bin/env python3
"""
Script de prueba para verificar la generación de PDFs de comparación
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Agregar backend al path
backend_dir = Path(__file__).parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Importar función de generación de PDF
from utils.report_generator import generate_comparison_pdf_report, generate_comparison_html

def test_comparison_pdf_generation():
    """
    Probar la generación de PDF de comparación con datos de ejemplo
    """
    print("🧪 Iniciando prueba de generación de PDF de comparación...")
    
    # Datos de ejemplo para un reporte de comparación
    sample_report_data = {
        "comparison_id": "test_comparison_123",
        "documents_included": 3,
        "comparison_summary": {
            "total_proposals": 3,
            "evaluation_criteria": ["price", "technical_score", "delivery_time"],
            "best_proposal": "Propuesta_A",
            "price_range": {
                "min": 85000,
                "max": 120000,
                "average": 102500
            },
            "technical_scores": {
                "Propuesta_A": 92,
                "Propuesta_B": 85,
                "Propuesta_C": 78
            },
            "delivery_times": {
                "Propuesta_A": "45 días",
                "Propuesta_B": "60 días", 
                "Propuesta_C": "30 días"
            }
        },
        "detailed_analysis": {
            "price_analysis": {
                "lowest_bidder": "Propuesta_A",
                "price_competitiveness": "Alta",
                "price_variance": "Moderada"
            },
            "technical_evaluation": {
                "methodology_scores": {
                    "Propuesta_A": 95,
                    "Propuesta_B": 88,
                    "Propuesta_C": 75
                },
                "experience_scores": {
                    "Propuesta_A": 90,
                    "Propuesta_B": 82,
                    "Propuesta_C": 80
                }
            },
            "compliance_check": {
                "fully_compliant": ["Propuesta_A", "Propuesta_B"],
                "partially_compliant": ["Propuesta_C"],
                "non_compliant": []
            }
        },
        "recommendations": [
            "Se recomienda seleccionar la Propuesta A debido a su excelente balance entre precio competitivo y alta calidad técnica.",
            "Considerar negociaciones menores con la Propuesta A para optimizar el cronograma de entrega.",
            "Realizar verificación adicional de referencias para todas las propuestas antes de la adjudicación final.",
            "Evaluar la posibilidad de contratación parcial si el presupuesto lo permite."
        ],
        "generated_at": datetime.now().isoformat()
    }
    
    # Crear directorio de prueba
    test_dir = Path("./test_reports")
    test_dir.mkdir(exist_ok=True)
    
    comparison_id = "test_comparison_123"
    
    # Probar generación de HTML
    print("📄 Generando HTML de prueba...")
    try:
        html_content = generate_comparison_html(sample_report_data, comparison_id)
        html_path = test_dir / f"test_comparison_{comparison_id}.html"
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML generado exitosamente: {html_path}")
        print(f"   Tamaño: {html_path.stat().st_size:,} bytes")
        
    except Exception as e:
        print(f"❌ Error generando HTML: {e}")
        return False
    
    # Probar generación de PDF
    print("📑 Generando PDF de prueba...")
    try:
        pdf_path = test_dir / f"test_comparison_{comparison_id}.pdf"
        
        success = generate_comparison_pdf_report(
            sample_report_data, 
            comparison_id, 
            pdf_path
        )
        
        if success and pdf_path.exists():
            print(f"✅ PDF generado exitosamente: {pdf_path}")
            print(f"   Tamaño: {pdf_path.stat().st_size:,} bytes")
            
            # Verificar contenido del archivo
            if pdf_path.stat().st_size > 1000:  # Al menos 1KB
                print("✅ El PDF parece tener contenido válido")
            else:
                print("⚠️ El PDF parece estar vacío o corrupto")
                
        else:
            print("❌ Error: No se pudo generar el PDF")
            return False
            
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n🎉 Prueba completada exitosamente!")
    print(f"📁 Archivos generados en: {test_dir.absolute()}")
    print("\n📋 Resumen:")
    print(f"   - HTML: {html_path.name} ({html_path.stat().st_size:,} bytes)")
    print(f"   - PDF:  {pdf_path.name} ({pdf_path.stat().st_size:,} bytes)")
    
    return True

def check_dependencies():
    """
    Verificar dependencias necesarias para generar PDFs
    """
    print("🔍 Verificando dependencias...")
    
    # Verificar ReportLab
    try:
        import reportlab
        print(f"✅ ReportLab disponible (versión: {reportlab.Version})")
        reportlab_available = True
    except ImportError:
        print("❌ ReportLab no está disponible")
        reportlab_available = False
    
    # Verificar WeasyPrint (con manejo de errores de dependencias)
    weasyprint_available = False
    try:
        import weasyprint
        print(f"✅ WeasyPrint disponible")
        weasyprint_available = True
    except ImportError:
        print("❌ WeasyPrint no está disponible")
    except OSError as e:
        print(f"⚠️ WeasyPrint instalado pero con dependencias faltantes: {e}")
        print("   (Esto es común en Windows - ReportLab será usado como alternativa)")
    except Exception as e:
        print(f"⚠️ Error verificando WeasyPrint: {e}")
    
    if not reportlab_available and not weasyprint_available:
        print("\n⚠️ ADVERTENCIA: No hay librerías de PDF disponibles.")
        print("   Instala al menos una de las siguientes:")
        print("   - pip install reportlab")
        print("   - pip install weasyprint")
        return False
    
    if reportlab_available:
        print("✅ Al menos ReportLab está disponible para generar PDFs")
    
    return True

if __name__ == "__main__":
    print("🚀 Iniciando prueba de generación de PDFs de comparación\n")
    
    # Verificar dependencias
    if not check_dependencies():
        print("\n❌ No se pueden ejecutar las pruebas sin las dependencias necesarias.")
        sys.exit(1)
    
    print("\n" + "="*60)
    
    # Ejecutar prueba
    if test_comparison_pdf_generation():
        print("\n✅ Todas las pruebas pasaron exitosamente!")
        sys.exit(0)
    else:
        print("\n❌ Algunas pruebas fallaron.")
        sys.exit(1)
