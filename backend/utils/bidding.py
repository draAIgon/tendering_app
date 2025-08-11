from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import logging
from datetime import datetime

# Importar todos los agentes implementados (manejo de errores para dependencias opcionales)
try:
    from .agents.document_extraction import DocumentExtractionAgent
except ImportError:
    DocumentExtractionAgent = None

try:
    from .agents.document_classification import DocumentClassificationAgent
except ImportError:
    DocumentClassificationAgent = None

try:
    from .agents.validator import ComplianceValidationAgent
except ImportError:
    ComplianceValidationAgent = None

try:
    from .agents.comparison import ComparisonAgent
except ImportError:
    ComparisonAgent = None

try:
    from .agents.risk_analyzer import RiskAnalyzerAgent
except ImportError:
    RiskAnalyzerAgent = None

try:
    from .agents.reporter import ReportGenerationAgent
except ImportError:
    ReportGenerationAgent = None

# Importar database manager
from .db_manager import get_standard_db_path, get_analysis_path

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

        # Inicializar agentes disponibles
        # (Extractor se instancia por documento en analyze_document)
        self.document_extractor = None

        self.classifier = DocumentClassificationAgent() if DocumentClassificationAgent else None

        # Validador SIN embeddings (no los usamos aquí)
        self.validator = (
            ComplianceValidationAgent(use_embeddings=False) if ComplianceValidationAgent else None
        )

        self.comparator = ComparisonAgent() if ComparisonAgent else None
        self.risk_analyzer = RiskAnalyzerAgent() if RiskAnalyzerAgent else None
        self.reporter = ReportGenerationAgent() if ReportGenerationAgent else None

        # Estado del sistema
        self.processed_documents = {}
        self.analysis_results = {}
        self.system_initialized = False

        logger.info("Todos los agentes han sido inicializados exitosamente")

    def initialize_system(self, provider="auto", model=None):
        """
        Inicializa el sistema de embeddings para agentes que lo necesitan

        Args:
            provider: Proveedor de embeddings ("openai", "ollama", "auto")
            model: Modelo específico a usar
        """
        try:
            logger.info("Inicializando embeddings para agentes...")

            # El validador aquí NO usa embeddings
            agents_with_embeddings = [
                self.classifier,
                self.comparator,
                self.risk_analyzer,
            ]

            for agent in agents_with_embeddings:
                if agent and hasattr(agent, "initialize_embeddings"):
                    success = agent.initialize_embeddings(provider=provider, model=model)
                    if not success:
                        logger.warning(
                            f"Fallo al inicializar embeddings en {agent.__class__.__name__}"
                        )

            self.system_initialized = True
            logger.info("Sistema completamente inicializado")

        except Exception as e:
            logger.error(f"Error inicializando sistema: {e}")
            self.system_initialized = False

    def analyze_document(
        self, document_path: str, document_type: str = "unknown", analysis_level: str = "comprehensive"
    ) -> Dict[str, Any]:
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
            "document_id": document_id,
            "document_path": document_path,
            "document_type": document_type,
            "analysis_level": analysis_level,
            "timestamp": datetime.now().isoformat(),
            "stages": {},
            "summary": {},
            "errors": [],
        }

        # Initialize content variable
        content = ""

        # 1) Extracción de documento (instancia por documento)
        try:
            logger.info("Etapa 1: Extrayendo contenido del documento...")

            if not DocumentExtractionAgent:
                raise RuntimeError("DocumentExtractionAgent no disponible")

            extractor = DocumentExtractionAgent(document_path)
            extracted_data = extractor.process_document()

            analysis_result["stages"]["extraction"] = {
                "status": "completed",
                "data": extracted_data,
            }

            content = extracted_data.get("content", "") if extracted_data else ""

            if not content:
                raise ValueError("No se pudo extraer contenido del documento")

        except Exception as e:
            error_msg = f"Error en extracción de documento: {e}"
            logger.error(error_msg)
            analysis_result["errors"].append(error_msg)
            analysis_result["stages"]["extraction"] = {"status": "failed", "error": str(e)}

        # 2) Clasificación de documento (DSPy)
        if analysis_level in ["standard", "comprehensive"] and content and self.classifier:
            try:
                logger.info("Etapa 2: Clasificando documento...")

                classifier_db_path = get_standard_db_path("classification", document_id)

                # Configurar classifier para este documento
                self.classifier.document_path = document_path
                self.classifier.vector_db_path = classifier_db_path
                self.classifier.collection_name = f"classification_{document_id}"

                classification_result = self.classifier.process_document(
                    provider="auto",
                    force_rebuild=True,
                )

                analysis_result["stages"]["classification"] = {
                    "status": "completed",
                    "data": classification_result,
                }

            except Exception as e:
                error_msg = f"Error en clasificación: {e}"
                logger.error(error_msg)
                analysis_result["errors"].append(error_msg)
                analysis_result["stages"]["classification"] = {"status": "failed", "error": str(e)}

        # 3) Validación de cumplimiento
        if analysis_level in ["standard", "comprehensive"] and content and self.validator:
            try:
                logger.info("Etapa 3: Validando cumplimiento...")

                validation_result = self.validator.validate_document(
                    content=content, document_type=document_type
                )

                analysis_result["stages"]["validation"] = {
                    "status": "completed",
                    "data": validation_result,
                }

            except Exception as e:
                error_msg = f"Error en validación: {e}"
                logger.error(error_msg)
                analysis_result["errors"].append(error_msg)
                analysis_result["stages"]["validation"] = {"status": "failed", "error": str(e)}

        # 4) Validación de RUC (para análisis comprehensivo)
        if analysis_level == "comprehensive" and content and self.validator:
            try:
                logger.info("Etapa 4: Validando RUC del contratista...")

                work_type = self._determine_work_type(content, document_type)

                ruc_result = self.validator.validate_ruc_in_document(content=content, work_type=work_type)

                analysis_result["stages"]["ruc_validation"] = {
                    "status": "completed",
                    "data": ruc_result,
                }

            except Exception as e:
                error_msg = f"Error en validación de RUC: {e}"
                logger.error(error_msg)
                analysis_result["errors"].append(error_msg)
                analysis_result["stages"]["ruc_validation"] = {"status": "failed", "error": str(e)}

        # 5) Análisis de riesgo (solo para análisis comprehensivo)
        if analysis_level == "comprehensive" and content and self.risk_analyzer:
            try:
                logger.info("Etapa 5: Analizando riesgos...")

                risk_result = self.risk_analyzer.analyze_document_risks(
                    content=content, document_type=document_type, doc_id=document_id
                )

                analysis_result["stages"]["risk_analysis"] = {
                    "status": "completed",
                    "data": risk_result,
                }

            except Exception as e:
                error_msg = f"Error en análisis de riesgo: {e}"
                logger.error(error_msg)
                analysis_result["errors"].append(error_msg)
                analysis_result["stages"]["risk_analysis"] = {"status": "failed", "error": str(e)}

        # 6) Generar resumen y métricas
        analysis_result["summary"] = self._generate_analysis_summary(analysis_result)

        # Almacenar resultado en memoria
        self.processed_documents[document_id] = document_path
        self.analysis_results[document_id] = analysis_result

        # Guardar resultado en disco para persistencia
        self._save_analysis_to_disk(document_id, analysis_result)

        logger.info(f"Análisis completado para documento {document_id}")

        return analysis_result

    def _save_analysis_to_disk(self, document_id: str, analysis_result: Dict[str, Any]) -> bool:
        """
        Guarda los resultados de análisis en disco para persistencia
        """
        try:
            analysis_db_path = get_analysis_path(document_id)
            analysis_db_path.mkdir(parents=True, exist_ok=True)

            # Resultado principal
            result_file = analysis_db_path / "analysis_result.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)

            # Resumen
            if "summary" in analysis_result:
                summary_file = analysis_db_path / "analysis_summary.json"
                summary_data = {
                    "document_id": document_id,
                    "timestamp": analysis_result.get("analysis_timestamp"),
                    "summary": analysis_result["summary"],
                    "status": analysis_result.get("status", "unknown"),
                }
                with open(summary_file, "w", encoding="utf-8") as f:
                    json.dump(summary_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Análisis guardado en disco: {analysis_db_path}")
            return True

        except Exception as e:
            logger.error(f"Error guardando análisis en disco: {e}")
            return False

    def compare_proposals(
        self, proposal_paths: List[str], comparison_criteria: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Compara múltiples propuestas usando los agentes de comparación
        """

        logger.info(f"Comparando {len(proposal_paths)} propuestas")

        comparison_result = {
            "comparison_id": f"comparison_{int(datetime.now().timestamp())}",
            "proposals": proposal_paths,
            "timestamp": datetime.now().isoformat(),
            "individual_analyses": {},
            "pairwise_comparisons": {},
            "overall_ranking": [],
            "recommendation": None,
            "errors": [],
        }

        # 1. Analizar cada propuesta individualmente
        proposal_analyses = {}
        for i, proposal_path in enumerate(proposal_paths):
            try:
                proposal_id = f"proposal_{i+1}"
                analysis = self.analyze_document(
                    proposal_path, document_type="proposal", analysis_level="comprehensive"
                )
                proposal_analyses[proposal_id] = analysis
                comparison_result["individual_analyses"][proposal_id] = analysis

            except Exception as e:
                error_msg = f"Error analizando propuesta {proposal_path}: {e}"
                logger.error(error_msg)
                comparison_result["errors"].append(error_msg)

        # 2. Usar ComparisonAgent para comparación avanzada
        if self.comparator and len(proposal_analyses) >= 2:
            try:
                # Preparar documentos
                for proposal_id, analysis in proposal_analyses.items():
                    if (
                        "extraction" in analysis["stages"]
                        and analysis["stages"]["extraction"]["status"] == "completed"
                    ):
                        content = analysis["stages"]["extraction"]["data"].get("content", "")
                        if content:
                            self.comparator.add_document(
                                doc_id=proposal_id,
                                content=content,
                                doc_type="proposal",
                                metadata={
                                    "path": proposal_paths[int(proposal_id.split("_")[1]) - 1],
                                    "analysis_summary": analysis.get("summary", {}),
                                },
                            )

                # Vector DB y comparación
                self.comparator.setup_vector_database()
                proposal_ids = list(proposal_analyses.keys())
                multi_comparison = self.comparator.compare_multiple_documents(
                    doc_ids=proposal_ids, comparison_type="comprehensive"
                )

                comparison_result["advanced_comparison"] = multi_comparison
                comparison_result["overall_ranking"] = multi_comparison.get("ranking", [])

                if multi_comparison.get("ranking"):
                    best_proposal = multi_comparison["ranking"][0]
                    comparison_result["recommendation"] = {
                        "recommended_proposal": best_proposal["document_id"],
                        "score": best_proposal["average_score"],
                        "reason": f"Mejor puntuación general: {best_proposal['average_score']:.2f}",
                    }

            except Exception as e:
                error_msg = f"Error en comparación avanzada: {e}"
                logger.error(error_msg)
                comparison_result["errors"].append(error_msg)

        # 3. Comparación estándar para 2 propuestas
        if self.comparator and len(proposal_paths) == 2:
            try:
                self.comparator.clear_documents()
                for i, proposal_id in enumerate(proposal_analyses.keys()):
                    content = proposal_analyses[proposal_id]["stages"]["extraction"]["data"].get("content", "")
                    self.comparator.add_proposal(
                        proposal_id,
                        content,
                        metadata={"path": str(proposal_paths[i])}
                    )


                self.comparator.setup_vector_database()
                standard_comparison = self.comparator.compare_proposals()
                comparison_result["standard_comparison"] = standard_comparison

            except Exception as e:
                error_msg = f"Error en comparación estándar: {e}"
                logger.error(error_msg)
                comparison_result["errors"].append(error_msg)

        return comparison_result

    def generate_comprehensive_report(self, document_ids: List[str], report_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Genera un reporte comprehensivo usando el ReportGenerationAgent
        """
        logger.info(f"Generando reporte {report_type} para {len(document_ids)} documentos")

        try:
            analysis_data = {}
            for doc_id in document_ids:
                if doc_id in self.analysis_results:
                    analysis_data[doc_id] = self.analysis_results[doc_id]

            if not analysis_data:
                raise ValueError("No hay datos de análisis disponibles para los documentos especificados")

            data_id = self.reporter.collect_analysis_data(
                classification_results=analysis_data,
                validation_results=analysis_data,
                risk_analysis=analysis_data,
                comparison_results=analysis_data if len(document_ids) > 1 else {},
                extraction_results=analysis_data,
            )

            if report_type == "comprehensive":
                report = self.reporter.generate_comprehensive_report(data_id=data_id)
            elif report_type == "executive":
                report = self.reporter.generate_executive_summary(data_id=data_id)
            elif report_type == "risk":
                report = self.reporter.generate_risk_assessment_report(data_id=data_id)
            elif report_type == "technical":
                report = self.reporter.generate_technical_analysis(data_id=data_id)
            elif report_type == "compliance":
                report = self.reporter.generate_compliance_report(data_id=data_id)
            elif report_type == "comparison":
                report = self.reporter.generate_proposal_comparison_report(data_id=data_id)
            else:
                report = self.reporter.generate_comprehensive_report(data_id=data_id)

            return report

        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            return {"error": str(e), "report_type": report_type, "timestamp": datetime.now().isoformat()}

    def analyze_rfp_requirements(self, rfp_path: str) -> Dict[str, Any]:
        """
        Análisis especializado de pliegos de condiciones (RFP)
        """
        logger.info(f"Analizando RFP: {rfp_path}")

        rfp_analysis = self.analyze_document(rfp_path, document_type="rfp", analysis_level="comprehensive")

        try:
            content = ""
            if "extraction" in rfp_analysis["stages"]:
                extraction_data = rfp_analysis["stages"]["extraction"].get("data", {})
                content = extraction_data.get("content", "")

            if content:
                rfp_requirements = self._extract_rfp_requirements(content)
                rfp_analysis["rfp_requirements"] = rfp_requirements

                evaluation_criteria = self._extract_evaluation_criteria(content)
                rfp_analysis["evaluation_criteria"] = evaluation_criteria

        except Exception as e:
            logger.error(f"Error en análisis específico de RFP: {e}")
            rfp_analysis["rfp_analysis_error"] = str(e)

        return rfp_analysis

    def _extract_rfp_requirements(self, content: str) -> Dict[str, Any]:
        """Extrae requisitos específicos del RFP"""
        import re

        requirements = {
            "technical_requirements": [],
            "functional_requirements": [],
            "compliance_requirements": [],
            "qualification_requirements": [],
            "submission_requirements": [],
        }

        patterns = {
            "technical": [r"requisitos?\s+t[éeé]cnicos?", r"especificaciones?\s+t[éeé]cnicas?", r"tecnolog[íi]a\s+requerida"],
            "functional": [r"requisitos?\s+funcionales?", r"funcionalidades?\s+requeridas?", r"caracter[íi]sticas\s+del\s+sistema"],
            "compliance": [r"cumplimiento\s+normativo", r"regulaciones?\s+aplicables?", r"est[áa]ndares?\s+requeridos?"],
        }

        for req_type, type_patterns in patterns.items():
            for pattern in type_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    start = max(0, match.start() - 200)
                    end = min(len(content), match.end() + 500)
                    context = content[start:end].strip()

                    if req_type == "technical":
                        requirements["technical_requirements"].append(context)
                    elif req_type == "functional":
                        requirements["functional_requirements"].append(context)
                    elif req_type == "compliance":
                        requirements["compliance_requirements"].append(context)

        return requirements

    def _extract_evaluation_criteria(self, content: str) -> Dict[str, Any]:
        """Extrae criterios de evaluación del RFP"""
        import re

        criteria = {
            "scoring_criteria": [],
            "weight_distribution": {},
            "minimum_scores": {},
            "evaluation_process": [],
        }

        score_patterns = [
            r"(\d+)\s*puntos?\s+por\s+(.{1,100})",
            r"(\d+%)\s+(.{1,100})",
            r"peso\s+(\d+)\s*%?\s+(.{1,100})",
        ]

        for pattern in score_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for score, criterion in matches:
                criteria["scoring_criteria"].append({"score": score, "criterion": criterion.strip()})

        return criteria

    def _generate_analysis_summary(self, analysis_result: Dict) -> Dict[str, Any]:
        """Genera un resumen del análisis realizado"""

        summary = {
            "total_stages": len(analysis_result.get("stages", {})),
            "completed_stages": 0,
            "failed_stages": 0,
            "overall_status": "unknown",
            "key_findings": [],
            "recommendations": [],
        }

        # Contar etapas
        for stage_name, stage_data in analysis_result.get("stages", {}).items():
            if stage_data.get("status") == "completed":
                summary["completed_stages"] += 1
            elif stage_data.get("status") == "failed":
                summary["failed_stages"] += 1

        # Estado general
        if summary["failed_stages"] == 0:
            summary["overall_status"] = "success"
        elif summary["completed_stages"] > 0:
            summary["overall_status"] = "partial_success"
        else:
            summary["overall_status"] = "failed"

        stages = analysis_result.get("stages", {})

        # Clasificación (DSPy ⇒ sections es dict)
        if "classification" in stages and stages["classification"].get("status") == "completed":
            classification_data = stages["classification"]["data"]
            sections = classification_data.get("sections", {})
            if isinstance(sections, dict):
                summary["key_findings"].append(f"Documento clasificado en {len(sections)} tipos de sección")
                # Top 3 por # de fragmentos si existe document_count
                try:
                    top = sorted(
                        sections.items(), key=lambda kv: kv[1].get("document_count", 0), reverse=True
                    )[:3]
                    nice = ", ".join(f"{name} ({info.get('document_count', 0)})" for name, info in top)
                    if nice:
                        summary["key_findings"].append(f"Secciones destacadas: {nice}")
                except Exception:
                    pass

        # Validación (usar campos reales del validator)
        if "validation" in stages and stages["validation"].get("status") == "completed":
            validation_data = stages["validation"]["data"]
            compliance_pct = (
                validation_data.get("compliance_validation", {}).get("overall_compliance_percentage")
            )
            if compliance_pct is None:
                compliance_pct = validation_data.get("overall_score", 0)
            try:
                summary["key_findings"].append(
                    f"Puntuación de cumplimiento: {round(float(compliance_pct), 2)}%"
                )
            except Exception:
                summary["key_findings"].append(f"Puntuación de cumplimiento: {compliance_pct}%")

        # Riesgo
        if "risk_analysis" in stages and stages["risk_analysis"].get("status") == "completed":
            risk_data = stages["risk_analysis"]["data"]
            if risk_data.get("overall_risk_score") is not None:
                risk_score = risk_data["overall_risk_score"]
                summary["key_findings"].append(f"Puntuación de riesgo general: {risk_score}")

        # RUC
        if "ruc_validation" in stages and stages["ruc_validation"].get("status") == "completed":
            ruc_data = stages["ruc_validation"]["data"]
            ruc_summary = ruc_data.get("validation_summary", {})
            total_rucs = ruc_summary.get("total_rucs", 0)
            if total_rucs > 0:
                valid_fmt = ruc_summary.get("valid_format", 0)
                compat = ruc_summary.get("compatible_entities", 0)
                summary["key_findings"].append(f"RUCs con formato válido: {valid_fmt}/{total_rucs}")
                summary["key_findings"].append(f"RUCs compatibles: {compat}/{total_rucs}")
                if ruc_data.get("overall_score") is not None:
                    ruc_score = ruc_data["overall_score"]
                    ruc_level = ruc_data.get("validation_level", "DESCONOCIDO")
                    summary["key_findings"].append(f"Validación RUC: {ruc_score}% ({ruc_level})")

        # Recomendaciones básicas
        if summary["overall_status"] == "success":
            summary["recommendations"].append("Análisis completado exitosamente. Revisar resultados detallados.")
        elif summary["overall_status"] == "partial_success":
            summary["recommendations"].append("Análisis parcialmente exitoso. Verificar etapas fallidas.")
        else:
            summary["recommendations"].append("Análisis falló. Verificar formato y contenido del documento.")

        return summary

    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sistema"""

        return {
            "initialized": self.system_initialized,
            "documents_processed": len(self.processed_documents),
            "analyses_completed": len(self.analysis_results),
            "agents_available": [
                "DocumentExtractionAgent",
                "DocumentClassificationAgent",
                "ComplianceValidationAgent",
                "ComparisonAgent",
                "RiskAnalyzerAgent",
                "ReportGenerationAgent",
                "RUCValidationAgent",
            ],
            "data_directory": str(self.data_dir),
            "timestamp": datetime.now().isoformat(),
        }

    def export_results(self, output_path: str) -> bool:
        """
        Exporta todos los resultados de análisis a un archivo JSON
        """
        try:
            export_data = {
                "system_info": self.get_system_status(),
                "processed_documents": self.processed_documents,
                "analysis_results": self.analysis_results,
                "export_timestamp": datetime.now().isoformat(),
            }

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Resultados exportados a: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exportando resultados: {e}")
            return False

    def _determine_work_type(self, content: str, document_type: str) -> str:
        """
        Determina el tipo de trabajo basado en el contenido del documento
        """
        content_lower = content.lower()

        construction_keywords = [
            "construcción",
            "edificación",
            "obra civil",
            "infraestructura",
            "concreto",
            "acero",
            "cemento",
            "excavación",
            "cimentación",
            "estructura",
            "albañilería",
            "arquitectura",
            "ingeniería civil",
            "proyecto de construcción",
            "obra pública",
            "edificio",
            "carretera",
            "puente",
            "túnel",
            "drenaje",
            "pavimento",
        ]

        services_keywords = [
            "servicios profesionales",
            "consultoría",
            "asesoría",
            "auditoría",
            "capacitación",
            "entrenamiento",
            "diseño",
            "estudios técnicos",
            "supervisión",
            "interventoría",
            "servicios de ingeniería",
            "servicios de arquitectura",
            "mantenimiento",
            "soporte técnico",
            "desarrollo de software",
        ]

        supplies_keywords = [
            "suministro",
            "adquisición",
            "compra",
            "equipos",
            "materiales",
            "insumos",
            "productos",
            "bienes",
            "mobiliario",
            "tecnología",
            "software",
            "hardware",
            "vehículos",
            "maquinaria",
            "herramientas",
            "instrumentos",
        ]

        construction_score = sum(1 for keyword in construction_keywords if keyword in content_lower)
        services_score = sum(1 for keyword in services_keywords if keyword in content_lower)
        supplies_score = sum(1 for keyword in supplies_keywords if keyword in content_lower)

        if construction_score >= services_score and construction_score >= supplies_score:
            return "CONSTRUCCION"
        elif services_score >= supplies_score:
            return "SERVICIOS"
        else:
            return "SUMINISTROS"


class RFPAnalyzer:
    """
    Analizador especializado de RFPs sobre el BiddingAnalysisSystem.
    """

    def __init__(self, data_dir: str = DATA_DIR):
        self.bidding_system = BiddingAnalysisSystem(data_dir)
        self.rfp_analyses = {}
        logger.info("RFPAnalyzer inicializado")

    def analyze_rfp(self, rfp_path: str) -> Dict[str, Any]:
        return self.bidding_system.analyze_rfp_requirements(rfp_path)

    def extract_requirements_summary(self, rfp_analysis: Dict) -> Dict[str, Any]:
        summary = {
            "document_id": rfp_analysis.get("document_id"),
            "total_requirements": 0,
            "technical_requirements_count": 0,
            "functional_requirements_count": 0,
            "compliance_requirements_count": 0,
            "key_sections": [],
            "critical_criteria": [],
        }

        rfp_requirements = rfp_analysis.get("rfp_requirements", {})

        for req_type, requirements in rfp_requirements.items():
            count = len(requirements) if isinstance(requirements, list) else 0
            summary["total_requirements"] += count

            if req_type == "technical_requirements":
                summary["technical_requirements_count"] = count
            elif req_type == "functional_requirements":
                summary["functional_requirements_count"] = count
            elif req_type == "compliance_requirements":
                summary["compliance_requirements_count"] = count

        if "classification" in rfp_analysis.get("stages", {}):
            classification_data = rfp_analysis["stages"]["classification"].get("data", {})
            sections = classification_data.get("sections", {})
            if isinstance(sections, dict):
                for name, info in sections.items():
                    try:
                        conf = info.get("dspy_analysis", {}).get("avg_combined_confidence", 0.0)
                        if conf > 0.7:
                            summary["key_sections"].append(
                                {
                                    "section": name,
                                    "confidence": conf,
                                    "content_preview": info.get("content_preview", "")[:100],
                                }
                            )
                    except Exception:
                        continue

        evaluation_criteria = rfp_analysis.get("evaluation_criteria", {})
        scoring_criteria = evaluation_criteria.get("scoring_criteria", [])
        for criterion in scoring_criteria[:5]:
            summary["critical_criteria"].append(criterion)

        return summary

    def compare_with_previous_rfps(self, current_rfp_path: str, previous_rfp_paths: List[str]) -> Dict[str, Any]:
        logger.info(f"Comparando RFP actual con {len(previous_rfp_paths)} RFPs anteriores")

        current_analysis = self.analyze_rfp(current_rfp_path)

        previous_analyses = []
        for rfp_path in previous_rfp_paths:
            try:
                analysis = self.analyze_rfp(rfp_path)
                previous_analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error analizando RFP anterior {rfp_path}: {e}")

        comparison_result = {
            "current_rfp": current_rfp_path,
            "previous_rfps": previous_rfp_paths,
            "timestamp": datetime.now().isoformat(),
            "comparisons": [],
            "trends_analysis": {},
            "recommendations": [],
        }

        try:
            comparator = self.bidding_system.comparator or ComparisonAgent()

            if getattr(comparator, "embeddings_provider", None) is None:
                ok = comparator.initialize_embeddings(provider="auto", model=None)
                if not ok:
                    logger.warning("No se pudieron inicializar embeddings; se hará comparación básica.")

            # Limpia cualquier estado previo por si se reutiliza el comparador del sistema
            comparator.clear_documents()

            current_content = ""
            if "extraction" in current_analysis["stages"]:
                current_content = current_analysis["stages"]["extraction"]["data"].get("content", "")

            if current_content:
                comparator.add_document(
                    doc_id="current_rfp",
                    content=current_content,
                    doc_type="rfp",
                    metadata={"path": current_rfp_path},
                )

            for i, prev_analysis in enumerate(previous_analyses):
                prev_content = ""
                if "extraction" in prev_analysis["stages"]:
                    prev_content = prev_analysis["stages"]["extraction"]["data"].get("content", "")

                if prev_content:
                    comparator.add_document(
                        doc_id=f"previous_rfp_{i}",
                        content=prev_content,
                        doc_type="rfp",
                        metadata={"path": previous_rfp_paths[i]},
                    )

            if previous_analyses:
                # ⚠️ Sólo tiene efecto “semántico” si embeddings se inicializaron
                comparator.setup_vector_database()

                for i in range(len(previous_analyses)):
                    comparison = comparator.comprehensive_comparison("current_rfp", f"previous_rfp_{i}")
                    comparison_result["comparisons"].append(comparison)

        except Exception as e:
            logger.error(f"Error en comparación de RFPs: {e}")
            comparison_result["error"] = str(e)

        return comparison_result
