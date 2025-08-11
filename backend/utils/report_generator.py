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
    Generar HTML profesional y atractivo desde los datos del reporte
    
    Args:
        report_data: Datos del reporte
        document_id: ID del documento
        report_type: Tipo de reporte
        
    Returns:
        Contenido HTML del reporte mejorado
    """
    # Generar tabla de contenidos
    toc_items = []
    for key in report_data.keys():
        if key not in ['error', 'status', 'html_content']:
            section_title = key.replace('_', ' ').title()
            toc_items.append(f'<li><a href="#{key.lower()}">{section_title}</a></li>')
    
    toc_html = '<ul>' + ''.join(toc_items) + '</ul>' if toc_items else ''
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reporte de Análisis - {document_id}</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {{
                --primary-color: #2563eb;
                --secondary-color: #1e40af;
                --accent-color: #3b82f6;
                --success-color: #10b981;
                --warning-color: #f59e0b;
                --danger-color: #ef4444;
                --light-bg: #f8fafc;
                --card-bg: #ffffff;
                --text-primary: #1e293b;
                --text-secondary: #64748b;
                --border-color: #e2e8f0;
                --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: var(--text-primary);
                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                min-height: 100vh;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            
            .header {{
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                color: white;
                padding: 40px;
                border-radius: 16px;
                margin-bottom: 30px;
                box-shadow: var(--shadow-lg);
                position: relative;
                overflow: hidden;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: 0;
                right: 0;
                width: 100px;
                height: 100px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 50%;
                transform: translate(30px, -30px);
            }}
            
            .header h1 {{
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 15px;
            }}
            
            .header-info {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }}
            
            .info-card {{
                background: rgba(255, 255, 255, 0.15);
                padding: 15px;
                border-radius: 12px;
                backdrop-filter: blur(10px);
            }}
            
            .info-card i {{
                font-size: 1.2rem;
                margin-right: 8px;
            }}
            
            .toc {{
                background: var(--card-bg);
                padding: 25px;
                border-radius: 12px;
                margin-bottom: 30px;
                box-shadow: var(--shadow);
                border: 1px solid var(--border-color);
            }}
            
            .toc h2 {{
                color: var(--primary-color);
                margin-bottom: 20px;
                font-size: 1.4rem;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .toc ul {{
                list-style: none;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 10px;
            }}
            
            .toc a {{
                color: var(--text-secondary);
                text-decoration: none;
                padding: 8px 12px;
                border-radius: 8px;
                transition: all 0.3s ease;
                display: block;
                border: 1px solid transparent;
            }}
            
            .toc a:hover {{
                background: var(--light-bg);
                color: var(--primary-color);
                border-color: var(--border-color);
                transform: translateX(5px);
            }}
            
            .section {{
                background: var(--card-bg);
                margin-bottom: 30px;
                border-radius: 16px;
                box-shadow: var(--shadow);
                border: 1px solid var(--border-color);
                overflow: hidden;
                transition: transform 0.3s ease;
            }}
            
            .section:hover {{
                transform: translateY(-2px);
                box-shadow: var(--shadow-lg);
            }}
            
            .section-header {{
                background: linear-gradient(135deg, var(--light-bg) 0%, #e0f2fe 100%);
                padding: 25px;
                border-bottom: 1px solid var(--border-color);
            }}
            
            .section h2 {{
                color: var(--primary-color);
                font-size: 1.6rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            
            .section-content {{
                padding: 25px;
            }}
            
            .data-item {{
                margin-bottom: 20px;
                padding: 20px;
                background: var(--light-bg);
                border-radius: 12px;
                border: 1px solid var(--border-color);
                transition: all 0.3s ease;
            }}
            
            .data-item:hover {{
                border-color: var(--accent-color);
                transform: translateX(5px);
            }}
            
            .data-item-title {{
                color: var(--text-primary);
                font-weight: 600;
                font-size: 1.1rem;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            .data-content {{
                background: var(--card-bg);
                padding: 15px;
                border-radius: 8px;
                border: 1px solid var(--border-color);
            }}
            
            .highlight {{
                background: linear-gradient(135deg, #dbeafe 0%, #e0f2fe 100%);
                padding: 20px;
                border-radius: 12px;
                margin: 15px 0;
                border-left: 4px solid var(--primary-color);
                box-shadow: var(--shadow);
            }}
            
            .code-block {{
                background: #1e293b;
                color: #e2e8f0;
                padding: 20px;
                border-radius: 8px;
                overflow-x: auto;
                white-space: pre-wrap;
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                font-size: 0.9rem;
                line-height: 1.5;
                border: 1px solid #334155;
            }}
            
            .json-content {{
                background: #f8fafc;
                border: 1px solid var(--border-color);
                border-radius: 8px;
                padding: 15px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.85rem;
                max-height: 400px;
                overflow-y: auto;
            }}
            
            .list-container {{
                background: var(--card-bg);
                border-radius: 8px;
                border: 1px solid var(--border-color);
                overflow: hidden;
                margin: 10px 0;
            }}
            
            .list-item {{
                padding: 12px 16px;
                border-bottom: 1px solid var(--border-color);
                transition: background-color 0.3s ease;
                display: block;
                word-wrap: break-word;
                overflow-wrap: break-word;
                line-height: 1.6;
                position: relative;
            }}
            
            .list-item i {{
                margin-right: 8px;
                color: var(--primary-color);
                display: inline-block;
                width: 16px;
            }}
            
            .list-item span {{
                display: inline;
                vertical-align: top;
            }}
            
            .list-item:last-child {{
                border-bottom: none;
            }}
            
            .list-item:hover {{
                background-color: #f8fafc;
            }}
            
            .badge {{
                display: inline-flex;
                align-items: center;
                padding: 4px 12px;
                background: var(--primary-color);
                color: white;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 500;
                gap: 5px;
            }}
            
            .badge.success {{ background: var(--success-color); }}
            .badge.warning {{ background: var(--warning-color); }}
            .badge.danger {{ background: var(--danger-color); }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            
            .stat-card {{
                background: var(--card-bg);
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border: 1px solid var(--border-color);
                transition: all 0.3s ease;
            }}
            
            .stat-card:hover {{
                transform: translateY(-5px);
                box-shadow: var(--shadow-lg);
            }}
            
            .stat-number {{
                font-size: 2rem;
                font-weight: 700;
                color: var(--primary-color);
                display: block;
            }}
            
            .stat-label {{
                color: var(--text-secondary);
                font-size: 0.9rem;
                margin-top: 5px;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 50px;
                padding: 30px;
                background: var(--card-bg);
                border-radius: 16px;
                border: 1px solid var(--border-color);
                color: var(--text-secondary);
            }}
            
            .footer-logo {{
                font-size: 1.5rem;
                color: var(--primary-color);
                margin-bottom: 10px;
            }}
            
            @media (max-width: 768px) {{
                .container {{ padding: 10px; }}
                .header {{ padding: 20px; }}
                .header h1 {{ font-size: 1.8rem; }}
                .header-info {{ grid-template-columns: 1fr; }}
                .section-content {{ padding: 15px; }}
                .toc ul {{ grid-template-columns: 1fr; }}
            }}
            
            .scroll-indicator {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 4px;
                background: linear-gradient(to right, var(--primary-color) 0%, var(--accent-color) 100%);
                transform-origin: left;
                z-index: 1000;
            }}
        </style>
    </head>
    <body>
        <div class="scroll-indicator"></div>
        <div class="container">
            <div class="header">
                <h1>
                    <i class="fas fa-file-contract"></i>
                    Reporte de Análisis de Licitación
                </h1>
                <div class="header-info">
                    <div class="info-card">
                        <i class="fas fa-file-alt"></i>
                        <strong>Documento:</strong> {document_id}
                    </div>
                    <div class="info-card">
                        <i class="fas fa-tag"></i>
                        <strong>Tipo:</strong> {report_type.title()}
                    </div>
                    <div class="info-card">
                        <i class="fas fa-calendar"></i>
                        <strong>Generado:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}
                    </div>
                    <div class="info-card">
                        <i class="fas fa-robot"></i>
                        <strong>Sistema:</strong> draAIgon AI
                    </div>
                </div>
            </div>
            
            {f'<div class="toc"><h2><i class="fas fa-list"></i>Índice de Contenidos</h2>{toc_html}</div>' if toc_items else ''}
    """
    
    # Procesar diferentes secciones del reporte
    for key, value in report_data.items():
        if key in ['error', 'status', 'html_content']:
            continue
            
        section_title = key.replace('_', ' ').title()
        section_icon = get_section_icon(key)
        
        html_template += f"""
        <div class="section" id="{key.lower()}">
            <div class="section-header">
                <h2>
                    <i class="{section_icon}"></i>
                    {section_title}
                </h2>
            </div>
            <div class="section-content">
        """
        
        if isinstance(value, dict):
            # Mostrar estadísticas si es apropiado
            if should_show_stats(key, value):
                html_template += generate_stats_grid(value)
            
            for sub_key, sub_value in value.items():
                item_icon = get_item_icon(sub_key, sub_value)
                html_template += f"""
                <div class="data-item">
                    <div class="data-item-title">
                        <i class="{item_icon}"></i>
                        {sub_key.replace('_', ' ').title()}
                    </div>
                    <div class="data-content">
                        {format_value_for_html_enhanced(sub_value, sub_key)}
                    </div>
                </div>
                """
        elif isinstance(value, list):
            html_template += f'<div class="list-container">'
            for i, item in enumerate(value):
                if i >= 50:  # Limitar elementos mostrados
                    html_template += f'<div class="list-item"><i class="fas fa-ellipsis-h"></i>... y {len(value)-50} elementos más</div>'
                    break
                html_template += f"""
                <div class="list-item">
                    <i class="fas fa-check-circle" style="color: var(--success-color);"></i>
                    {format_value_for_html_enhanced(item, key)}
                </div>
                """
            html_template += "</div>"
        else:
            html_template += f"""
            <div class="highlight">
                {format_value_for_html_enhanced(value, key)}
            </div>
            """
        
        html_template += """
            </div>
        </div>
        """
    
    # Footer
    html_template += """
        <div class="footer">
            <div class="footer-logo">
                <i class="fas fa-dragon"></i>
                draAIgon
            </div>
            <p><strong>Sistema de Análisis Inteligente de Licitaciones</strong></p>
            <p>Este reporte contiene información confidencial del análisis de documentos</p>
            <p style="margin-top: 15px; font-size: 0.8rem;">
                <i class="fas fa-shield-alt"></i>
                Generado con tecnología de IA avanzada | 
                <i class="fas fa-clock"></i>
                {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            </p>
        </div>
        
        <script>
            // Scroll indicator
            window.addEventListener('scroll', function() {{
                const scrollTop = window.pageYOffset;
                const docHeight = document.body.offsetHeight;
                const winHeight = window.innerHeight;
                const scrollPercent = scrollTop / (docHeight - winHeight);
                const scrollIndicator = document.querySelector('.scroll-indicator');
                if (scrollIndicator) {{
                    scrollIndicator.style.transform = `scaleX(${{scrollPercent}})`;
                }}
            }});
            
            // Smooth scrolling for TOC links
            document.querySelectorAll('.toc a[href^="#"]').forEach(anchor => {{
                anchor.addEventListener('click', function (e) {{
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {{
                        target.scrollIntoView({{
                            behavior: 'smooth',
                            block: 'start'
                        }});
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    """
    
    return html_template

