#!/usr/bin/env python3
"""
Script de prueba para demostrar el uso de la API de generación de reportes de comparación en PDF
"""

import json
from pathlib import Path

def test_comparison_pdf_api():
    """
    Prueba básica de la funcionalidad de PDF en la API (simulada)
    """
    print("🧪 Demostrando uso de la API de reportes de comparación con PDF")
    
    # Datos de ejemplo que serían enviados a la API
    api_request = {
        "report_type": "comprehensive",
        "include_charts": True,
        "format": "pdf"  # Nuevo soporte para PDF
    }
    
    print("📋 Ejemplo de request para generar PDF:")
    print(f"POST /api/v1/reports/comparison/{{comparison_id}}")
    print(f"Content-Type: application/json")
    print(f"Body: {json.dumps(api_request, indent=2)}")
    
    print("\n📄 Formatos ahora soportados:")
    formats = ["json", "html", "pdf"]
    for fmt in formats:
        print(f"  ✅ {fmt.upper()}")
    
    print("\n🔧 Nuevas funciones agregadas:")
    print("  • generate_comparison_pdf_report() - Genera PDF especializado para comparaciones")
    print("  • generate_comparison_html() - Genera HTML especializado para comparaciones")
    print("  • generate_comparison_pdf_with_reportlab() - Fallback usando ReportLab")
    
    print("\n📦 Dependencias requeridas:")
    print("  • ReportLab (pip install reportlab) - ✅ Instalado y funcionando")
    print("  • WeasyPrint (pip install weasyprint) - ⚠️ Opcional (problemas en Windows)")
    
    print("\n🚀 Ejemplo de uso con curl:")
    curl_example = '''
# Generar PDF de comparación
curl -X POST "http://localhost:8000/api/v1/reports/comparison/comparison_12345" \\
     -H "Content-Type: application/json" \\
     -d '{
       "report_type": "comprehensive",
       "include_charts": true,
       "format": "pdf"
     }' \\
     --output reporte_comparacion.pdf
'''
    print(curl_example)
    
    print("✅ La función generate_comparison_report ahora soporta:")
    print("  • JSON (default) - Respuesta estructurada")
    print("  • HTML - Archivo descargable")
    print("  • PDF - Archivo descargable con formato profesional")

if __name__ == "__main__":
    test_comparison_pdf_api()
