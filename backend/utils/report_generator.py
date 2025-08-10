"""
Generador de reportes en múltiples formatos
Funciones auxiliares para generar HTML y PDF desde datos de análisis
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Configurar logging
logger = logging.getLogger(__name__)

def generate_html_from_report_data(report_data: Dict[str, Any], document_id: str, report_type: str) -> str:
    """
    Generar HTML básico desde los datos del reporte cuando no hay html_content
    
    Args:
        report_data: Datos del reporte
        document_id: ID del documento
        report_type: Tipo de reporte
        
    Returns:
        Contenido HTML del reporte
    """
    html_template = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reporte de Análisis - {document_id}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                margin: 40px;
                color: #333;
                background-color: #fafafa;
            }}
            .header {{
                text-align: center;
                border-bottom: 3px solid #007acc;
                padding-bottom: 20px;
                margin-bottom: 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }}
            .header p {{
                margin: 5px 0;
                opacity: 0.9;
            }}
            .section {{
                margin-bottom: 30px;
                padding: 25px;
                border-left: 5px solid #007acc;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            .section h2 {{
                color: #007acc;
                margin-top: 0;
                margin-bottom: 20px;
                font-size: 1.8em;
                border-bottom: 2px solid #e0e0e0;
                padding-bottom: 10px;
            }}
            .data-item {{
                margin: 15px 0;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 6px;
                border: 1px solid #e9ecef;
            }}
            .data-item strong {{
                color: #495057;
                display: block;
                margin-bottom: 8px;
                font-size: 1.1em;
            }}
            .highlight {{
                background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
                padding: 20px;
                border-radius: 10px;
                margin: 15px 0;
                border: 1px solid #bbdefb;
            }}
            pre {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 6px;
                overflow-x: auto;
                white-space: pre-wrap;
                border: 1px solid #dee2e6;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                line-height: 1.4;
            }}
            ul {{
                padding-left: 20px;
            }}
            li {{
                margin: 8px 0;
                padding: 5px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 50px;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 8px;
                color: #6c757d;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Reporte de Análisis de Licitación</h1>
            <p><strong>Documento ID:</strong> {document_id}</p>
            <p><strong>Tipo de Reporte:</strong> {report_type.title()}</p>
            <p><strong>Generado:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </div>
    """
    
    # Procesar diferentes secciones del reporte
    for key, value in report_data.items():
        if key in ['error', 'status']:
            continue
            
        section_title = key.replace('_', ' ').title()
        html_template += f"""
        <div class="section">
            <h2>{section_title}</h2>
        """
        
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                html_template += f"""
                <div class="data-item">
                    <strong>{sub_key.replace('_', ' ').title()}:</strong>
                    <div class="highlight">
                        {format_value_for_html(sub_value)}
                    </div>
                </div>
                """
        elif isinstance(value, list):
            html_template += "<ul>"
            for item in value:
                html_template += f"<li>{format_value_for_html(item)}</li>"
            html_template += "</ul>"
        else:
            html_template += f"""
            <div class="highlight">
                {format_value_for_html(value)}
            </div>
            """
        
        html_template += "</div>"
    
    # Footer
    html_template += """
        <div class="footer">
            <p>Generado por Sistema de Análisis de Licitaciones - Team draAIgon</p>
            <p>Este reporte contiene información confidencial del análisis de documentos</p>
        </div>
    </body>
    </html>
    """
    
    return html_template

def format_value_for_html(value: Any) -> str:
    """
    Formatear un valor para mostrar en HTML
    
    Args:
        value: Valor a formatear
        
    Returns:
        Valor formateado como string HTML
    """
    if isinstance(value, dict):
        return f"<pre>{json.dumps(value, indent=2, ensure_ascii=False, default=str)}</pre>"
    elif isinstance(value, list):
        if len(value) > 10:  # Limitar listas muy largas
            return f"<pre>{json.dumps(value[:10], indent=2, ensure_ascii=False, default=str)}\n... y {len(value)-10} elementos más</pre>"
        else:
            return f"<pre>{json.dumps(value, indent=2, ensure_ascii=False, default=str)}</pre>"
    elif isinstance(value, str) and len(value) > 500:  # Limitar strings muy largos
        return f"<p>{value[:500]}...</p>"
    else:
        return f"<p>{str(value)}</p>"

def generate_pdf_with_weasyprint(html_content: str, output_path: Path) -> bool:
    """
    Generar PDF usando WeasyPrint desde contenido HTML
    
    Args:
        html_content: Contenido HTML a convertir
        output_path: Ruta donde guardar el PDF
        
    Returns:
        True si se generó correctamente, False en caso contrario
    """
    try:
        from weasyprint import HTML
        
        # Generar PDF con WeasyPrint
        HTML(string=html_content).write_pdf(output_path)
        logger.info(f"PDF generado exitosamente con WeasyPrint: {output_path}")
        return True
        
    except ImportError:
        logger.warning("WeasyPrint no está disponible")
        return False
    except Exception as e:
        logger.error(f"Error generando PDF con WeasyPrint: {e}")
        return False