def get_section_icon(section_key: str) -> str:
    """
    Obtener icono apropiado para cada sección del reporte
    
    Args:
        section_key: Clave de la sección
        
    Returns:
        Clase CSS del icono Font Awesome
    """
    icon_map = {
        'document_analysis': 'fas fa-file-search',
        'risk_analysis': 'fas fa-exclamation-triangle',
        'classification': 'fas fa-tags',
        'validation': 'fas fa-check-circle',
        'comparison': 'fas fa-balance-scale',
        'requirements': 'fas fa-list-check',
        'legal_compliance': 'fas fa-gavel',
        'financial_analysis': 'fas fa-chart-line',
        'timeline': 'fas fa-clock',
        'participants': 'fas fa-users',
        'documents': 'fas fa-folder-open',
        'summary': 'fas fa-clipboard-list',
        'recommendations': 'fas fa-lightbulb',
        'alerts': 'fas fa-bell',
        'metadata': 'fas fa-info-circle'
    }
    
    # Buscar coincidencias parciales
    for key, icon in icon_map.items():
        if key in section_key.lower():
            return icon
    
    return 'fas fa-file-alt'  # Icono por defecto

def get_item_icon(item_key: str, item_value: Any) -> str:
    """
    Obtener icono apropiado para cada elemento de datos
    
    Args:
        item_key: Clave del elemento
        item_value: Valor del elemento
        
    Returns:
        Clase CSS del icono Font Awesome
    """
    key_lower = item_key.lower()
    
    # Iconos específicos por tipo de contenido
    if 'error' in key_lower or 'issue' in key_lower:
        return 'fas fa-exclamation-circle'
    elif 'success' in key_lower or 'valid' in key_lower or 'approved' in key_lower:
        return 'fas fa-check-circle'
    elif 'warning' in key_lower or 'alert' in key_lower:
        return 'fas fa-exclamation-triangle'
    elif 'date' in key_lower or 'time' in key_lower:
        return 'fas fa-calendar'
    elif 'amount' in key_lower or 'price' in key_lower or 'cost' in key_lower:
        return 'fas fa-dollar-sign'
    elif 'score' in key_lower or 'rating' in key_lower:
        return 'fas fa-star'
    elif 'count' in key_lower or 'number' in key_lower:
        return 'fas fa-hashtag'
    elif 'percentage' in key_lower or 'percent' in key_lower:
        return 'fas fa-percent'
    elif 'email' in key_lower:
        return 'fas fa-envelope'
    elif 'phone' in key_lower or 'tel' in key_lower:
        return 'fas fa-phone'
    elif 'address' in key_lower or 'location' in key_lower:
        return 'fas fa-map-marker-alt'
    elif 'url' in key_lower or 'link' in key_lower:
        return 'fas fa-external-link-alt'
    elif isinstance(item_value, bool):
        return 'fas fa-toggle-on' if item_value else 'fas fa-toggle-off'
    elif isinstance(item_value, (int, float)):
        return 'fas fa-calculator'
    elif isinstance(item_value, list):
        return 'fas fa-list'
    elif isinstance(item_value, dict):
        return 'fas fa-project-diagram'
    else:
        return 'fas fa-info'

