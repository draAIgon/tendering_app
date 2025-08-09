import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import uuid
from collections import defaultdict
import base64
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReportGenerationAgent:
    """
    Agente especializado en la generación de reportes comprehensivos
    para procesos de licitación. Combina datos de múltiples agentes
    para crear reportes ejecutivos, técnicos y operacionales.
    """
    
    # Tipos de reportes soportados
    REPORT_TYPES = {
        'EXECUTIVE_SUMMARY': {
            'name': 'Resumen Ejecutivo',
            'description': 'Reporte de alto nivel para toma de decisiones',
            'sections': ['overview', 'key_findings', 'recommendations', 'risk_summary', 'financial_impact']
        },
        'TECHNICAL_ANALYSIS': {
            'name': 'Análisis Técnico',
            'description': 'Reporte detallado de aspectos técnicos',
            'sections': ['technical_specs', 'compliance_analysis', 'capability_assessment', 'integration_requirements']
        },
        'RISK_ASSESSMENT': {
            'name': 'Evaluación de Riesgos',
            'description': 'Análisis completo de riesgos del proyecto',
            'sections': ['risk_identification', 'impact_analysis', 'mitigation_strategies', 'monitoring_plan']
        },
        'PROPOSAL_COMPARISON': {
            'name': 'Comparación de Propuestas',
            'description': 'Análisis comparativo de múltiples propuestas',
            'sections': ['scoring_matrix', 'technical_comparison', 'economic_comparison', 'risk_comparison']
        },
        'COMPLIANCE_REPORT': {
            'name': 'Reporte de Cumplimiento',
            'description': 'Evaluación de cumplimiento normativo y contractual',
            'sections': ['regulatory_compliance', 'document_completeness', 'legal_requirements', 'recommendations']
        },
        'COMPREHENSIVE': {
            'name': 'Reporte Integral',
            'description': 'Reporte completo con todos los análisis',
            'sections': ['executive_summary', 'technical_analysis', 'risk_assessment', 'compliance_review', 'financial_analysis', 'recommendations']
        }
    }
    
    def __init__(self, output_directory: Optional[Path] = None):
        self.output_directory = output_directory or Path("./reports")
        self.output_directory.mkdir(parents=True, exist_ok=True)
        self.report_data = {}
        self.generated_reports = {}
        
    def collect_analysis_data(self, 
                            classification_results: Optional[Dict] = None,
                            validation_results: Optional[Dict] = None,
                            risk_analysis: Optional[Dict] = None,
                            comparison_results: Optional[Dict] = None,
                            extraction_results: Optional[Dict] = None) -> str:
        """
        Recopila datos de análisis de diferentes agentes
        
        Args:
            classification_results: Resultados del DocumentClassificationAgent
            validation_results: Resultados del ComplianceValidationAgent
            risk_analysis: Resultados del RiskAnalyzerAgent
            comparison_results: Resultados del ProposalComparisonAgent
            extraction_results: Resultados del DocumentExtractionAgent
            
        Returns:
            ID único para el conjunto de datos recopilados
        """
        
        data_id = str(uuid.uuid4())
        
        self.report_data[data_id] = {
            'collection_timestamp': datetime.now().isoformat(),
            'classification': classification_results or {},
            'validation': validation_results or {},
            'risk_analysis': risk_analysis or {},
            'comparison': comparison_results or {},
            'extraction': extraction_results or {},
            'metadata': {
                'data_sources': [
                    source for source, data in [
                        ('classification', classification_results),
                        ('validation', validation_results),
                        ('risk_analysis', risk_analysis),
                        ('comparison', comparison_results),
                        ('extraction', extraction_results)
                    ] if data
                ]
            }
        }
        
        logger.info(f"Datos recopilados con ID: {data_id}")
        return data_id
    
    def generate_executive_summary(self, data_id: str) -> Dict[str, Any]:
        """Genera un resumen ejecutivo de alto nivel"""
        
        if data_id not in self.report_data:
            raise ValueError(f"No se encontraron datos para ID: {data_id}")
        
        data = self.report_data[data_id]
        
        # Extraer información clave
        overall_score = 0
        key_findings = []
        critical_issues = []
        recommendations = []
        
        # Análisis de clasificación
        if data['classification']:
            sections = data['classification'].get('sections', {})
            key_findings.append(f"Documento clasificado en {len(sections)} secciones principales")
            
            if data['classification'].get('confidence_scores'):
                avg_confidence = sum(data['classification']['confidence_scores'].values()) / len(data['classification']['confidence_scores'])
                key_findings.append(f"Confianza promedio de clasificación: {avg_confidence:.1f}%")
        
        # Análisis de validación
        if data['validation']:
            val_score = data['validation'].get('overall_score', 0)
            overall_score = max(overall_score, val_score)
            
            if val_score < 70:
                critical_issues.append(f"Score de validación bajo: {val_score:.1f}%")
            
            total_issues = data['validation'].get('summary', {}).get('total_issues', 0)
            if total_issues > 0:
                key_findings.append(f"Se identificaron {total_issues} issues de cumplimiento")
        
        # Análisis de riesgos
        if data['risk_analysis']:
            risk_score = data['risk_analysis'].get('overall_assessment', {}).get('total_risk_score', 0)
            risk_level = data['risk_analysis'].get('overall_assessment', {}).get('risk_level', 'UNKNOWN')
            
            key_findings.append(f"Nivel de riesgo: {risk_level} ({risk_score:.1f}%)")
            
            critical_risks = data['risk_analysis'].get('critical_risks', [])
            if critical_risks:
                critical_issues.append(f"{len(critical_risks)} riesgos críticos identificados")
            
            # Agregar recomendaciones de riesgo
            risk_recommendations = data['risk_analysis'].get('mitigation_recommendations', [])
            recommendations.extend([rec['recommendation'] for rec in risk_recommendations[:3]])
        
        # Análisis de comparación
        if data['comparison']:
            total_proposals = data['comparison'].get('total_proposals', 0)
            if total_proposals > 0:
                key_findings.append(f"Comparación realizada entre {total_proposals} propuestas")
                
                winner = data['comparison'].get('summary_statistics', {}).get('winner')
                if winner:
                    key_findings.append(f"Propuesta recomendada: {winner}")
        
        # Determinar estado general del proyecto
        if critical_issues:
            project_status = "REQUIERE_ATENCION"
            status_color = "orange"
        elif overall_score >= 80:
            project_status = "APROBADO"
            status_color = "green"
        elif overall_score >= 60:
            project_status = "APROBADO_CON_OBSERVACIONES"
            status_color = "yellow"
        else:
            project_status = "REQUIERE_REVISION"
            status_color = "red"
        
        executive_summary = {
            'report_type': 'EXECUTIVE_SUMMARY',
            'generation_timestamp': datetime.now().isoformat(),
            'project_status': project_status,
            'status_color': status_color,
            'overall_score': overall_score,
            'key_findings': key_findings,
            'critical_issues': critical_issues,
            'top_recommendations': recommendations[:5],
            'next_steps': self._generate_next_steps(project_status, critical_issues),
            'summary_metrics': {
                'total_documents_analyzed': len([d for d in data.values() if isinstance(d, dict) and d]),
                'analysis_completeness': self._calculate_analysis_completeness(data),
                'confidence_level': self._calculate_overall_confidence(data)
            }
        }
        
        return executive_summary
    
    def generate_technical_analysis(self, data_id: str) -> Dict[str, Any]:
        """Genera análisis técnico detallado"""
        
        if data_id not in self.report_data:
            raise ValueError(f"No se encontraron datos para ID: {data_id}")
        
        data = self.report_data[data_id]
        
        technical_analysis = {
            'report_type': 'TECHNICAL_ANALYSIS',
            'generation_timestamp': datetime.now().isoformat(),
            'technical_specifications': {},
            'compliance_analysis': {},
            'capability_assessment': {},
            'integration_requirements': {}
        }
        
        # Especificaciones técnicas desde clasificación
        if data['classification']:
            tech_sections = {}
            for section, info in data['classification'].get('sections', {}).items():
                if 'TECNIC' in section.upper() or 'ESPECIFIC' in section.upper():
                    tech_sections[section] = {
                        'fragments': info.get('document_count', 0),
                        'content_length': info.get('total_characters', 0),
                        'confidence': data['classification'].get('confidence_scores', {}).get(section, 0)
                    }
            technical_analysis['technical_specifications'] = tech_sections
        
        # Análisis de cumplimiento técnico desde validación
        if data['validation']:
            tech_validation = {}
            for category, results in data['validation'].get('compliance_validation', {}).get('category_results', {}).items():
                if 'TECNIC' in category:
                    tech_validation[category] = {
                        'compliance_percentage': results.get('compliance_percentage', 0),
                        'rules_passed': results.get('rules_passed', 0),
                        'missing_rules': results.get('missing_rules', [])[:5]  # Top 5
                    }
            technical_analysis['compliance_analysis'] = tech_validation
        
        # Evaluación de capacidades
        if data['risk_analysis']:
            tech_risks = {}
            tech_risk_data = data['risk_analysis'].get('category_risks', {}).get('TECHNICAL_RISKS', {})
            if tech_risk_data and 'error' not in tech_risk_data:
                tech_risks = {
                    'risk_score': tech_risk_data.get('risk_score', 0),
                    'risk_level': tech_risk_data.get('risk_level', 'UNKNOWN'),
                    'indicators_detected': tech_risk_data.get('indicators_detected', 0),
                    'critical_indicators': [
                        ind for ind in tech_risk_data.get('detected_indicators', [])
                        if ind.get('severity') in ['HIGH', 'VERY_HIGH']
                    ]
                }
            technical_analysis['capability_assessment'] = tech_risks
        
        # Requisitos de integración
        integration_requirements = []
        if data['classification']:
            for section, info in data['classification'].get('sections', {}).items():
                if any(keyword in section.upper() for keyword in ['INTEGRA', 'COMPAT', 'INTERFACE']):
                    integration_requirements.append({
                        'section': section,
                        'complexity': 'HIGH' if info.get('total_characters', 0) > 2000 else 'MEDIUM'
                    })
        
        technical_analysis['integration_requirements'] = integration_requirements
        
        return technical_analysis
    
    def generate_risk_assessment_report(self, data_id: str) -> Dict[str, Any]:
        """Genera reporte especializado en análisis de riesgos"""
        
        if data_id not in self.report_data:
            raise ValueError(f"No se encontraron datos para ID: {data_id}")
        
        data = self.report_data[data_id]
        
        if not data['risk_analysis']:
            raise ValueError("No hay datos de análisis de riesgos disponibles")
        
        risk_data = data['risk_analysis']
        
        risk_report = {
            'report_type': 'RISK_ASSESSMENT',
            'generation_timestamp': datetime.now().isoformat(),
            'executive_summary': {
                'overall_risk_score': risk_data.get('overall_assessment', {}).get('total_risk_score', 0),
                'risk_level': risk_data.get('overall_assessment', {}).get('risk_level', 'UNKNOWN'),
                'critical_risks_count': len(risk_data.get('critical_risks', [])),
                'assessment_summary': risk_data.get('overall_assessment', {}).get('assessment_summary', '')
            },
            'risk_breakdown': [],
            'critical_risks': risk_data.get('critical_risks', []),
            'mitigation_plan': {
                'immediate_actions': [],
                'short_term_actions': [],
                'long_term_monitoring': []
            },
            'risk_matrix': risk_data.get('risk_matrix', {}),
            'monitoring_recommendations': []
        }
        
        # Desglose detallado por categorías
        for category, cat_data in risk_data.get('category_risks', {}).items():
            if 'error' not in cat_data:
                risk_breakdown_item = {
                    'category': category.replace('_', ' ').title(),
                    'risk_score': cat_data.get('risk_score', 0),
                    'risk_level': cat_data.get('risk_level', 'UNKNOWN'),
                    'weight': cat_data.get('weight', 0) * 100,
                    'indicators_count': cat_data.get('indicators_detected', 0),
                    'top_indicators': [
                        {
                            'pattern': ind.get('pattern', ''),
                            'severity': ind.get('severity', 'UNKNOWN'),
                            'occurrences': ind.get('count', 0)
                        }
                        for ind in cat_data.get('detected_indicators', [])[:3]
                    ]
                }
                risk_report['risk_breakdown'].append(risk_breakdown_item)
        
        # Plan de mitigación estructurado
        recommendations = risk_data.get('mitigation_recommendations', [])
        for rec in recommendations:
            priority = rec.get('priority', 'MEDIUM')
            if priority == 'CRITICAL':
                risk_report['mitigation_plan']['immediate_actions'].append(rec)
            elif priority == 'HIGH':
                risk_report['mitigation_plan']['short_term_actions'].append(rec)
            else:
                risk_report['mitigation_plan']['long_term_monitoring'].append(rec)
        
        # Recomendaciones de monitoreo
        risk_report['monitoring_recommendations'] = [
            'Implementar dashboard de monitoreo de riesgos en tiempo real',
            'Establecer revisiones periódicas de evaluación de riesgos',
            'Definir KPIs específicos para cada categoría de riesgo',
            'Crear planes de contingencia para riesgos críticos'
        ]
        
        return risk_report
    
    def generate_proposal_comparison_report(self, data_id: str) -> Dict[str, Any]:
        """Genera reporte de comparación de propuestas"""
        
        if data_id not in self.report_data:
            raise ValueError(f"No se encontraron datos para ID: {data_id}")
        
        data = self.report_data[data_id]
        
        if not data['comparison']:
            raise ValueError("No hay datos de comparación de propuestas disponibles")
        
        comparison_data = data['comparison']
        
        comparison_report = {
            'report_type': 'PROPOSAL_COMPARISON',
            'generation_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_proposals': comparison_data.get('total_proposals', 0),
                'winner': comparison_data.get('summary_statistics', {}).get('winner'),
                'average_score': comparison_data.get('summary_statistics', {}).get('average_score', 0),
                'score_spread': comparison_data.get('summary_statistics', {}).get('score_spread', 0)
            },
            'ranking': comparison_data.get('ranking', []),
            'detailed_analysis': [],
            'scoring_methodology': {
                'technical_weight': 40,
                'economic_weight': 35,
                'compliance_weight': 25
            },
            'recommendations': []
        }
        
        # Análisis detallado por propuesta
        for proposal_id, proposal_data in comparison_data.get('proposals', {}).items():
            if 'error' not in proposal_data:
                detailed_item = {
                    'proposal_id': proposal_id,
                    'company': proposal_data.get('metadata', {}).get('company', 'N/A'),
                    'total_score': proposal_data.get('scores', {}).get('total_score', 0),
                    'technical_score': proposal_data.get('scores', {}).get('technical_weighted', 0),
                    'economic_score': proposal_data.get('scores', {}).get('economic', 0),
                    'compliance_score': proposal_data.get('scores', {}).get('compliance_weighted', 0),
                    'strengths': proposal_data.get('strengths', []),
                    'weaknesses': proposal_data.get('weaknesses', []),
                    'price': proposal_data.get('scores', {}).get('economic_data', {}).get('total_price')
                }
                comparison_report['detailed_analysis'].append(detailed_item)
        
        # Generar recomendaciones
        if comparison_report['ranking']:
            top_proposal = comparison_report['ranking'][0]
            comparison_report['recommendations'].append(
                f"Se recomienda seleccionar la propuesta {top_proposal['proposal_id']} "
                f"con un score de {top_proposal['total_score']:.1f}"
            )
            
            if len(comparison_report['ranking']) > 1:
                second_proposal = comparison_report['ranking'][1]
                score_diff = top_proposal['total_score'] - second_proposal['total_score']
                
                if score_diff < 10:
                    comparison_report['recommendations'].append(
                        f"Diferencia mínima con segunda opción ({score_diff:.1f} puntos). "
                        "Considerar negociación."
                    )
        
        return comparison_report
    
    def generate_compliance_report(self, data_id: str) -> Dict[str, Any]:
        """Genera reporte de cumplimiento normativo"""
        
        if data_id not in self.report_data:
            raise ValueError(f"No se encontraron datos para ID: {data_id}")
        
        data = self.report_data[data_id]
        
        if not data['validation']:
            raise ValueError("No hay datos de validación disponibles")
        
        validation_data = data['validation']
        
        compliance_report = {
            'report_type': 'COMPLIANCE_REPORT',
            'generation_timestamp': datetime.now().isoformat(),
            'overall_compliance': {
                'score': validation_data.get('overall_score', 0),
                'level': validation_data.get('validation_level', 'UNKNOWN'),
                'total_issues': validation_data.get('summary', {}).get('total_issues', 0),
                'critical_issues': validation_data.get('summary', {}).get('critical_issues', 0)
            },
            'structural_compliance': validation_data.get('structural_validation', {}),
            'regulatory_compliance': validation_data.get('compliance_validation', {}),
            'document_completeness': [],
            'legal_requirements': [],
            'recommendations': validation_data.get('recommendations', [])
        }
        
        # Análisis de completitud documental
        structural = validation_data.get('structural_validation', {})
        if structural:
            compliance_report['document_completeness'] = {
                'completion_percentage': structural.get('completion_percentage', 0),
                'sections_found': structural.get('sections_found', 0),
                'sections_missing': structural.get('sections_missing', 0),
                'missing_sections': structural.get('missing_sections', []),
                'structural_issues': structural.get('structural_issues', [])
            }
        
        # Análisis de requisitos legales
        compliance_validation = validation_data.get('compliance_validation', {})
        if compliance_validation:
            for category, results in compliance_validation.get('category_results', {}).items():
                if 'LEGAL' in category.upper():
                    compliance_report['legal_requirements'].append({
                        'category': category.replace('_', ' ').title(),
                        'compliance_percentage': results.get('compliance_percentage', 0),
                        'rules_passed': results.get('rules_passed', 0),
                        'missing_rules': results.get('missing_rules', [])
                    })
        
        return compliance_report
    
    def generate_comprehensive_report(self, data_id: str, 
                                    include_charts: bool = False) -> Dict[str, Any]:
        """
        Genera un reporte integral que combina todos los análisis disponibles
        
        Args:
            data_id: ID de los datos recopilados
            include_charts: Si incluir datos para gráficos
            
        Returns:
            Reporte integral completo
        """
        
        if data_id not in self.report_data:
            raise ValueError(f"No se encontraron datos para ID: {data_id}")
        
        logger.info(f"Generando reporte integral para {data_id}")
        
        comprehensive_report = {
            'report_type': 'COMPREHENSIVE',
            'generation_timestamp': datetime.now().isoformat(),
            'report_id': str(uuid.uuid4()),
            'data_id': data_id,
            'executive_summary': {},
            'technical_analysis': {},
            'risk_assessment': {},
            'compliance_review': {},
            'proposal_comparison': {},
            'financial_analysis': {},
            'recommendations': {
                'immediate_actions': [],
                'strategic_recommendations': [],
                'long_term_considerations': []
            },
            'appendices': {},
            'metadata': {
                'analysis_completeness': self._calculate_analysis_completeness(self.report_data[data_id]),
                'data_sources': self.report_data[data_id]['metadata']['data_sources'],
                'generation_time': datetime.now().isoformat()
            }
        }
        
        # Generar cada sección si hay datos disponibles
        try:
            comprehensive_report['executive_summary'] = self.generate_executive_summary(data_id)
        except Exception as e:
            logger.warning(f"No se pudo generar resumen ejecutivo: {e}")
        
        try:
            comprehensive_report['technical_analysis'] = self.generate_technical_analysis(data_id)
        except Exception as e:
            logger.warning(f"No se pudo generar análisis técnico: {e}")
        
        try:
            comprehensive_report['risk_assessment'] = self.generate_risk_assessment_report(data_id)
        except Exception as e:
            logger.warning(f"No se pudo generar análisis de riesgos: {e}")
        
        try:
            comprehensive_report['compliance_review'] = self.generate_compliance_report(data_id)
        except Exception as e:
            logger.warning(f"No se pudo generar reporte de cumplimiento: {e}")
        
        try:
            comprehensive_report['proposal_comparison'] = self.generate_proposal_comparison_report(data_id)
        except Exception as e:
            logger.warning(f"No se pudo generar comparación de propuestas: {e}")
        
        # Análisis financiero consolidado
        comprehensive_report['financial_analysis'] = self._generate_financial_analysis(data_id)
        
        # Consolidar recomendaciones
        comprehensive_report['recommendations'] = self._consolidate_recommendations(comprehensive_report)
        
        # Generar datos para gráficos si se solicita
        if include_charts:
            comprehensive_report['chart_data'] = self._generate_chart_data(comprehensive_report)
        
        return comprehensive_report
    
    def export_report(self, report_data: Dict[str, Any], 
                     output_format: str = "json",
                     filename: Optional[str] = None) -> Path:
        """
        Exporta un reporte en el formato especificado
        
        Args:
            report_data: Datos del reporte a exportar
            output_format: Formato de salida (json, html, pdf)
            filename: Nombre personalizado del archivo
            
        Returns:
            Ruta del archivo generado
        """
        
        report_type = report_data.get('report_type', 'UNKNOWN')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not filename:
            filename = f"{report_type}_{timestamp}"
        
        if output_format.lower() == "json":
            output_path = self.output_directory / f"{filename}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        elif output_format.lower() == "html":
            output_path = self.output_directory / f"{filename}.html"
            html_content = self._generate_html_report(report_data)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        else:
            raise ValueError(f"Formato no soportado: {output_format}")
        
        logger.info(f"Reporte exportado a: {output_path}")
        return output_path
    
    def _calculate_analysis_completeness(self, data: Dict) -> float:
        """Calcula qué tan completo está el análisis"""
        total_sources = 5  # classification, validation, risk, comparison, extraction
        available_sources = len([d for d in data.values() if isinstance(d, dict) and d])
        return (available_sources / total_sources) * 100
    
    def _calculate_overall_confidence(self, data: Dict) -> float:
        """Calcula el nivel de confianza general del análisis"""
        confidence_scores = []
        
        # Confianza de clasificación
        if data['classification'] and data['classification'].get('confidence_scores'):
            avg_conf = sum(data['classification']['confidence_scores'].values()) / len(data['classification']['confidence_scores'])
            confidence_scores.append(avg_conf)
        
        # Confianza de validación
        if data['validation']:
            val_score = data['validation'].get('overall_score', 0)
            confidence_scores.append(val_score)
        
        return sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    def _generate_next_steps(self, project_status: str, critical_issues: List[str]) -> List[str]:
        """Genera pasos siguientes basados en el estado del proyecto"""
        next_steps = []
        
        if project_status == "APROBADO":
            next_steps = [
                "Proceder con la adjudicación del contrato",
                "Definir cronograma detallado de implementación",
                "Establecer métricas de seguimiento y control"
            ]
        elif project_status == "APROBADO_CON_OBSERVACIONES":
            next_steps = [
                "Abordar las observaciones identificadas",
                "Solicitar aclaraciones o documentación adicional",
                "Proceder con adjudicación condicional"
            ]
        elif project_status == "REQUIERE_REVISION":
            next_steps = [
                "Realizar revisión detallada de los issues identificados",
                "Solicitar modificaciones a la propuesta",
                "Considerar negociación con el oferente"
            ]
        else:  # REQUIERE_ATENCION
            next_steps = [
                "Atender inmediatamente los issues críticos",
                "Evaluar viabilidad del proyecto",
                "Considerar rechazo de la propuesta"
            ]
        
        if critical_issues:
            next_steps.insert(0, "PRIORIDAD: Resolver issues críticos identificados")
        
        return next_steps
    
    def _generate_financial_analysis(self, data_id: str) -> Dict[str, Any]:
        """Genera análisis financiero consolidado"""
        data = self.report_data[data_id]
        
        financial_analysis = {
            'budget_analysis': {},
            'cost_breakdown': {},
            'financial_risks': {},
            'roi_projection': {}
        }
        
        # Datos de comparación de propuestas
        if data['comparison']:
            proposals = data['comparison'].get('proposals', {})
            prices = []
            for prop_id, prop_data in proposals.items():
                if 'error' not in prop_data:
                    price = prop_data.get('scores', {}).get('economic_data', {}).get('total_price')
                    if price:
                        prices.append({'proposal': prop_id, 'price': price})
            
            if prices:
                financial_analysis['budget_analysis'] = {
                    'price_range': {
                        'min': min(p['price'] for p in prices),
                        'max': max(p['price'] for p in prices),
                        'average': sum(p['price'] for p in prices) / len(prices)
                    },
                    'proposals_analyzed': len(prices)
                }
        
        # Riesgos financieros del análisis de riesgos
        if data['risk_analysis']:
            economic_risks = data['risk_analysis'].get('category_risks', {}).get('ECONOMIC_RISKS', {})
            if economic_risks and 'error' not in economic_risks:
                financial_analysis['financial_risks'] = {
                    'risk_score': economic_risks.get('risk_score', 0),
                    'risk_level': economic_risks.get('risk_level', 'UNKNOWN'),
                    'key_indicators': [
                        ind.get('pattern', '') for ind in economic_risks.get('detected_indicators', [])[:3]
                    ]
                }
        
        return financial_analysis
    
    def _consolidate_recommendations(self, comprehensive_report: Dict) -> Dict[str, List[str]]:
        """Consolida recomendaciones de todos los análisis"""
        
        immediate_actions = []
        strategic_recommendations = []
        long_term_considerations = []
        
        # Recomendaciones del resumen ejecutivo
        exec_recs = comprehensive_report.get('executive_summary', {}).get('top_recommendations', [])
        strategic_recommendations.extend(exec_recs[:3])
        
        # Recomendaciones de riesgos
        risk_recs = comprehensive_report.get('risk_assessment', {}).get('mitigation_plan', {})
        immediate_actions.extend([r.get('recommendation', '') for r in risk_recs.get('immediate_actions', [])])
        strategic_recommendations.extend([r.get('recommendation', '') for r in risk_recs.get('short_term_actions', [])])
        
        # Recomendaciones de cumplimiento
        compliance_recs = comprehensive_report.get('compliance_review', {}).get('recommendations', [])
        strategic_recommendations.extend(compliance_recs[:3])
        
        # Recomendaciones de comparación
        comparison_recs = comprehensive_report.get('proposal_comparison', {}).get('recommendations', [])
        strategic_recommendations.extend(comparison_recs)
        
        # Consideraciones de largo plazo
        long_term_considerations = [
            "Establecer proceso de monitoreo continuo post-implementación",
            "Desarrollar métricas de éxito y KPIs específicos",
            "Planificar revisiones periódicas del contrato",
            "Considerar actualizaciones tecnológicas futuras"
        ]
        
        return {
            'immediate_actions': list(set(immediate_actions))[:5],
            'strategic_recommendations': list(set(strategic_recommendations))[:8],
            'long_term_considerations': long_term_considerations[:4]
        }
    
    def _generate_chart_data(self, comprehensive_report: Dict) -> Dict[str, Any]:
        """Genera datos estructurados para visualizaciones"""
        
        chart_data = {
            'risk_breakdown': [],
            'compliance_scores': [],
            'proposal_comparison': [],
            'timeline_data': []
        }
        
        # Datos para gráfico de riesgos
        risk_assessment = comprehensive_report.get('risk_assessment', {})
        if risk_assessment.get('risk_breakdown'):
            for risk_cat in risk_assessment['risk_breakdown']:
                chart_data['risk_breakdown'].append({
                    'category': risk_cat['category'],
                    'score': risk_cat['risk_score'],
                    'weight': risk_cat['weight']
                })
        
        # Datos de comparación de propuestas
        proposal_comp = comprehensive_report.get('proposal_comparison', {})
        if proposal_comp.get('detailed_analysis'):
            for proposal in proposal_comp['detailed_analysis']:
                chart_data['proposal_comparison'].append({
                    'id': proposal['proposal_id'],
                    'total': proposal['total_score'],
                    'technical': proposal['technical_score'],
                    'economic': proposal['economic_score'],
                    'compliance': proposal['compliance_score']
                })
        
        return chart_data
    
    def _generate_html_report(self, report_data: Dict) -> str:
        """Genera reporte en formato HTML"""
        
        report_type = report_data.get('report_type', 'UNKNOWN')
        timestamp = report_data.get('generation_timestamp', datetime.now().isoformat())
        
        html_template = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reporte {report_type}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-left: 5px solid #333; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #e9e9e9; }}
                .high-risk {{ color: #d32f2f; font-weight: bold; }}
                .medium-risk {{ color: #f57c00; font-weight: bold; }}
                .low-risk {{ color: #388e3c; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Reporte de Análisis de Licitación</h1>
                <p><strong>Tipo:</strong> {report_type}</p>
                <p><strong>Generado:</strong> {timestamp}</p>
            </div>
        """
        
        # Agregar contenido específico según el tipo de reporte
        if report_type == 'EXECUTIVE_SUMMARY':
            html_template += self._add_executive_summary_html(report_data)
        elif report_type == 'COMPREHENSIVE':
            html_template += self._add_comprehensive_html(report_data)
        else:
            html_template += f"<div class='section'><pre>{json.dumps(report_data, indent=2, ensure_ascii=False)}</pre></div>"
        
        html_template += """
        </body>
        </html>
        """
        
        return html_template
    
    def _add_executive_summary_html(self, report_data: Dict) -> str:
        """Añade contenido HTML específico para resumen ejecutivo"""
        
        status = report_data.get('project_status', 'UNKNOWN')
        status_class = 'low-risk' if status == 'APROBADO' else 'medium-risk' if 'OBSERVACIONES' in status else 'high-risk'
        
        html_content = f"""
        <div class="section">
            <h2>Estado del Proyecto</h2>
            <p class="{status_class}">Estado: {status}</p>
            <p>Score General: {report_data.get('overall_score', 0):.1f}%</p>
        </div>
        
        <div class="section">
            <h2>Hallazgos Clave</h2>
            <ul>
        """
        
        for finding in report_data.get('key_findings', []):
            html_content += f"<li>{finding}</li>"
        
        html_content += """
            </ul>
        </div>
        """
        
        if report_data.get('critical_issues'):
            html_content += """
            <div class="section">
                <h2>Issues Críticos</h2>
                <ul>
            """
            for issue in report_data['critical_issues']:
                html_content += f"<li class='high-risk'>{issue}</li>"
            html_content += "</ul></div>"
        
        return html_content
    
    def _add_comprehensive_html(self, report_data: Dict) -> str:
        """Añade contenido HTML para reporte integral"""
        
        html_content = "<div class='section'><h2>Análisis Integral</h2>"
        
        # Resumen ejecutivo
        if report_data.get('executive_summary'):
            exec_summary = report_data['executive_summary']
            html_content += f"""
            <h3>Resumen Ejecutivo</h3>
            <p><strong>Estado:</strong> {exec_summary.get('project_status', 'N/A')}</p>
            <p><strong>Score General:</strong> {exec_summary.get('overall_score', 0):.1f}%</p>
            """
        
        # Análisis de riesgos
        if report_data.get('risk_assessment'):
            risk_data = report_data['risk_assessment']
            html_content += f"""
            <h3>Análisis de Riesgos</h3>
            <p><strong>Score de Riesgo:</strong> {risk_data.get('executive_summary', {}).get('overall_risk_score', 0):.1f}%</p>
            <p><strong>Nivel de Riesgo:</strong> {risk_data.get('executive_summary', {}).get('risk_level', 'N/A')}</p>
            """
        
        html_content += "</div>"
        
        return html_content
    
    def list_generated_reports(self) -> List[Dict[str, Any]]:
        """Lista todos los reportes generados"""
        
        reports = []
        if self.output_directory.exists():
            for file_path in self.output_directory.iterdir():
                if file_path.is_file():
                    reports.append({
                        'filename': file_path.name,
                        'path': str(file_path),
                        'size_kb': file_path.stat().st_size / 1024,
                        'created': datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
        
        return sorted(reports, key=lambda x: x['created'], reverse=True)
    
    def cleanup_old_reports(self, days_old: int = 30):
        """Elimina reportes más antiguos que el número de días especificado"""
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_count = 0
        
        if self.output_directory.exists():
            for file_path in self.output_directory.iterdir():
                if file_path.is_file():
                    file_date = datetime.fromtimestamp(file_path.stat().st_ctime)
                    if file_date < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
        
        logger.info(f"Eliminados {deleted_count} reportes antiguos")
        return deleted_count