def generate_pdf_with_reportlab(report_data: Dict[str, Any], document_id: str, report_type: str, output_path: Path) -> bool:
    """
    Generar PDF usando ReportLab como alternativa a WeasyPrint
    
    Args:
        report_data: Datos del reporte
        document_id: ID del documento  
        report_type: Tipo de reporte
        output_path: Ruta donde guardar el PDF
        
    Returns:
        True si se generó correctamente, False en caso contrario
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        # Crear documento
        doc = SimpleDocTemplate(str(output_path), pagesize=A4, 
                               topMargin=0.8*inch, bottomMargin=0.8*inch,
                               leftMargin=0.8*inch, rightMargin=0.8*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Título principal
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=colors.HexColor('#007acc'),
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph("Reporte de Análisis de Licitación", title_style))
        story.append(Spacer(1, 20))
        
        # Información básica en tabla
        info_data = [
            ['Documento ID:', document_id],
            ['Tipo de Reporte:', report_type.title()],
            ['Generado:', datetime.now().strftime('%d/%m/%Y %H:%M:%S')],
            ['Sistema:', 'Análisis Inteligente de Licitaciones']
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#007acc')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 40))
        
        # Estilo para secciones
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=15,
            textColor=colors.HexColor('#007acc'),
            borderWidth=1,
            borderColor=colors.HexColor('#007acc'),
            borderPadding=10,
            backColor=colors.HexColor('#f8f9fa')
        )
        
        # Procesar secciones del reporte
        for key, value in report_data.items():
            if key in ['error', 'status']:
                continue
                
            # Título de sección
            section_title = key.replace('_', ' ').title()
            story.append(Paragraph(section_title, section_style))
            story.append(Spacer(1, 15))
            
            # Contenido de la sección
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    # Subtítulo
                    story.append(Paragraph(f"<b>{sub_key.replace('_', ' ').title()}:</b>", styles['Normal']))
                    
                    # Contenido limitado
                    content = str(sub_value)
                    if len(content) > 800:
                        content = content[:800] + "..."
                    
                    story.append(Paragraph(content, styles['Normal']))
                    story.append(Spacer(1, 10))
                    
            elif isinstance(value, list):
                # Mostrar lista con límite
                for i, item in enumerate(value[:15]):  # Limitar a 15 items
                    item_text = str(item)
                    if len(item_text) > 300:
                        item_text = item_text[:300] + "..."
                    story.append(Paragraph(f"• {item_text}", styles['Normal']))
                    
                if len(value) > 15:
                    story.append(Paragraph(f"<i>... y {len(value)-15} elementos más</i>", styles['Italic']))
                    
            else:
                # Contenido simple
                content = str(value)
                if len(content) > 1500:
                    content = content[:1500] + "..."
                story.append(Paragraph(content, styles['Normal']))
            
            story.append(Spacer(1, 25))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            textColor=colors.grey
        )
        story.append(Spacer(1, 30))
        story.append(Paragraph("Generado por Sistema de Análisis de Licitaciones - Team draAIgon", footer_style))
        story.append(Paragraph("Este reporte contiene información confidencial del análisis de documentos", footer_style))
        
        # Construir PDF
        doc.build(story)
        logger.info(f"PDF generado exitosamente con ReportLab: {output_path}")
        return True
        
    except ImportError:
        logger.warning("ReportLab no está disponible para generación de PDF")
        return False
    except Exception as e:
        logger.error(f"Error generando PDF con ReportLab: {e}")
        return False

def generate_pdf_report(report_data: Dict[str, Any], document_id: str, report_type: str, output_path: Path) -> bool:
    """
    Función principal para generar PDF con fallback automático
    
    Args:
        report_data: Datos del reporte
        document_id: ID del documento
        report_type: Tipo de reporte
        output_path: Ruta donde guardar el PDF
        
    Returns:
        True si se generó correctamente, False en caso contrario
    """
    # Primero intentar con HTML si existe
    html_content = report_data.get('html_content')
    if html_content and generate_pdf_with_weasyprint(html_content, output_path):
        return True
    
    # Si no hay HTML, generar uno y intentar con WeasyPrint
    if not html_content:
        html_content = generate_html_from_report_data(report_data, document_id, report_type)
        if generate_pdf_with_weasyprint(html_content, output_path):
            return True
    
    # Fallback a ReportLab
    logger.info("Usando ReportLab como alternativa para generar PDF")
    return generate_pdf_with_reportlab(report_data, document_id, report_type, output_path)