def should_show_stats(section_key: str, section_value: dict) -> bool:
    """
    Determinar si mostrar estadísticas para una sección
    
    Args:
        section_key: Clave de la sección
        section_value: Valor de la sección
        
    Returns:
        True si debe mostrar estadísticas, False en caso contrario
    """
    if not isinstance(section_value, dict):
        return False
    
    # Contar valores numéricos, booleanos y listas
    numeric_values = []
    for key, value in section_value.items():
        if isinstance(value, (int, float)) and key.lower() not in ['id', 'version']:
            numeric_values.append((key, value))
        elif isinstance(value, bool):
            numeric_values.append((key, 1 if value else 0))
        elif isinstance(value, list):
            numeric_values.append((key, len(value)))
    
    return len(numeric_values) >= 2  # Mostrar stats si hay al menos 2 valores numéricos

def generate_stats_grid(section_value: dict) -> str:
    """
    Generar grid de estadísticas para una sección
    
    Args:
        section_value: Valor de la sección
        
    Returns:
        HTML del grid de estadísticas
    """
    stats_html = '<div class="stats-grid">'
    
    for key, value in section_value.items():
        if isinstance(value, (int, float)) and key.lower() not in ['id', 'version']:
            stats_html += f"""
            <div class="stat-card">
                <span class="stat-number">{value:,.0f}</span>
                <div class="stat-label">{key.replace('_', ' ').title()}</div>
            </div>
            """
        elif isinstance(value, bool):
            badge_class = 'success' if value else 'danger'
            stats_html += f"""
            <div class="stat-card">
                <span class="badge {badge_class}">
                    <i class="fas fa-{'check' if value else 'times'}"></i>
                    {'Sí' if value else 'No'}
                </span>
                <div class="stat-label">{key.replace('_', ' ').title()}</div>
            </div>
            """
        elif isinstance(value, list):
            stats_html += f"""
            <div class="stat-card">
                <span class="stat-number">{len(value)}</span>
                <div class="stat-label">{key.replace('_', ' ').title()}</div>
            </div>
            """
    
    stats_html += '</div>'
    return stats_html

def format_scoring_criteria(value: dict, context_key: str = '') -> str:
    """
    Formatear criterios de evaluación de manera más legible
    
    Args:
        value: Diccionario con criterios de evaluación
        context_key: Clave del contexto
        
    Returns:
        HTML formateado para criterios de evaluación
    """
    if not isinstance(value, dict):
        return str(value)
    
    # Detectar si es un criterio de evaluación técnica o económica
    if 'weight_percentage' in value or 'max_points' in value or 'subcriteria' in value:
        html = '<div class="evaluation-criteria">'
        
        # Mostrar peso y puntos máximos
        if 'weight_percentage' in value:
            html += f'''
            <div class="criteria-header">
                <div class="criteria-weight">
                    <i class="fas fa-percentage"></i>
                    <span class="weight-label">Peso:</span>
                    <span class="weight-value">{value['weight_percentage']}%</span>
                </div>
            '''
        
        if 'max_points' in value:
            html += f'''
                <div class="criteria-points">
                    <i class="fas fa-star"></i>
                    <span class="points-label">Puntos máximos:</span>
                    <span class="points-value">{value['max_points']}</span>
                </div>
            </div>
            '''
        
        # Mostrar subcriterios si existen
        if 'subcriteria' in value and isinstance(value['subcriteria'], dict):
            html += '''
            <div class="subcriteria-section">
                <h4><i class="fas fa-list-ul"></i> Subcriterios:</h4>
                <div class="subcriteria-grid">
            '''
            
            for sub_name, sub_points in value['subcriteria'].items():
                html += f'''
                <div class="subcriteria-item">
                    <div class="subcriteria-name">{sub_name.replace('_', ' ').title()}</div>
                    <div class="subcriteria-points">{sub_points} pts</div>
                </div>
                '''
            
            html += '</div></div>'
        
        # Mostrar método de evaluación si existe
        if 'evaluation_method' in value:
            html += f'''
            <div class="evaluation-method">
                <i class="fas fa-calculator"></i>
                <span class="method-label">Método de evaluación:</span>
                <span class="method-value">{value['evaluation_method']}</span>
            </div>
            '''
        
        # Mostrar otros campos
        other_fields = {k: v for k, v in value.items() 
                       if k not in ['weight_percentage', 'max_points', 'subcriteria', 'evaluation_method']}
        
        if other_fields:
            html += '<div class="other-criteria">'
            for field_key, field_value in other_fields.items():
                html += f'''
                <div class="criteria-field">
                    <span class="field-label">{field_key.replace('_', ' ').title()}:</span>
                    <span class="field-value">{field_value}</span>
                </div>
                '''
            html += '</div>'
        
        html += '</div>'
        
        # Agregar estilos CSS específicos para criterios
        html += '''
        <style>
        .evaluation-criteria {
            background: linear-gradient(135deg, #f8fafc 0%, #e0f2fe 100%);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
        }
        
        .criteria-header {
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .criteria-weight, .criteria-points {
            background: var(--card-bg);
            padding: 10px 15px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: var(--shadow);
        }
        
        .weight-value, .points-value {
            font-weight: 700;
            color: var(--primary-color);
            font-size: 1.1rem;
        }
        
        .subcriteria-section h4 {
            color: var(--text-primary);
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .subcriteria-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
        
        .subcriteria-item {
            background: var(--card-bg);
            padding: 12px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease;
        }
        
        .subcriteria-item:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }
        
        .subcriteria-name {
            font-weight: 500;
            color: var(--text-primary);
        }
        
        .subcriteria-points {
            background: var(--accent-color);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .evaluation-method {
            background: var(--light-bg);
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid var(--success-color);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .method-value {
            background: var(--success-color);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 500;
        }
        
        .other-criteria {
            margin-top: 15px;
        }
        
        .criteria-field {
            background: var(--card-bg);
            padding: 8px 12px;
            margin-bottom: 5px;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            display: flex;
            gap: 10px;
        }
        
        .field-label {
            font-weight: 500;
            color: var(--text-secondary);
        }
        
        .field-value {
            color: var(--text-primary);
            font-weight: 600;
        }
        </style>
        '''
        
        return html
    
    # Si no es un criterio de evaluación específico, usar formato JSON mejorado
    return f'<div class="json-content">{json.dumps(value, indent=2, ensure_ascii=False, default=str)}</div>'

