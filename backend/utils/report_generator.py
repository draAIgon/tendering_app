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
            }}
            
            .list-item {{
                padding: 12px 16px;
                border-bottom: 1px solid var(--border-color);
                transition: background-color 0.3s ease;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .list-item:last-child {{
                border-bottom: none;
            }}
            
            .list-item:hover {{
                background: var(--light-bg);
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
            preview_html = '<div class="list-container">'
            for item in preview_items:
                preview_html += f'<div class="list-item"><i class="fas fa-arrow-right"></i> {str(item)[:150]}{"..." if len(str(item)) > 150 else ""}</div>'
            preview_html += f'<div class="list-item" style="font-style: italic; color: var(--text-secondary);"><i class="fas fa-ellipsis-h"></i> ... y {len(value)-10} elementos más</div>'
            preview_html += '</div>'
            return preview_html
        elif len(value) > 0:
            items_html = '<div class="list-container">'
            for item in value:
                items_html += f'<div class="list-item"><i class="fas fa-arrow-right"></i> {format_value_for_html_enhanced(item, context_key)}</div>'
            items_html += '</div>'
            return items_html
        else:
            return '<span class="badge" style="background: var(--text-secondary);"><i class="fas fa-list"></i> Lista vacía</span>'
    
    return f'<span>{str(value)}</span>'

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
            fontSize=11,
            spaceAfter=8,
            textColor=colors.HexColor('#374151'),
            fontName='Helvetica',
            leading=14,
            alignment=TA_JUSTIFY
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
                for sub_key, sub_value in list(value.items())[:10]:  # Limitar elementos
                    # Formatear clave
                    formatted_key = f"🔹 {sub_key.replace('_', ' ').title()}"
                    
                    # Formatear valor
                    if isinstance(sub_value, bool):
                        formatted_value = "✅ Sí" if sub_value else "❌ No"
                    elif isinstance(sub_value, (int, float)):
                        if 'percentage' in sub_key.lower():
                            formatted_value = f"{sub_value:.1f}%"
                        elif 'amount' in sub_key.lower() or 'price' in sub_key.lower():
                            formatted_value = f"${sub_value:,.2f}"
                        else:
                            formatted_value = f"{sub_value:,}"
                    elif isinstance(sub_value, str) and len(sub_value) > 100:
                        formatted_value = f"{sub_value[:100]}..."
                    else:
                        formatted_value = str(sub_value)
                    
                    table_data.append([formatted_key, formatted_value])
                
                if table_data:
                    content_table = Table(table_data, colWidths=[2.5*inch, 3.5*inch])
                    content_table.setStyle(TableStyle([
                        # Alternating row colors
                        ('BACKGROUND', (0, 0), (-1, 0), light_bg),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, light_bg]),
                        
                        # Text formatting
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('TEXTCOLOR', (0, 0), (0, -1), primary_color),
                        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#374151')),
                        
                        # Alignment and padding
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('LEFTPADDING', (0, 0), (-1, -1), 10),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                        
                        # Borders
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                    ]))
                    story.append(content_table)
                    
                if len(value) > 10:
                    story.append(Spacer(1, 8))
                    story.append(Paragraph(f"<i>... y {len(value)-10} elementos adicionales</i>", 
                                         ParagraphStyle('Italic', parent=content_style, 
                                                      textColor=colors.HexColor('#9ca3af'))))
                    
            elif isinstance(value, list):
                # Mostrar lista con viñetas elegantes
                list_items = []
                for i, item in enumerate(value[:12]):  # Limitar elementos
                    item_text = str(item)
                    if len(item_text) > 200:
                        item_text = item_text[:200] + "..."
                    list_items.append(f"• {item_text}")
                
                if list_items:
                    for item in list_items:
                        story.append(Paragraph(item, content_style))
                        story.append(Spacer(1, 4))
                        
                if len(value) > 12:
                    story.append(Paragraph(f"<i>... y {len(value)-12} elementos más</i>", 
                                         ParagraphStyle('Italic', parent=content_style, 
                                                      textColor=colors.HexColor('#9ca3af'))))
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
