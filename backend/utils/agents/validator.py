import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json

# Importar funciones del sistema de embeddings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from Embedding import get_embeddings_provider
from langchain_chroma import Chroma
from langchain.schema import Document

# Importar database manager para ubicaciones estandarizadas
from ..db_manager import get_standard_db_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComplianceValidationAgent:
    """
    Agente especializado en validar el cumplimiento de documentos de licitación 
    con regulaciones, requisitos técnicos y normas establecidas.
    """
    
    # Reglas de validación predefinidas
    COMPLIANCE_RULES = {
        'DOCUMENTOS_OBLIGATORIOS': {
            'description': 'Documentos que deben estar presentes',
            'rules': [
                r'certificado\s+de\s+existencia\s+y\s+representaci[óo]n\s+legal',
                r'rut\s+de\s+la\s+empresa',
                r'estados\s+financieros',
                r'p[óo]liza\s+de\s+cumplimiento',
                r'certificado\s+de\s+antecedentes\s+disciplinarios',
                r'experiencia\s+espec[íi]fica',
                r'propuesta\s+t[ée]cnica',
                r'propuesta\s+econ[óo]mica'
            ]
        },
        'REQUISITOS_TECNICOS': {
            'description': 'Validación de especificaciones técnicas',
            'rules': [
                r'especificaciones\s+t[ée]cnicas\s+m[íi]nimas',
                r'certificaciones\s+requeridas',
                r'normas\s+de\s+calidad',
                r'est[áa]ndares\s+internacionales',
                r'compatibilidad\s+del\s+sistema',
                r'requisitos\s+de\s+seguridad'
            ]
        },
        'REQUISITOS_LEGALES': {
            'description': 'Cumplimiento legal y regulatorio',
            'rules': [
                r'ley\s+\d+\s+de\s+\d{4}',
                r'decreto\s+\d+',
                r'resoluci[óo]n\s+\d+',
                r'norma\s+iso\s+\d+',
                r'normatividad\s+vigente',
                r'marco\s+legal\s+aplicable'
            ]
        },
        'REQUISITOS_ECONOMICOS': {
            'description': 'Validación de aspectos económicos',
            'rules': [
                r'valor\s+del\s+contrato',
                r'forma\s+de\s+pago',
                r'anticipo\s+permitido',
                r'garant[íi]as\s+econ[óo]micas',
                r'retenci[óo]n\s+de\s+garant[íi]a',
                r'ajustes\s+de\s+precios'
            ]
        },
        'PLAZOS_Y_CRONOGRAMAS': {
            'description': 'Validación de fechas y cronogramas',
            'rules': [
                r'plazo\s+de\s+ejecuci[óo]n',
                r'cronograma\s+de\s+actividades',
                r'fechas\s+de\s+entrega',
                r'hitos\s+del\s+proyecto',
                r'penalidades\s+por\s+retraso'
            ]
        }
    }
    
    def __init__(self, vector_db_path: Optional[Path] = None, use_embeddings: bool = True):
        # Use standardized database path
        if vector_db_path:
            self.vector_db_path = vector_db_path
        else:
            self.vector_db_path = get_standard_db_path('validation', 'global')
            
        self.use_embeddings = use_embeddings
        self.embeddings_provider = None
        self.vector_db = None
        self.validation_results = {}
        self.compliance_issues = []
        
        logger.info(f"ComplianceValidationAgent iniciado con DB: {self.vector_db_path}")
        
    def initialize_embeddings(self, provider="auto", model=None):
        """Inicializa el sistema de embeddings para validación semántica"""
        if not self.use_embeddings:
            return True
            
        try:
            self.embeddings_provider = get_embeddings_provider(provider=provider, model=model)
            logger.info("Sistema de embeddings inicializado para validación")
            return True
        except Exception as e:
            logger.error(f"Error inicializando embeddings: {e}")
            return False
    
    def setup_vector_db(self, documents: List[Document]):
        """Configura la base de datos vectorial con documentos a validar"""
        if not self.use_embeddings or not self.embeddings_provider:
            return True
            
        try:
            self.vector_db = Chroma(
                collection_name="compliance_validation",
                persist_directory=str(self.vector_db_path),
                embedding_function=self.embeddings_provider
            )
            
            if documents:
                self.vector_db.add_documents(documents)
                self.vector_db.persist()
                logger.info(f"Base de datos vectorial configurada con {len(documents)} documentos")
            
            return True
        except Exception as e:
            logger.error(f"Error configurando base de datos vectorial: {e}")
            return False
    
    def validate_document_structure(self, content: str, document_type: str = "RFP") -> Dict[str, Any]:
        """
        Valida la estructura básica del documento
        
        Args:
            content: Contenido del documento
            document_type: Tipo de documento (RFP, Proposal, etc.)
        
        Returns:
            Diccionario con resultados de validación estructural
        """
        
        structural_issues = []
        required_sections = []
        
        if document_type.upper() == "RFP":
            required_sections = [
                r'(objeto|finalidad|prop[óo]sito)',
                r'(condiciones?\s+(generales?|particulares?))',
                r'(requisitos?\s+t[ée]cnicos?)',
                r'(especificaciones?\s+t[ée]cnicas?)',
                r'(condiciones?\s+econ[óo]micas?)',
                r'(garant[íi]as?|seguros?)',
                r'(plazos?|cronograma)',
                r'(evaluaci[óo]n|calificaci[óo]n)'
            ]
        elif document_type.upper() == "PROPOSAL":
            required_sections = [
                r'(propuesta\s+t[ée]cnica)',
                r'(propuesta\s+econ[óo]mica)',
                r'(experiencia|antecedentes)',
                r'(certificaciones?|certificados?)',
                r'(cronograma|plan\s+de\s+trabajo)'
            ]
        
        found_sections = []
        missing_sections = []
        
        for section_pattern in required_sections:
            if re.search(section_pattern, content, re.IGNORECASE | re.UNICODE):
                found_sections.append(section_pattern)
            else:
                missing_sections.append(section_pattern)
                structural_issues.append(f"Sección faltante: {section_pattern}")
        
        # Validar longitud mínima
        if len(content.strip()) < 1000:
            structural_issues.append("Documento demasiado corto (< 1000 caracteres)")
        
        # Validar presencia de fechas
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'\d{4}/\d{1,2}/\d{1,2}'
        ]
        
        has_dates = any(re.search(pattern, content) for pattern in date_patterns)
        if not has_dates:
            structural_issues.append("No se encontraron fechas en el documento")
        
        return {
            "document_type": document_type,
            "total_sections_required": len(required_sections),
            "sections_found": len(found_sections),
            "sections_missing": len(missing_sections),
            "missing_sections": missing_sections,
            "structural_issues": structural_issues,
            "completion_percentage": (len(found_sections) / len(required_sections) * 100) if required_sections else 100,
            "has_adequate_length": len(content.strip()) >= 1000,
            "has_dates": has_dates
        }
    
    def validate_compliance_rules(self, content: str) -> Dict[str, Any]:
        """
        Valida el cumplimiento con reglas predefinidas
        
        Args:
            content: Contenido del documento a validar
            
        Returns:
            Diccionario con resultados de validación de reglas
        """
        
        compliance_results = {}
        total_rules = 0
        passed_rules = 0
        
        for rule_category, rule_info in self.COMPLIANCE_RULES.items():
            category_results = {
                "description": rule_info["description"],
                "rules_checked": len(rule_info["rules"]),
                "rules_passed": 0,
                "missing_rules": [],
                "found_rules": []
            }
            
            for rule_pattern in rule_info["rules"]:
                total_rules += 1
                if re.search(rule_pattern, content, re.IGNORECASE | re.UNICODE):
                    category_results["rules_passed"] += 1
                    category_results["found_rules"].append(rule_pattern)
                    passed_rules += 1
                else:
                    category_results["missing_rules"].append(rule_pattern)
            
            category_results["compliance_percentage"] = (
                category_results["rules_passed"] / category_results["rules_checked"] * 100
            )
            
            compliance_results[rule_category] = category_results
        
        overall_compliance = (passed_rules / total_rules * 100) if total_rules > 0 else 0
        
        return {
            "overall_compliance_percentage": overall_compliance,
            "total_rules": total_rules,
            "passed_rules": passed_rules,
            "failed_rules": total_rules - passed_rules,
            "category_results": compliance_results,
            "compliance_level": self._get_compliance_level(overall_compliance)
        }
    
    def validate_dates_and_deadlines(self, content: str) -> Dict[str, Any]:
        """
        Valida fechas y plazos en el documento
        
        Args:
            content: Contenido del documento
            
        Returns:
            Resultados de validación de fechas
        """
        
        # Patrones para encontrar fechas
        date_patterns = [
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            r'(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})',
            r'(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})'
        ]
        
        found_dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_dates.extend(matches)
        
        # Buscar plazos específicos
        deadline_patterns = [
            r'plazo[^.]{0,50}(\d+)\s*(d[íi]as?|meses?|a[ñn]os?)',
            r'fecha[^.]{0,30}(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            r'vencimiento[^.]{0,30}(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})'
        ]
        
        found_deadlines = []
        for pattern in deadline_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_deadlines.extend(matches)
        
        # Validar coherencia temporal
        date_issues = []
        if len(found_dates) < 2:
            date_issues.append("Pocas fechas encontradas en el documento")
        
        return {
            "dates_found": len(found_dates),
            "deadlines_found": len(found_deadlines),
            "sample_dates": found_dates[:5],  # Muestra las primeras 5
            "sample_deadlines": found_deadlines[:5],
            "date_issues": date_issues,
            "has_adequate_dates": len(found_dates) >= 3
        }
    
    def semantic_compliance_check(self, query: str, threshold: float = 0.7) -> List[Tuple[Document, float]]:
        """
        Realiza validación de cumplimiento usando búsqueda semántica
        
        Args:
            query: Consulta sobre cumplimiento específico
            threshold: Umbral mínimo de similitud
            
        Returns:
            Lista de documentos relevantes con sus scores
        """
        
        if not self.vector_db:
            logger.warning("Base de datos vectorial no disponible para validación semántica")
            return []
        
        try:
            results = self.vector_db.similarity_search_with_score(query, k=10)
            # Filtrar por umbral
            filtered_results = [(doc, score) for doc, score in results if score >= threshold]
            return filtered_results
        except Exception as e:
            logger.error(f"Error en validación semántica: {e}")
            return []
    
    def validate_document(self, document_path: Optional[str] = None, 
                         content: Optional[str] = None, 
                         document_type: str = "RFP") -> Dict[str, Any]:
        """
        Validación completa de un documento
        
        Args:
            document_path: Ruta al documento (opcional si se proporciona content)
            content: Contenido del documento (opcional si se proporciona document_path)
            document_type: Tipo de documento a validar
            
        Returns:
            Reporte completo de validación
        """
        
        if not content and not document_path:
            raise ValueError("Debe proporcionar content o document_path")
        
        # Obtener contenido si se proporciona ruta
        if document_path and not content:
            try:
                from document_extraction import DocumentExtractionAgent
                extractor = DocumentExtractionAgent(document_path)
                content = extractor.extract_text()
            except Exception as e:
                logger.error(f"Error extrayendo contenido de {document_path}: {e}")
                return {"error": f"No se pudo extraer contenido: {e}"}
        
        logger.info(f"Iniciando validación de documento tipo {document_type}")
        
        # Realizar todas las validaciones
        structural_validation = self.validate_document_structure(content, document_type)
        compliance_validation = self.validate_compliance_rules(content)
        dates_validation = self.validate_dates_and_deadlines(content)
        
        # Calcular score general
        structural_score = structural_validation["completion_percentage"]
        compliance_score = compliance_validation["overall_compliance_percentage"]
        dates_score = 100 if dates_validation["has_adequate_dates"] else 50
        
        overall_score = (structural_score + compliance_score + dates_score) / 3
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(
            structural_validation, compliance_validation, dates_validation
        )
        
        validation_report = {
            "document_type": document_type,
            "validation_timestamp": datetime.now().isoformat(),
            "overall_score": round(overall_score, 2),
            "validation_level": self._get_validation_level(overall_score),
            "structural_validation": structural_validation,
            "compliance_validation": compliance_validation,
            "dates_validation": dates_validation,
            "recommendations": recommendations,
            "summary": {
                "total_issues": len(structural_validation.get("structural_issues", [])) + 
                              compliance_validation["failed_rules"] + 
                              len(dates_validation.get("date_issues", [])),
                "critical_issues": self._count_critical_issues(structural_validation, compliance_validation),
                "document_length": len(content),
                "validation_success": overall_score >= 70
            }
        }
        
        self.validation_results = validation_report
        logger.info(f"Validación completada. Score: {overall_score:.1f}%")
        
        return validation_report
    
    def _get_compliance_level(self, percentage: float) -> str:
        """Determina el nivel de cumplimiento basado en el porcentaje"""
        if percentage >= 90:
            return "EXCELENTE"
        elif percentage >= 80:
            return "BUENO"
        elif percentage >= 70:
            return "ACEPTABLE"
        elif percentage >= 60:
            return "DEFICIENTE"
        else:
            return "INACEPTABLE"
    
    def _get_validation_level(self, score: float) -> str:
        """Determina el nivel de validación general"""
        if score >= 85:
            return "APROBADO"
        elif score >= 70:
            return "APROBADO_CON_OBSERVACIONES"
        elif score >= 50:
            return "REQUIERE_REVISION"
        else:
            return "RECHAZADO"
    
    def _count_critical_issues(self, structural: Dict, compliance: Dict) -> int:
        """Cuenta los issues críticos"""
        critical_count = 0
        
        # Issues estructurales críticos
        if structural["completion_percentage"] < 50:
            critical_count += 1
        
        # Issues de cumplimiento críticos  
        if compliance["overall_compliance_percentage"] < 60:
            critical_count += 1
            
        return critical_count
    
    def _generate_recommendations(self, structural: Dict, compliance: Dict, dates: Dict) -> List[str]:
        """Genera recomendaciones basadas en los resultados de validación"""
        recommendations = []
        
        # Recomendaciones estructurales
        if structural["completion_percentage"] < 70:
            recommendations.append("Completar las secciones faltantes del documento")
        
        if not structural["has_adequate_length"]:
            recommendations.append("Ampliar el contenido del documento con más detalles")
        
        # Recomendaciones de cumplimiento
        for category, results in compliance["category_results"].items():
            if results["compliance_percentage"] < 70:
                recommendations.append(f"Mejorar cumplimiento en {category}: {results['description']}")
        
        # Recomendaciones de fechas
        if not dates["has_adequate_dates"]:
            recommendations.append("Incluir más fechas y plazos específicos")
        
        if len(dates.get("date_issues", [])) > 0:
            recommendations.append("Revisar y corregir las fechas identificadas como problemáticas")
        
        return recommendations[:10]  # Máximo 10 recomendaciones
    
    def export_validation_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Exporta el reporte de validación a un archivo JSON
        
        Args:
            output_path: Ruta donde guardar el reporte
            
        Returns:
            El reporte de validación
        """
        
        if not self.validation_results:
            raise ValueError("No hay resultados de validación para exportar")
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.validation_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Reporte de validación guardado en: {output_path}")
        
        return self.validation_results
    
    def validate_multiple_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Valida múltiples documentos y genera un reporte comparativo
        
        Args:
            documents: Lista de diccionarios con 'path' o 'content' y 'type'
            
        Returns:
            Reporte comparativo de validación
        """
        
        results = []
        
        for i, doc in enumerate(documents):
            try:
                result = self.validate_document(
                    document_path=doc.get('path'),
                    content=doc.get('content'),
                    document_type=doc.get('type', 'RFP')
                )
                result['document_id'] = doc.get('id', f"doc_{i}")
                results.append(result)
            except Exception as e:
                logger.error(f"Error validando documento {i}: {e}")
                results.append({
                    'document_id': doc.get('id', f"doc_{i}"),
                    'error': str(e),
                    'overall_score': 0,
                    'validation_level': 'ERROR'
                })
        
        # Generar estadísticas comparativas
        scores = [r['overall_score'] for r in results if 'overall_score' in r]
        
        comparative_report = {
            "validation_timestamp": datetime.now().isoformat(),
            "total_documents": len(documents),
            "successful_validations": len([r for r in results if 'error' not in r]),
            "failed_validations": len([r for r in results if 'error' in r]),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "best_score": max(scores) if scores else 0,
            "worst_score": min(scores) if scores else 0,
            "documents_results": results
        }
        
        return comparative_report