def format_value_for_html_enhanced(value: Any, context_key: str = '') -> str:
    """
    Formatear un valor para mostrar en HTML con mejoras visuales
    
    Args:
        value: Valor a formatear
        context_key: Clave del contexto para formateo específico
        
    Returns:
        Valor formateado como string HTML
    """
    if value is None:
        return '<span class="badge" style="background: var(--text-secondary);">Sin datos</span>'
    
    if isinstance(value, bool):
        badge_class = 'success' if value else 'danger'
        icon = 'check' if value else 'times'
        text = 'Sí' if value else 'No'
        return f'<span class="badge {badge_class}"><i class="fas fa-{icon}"></i> {text}</span>'
    
    if isinstance(value, (int, float)):
        if 'percentage' in context_key.lower() or 'percent' in context_key.lower():
            return f'<span class="badge" style="background: var(--accent-color);"><i class="fas fa-percent"></i> {value:.1f}%</span>'
        elif 'score' in context_key.lower() or 'rating' in context_key.lower():
            return f'<span class="badge warning"><i class="fas fa-star"></i> {value:.1f}</span>'
        elif 'amount' in context_key.lower() or 'price' in context_key.lower():
            return f'<span class="badge" style="background: var(--success-color);"><i class="fas fa-dollar-sign"></i> {value:,.2f}</span>'
        else:
            return f'<strong style="color: var(--primary-color); font-size: 1.2em;">{value:,}</strong>'
    
    if isinstance(value, str):
        # Detectar URLs
        if value.startswith(('http://', 'https://')):
            return f'<a href="{value}" target="_blank" class="badge" style="background: var(--accent-color);"><i class="fas fa-external-link-alt"></i> Enlace</a>'
        
        # Detectar emails
        if '@' in value and '.' in value.split('@')[-1]:
            return f'<a href="mailto:{value}" class="badge" style="background: var(--success-color);"><i class="fas fa-envelope"></i> {value}</a>'
        
        # Texto largo
        if len(value) > 500:
            return f"""
            <div class="code-block">
                {value[:500]}...
                <br><small style="color: var(--text-secondary);"><i class="fas fa-ellipsis-h"></i> Texto truncado ({len(value)} caracteres total)</small>
            </div>
            """
        elif len(value) > 100:
            return f'<div class="code-block">{value}</div>'
        else:
            return f'<span>{value}</span>'
    
    if isinstance(value, dict):
        # Formateo especial para criterios de evaluación
        if ('evaluation' in context_key.lower() or 
            'criteria' in context_key.lower() or
            'weight_percentage' in value or 
            'max_points' in value or 
            'subcriteria' in value):
            return format_scoring_criteria(value, context_key)
        
        if len(value) > 20:  # Diccionario muy grande
            preview_items = list(value.items())[:5]
            preview_html = '<div class="json-content">'
            for k, v in preview_items:
                preview_html += f'<div><strong>{k}:</strong> {str(v)[:100]}{"..." if len(str(v)) > 100 else ""}</div>'
            preview_html += f'<div style="margin-top: 10px;"><i class="fas fa-ellipsis-h"></i> ... y {len(value)-5} elementos más</div>'
            preview_html += '</div>'
            return preview_html
        else:
            return f'<div class="json-content">{json.dumps(value, indent=2, ensure_ascii=False, default=str)}</div>'
    
    if isinstance(value, list):
        if len(value) > 20:  # Lista muy larga
            preview_items = value[:10]
            preview_html = '<div class="list-container">\n'
            for item in preview_items:
                # No truncar el texto, mostrarlo completo
                item_text = str(item) if len(str(item)) <= 300 else str(item)[:300] + "..."
                preview_html += f'                <div class="list-item">\n                    <i class="fas fa-arrow-right" style="margin-right: 8px; color: var(--primary-color);"></i>\n                    <span>{item_text}</span>\n                </div>\n'
            preview_html += f'                <div class="list-item" style="font-style: italic; color: var(--text-secondary);">\n                    <i class="fas fa-ellipsis-h"></i> ... y {len(value)-10} elementos más\n                </div>\n'
            preview_html += '            </div>'
            return preview_html
        elif len(value) > 0:
            items_html = '<div class="list-container">\n'
            for i, item in enumerate(value):
                # Formatear cada elemento de la lista sin truncar
                if isinstance(item, str):
                    item_text = item  # Mostrar texto completo
                else:
                    item_text = format_value_for_html_enhanced(item, f"{context_key}_item_{i}")
                items_html += f'                <div class="list-item">\n                    <i class="fas fa-arrow-right" style="margin-right: 8px; color: var(--primary-color);"></i>\n                    <span>{item_text}</span>\n                </div>\n'
            items_html += '            </div>'
            return items_html
        else:
            return '<span class="badge" style="background: var(--text-secondary);"><i class="fas fa-list"></i> Lista vacía</span>'
    
    return f'<span>{str(value)}</span>'

def create_table_paragraph(text: str, style):
    """
    Crear un párrafo para usar en celdas de tabla con manejo de saltos de línea
    
    Args:
        text: Texto a formatear
        style: Estilo base a usar
        
    Returns:
        Paragraph formateado para tabla
    """
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    
    # Crear estilo específico para celdas de tabla
    cell_style = ParagraphStyle(
        'TableCell',
        parent=style,
        fontSize=9,
        leading=12,  # Interlineado para texto multilínea
        textColor=style.textColor,
        fontName='Helvetica',
        alignment=0,  # Alineación izquierda
        spaceBefore=0,
        spaceAfter=0,
        leftIndent=0,
        rightIndent=0
    )
    
    # Reemplazar saltos de línea con <br/> para HTML
    formatted_text = text.replace('\n', '<br/>')
    
    return Paragraph(formatted_text, cell_style)

