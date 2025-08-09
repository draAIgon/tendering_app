import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from datetime import datetime

# Importar todos los agentes implementados
from .agents.document_extraction import DocumentExtractionAgent
from .agents.document_classification import DocumentClassificationAgent
from .agents.validator import ComplianceValidationAgent
from .agents.proposal_comparison import ProposalComparisonAgent
from .agents.risk_analyzer import RiskAnalyzerAgent
from .agents.reporter import ReportGenerationAgent
from .agents.comparator import ComparatorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = "../../data"

class BiddingAnalysisSystem:
    """
    Sistema completo de análisis de licitaciones que integra todos los agentes
    especializados para proporcionar análisis comprehensivo de documentos,
    propuestas y procesos de licitación.
    """

    def __init__(self, data_dir: str = DATA_DIR):
        """
        Inicializa el sistema de análisis con todos los agentes
        
        Args:
            data_dir: Directorio base para datos y archivos
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Inicializando Sistema de Análisis de Licitaciones...")
        
        # Inicializar todos los agentes
        self.document_extractor = DocumentExtractionAgent()
        self.classifier = DocumentClassificationAgent()
        self.validator = ComplianceValidationAgent()
        self.comparator = ProposalComparisonAgent()
        self.risk_analyzer = RiskAnalyzerAgent()
        self.reporter = ReportGenerationAgent()
        self.advanced_comparator = ComparatorAgent()
        
        # Estado del sistema
        self.processed_documents = {}
        self.analysis_results = {}
        self.system_initialized = False
        
        logger.info("Todos los agentes han sido inicializados exitosamente")

    def initialize_system(self, provider="auto", model=None):
        """
        Inicializa el sistema de embeddings para todos los agentes
        
        Args:
            provider: Proveedor de embeddings ("openai", "ollama", "auto")
            model: Modelo específico a usar
        """
        try:
            logger.info("Inicializando sistema de embeddings...")
            
            # Inicializar embeddings en agentes que lo requieren
            agents_with_embeddings = [
                self.classifier,
                self.advanced_comparator
            ]
            
            for agent in agents_with_embeddings:
                if hasattr(agent, 'initialize_embeddings'):
                    success = agent.initialize_embeddings(provider=provider, model=model)
                    if not success:
                        logger.warning(f"Fallo al inicializar embeddings en {agent.__class__.__name__}")
            
            self.system_initialized = True
            logger.info("Sistema completamente inicializado")
            
        except Exception as e:
            logger.error(f"Error inicializando sistema: {e}")
            self.system_initialized = False

    def analyze_document(self, document_path: str, document_type: str = "unknown", 
                        analysis_level: str = "comprehensive") -> Dict[str, Any]:
        """
        Análisis completo de un documento usando todos los agentes apropiados
        
        Args:
            document_path: Ruta al documento a analizar
            document_type: Tipo de documento (rfp, proposal, contract, etc.)
            analysis_level: Nivel de análisis ("basic", "standard", "comprehensive")
            
        Returns:
            Resultados completos del análisis
        """
        
        if not self.system_initialized:
            logger.warning("Sistema no inicializado. Inicializando automáticamente...")
            self.initialize_system()
        
        document_id = f"doc_{int(datetime.now().timestamp())}_{Path(document_path).stem}"
        
        logger.info(f"Iniciando análisis {analysis_level} del documento: {document_path}")
        
        analysis_result = {
            'document_id': document_id,
            'document_path': document_path,
            'document_type': document_type,
            'analysis_level': analysis_level,
            'timestamp': datetime.now().isoformat(),
            'stages': {},
            'summary': {},
            'errors': []
        }
        
        try:
            # 1. Extracción de documento
            logger.info("Etapa 1: Extrayendo contenido del documento...")
            self.document_extractor.document = document_path
            extracted_data = self.document_extractor.process_document()
            
            analysis_result['stages']['extraction'] = {
                'status': 'completed',
                'data': extracted_data
            }
            
            content = extracted_data.get('content', '') if extracted_data else ''
            
            if not content:
                raise ValueError("No se pudo extraer contenido del documento")
            
        except Exception as e:
            error_msg = f"Error en extracción de documento: {e}"
            logger.error(error_msg)
            analysis_result['errors'].append(error_msg)
            analysis_result['stages']['extraction'] = {'status': 'failed', 'error': str(e)}
        
        # 2. Clasificación de documento
        if analysis_level in ["standard", "comprehensive"] and content:
            try:
                logger.info("Etapa 2: Clasificando documento...")
                
                classification_result = self.classifier.classify_document(
                    content=content,
                    doc_type=document_type,
                    metadata={'document_path': document_path}
                )
                
                analysis_result['stages']['classification'] = {
                    'status': 'completed',
                    'data': classification_result
                }
                
            except Exception as e:
                error_msg = f"Error en clasificación: {e}"
                logger.error(error_msg)
                analysis_result['errors'].append(error_msg)
                analysis_result['stages']['classification'] = {'status': 'failed', 'error': str(e)}
        
        # 3. Validación de cumplimiento
        if analysis_level in ["standard", "comprehensive"] and content:
            try:
                logger.info("Etapa 3: Validando cumplimiento...")
                
                validation_result = self.validator.validate_compliance(
                    document_content=content,
                    document_type=document_type
                )
                
                analysis_result['stages']['validation'] = {
                    'status': 'completed',
                    'data': validation_result
                }
                
            except Exception as e:
                error_msg = f"Error en validación: {e}"
                logger.error(error_msg)
                analysis_result['errors'].append(error_msg)
                analysis_result['stages']['validation'] = {'status': 'failed', 'error': str(e)}
        
        # 4. Análisis de riesgo (solo para análisis comprehensivo)
        if analysis_level == "comprehensive" and content:
            try:
                logger.info("Etapa 4: Analizando riesgos...")
                
                risk_result = self.risk_analyzer.analyze_document_risks(
                    content=content,
                    doc_type=document_type,
                    doc_id=document_id
                )
                
                analysis_result['stages']['risk_analysis'] = {
                    'status': 'completed',
                    'data': risk_result
                }
                
            except Exception as e:
                error_msg = f"Error en análisis de riesgo: {e}"
                logger.error(error_msg)
                analysis_result['errors'].append(error_msg)
                analysis_result['stages']['risk_analysis'] = {'status': 'failed', 'error': str(e)}
        
        # 5. Generar resumen y métricas
        analysis_result['summary'] = self._generate_analysis_summary(analysis_result)
        
        # Almacenar resultado
        self.processed_documents[document_id] = document_path
        self.analysis_results[document_id] = analysis_result
        
        logger.info(f"Análisis completado para documento {document_id}")
        
        return analysis_result

    def compare_proposals(self, proposal_paths: List[str], 
                         comparison_criteria: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Compara múltiples propuestas usando los agentes de comparación
        
        Args:
            proposal_paths: Lista de rutas a los documentos de propuesta
            comparison_criteria: Criterios personalizados de comparación
            
        Returns:
            Resultados de la comparación de propuestas
        """
        
        logger.info(f"Comparando {len(proposal_paths)} propuestas")
        
        comparison_result = {
            'comparison_id': f"comparison_{int(datetime.now().timestamp())}",
            'proposals': proposal_paths,
            'timestamp': datetime.now().isoformat(),
            'individual_analyses': {},
            'pairwise_comparisons': {},
            'overall_ranking': [],
            'recommendation': None,
            'errors': []
        }
        
        # 1. Analizar cada propuesta individualmente
        proposal_analyses = {}
        for i, proposal_path in enumerate(proposal_paths):
            try:
                proposal_id = f"proposal_{i+1}"
                analysis = self.analyze_document(
                    proposal_path, 
                    document_type="proposal", 
                    analysis_level="comprehensive"
                )
                proposal_analyses[proposal_id] = analysis
                comparison_result['individual_analyses'][proposal_id] = analysis
                
            except Exception as e:
                error_msg = f"Error analizando propuesta {proposal_path}: {e}"
                logger.error(error_msg)
                comparison_result['errors'].append(error_msg)
        
        # 2. Usar ComparatorAgent para comparación avanzada
        if len(proposal_analyses) >= 2:
            try:
                # Preparar documentos para ComparatorAgent
                for proposal_id, analysis in proposal_analyses.items():
                    if 'extraction' in analysis['stages'] and analysis['stages']['extraction']['status'] == 'completed':
                        content = analysis['stages']['extraction']['data'].get('content', '')
                        if content:
                            self.advanced_comparator.add_document(
                                doc_id=proposal_id,
                                content=content,
                                doc_type="proposal",
                                metadata={
                                    'path': proposal_paths[int(proposal_id.split('_')[1]) - 1],
                                    'analysis_summary': analysis.get('summary', {})
                                }
                            )
                
                # Configurar base de datos vectorial
                self.advanced_comparator.setup_vector_database()
                
                # Realizar comparación múltiple
                proposal_ids = list(proposal_analyses.keys())
                multi_comparison = self.advanced_comparator.compare_multiple_documents(
                    doc_ids=proposal_ids,
                    comparison_type="comprehensive"
                )
                
                comparison_result['advanced_comparison'] = multi_comparison
                comparison_result['overall_ranking'] = multi_comparison.get('ranking', [])
                
                # Generar recomendación
                if multi_comparison.get('ranking'):
                    best_proposal = multi_comparison['ranking'][0]
                    comparison_result['recommendation'] = {
                        'recommended_proposal': best_proposal['document_id'],
                        'score': best_proposal['average_score'],
                        'reason': f"Mejor puntuación general: {best_proposal['average_score']:.2f}"
                    }
                
            except Exception as e:
                error_msg = f"Error en comparación avanzada: {e}"
                logger.error(error_msg)
                comparison_result['errors'].append(error_msg)
        
        # 3. Usar ProposalComparisonAgent para comparación estándar
        try:
            if len(proposal_paths) == 2:
                standard_comparison = self.comparator.compare_proposals(
                    proposal_paths[0], 
                    proposal_paths[1],
                    comparison_criteria
                )
                comparison_result['standard_comparison'] = standard_comparison
                
        except Exception as e:
            error_msg = f"Error en comparación estándar: {e}"
            logger.error(error_msg)
            comparison_result['errors'].append(error_msg)
        
        return comparison_result

    def generate_comprehensive_report(self, document_ids: List[str], 
                                    report_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Genera un reporte comprehensivo usando el ReportGenerationAgent
        
        Args:
            document_ids: IDs de documentos analizados a incluir
            report_type: Tipo de reporte a generar
            
        Returns:
            Reporte generado
        """
        
        logger.info(f"Generando reporte {report_type} para {len(document_ids)} documentos")
        
        try:
            # Recopilar datos de análisis
            analysis_data = {}
            for doc_id in document_ids:
                if doc_id in self.analysis_results:
                    analysis_data[doc_id] = self.analysis_results[doc_id]
            
            if not analysis_data:
                raise ValueError("No hay datos de análisis disponibles para los documentos especificados")
            
            # Generar reporte usando ReportGenerationAgent
            report = self.reporter.generate_report(
                analysis_data=analysis_data,
                report_type=report_type,
                metadata={
                    'generated_by': 'BiddingAnalysisSystem',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return {
                'error': str(e),
                'report_type': report_type,
                'timestamp': datetime.now().isoformat()
            }

    def analyze_rfp_requirements(self, rfp_path: str) -> Dict[str, Any]:
        """
        Análisis especializado de pliegos de condiciones (RFP)
        
        Args:
            rfp_path: Ruta al documento RFP
            
        Returns:
            Análisis especializado del RFP
        """
        
        logger.info(f"Analizando RFP: {rfp_path}")
        
        # Análisis base del documento
        rfp_analysis = self.analyze_document(
            rfp_path, 
            document_type="rfp", 
            analysis_level="comprehensive"
        )
        
        # Análisis adicional específico para RFP
        try:
            content = ""
            if 'extraction' in rfp_analysis['stages']:
                extraction_data = rfp_analysis['stages']['extraction'].get('data', {})
                content = extraction_data.get('content', '')
            
            if content:
                # Extraer requisitos específicos
                rfp_requirements = self._extract_rfp_requirements(content)
                rfp_analysis['rfp_requirements'] = rfp_requirements
                
                # Análisis de criterios de evaluación
                evaluation_criteria = self._extract_evaluation_criteria(content)
                rfp_analysis['evaluation_criteria'] = evaluation_criteria
                
        except Exception as e:
            logger.error(f"Error en análisis específico de RFP: {e}")
            rfp_analysis['rfp_analysis_error'] = str(e)
        
        return rfp_analysis

    def _extract_rfp_requirements(self, content: str) -> Dict[str, Any]:
        """Extrae requisitos específicos del RFP"""
        
        import re
        
        requirements = {
            'technical_requirements': [],
            'functional_requirements': [],
            'compliance_requirements': [],
            'qualification_requirements': [],
            'submission_requirements': []
        }
        
        # Patrones para diferentes tipos de requisitos
        patterns = {
            'technical': [
                r'requisitos?\s+t[éeé]cnicos?',
                r'especificaciones?\s+t[éeé]cnicas?',
                r'tecnolog[íi]a\s+requerida'
            ],
            'functional': [
                r'requisitos?\s+funcionales?',
                r'funcionalidades?\s+requeridas?',
                r'caracter[íi]sticas\s+del\s+sistema'
            ],
            'compliance': [
                r'cumplimiento\s+normativo',
                r'regulaciones?\s+aplicables?',
                r'est[áa]ndares?\s+requeridos?'
            ]
        }
        
        for req_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Extraer texto alrededor del match
                    start = max(0, match.start() - 200)
                    end = min(len(content), match.end() + 500)
                    context = content[start:end].strip()
                    
                    if req_type == 'technical':
                        requirements['technical_requirements'].append(context)
                    elif req_type == 'functional':
                        requirements['functional_requirements'].append(context)
                    elif req_type == 'compliance':
                        requirements['compliance_requirements'].append(context)
        
        return requirements

    def _extract_evaluation_criteria(self, content: str) -> Dict[str, Any]:
        """Extrae criterios de evaluación del RFP"""
        
        import re
        
        criteria = {
            'scoring_criteria': [],
            'weight_distribution': {},
            'minimum_scores': {},
            'evaluation_process': []
        }
        
        # Buscar criterios de puntuación
        score_patterns = [
            r'(\d+)\s*puntos?\s+por\s+(.{1,100})',
            r'(\d+%)\s+(.{1,100})',
            r'peso\s+(\d+)\s*%?\s+(.{1,100})'
        ]
        
        for pattern in score_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for score, criterion in matches:
                criteria['scoring_criteria'].append({
                    'score': score,
                    'criterion': criterion.strip()
                })
        
        return criteria

    def _generate_analysis_summary(self, analysis_result: Dict) -> Dict[str, Any]:
        """Genera un resumen del análisis realizado"""
        
        summary = {
            'total_stages': len(analysis_result.get('stages', {})),
            'completed_stages': 0,
            'failed_stages': 0,
            'overall_status': 'unknown',
            'key_findings': [],
            'recommendations': []
        }
        
        # Contar etapas completadas y fallidas
        for stage_name, stage_data in analysis_result.get('stages', {}).items():
            if stage_data.get('status') == 'completed':
                summary['completed_stages'] += 1
            elif stage_data.get('status') == 'failed':
                summary['failed_stages'] += 1
        
        # Determinar estado general
        if summary['failed_stages'] == 0:
            summary['overall_status'] = 'success'
        elif summary['completed_stages'] > 0:
            summary['overall_status'] = 'partial_success'
        else:
            summary['overall_status'] = 'failed'
        
        # Extraer hallazgos clave de cada etapa
        stages = analysis_result.get('stages', {})
        
        if 'classification' in stages and stages['classification'].get('status') == 'completed':
            classification_data = stages['classification']['data']
            if classification_data.get('sections'):
                summary['key_findings'].append(f"Documento clasificado con {len(classification_data['sections'])} secciones identificadas")
        
        if 'validation' in stages and stages['validation'].get('status') == 'completed':
            validation_data = stages['validation']['data']
            compliance_score = validation_data.get('overall_compliance_score', 0)
            summary['key_findings'].append(f"Puntuación de cumplimiento: {compliance_score}%")
        
        if 'risk_analysis' in stages and stages['risk_analysis'].get('status') == 'completed':
            risk_data = stages['risk_analysis']['data']
            if risk_data.get('overall_risk_score'):
                risk_score = risk_data['overall_risk_score']
                summary['key_findings'].append(f"Puntuación de riesgo general: {risk_score}")
        
        # Generar recomendaciones básicas
        if summary['overall_status'] == 'success':
            summary['recommendations'].append("Análisis completado exitosamente. Revisar resultados detallados.")
        elif summary['overall_status'] == 'partial_success':
            summary['recommendations'].append("Análisis parcialmente exitoso. Verificar etapas fallidas.")
        else:
            summary['recommendations'].append("Análisis falló. Verificar formato y contenido del documento.")
        
        return summary

    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sistema"""
        
        return {
            'initialized': self.system_initialized,
            'documents_processed': len(self.processed_documents),
            'analyses_completed': len(self.analysis_results),
            'agents_available': [
                'DocumentExtractionAgent',
                'DocumentClassificationAgent', 
                'ComplianceValidationAgent',
                'ProposalComparisonAgent',
                'RiskAnalyzerAgent',
                'ReportGenerationAgent',
                'ComparatorAgent'
            ],
            'data_directory': str(self.data_dir),
            'timestamp': datetime.now().isoformat()
        }

    def export_results(self, output_path: str) -> bool:
        """
        Exporta todos los resultados de análisis a un archivo JSON
        
        Args:
            output_path: Ruta donde guardar los resultados
            
        Returns:
            True si la exportación fue exitosa
        """
        
        try:
            export_data = {
                'system_info': self.get_system_status(),
                'processed_documents': self.processed_documents,
                'analysis_results': self.analysis_results,
                'export_timestamp': datetime.now().isoformat()
            }
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Resultados exportados a: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando resultados: {e}")
            return False


class RFPAnalyzer:
    """
    Sistema especializado de análisis de pliegos de condiciones (RFP).
    Proporciona funcionalidad específica para analizar documentos de licitación
    y extraer requisitos, criterios de evaluación, y especificaciones técnicas.
    """
    
    def __init__(self, data_dir: str = DATA_DIR):
        """
        Inicializa el analizador de RFP
        
        Args:
            data_dir: Directorio base para datos
        """
        self.bidding_system = BiddingAnalysisSystem(data_dir)
        self.rfp_analyses = {}
        
        logger.info("RFPAnalyzer inicializado")

    def analyze_rfp(self, rfp_path: str) -> Dict[str, Any]:
        """
        Analiza un documento RFP completo
        
        Args:
            rfp_path: Ruta al documento RFP
            
        Returns:
            Análisis completo del RFP
        """
        
        return self.bidding_system.analyze_rfp_requirements(rfp_path)

    def extract_requirements_summary(self, rfp_analysis: Dict) -> Dict[str, Any]:
        """
        Extrae un resumen de requisitos del análisis de RFP
        
        Args:
            rfp_analysis: Resultado del análisis de RFP
            
        Returns:
            Resumen de requisitos
        """
        
        summary = {
            'document_id': rfp_analysis.get('document_id'),
            'total_requirements': 0,
            'technical_requirements_count': 0,
            'functional_requirements_count': 0,
            'compliance_requirements_count': 0,
            'key_sections': [],
            'critical_criteria': []
        }
        
        # Contar requisitos por tipo
        rfp_requirements = rfp_analysis.get('rfp_requirements', {})
        
        for req_type, requirements in rfp_requirements.items():
            count = len(requirements) if isinstance(requirements, list) else 0
            summary['total_requirements'] += count
            
            if req_type == 'technical_requirements':
                summary['technical_requirements_count'] = count
            elif req_type == 'functional_requirements':
                summary['functional_requirements_count'] = count
            elif req_type == 'compliance_requirements':
                summary['compliance_requirements_count'] = count
        
        # Extraer secciones clave de la clasificación
        if 'classification' in rfp_analysis.get('stages', {}):
            classification_data = rfp_analysis['stages']['classification'].get('data', {})
            sections = classification_data.get('sections', [])
            
            for section in sections:
                if section.get('confidence', 0) > 0.7:  # Alta confianza
                    summary['key_sections'].append({
                        'section': section.get('section'),
                        'confidence': section.get('confidence'),
                        'content_preview': section.get('content', '')[:100]
                    })
        
        # Extraer criterios críticos de evaluación
        evaluation_criteria = rfp_analysis.get('evaluation_criteria', {})
        scoring_criteria = evaluation_criteria.get('scoring_criteria', [])
        
        for criterion in scoring_criteria[:5]:  # Top 5
            summary['critical_criteria'].append(criterion)
        
        return summary

    def compare_with_previous_rfps(self, current_rfp_path: str, 
                                  previous_rfp_paths: List[str]) -> Dict[str, Any]:
        """
        Compara el RFP actual con RFPs anteriores
        
        Args:
            current_rfp_path: Ruta al RFP actual
            previous_rfp_paths: Lista de rutas a RFPs anteriores
            
        Returns:
            Comparación entre RFPs
        """
        
        logger.info(f"Comparando RFP actual con {len(previous_rfp_paths)} RFPs anteriores")
        
        # Analizar RFP actual
        current_analysis = self.analyze_rfp(current_rfp_path)
        
        # Analizar RFPs anteriores
        previous_analyses = []
        for rfp_path in previous_rfp_paths:
            try:
                analysis = self.analyze_rfp(rfp_path)
                previous_analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error analizando RFP anterior {rfp_path}: {e}")
        
        # Usar ComparatorAgent para comparación detallada
        comparison_result = {
            'current_rfp': current_rfp_path,
            'previous_rfps': previous_rfp_paths,
            'timestamp': datetime.now().isoformat(),
            'comparisons': [],
            'trends_analysis': {},
            'recommendations': []
        }
        
        try:
            # Preparar documentos para comparación
            comparator = ComparatorAgent()
            
            # Añadir RFP actual
            current_content = ""
            if 'extraction' in current_analysis['stages']:
                current_content = current_analysis['stages']['extraction']['data'].get('content', '')
            
            if current_content:
                comparator.add_document(
                    doc_id="current_rfp",
                    content=current_content,
                    doc_type="rfp",
                    metadata={'path': current_rfp_path}
                )
            
            # Añadir RFPs anteriores
            for i, prev_analysis in enumerate(previous_analyses):
                prev_content = ""
                if 'extraction' in prev_analysis['stages']:
                    prev_content = prev_analysis['stages']['extraction']['data'].get('content', '')
                
                if prev_content:
                    comparator.add_document(
                        doc_id=f"previous_rfp_{i}",
                        content=prev_content,
                        doc_type="rfp",
                        metadata={'path': previous_rfp_paths[i]}
                    )
            
            # Realizar comparaciones
            if len(previous_analyses) > 0:
                comparator.setup_vector_database()
                
                for i in range(len(previous_analyses)):
                    comparison = comparator.comprehensive_comparison(
                        "current_rfp", 
                        f"previous_rfp_{i}"
                    )
                    comparison_result['comparisons'].append(comparison)
        
        except Exception as e:
            logger.error(f"Error en comparación de RFPs: {e}")
            comparison_result['error'] = str(e)
        
        return comparison_result