def format_list_for_pdf(value: list, content_style, max_items: int = 20) -> list:
    """
    Formatear una lista para PDF con manejo inteligente de texto largo
    
    Args:
        value: Lista a formatear
        content_style: Estilo a aplicar
        max_items: Número máximo de elementos a mostrar
        
    Returns:
        Lista de elementos formateados para ReportLab
    """
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    
    formatted_items = []
    items_to_show = min(len(value), max_items)
    
    # Crear estilo específico para listas con ancho controlado
    list_style = content_style.__class__(
        'ListContent',
        parent=content_style,
        fontSize=content_style.fontSize,
        leftIndent=15,  # Sangría para viñetas
        rightIndent=10,
        spaceBefore=2,
        spaceAfter=2,
        bulletIndent=5,
        bulletFontName='Symbol',
        wordWrap='LTR'
    )
    
    # Crear una tabla para controlar mejor el ancho del contenido
    table_data = []
    for i, item in enumerate(value[:items_to_show]):
        item_text = str(item)
        
        # Manejar texto muy largo de manera inteligente
        if len(item_text) > 300:
            # Buscar un punto de corte natural
            cut_point = item_text.rfind('. ', 0, 300)
            if cut_point == -1:
                cut_point = item_text.rfind(' ', 0, 300)
            if cut_point == -1:
                cut_point = 300
            item_text = item_text[:cut_point] + "..."
        
        # Agregar a la tabla con viñeta
        table_data.append(['•', item_text])
    
    # Crear tabla con formato de lista
    if table_data:
        list_table = Table(table_data, colWidths=[0.2*inch, 5.5*inch])
        list_table.setStyle(TableStyle([
            # Estilo de texto
            ('FONTNAME', (0, 0), (0, -1), 'Symbol'),  # Viñetas
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),  # Contenido
            ('FONTSIZE', (0, 0), (-1, -1), content_style.fontSize),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2563eb')),  # Color viñetas
            ('TEXTCOLOR', (1, 0), (1, -1), content_style.textColor),
            
            # Alineación y espaciado
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # Centrar viñetas
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            
            # Sin bordes para efecto de lista
            ('GRID', (0, 0), (-1, -1), 0, colors.white),
            
            # Permitir ajuste de texto
            ('WORDWRAP', (1, 0), (1, -1), 'LTR'),
            ('SPLITLONGWORDS', (1, 0), (1, -1), True),
        ]))
        formatted_items.append(list_table)
    
    # Agregar nota si hay más elementos
    if len(value) > max_items:
        remaining_count = len(value) - max_items
        note_style = content_style.__class__(
            'ListNote',
            parent=content_style,
            textColor=colors.HexColor('#9ca3af'),
            fontName='Helvetica-Oblique',
            fontSize=content_style.fontSize - 1,
            leftIndent=15,
            spaceBefore=5
        )
        note_text = f"... y {remaining_count} elemento{'s' if remaining_count > 1 else ''} más"
        formatted_items.append(Paragraph(note_text, note_style))
    
    return formatted_items

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
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch, cm
        from reportlab.lib import colors
        from reportlab.platypus.flowables import HRFlowable
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
        
        # Crear documento con márgenes más elegantes
        doc = SimpleDocTemplate(
            str(output_path), 
            pagesize=A4,
            topMargin=1*inch, 
            bottomMargin=1*inch,
            leftMargin=0.75*inch, 
            rightMargin=0.75*inch,
            title=f"Reporte de Análisis - {document_id}"
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # Colores personalizados
        primary_color = colors.HexColor('#2563eb')
        secondary_color = colors.HexColor('#1e40af')
        accent_color = colors.HexColor('#3b82f6')
        success_color = colors.HexColor('#10b981')
        warning_color = colors.HexColor('#f59e0b')
        light_bg = colors.HexColor('#f8fafc')
        
        # === PORTADA ELEGANTE ===
        # Título principal con estilo moderno
        title_style = ParagraphStyle(
            'ModernTitle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=primary_color,
            fontName='Helvetica-Bold',
            leading=34
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#64748b'),
            fontName='Helvetica',
            leading=20
        )
        
        # Espaciado superior
        story.append(Spacer(1, 0.5*inch))
        
        # Título principal
        story.append(Paragraph("REPORTE DE ANÁLISIS", title_style))
        story.append(Paragraph("DE LICITACIÓN", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Subtítulo
        story.append(Paragraph("Análisis Inteligente con IA Avanzada", subtitle_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Información del documento en tarjetas elegantes
        info_data = [
            ['📄 Documento ID:', document_id],
            ['🏷️ Tipo de Reporte:', report_type.title()],
            ['📅 Fecha de Generación:', datetime.now().strftime('%d de %B de %Y')],
            ['⏰ Hora:', datetime.now().strftime('%H:%M:%S')],
            ['🤖 Sistema:', 'draAIgon AI Platform'],
            ['🔍 Versión:', 'v2.0 Professional']
        ]
        
        info_table = Table(info_data, colWidths=[2.2*inch, 3.8*inch])
        info_table.setStyle(TableStyle([
            # Encabezados
            ('BACKGROUND', (0, 0), (0, -1), primary_color),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, -1), 12),
            
            # Contenido
            ('BACKGROUND', (1, 0), (1, -1), light_bg),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1e293b')),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (1, 0), (1, -1), 11),
            
            # Espaciado y bordes
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            
            # Bordes elegantes
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROUNDEDCORNERS', [5, 5, 5, 5]),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 1*inch))
        
        # Línea decorativa
        story.append(HRFlowable(width="100%", thickness=2, color=primary_color))
        story.append(Spacer(1, 0.3*inch))
        
        # Nota de confidencialidad
        confidential_style = ParagraphStyle(
            'Confidential',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#64748b'),
            fontName='Helvetica-Oblique',
            leading=12
        )
        
        story.append(Paragraph("🔒 DOCUMENTO CONFIDENCIAL", confidential_style))
        story.append(Paragraph("Este reporte contiene información privilegiada del análisis automatizado", confidential_style))
        story.append(PageBreak())
        
        # === ESTILOS PARA CONTENIDO ===
        section_style = ParagraphStyle(
            'ModernSectionHeader',
            parent=styles['Heading2'],
            fontSize=18,
            spaceAfter=20,
            spaceBefore=25,
            textColor=primary_color,
            fontName='Helvetica-Bold',
            borderWidth=0,
            borderPadding=0,
            leading=22
        )
        
        subsection_style = ParagraphStyle(
            'SubSection',
            parent=styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=secondary_color,
            fontName='Helvetica-Bold',
            leading=17
        )
        
        content_style = ParagraphStyle(
            'ModernContent',
            parent=styles['Normal'],
            fontSize=10,  # Reducir ligeramente el tamaño de fuente
            spaceAfter=8,
            textColor=colors.HexColor('#374151'),
            fontName='Helvetica',
            leading=13,  # Ajustar interlineado
            alignment=TA_JUSTIFY,
            leftIndent=0,
            rightIndent=0,
            wordWrap='LTR'  # Permitir ajuste de texto
        )
        
        # === PROCESAMIENTO DE SECCIONES ===
        for key, value in report_data.items():
            if key in ['error', 'status', 'html_content']:
                continue
                
            # Título de sección con icono
            section_title = f"📋 {key.replace('_', ' ').title()}"
            story.append(Paragraph(section_title, section_style))
            
            # Línea decorativa bajo el título
            story.append(HRFlowable(width="30%", thickness=1, color=accent_color))
            story.append(Spacer(1, 10))
            
            # Contenido de la sección
            if isinstance(value, dict):
                # Crear tabla para datos estructurados
                table_data = []
                for sub_key, sub_value in list(value.items())[:15]:  # Aumentar límite de elementos mostrados
                    # Formatear clave con manejo de nombres largos
                    key_title = sub_key.replace('_', ' ').title()
                    
                    # Si la clave es muy larga, dividirla inteligentemente
                    if len(key_title) > 25:
                        # Buscar puntos naturales de división en títulos largos
                        words = key_title.split()
                        if len(words) > 2:
                            # Dividir aproximadamente por la mitad
                            mid_point = len(words) // 2
                            first_line = ' '.join(words[:mid_point])
                            second_line = ' '.join(words[mid_point:])
                            formatted_key = f"🔹 {first_line}\n{second_line}"
                        else:
                            # Solo 1-2 palabras pero muy largas
                            if ' ' in key_title:
                                parts = key_title.split(' ', 1)
                                formatted_key = f"🔹 {parts[0]}\n{parts[1]}"
                            else:
                                formatted_key = f"🔹 {key_title}"
                    else:
                        formatted_key = f"🔹 {key_title}"
                    
                    # Formatear valor con manejo especial para listas
                    if isinstance(sub_value, bool):
                        formatted_value = "✅ Sí" if sub_value else "❌ No"
                    elif isinstance(sub_value, (int, float)):
                        if 'percentage' in sub_key.lower():
                            formatted_value = f"{sub_value:.1f}%"
                        elif 'amount' in sub_key.lower() or 'price' in sub_key.lower():
                            formatted_value = f"${sub_value:,.2f}"
                        else:
                            formatted_value = f"{sub_value:,}"
                    elif isinstance(sub_value, list):
                        # Manejo especial para listas en tablas - mantenerlas dentro del contenedor
                        if len(sub_value) <= 2:
                            # Listas muy cortas: una línea por elemento
                            formatted_items = []
                            for item in sub_value:
                                item_str = str(item)[:150]  # Limitar longitud por elemento
                                formatted_items.append(f"• {item_str}")
                            formatted_value = "\n".join(formatted_items)
                        elif len(sub_value) <= 5:
                            # Listas medianas: formato compacto
                            formatted_items = []
                            for item in sub_value:
                                item_str = str(item)[:120]  # Texto más corto para más elementos
                                formatted_items.append(f"• {item_str}")
                            formatted_value = "\n".join(formatted_items)
                        else:
                            # Listas largas: mostrar solo los primeros elementos más contador
                            formatted_items = []
                            for item in sub_value[:3]:
                                item_str = str(item)[:100]
                                formatted_items.append(f"• {item_str}")
                            formatted_items.append(f"• ... y {len(sub_value)-3} elementos más")
                            formatted_value = "\n".join(formatted_items)
                    elif isinstance(sub_value, str) and len(sub_value) > 300:
                        # Buscar un punto de corte más natural (final de palabra)
                        cut_point = sub_value.rfind(' ', 0, 300)
                        if cut_point == -1:
                            cut_point = 300
                        formatted_value = f"{sub_value[:cut_point]}..."
                    elif isinstance(sub_value, dict):
                        # Manejar diccionarios anidados de manera estructurada
                        if len(sub_value) <= 5:
                            # Diccionarios pequeños: formatear como lista de elementos
                            dict_items = []
                            for dict_key, dict_val in sub_value.items():
                                key_formatted = dict_key.replace('_', ' ').title()
                                if isinstance(dict_val, dict):
                                    # Diccionario anidado - procesarlo recursivamente
                                    nested_items = []
                                    for nested_key, nested_val in dict_val.items():
                                        nested_key_formatted = nested_key.replace('_', ' ').title()
                                        nested_items.append(f"  - {nested_key_formatted}: {nested_val}")
                                    dict_items.append(f"• {key_formatted}:\n" + "\n".join(nested_items))
                                elif isinstance(dict_val, (int, float)):
                                    dict_items.append(f"• {key_formatted}: {dict_val}")
                                elif isinstance(dict_val, bool):
                                    dict_items.append(f"• {key_formatted}: {'Sí' if dict_val else 'No'}")
                                else:
                                    dict_items.append(f"• {key_formatted}: {str(dict_val)}")
                            formatted_value = "\n".join(dict_items)
                        else:
                            # Diccionarios grandes: mostrar solo algunos elementos
                            dict_items = []
                            for i, (dict_key, dict_val) in enumerate(list(sub_value.items())[:3]):
                                key_formatted = dict_key.replace('_', ' ').title()
                                if isinstance(dict_val, (int, float)):
                                    dict_items.append(f"• {key_formatted}: {dict_val}")
                                else:
                                    dict_items.append(f"• {key_formatted}: {str(dict_val)[:50]}")
                            if len(sub_value) > 3:
                                dict_items.append(f"• ... y {len(sub_value)-3} elementos más")
                            formatted_value = "\n".join(dict_items)
                    elif isinstance(sub_value, str):
                        # Manejo especial para fechas, timestamps y strings largos
                        if ' al ' in sub_value:
                            # Formato de rango de fechas - dividir en dos líneas
                            parts = sub_value.split(' al ')
                            if len(parts) == 2:
                                formatted_value = f"{parts[0]}\nal {parts[1]}"
                            else:
                                formatted_value = sub_value
                        elif ':' in sub_value and len(sub_value) > 16:
                            # Timestamps con hora (formato: YYYY-MM-DD HH:MM:SS)
                            if ' ' in sub_value:
                                date_part, time_part = sub_value.split(' ', 1)
                                formatted_value = f"{date_part}\n{time_part}"
                            else:
                                formatted_value = sub_value
                        elif len(sub_value) > 18:
                            # Strings largos en general
                            if len(sub_value) > 40:
                                # String muy largo - buscar punto de división natural
                                cut_point = sub_value.rfind(' ', 20, 40)
                                if cut_point == -1:
                                    cut_point = sub_value.rfind('-', 20, 40)
                                if cut_point == -1:
                                    cut_point = 35
                                formatted_value = f"{sub_value[:cut_point]}\n{sub_value[cut_point:].strip()}"
                            else:
                                # String mediano - dividir aproximadamente por la mitad
                                mid_point = len(sub_value) // 2
                                cut_point = sub_value.rfind(' ', mid_point - 5, mid_point + 5)
                                if cut_point == -1:
                                    cut_point = sub_value.rfind('-', mid_point - 5, mid_point + 5)
                                if cut_point == -1:
                                    cut_point = mid_point
                                formatted_value = f"{sub_value[:cut_point]}\n{sub_value[cut_point:].strip()}"
                        elif len(sub_value) > 300:
                            # Strings muy largos - truncar con ellipsis
                            cut_point = sub_value.rfind(' ', 0, 300)
                            if cut_point == -1:
                                cut_point = 300
                            formatted_value = f"{sub_value[:cut_point]}..."
                        else:
                            formatted_value = sub_value
                    else:
                        formatted_value = str(sub_value)
                    
                    table_data.append([create_table_paragraph(formatted_key, content_style), create_table_paragraph(formatted_value, content_style)])
                
                if table_data:
                    # Ajustar anchos de columna - más espacio para etiquetas largas
                    content_table = Table(table_data, colWidths=[2.5*inch, 3.5*inch])
                    content_table.setStyle(TableStyle([
                        # Alternating row colors
                        ('BACKGROUND', (0, 0), (-1, 0), light_bg),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
                        
                        # Text formatting
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),  # Reducir tamaño de fuente para más contenido
                        ('TEXTCOLOR', (0, 0), (0, -1), primary_color),
                        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#374151')),
                        
                        # Alignment and padding - aumentar padding vertical para texto multilínea
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('TOPPADDING', (0, 0), (-1, -1), 10),  # Más padding superior
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),  # Más padding inferior
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                        
                        # Borders
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                        
                        # Permitir que el texto se ajuste en múltiples líneas en ambas columnas
                        ('WORDWRAP', (0, 0), (-1, -1), 'LTR'),
                        # Ajustar altura de filas automáticamente para contenido de múltiples líneas
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('SPLITLONGWORDS', (0, 0), (-1, -1), True),
                        # Permitir ajuste automático de altura de fila
                        ('ROWMINHEIGHT', (0, 0), (-1, -1), 25),  # Altura mínima mayor para texto multilínea
                    ]))
                    story.append(content_table)
                    
                if len(value) > 15:
                    story.append(Spacer(1, 8))
                    story.append(Paragraph(f"<i>... y {len(value)-15} elementos adicionales</i>", 
                                         ParagraphStyle('Italic', parent=content_style, 
                                                      textColor=colors.HexColor('#9ca3af'))))
                    
            elif isinstance(value, list):
                # Usar la nueva función especializada para listas
                formatted_list_items = format_list_for_pdf(value, content_style, max_items=20)
                for item in formatted_list_items:
                    story.append(item)
            else:
                # Contenido simple en párrafo
                content = str(value)
                if len(content) > 1000:
                    content = content[:1000] + "..."
                story.append(Paragraph(content, content_style))
            
            story.append(Spacer(1, 25))
        
        # === FOOTER PROFESIONAL ===
        story.append(Spacer(1, 50))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb')))
        story.append(Spacer(1, 20))
        
        footer_style = ParagraphStyle(
            'ModernFooter',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#6b7280'),
            fontName='Helvetica',
            leading=12
        )
        
        brand_style = ParagraphStyle(
            'Brand',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=primary_color,
            fontName='Helvetica-Bold',
            leading=15
        )
        
        story.append(Paragraph("🐉 <b>draAIgon AI Platform</b>", brand_style))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Sistema de Análisis Inteligente de Licitaciones", footer_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph("Este reporte contiene información confidencial del análisis automatizado", footer_style))
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}", footer_style))
        
        # Construir PDF con manejo de errores mejorado
        try:
            doc.build(story)
            logger.info(f"PDF generado exitosamente con ReportLab: {output_path}")
            return True
        except Exception as build_error:
            logger.error(f"Error durante la construcción del PDF: {build_error}")
            return False
        
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

def format_data_for_pdf(data, max_length=300):
    """
    Formatear datos complejos para mostrar en PDF de manera legible
    
    Args:
        data: Datos a formatear (dict, list, str, etc.)
        max_length: Longitud máxima del texto resultante
        
    Returns:
        String formateado para mostrar en PDF
    """
    if isinstance(data, dict):
        if not data:
            return "No hay datos disponibles"
        
        # Formatear diccionario como lista de elementos
        items = []
        for key, value in data.items():
            # Formatear la clave
            formatted_key = key.replace('_', ' ').title()
            
            # Formatear el valor
            if isinstance(value, (dict, list)):
                formatted_value = format_data_for_pdf(value, max_length=100)
            else:
                formatted_value = str(value)
            
            items.append(f"• {formatted_key}: {formatted_value}")
        
        result = '\n'.join(items)
        
    elif isinstance(data, list):
        if not data:
            return "No hay elementos"
        
        # Formatear lista como elementos con viñetas
        items = []
        for i, item in enumerate(data[:10]):  # Limitar a 10 elementos
            if isinstance(item, (dict, list)):
                formatted_item = format_data_for_pdf(item, max_length=100)
            else:
                formatted_item = str(item)
            items.append(f"• {formatted_item}")
        
        if len(data) > 10:
            items.append(f"• ... y {len(data) - 10} elementos más")
        
        result = '\n'.join(items)
        
    else:
        result = str(data)
    
    # Truncar si es muy largo
    if len(result) > max_length:
        result = result[:max_length] + "..."
    
    return result

def format_data_for_html(data):
    """
    Formatear datos complejos para mostrar en HTML de manera legible
    
    Args:
        data: Datos a formatear (dict, list, str, etc.)
        
    Returns:
        String HTML formateado
    """
    if isinstance(data, dict):
        if not data:
            return "<em>No hay datos disponibles</em>"
        
        items = []
        for key, value in data.items():
            formatted_key = key.replace('_', ' ').title()
            
            if isinstance(value, dict):
                # Sub-diccionario: mostrar como lista anidada
                sub_items = []
                for sub_key, sub_value in value.items():
                    sub_items.append(f"  ◦ {sub_key.replace('_', ' ').title()}: {sub_value}")
                formatted_value = "<br>" + "<br>".join(sub_items)
            elif isinstance(value, list):
                # Lista: mostrar primeros elementos
                if len(value) <= 5:
                    formatted_value = ", ".join([str(v) for v in value])
                else:
                    formatted_value = ", ".join([str(v) for v in value[:5]]) + f"... (+{len(value)-5} más)"
            else:
                formatted_value = str(value)
            
            items.append(f"<strong>{formatted_key}:</strong> {formatted_value}")
        
        return "<br>".join(items)
        
    elif isinstance(data, list):
        if not data:
            return "<em>No hay elementos</em>"
        
        items = []
        for item in data[:8]:  # Mostrar hasta 8 elementos
            if isinstance(item, (dict, list)):
                formatted_item = str(item)[:50] + ("..." if len(str(item)) > 50 else "")
            else:
                formatted_item = str(item)
            items.append(f"• {formatted_item}")
        
        if len(data) > 8:
            items.append(f"<em>... y {len(data) - 8} elementos más</em>")
        
        return "<br>".join(items)
        
    else:
        return str(data)

def generate_comparison_pdf_report(report_data: Dict[str, Any], comparison_id: str, output_path: Path) -> bool:
    """
    Función especializada para generar PDF de reportes de comparación
    
    Args:
        report_data: Datos del reporte de comparación
        comparison_id: ID de la comparación
        output_path: Ruta donde guardar el PDF
        
    Returns:
        True si se generó correctamente, False en caso contrario
    """
    try:
        # Generar HTML especializado para comparación
        html_content = generate_comparison_html(report_data, comparison_id)
        
        # Intentar con WeasyPrint primero
        if generate_pdf_with_weasyprint(html_content, output_path):
            return True
        
        # Fallback a ReportLab para comparaciones
        logger.info("Usando ReportLab como alternativa para generar PDF de comparación")
        return generate_comparison_pdf_with_reportlab(report_data, comparison_id, output_path)
        
    except Exception as e:
        logger.error(f"Error generando PDF de comparación: {e}")
        return False

def generate_comparison_html(report_data: Dict[str, Any], comparison_id: str) -> str:
    """
    Generar HTML especializado para reportes de comparación
    
    Args:
        report_data: Datos del reporte de comparación
        comparison_id: ID de la comparación
        
    Returns:
        Contenido HTML del reporte de comparación
    """
    # Extraer información específica de comparación
    documents_count = report_data.get('documents_included', 0)
    comparison_summary = report_data.get('comparison_summary', {})
    detailed_analysis = report_data.get('detailed_analysis', {})
    recommendations = report_data.get('recommendations', [])
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reporte de Comparación - {comparison_id}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f8fafc;
            }}
            .header {{
                text-align: center;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 20px;
                border-radius: 12px;
                margin-bottom: 30px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            }}
            .header h1 {{
                margin: 0 0 10px 0;
                font-size: 2.5em;
                font-weight: 300;
            }}
            .header .subtitle {{
                font-size: 1.2em;
                opacity: 0.9;
            }}
            .comparison-summary {{
                background: white;
                padding: 30px;
                border-radius: 12px;
                margin-bottom: 30px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }}
            .section {{
                background: white;
                margin-bottom: 25px;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }}
            .section-header {{
                background: #4f46e5;
                color: white;
                padding: 20px 30px;
                font-size: 1.3em;
                font-weight: 600;
            }}
            .section-content {{
                padding: 30px;
            }}
            .comparison-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            .comparison-table th,
            .comparison-table td {{
                padding: 15px;
                text-align: left;
                border-bottom: 1px solid #e5e7eb;
            }}
            .comparison-table th {{
                background: #f9fafb;
                font-weight: 600;
                color: #374151;
            }}
            .comparison-table tr:hover {{
                background: #f9fafb;
            }}
            .score-high {{ 
                color: #059669; 
                font-weight: bold; 
            }}
            .score-medium {{ 
                color: #d97706; 
                font-weight: bold; 
            }}
            .score-low {{ 
                color: #dc2626; 
                font-weight: bold; 
            }}
            .recommendation {{
                background: #f0f9ff;
                border-left: 4px solid #0ea5e9;
                padding: 20px;
                margin: 15px 0;
                border-radius: 0 8px 8px 0;
            }}
            .metric-card {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
                margin: 15px 0;
            }}
            .metric-value {{
                font-size: 2em;
                font-weight: bold;
                color: #4f46e5;
                margin-bottom: 5px;
            }}
            .metric-label {{
                color: #64748b;
                font-size: 0.9em;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Reporte de Comparación</h1>
            <div class="subtitle">Análisis Comparativo de Propuestas • {comparison_id}</div>
            <div style="margin-top: 15px; font-size: 1em;">
                {documents_count} documentos comparados • {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </div>
        </div>

        <div class="comparison-summary">
            <h2>📋 Resumen Ejecutivo</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0;">
                <div class="metric-card">
                    <div class="metric-value">{documents_count}</div>
                    <div class="metric-label">Documentos Analizados</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{len(comparison_summary)}</div>
                    <div class="metric-label">Criterios Evaluados</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{len(recommendations)}</div>
                    <div class="metric-label">Recomendaciones</div>
                </div>
            </div>
        </div>
    """
    
    # Agregar tabla de comparación si hay datos de resumen
    if comparison_summary:
        html_template += f"""
        <div class="section">
            <div class="section-header">🔍 Comparación Detallada</div>
            <div class="section-content">
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Criterio</th>
                            <th>Valores</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        for key, value in comparison_summary.items():
            formatted_value = format_data_for_html(value)
            
            html_template += f"""
                        <tr>
                            <td><strong>{key.replace('_', ' ').title()}</strong></td>
                            <td>{formatted_value}</td>
                        </tr>
            """
        
        html_template += """
                    </tbody>
                </table>
            </div>
        </div>
        """
    
    # Agregar análisis detallado
    if detailed_analysis:
        html_template += f"""
        <div class="section">
            <div class="section-header">📈 Análisis Detallado</div>
            <div class="section-content">
        """
        
        for section_name, section_data in detailed_analysis.items():
            html_template += f"""
                <h3>{section_name.replace('_', ' ').title()}</h3>
            """
            
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    formatted_value = format_data_for_html(value)
                    html_template += f"""
                        <div class="metric-card">
                            <strong>{key.replace('_', ' ').title()}:</strong><br>
                            {formatted_value}
                        </div>
                    """
            else:
                html_template += f"""
                    <div class="metric-card">{section_data}</div>
                """
        
        html_template += """
            </div>
        </div>
        """
    
    # Agregar recomendaciones
    if recommendations:
        html_template += f"""
        <div class="section">
            <div class="section-header">💡 Recomendaciones</div>
            <div class="section-content">
        """
        
        for i, recommendation in enumerate(recommendations, 1):
            html_template += f"""
                <div class="recommendation">
                    <strong>Recomendación {i}:</strong><br>
                    {recommendation}
                </div>
            """
        
        html_template += """
            </div>
        </div>
        """
    
    # Agregar pie de página
    html_template += f"""
        <div style="text-align: center; margin-top: 40px; padding: 20px; color: #64748b; border-top: 1px solid #e2e8f0;">
            <p>Reporte generado el {datetime.now().strftime('%d de %B de %Y a las %H:%M:%S')}</p>
            <p>Sistema de Análisis de Licitaciones • Versión 1.0</p>
        </div>
    </body>
    </html>
    """
    
    return html_template

def generate_comparison_pdf_with_reportlab(report_data: Dict[str, Any], comparison_id: str, output_path: Path) -> bool:
    """
    Generar PDF de comparación usando ReportLab como fallback
    
    Args:
        report_data: Datos del reporte de comparación
        comparison_id: ID de la comparación
        output_path: Ruta donde guardar el PDF
        
    Returns:
        True si se generó correctamente, False en caso contrario
    """
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        
        # Crear documento
        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#4f46e5'),
            alignment=1  # Centrado
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.HexColor('#64748b'),
            alignment=1  # Centrado
        )
        
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=12,
            textColor=colors.HexColor('#1e40af'),
            borderWidth=0,
            borderColor=colors.HexColor('#e2e8f0'),
            borderPadding=10
        )
        
        # Título principal
        story.append(Paragraph(f"📊 Reporte de Comparación", title_style))
        story.append(Paragraph(f"Análisis Comparativo • {comparison_id}", subtitle_style))
        story.append(Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", subtitle_style))
        story.append(Spacer(1, 30))
        
        # Resumen ejecutivo
        documents_count = report_data.get('documents_included', 0)
        story.append(Paragraph("📋 Resumen Ejecutivo", section_style))
        
        summary_data = [
            ['Métrica', 'Valor'],
            ['Documentos Analizados', str(documents_count)],
            ['Criterios Evaluados', str(len(report_data.get('comparison_summary', {})))],
            ['Recomendaciones', str(len(report_data.get('recommendations', [])))]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f9fafb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb'))
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Comparación detallada
        comparison_summary = report_data.get('comparison_summary', {})
        if comparison_summary:
            story.append(Paragraph("🔍 Comparación Detallada", section_style))
            
            comparison_data = [['Criterio', 'Detalles']]
            for key, value in comparison_summary.items():
                formatted_value = format_data_for_pdf(value, max_length=250)
                comparison_data.append([
                    key.replace('_', ' ').title(),
                    formatted_value
                ])
            
            comparison_table = Table(comparison_data, colWidths=[2*inch, 4*inch])
            comparison_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f9fafb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('WORDWRAP', (0, 0), (-1, -1), 'LTR')
            ]))
            story.append(comparison_table)
            story.append(Spacer(1, 20))
        
        # Análisis detallado
        detailed_analysis = report_data.get('detailed_analysis', {})
        if detailed_analysis:
            story.append(Paragraph("📈 Análisis Detallado", section_style))
            
            for section_name, section_data in detailed_analysis.items():
                story.append(Paragraph(section_name.replace('_', ' ').title(), 
                                     ParagraphStyle('SubSection', parent=styles['Heading3'], 
                                                  fontSize=14, spaceBefore=15, spaceAfter=10)))
                
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        story.append(Paragraph(f"<b>{key.replace('_', ' ').title()}:</b>", styles['Normal']))
                        formatted_value = format_data_for_pdf(value, max_length=400)
                        story.append(Paragraph(formatted_value, styles['Normal']))
                        story.append(Spacer(1, 10))
                else:
                    story.append(Paragraph(str(section_data)[:500] + ("..." if len(str(section_data)) > 500 else ""), 
                                         styles['Normal']))
                
                story.append(Spacer(1, 15))
        
        # Recomendaciones
        recommendations = report_data.get('recommendations', [])
        if recommendations:
            story.append(Paragraph("💡 Recomendaciones", section_style))
            
            for i, recommendation in enumerate(recommendations, 1):
                story.append(Paragraph(f"<b>Recomendación {i}:</b>", styles['Normal']))
                story.append(Paragraph(str(recommendation), styles['Normal']))
                story.append(Spacer(1, 12))
        
        # Generar PDF
        doc.build(story)
        logger.info(f"PDF de comparación generado exitosamente: {output_path}")
        return True
        
    except ImportError:
        logger.error("ReportLab no está instalado. No se puede generar PDF de comparación.")
        return False
    except Exception as e:
        logger.error(f"Error generando PDF de comparación con ReportLab: {e}")
        return False
