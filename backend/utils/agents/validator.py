import re
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import json
import hashlib

from langchain_chroma import Chroma
from langchain_core.documents import Document

# Importar utilidades del paquete (ajusta las rutas relativas según tu estructura)
from ..db_manager import get_standard_db_path
from ..utils.embedding import get_embeddings_provider, detect_section_boundaries_semantic

logger = logging.getLogger(__name__)


class ComplianceValidationAgent:
    """
    Agente especializado en validar el cumplimiento de documentos de licitación
    con regulaciones, requisitos técnicos y normas establecidas.
    """

    # --------------------------
    # Reglas / catálogos de clase
    # --------------------------
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

    # Patrones de RUC/NIT por país
    RUC_PATTERNS = {
        'ECUADOR': {
            'pattern': r'\b\d{10}001\b|\b\d{13}\b',
            'description': 'RUC Ecuador: 10 dígitos + 001 o 13 dígitos',
            'validation_url': 'https://srienlinea.sri.gob.ec/sri-catastro-sujeto-servicio-internet/rest/ConsolidadoContribuyente/existePorNumeroRuc',
            'headers': {'Accept': 'application/json, text/plain, */*'}
        },
        'COLOMBIA': {
            'pattern': r'\b\d{9,10}\b',
            'description': 'NIT Colombia: 9-10 dígitos',
            'validation_url': None,
            'headers': {}
        },
        'PERU': {
            'pattern': r'\b\d{11}\b',
            'description': 'RUC Perú: 11 dígitos',
            'validation_url': None,
            'headers': {}
        }
    }

    # Tipos de empresa y compatibilidad
    ENTITY_TYPES = {
        'CONSTRUCCION': {
            'compatible_activities': [
                'construcción', 'edificación', 'obra civil', 'ingeniería civil',
                'arquitectura', 'consultoría técnica', 'supervisión de obras',
                'construcción de edificios', 'obras de ingeniería civil',
                'actividades especializadas de construcción'
            ],
            'ciiu_codes': ['F41', 'F42', 'F43', 'M71', 'M74'],
            'required_qualifications': [
                'registro de construcción', 'certificación técnica',
                'personal técnico calificado', 'experiencia en construcción'
            ]
        },
        'SERVICIOS': {
            'compatible_activities': [
                'servicios profesionales', 'consultoría', 'asesoría técnica',
                'servicios de ingeniería', 'servicios de arquitectura'
            ],
            'ciiu_codes': ['M69', 'M70', 'M71', 'M74'],
            'required_qualifications': []
        },
        'SUMINISTROS': {
            'compatible_activities': [
                'comercio al por mayor', 'suministro de materiales',
                'venta de equipos', 'importación', 'distribución'
            ],
            'ciiu_codes': ['G46', 'G47', 'C23', 'C25'],
            'required_qualifications': []
        }
    }

    # --------------------------
    # Inicialización
    # --------------------------
    def __init__(self, vector_db_path: Optional[Path] = None, use_embeddings: bool = True):
        self.vector_db_path = vector_db_path or get_standard_db_path('validation', 'global')
        self.use_embeddings = use_embeddings
        self.embeddings_provider = None
        self._emb_provider = None
        self._emb_model = None
        self.vector_db = None
        self.validation_results: Dict[str, Any] = {}
        self.compliance_issues: List[str] = []
        logger.info(f"ComplianceValidationAgent iniciado con DB: {self.vector_db_path}")

    def initialize_embeddings(self, provider: str = "auto", model: Optional[str] = None) -> bool:
        """Inicializa el sistema de embeddings para validación semántica."""
        if not self.use_embeddings:
            return True
        try:
            # get_embeddings_provider ahora devuelve (embeddings, provider, model)
            self.embeddings_provider, self._emb_provider, self._emb_model = get_embeddings_provider(
                provider=provider, model=model
            )
            logger.info(f"Sistema de embeddings inicializado para validación ({self._emb_provider}/{self._emb_model})")
            return True
        except Exception as e:
            logger.error(f"Error inicializando embeddings: {e}")
            return False

    def setup_vector_db(self, documents: List[Document]) -> bool:
        """Configura la base de datos vectorial y evita duplicados con IDs estables."""
        if not self.use_embeddings or not self.embeddings_provider:
            return True
        try:
            Path(self.vector_db_path).mkdir(parents=True, exist_ok=True)
            self.vector_db = Chroma(
                collection_name="compliance_validation",
                persist_directory=str(self.vector_db_path),
                embedding_function=self.embeddings_provider  # ← objeto embeddings, no la tupla
            )
            if documents:
                ids: List[str] = []
                for i, d in enumerate(documents):
                    src = (d.metadata or {}).get("source", f"doc_{i}")
                    raw = (src + "|" + d.page_content).encode("utf-8")
                    ids.append(hashlib.sha1(raw).hexdigest())  # estable entre ejecuciones
                self.vector_db.add_documents(documents, ids=ids)
                # persist() es no-op en Chroma moderno, pero no molesta
                try:
                    self.vector_db.persist()
                except AttributeError:
                    pass
                logger.info(f"Base de datos vectorial configurada con {len(documents)} documentos")
            return True
        except Exception as e:
            logger.error(f"Error configurando base de datos vectorial: {e}")
            return False

    # --------------------------
    # Validaciones principales
    # --------------------------
    def validate_document_structure(self, content: str, document_type: str = "RFP") -> Dict[str, Any]:
        """
        Valida la estructura del documento usando el **sectioner semántico**
        (sin regex para detección de secciones).
        """
        SECTION_CONF_THRESHOLD = 0.30  # umbral mínimo para considerar que una sección existe

        # 1) Detectar límites y labels con el sectioner semántico (embedding.py)
        try:
            boundaries = detect_section_boundaries_semantic(content)
        except Exception as e:
            logger.warning(f"No se pudo ejecutar el sectioner semántico: {e}")
            boundaries = []

        # 2) Consolidar secciones detectadas (label -> max_conf) y filtrar ruido
        detected: Dict[str, float] = {}
        for i, (start, label, conf) in enumerate(boundaries):
            # descartar fragmentos ínfimos
            end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(content)
            if len(content[start:end].strip()) < 50:
                continue
            detected[label.upper()] = max(conf, detected.get(label.upper(), 0.0))

        # 3) Definir requeridas por tipo
        if document_type.upper() == "RFP":
            required_labels = [
                "CONVOCATORIA",
                "OBJETO",
                "CONDICIONES_GENERALES",
                "REQUISITOS_TECNICOS",
                "CONDICIONES_ECONOMICAS",
                "GARANTIAS",
                "PLAZOS",
                "FORMULARIOS",
            ]
        else:  # PROPOSAL u otros
            # El sectioner quizá no devuelva estos labels exactos; usamos alias + keywords
            required_labels = [
                "PROPUESTA_TECNICA",
                "PROPUESTA_ECONOMICA",
                "EXPERIENCIA",
                "CERTIFICACIONES",
                "PLAN_TRABAJO",
            ]

        # 4) Alias para mapear labels del sectioner a los esperados por el validador
        alias_map = {
            "CRONOGRAMA": "PLAZOS",
            "ESPECIFICACIONES_TECNICAS": "REQUISITOS_TECNICOS",
            "CONDICIONES": "CONDICIONES_GENERALES",
        }
        detected_norm = {}
        for k, v in detected.items():
            detected_norm[alias_map.get(k, k)] = max(v, detected_norm.get(alias_map.get(k, k), 0.0))

        # 5) Hallar encontradas vs faltantes
        found = [sec for sec in required_labels if detected_norm.get(sec, 0.0) >= SECTION_CONF_THRESHOLD]
        missing = [sec for sec in required_labels if sec not in found]

        # 5b) Para PROPOSAL, fallback liviano por keywords si el sectioner no cubre
        if document_type.upper() != "RFP" and missing:
            lc = content.lower()
            kw = {
                "PROPUESTA_TECNICA": ["propuesta técnica", "alcance técnico", "metodología"],
                "PROPUESTA_ECONOMICA": ["propuesta económica", "precio", "valor ofertado", "presupuesto"],
                "EXPERIENCIA": ["experiencia", "antecedentes", "contratos ejecutados"],
                "CERTIFICACIONES": ["certificaciones", "certificados", "iso", "acreditación"],
                "PLAN_TRABAJO": ["plan de trabajo", "cronograma de actividades", "actividades", "entregables"],
            }
            for sec in list(missing):
                if any(k in lc for k in kw.get(sec, [])):
                    found.append(sec)
                    missing.remove(sec)

        structural_issues: List[str] = []
        # Longitud mínima
        if len(content.strip()) < 1000:
            structural_issues.append("Documento demasiado corto (< 1000 caracteres)")

        # Presencia de fechas (esto sí con regex porque es puntual)
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',
            r'\b\d{4}/\d{1,2}/\d{1,2}\b',
            r'\b\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\b'
        ]
        has_dates = any(re.search(p, content, re.IGNORECASE) for p in date_patterns)
        if not has_dates:
            structural_issues.append("No se encontraron fechas en el documento")

        return {
            "document_type": document_type,
            "total_sections_required": len(required_labels),
            "sections_found": len(found),
            "sections_missing": len(missing),
            "missing_sections": missing,
            "detected_sections": [{"label": k, "max_conf": float(v)} for k, v in sorted(detected_norm.items())],
            "structural_issues": structural_issues,
            "completion_percentage": (len(found) / len(required_labels) * 100) if required_labels else 100.0,
            "has_adequate_length": len(content.strip()) >= 1000,
            "has_dates": has_dates
        }

    def validate_compliance_rules(self, content: str) -> Dict[str, Any]:
        """Valida cumplimiento con reglas predefinidas basadas en regex."""
        compliance_results: Dict[str, Any] = {}
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
        """Valida fechas y plazos en el documento."""
        date_patterns = [
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            r'(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})',
            r'(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})'
        ]
        found_dates: List[str] = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_dates.extend(matches)

        deadline_patterns = [
            r'plazo[^.]{0,50}(\d+)\s*(d[íi]as?|meses?|a[ñn]os?)',
            r'fecha[^.]{0,30}(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})',
            r'vencimiento[^.]{0,30}(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})'
        ]
        found_deadlines: List[str] = []
        for pattern in deadline_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_deadlines.extend(matches)

        date_issues: List[str] = []
        if len(found_dates) < 2:
            date_issues.append("Pocas fechas encontradas en el documento")

        return {
            "dates_found": len(found_dates),
            "deadlines_found": len(found_deadlines),
            "sample_dates": found_dates[:5],
            "sample_deadlines": found_deadlines[:5],
            "date_issues": date_issues,
            "has_adequate_dates": len(found_dates) >= 3
        }

    def semantic_compliance_check(self, query: str, threshold: float = 0.3) -> List[Tuple[Document, float]]:
        """
        Validación semántica con búsqueda por vectores.
        NOTA: Chroma devuelve distancia (menor es más similar).
        """
        if not self.vector_db:
            logger.warning("Base de datos vectorial no disponible para validación semántica")
            return []
        try:
            results = self.vector_db.similarity_search_with_score(query, k=10)
            return [(doc, score) for doc, score in results if score <= threshold]
        except Exception as e:
            logger.error(f"Error en validación semántica: {e}")
            return []

    # --------------------------
    # Scoring / utilidades
    # --------------------------
    def _get_compliance_level(self, percentage: float) -> str:
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
        if score >= 85:
            return "APROBADO"
        elif score >= 70:
            return "APROBADO_CON_OBSERVACIONES"
        elif score >= 50:
            return "REQUIERE_REVISION"
        else:
            return "RECHAZADO"

    def _count_critical_issues(
        self,
        structural: Dict[str, Any],
        compliance: Dict[str, Any],
        ruc_overall: Optional[float] = None,
        total_rucs: Optional[int] = None
    ) -> int:
        c = 0
        if structural["completion_percentage"] < 50:
            c += 1
        if compliance["overall_compliance_percentage"] < 60:
            c += 1
        if ruc_overall is not None and (ruc_overall < 60 or (total_rucs is not None and total_rucs == 0)):
            c += 1
        return c

    def _generate_recommendations(self, structural: Dict[str, Any], compliance: Dict[str, Any], dates: Dict[str, Any]) -> List[str]:
        recommendations: List[str] = []

        if structural["completion_percentage"] < 70:
            recommendations.append("Completar las secciones faltantes del documento")
        if not structural["has_adequate_length"]:
            recommendations.append("Ampliar el contenido del documento con más detalles")

        for category, results in compliance["category_results"].items():
            if results["compliance_percentage"] < 70:
                recommendations.append(f"Mejorar cumplimiento en {category}: {results['description']}")

        if not dates["has_adequate_dates"]:
            recommendations.append("Incluir más fechas y plazos específicos")
        if len(dates.get("date_issues", [])) > 0:
            recommendations.append("Revisar y corregir las fechas identificadas como problemáticas")

        return recommendations[:10]

    # --------------------------
    # RUC / compatibilidad
    # --------------------------
    def extract_ruc_from_content(self, content: str) -> List[Dict[str, Any]]:
        found_rucs: List[Dict[str, Any]] = []
        for country, config in self.RUC_PATTERNS.items():
            pattern = config['pattern']
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                ruc_number = match.group().strip()
                context_start = max(0, match.start() - 100)
                context_end = min(len(content), match.end() + 100)
                context = content[context_start:context_end]
                found_rucs.append({
                    'ruc_number': ruc_number,
                    'country': country,
                    'position': match.span(),
                    'context': context.strip(),
                    'pattern_description': config['description'],
                    'validation_status': 'pending'
                })
        logger.info(f"RUCs encontrados: {len(found_rucs)}")
        return found_rucs

    def validate_ruc_format(self, ruc_number: str, country: str = 'ECUADOR') -> Dict[str, Any]:
        if country not in self.RUC_PATTERNS:
            return {'valid_format': False, 'error': f'País {country} no soportado'}
        config = self.RUC_PATTERNS[country]
        pattern = config['pattern']
        if re.match(pattern, ruc_number.strip()):
            validation_result: Dict[str, Any] = {
                'valid_format': True,
                'country': country,
                'ruc_number': ruc_number.strip(),
                'description': config['description']
            }
            if country == 'ECUADOR':
                ecu = self._validate_ecuador_ruc(ruc_number)
                validation_result.update(ecu)
                # “Válido” solo si pasó las reglas de EC y sufijo válido
                validation_result['valid_format'] = (
                    validation_result['valid_format']
                    and ecu.get('ecuador_validation', False)
                    and ecu.get('valid_suffix', True)
                )
            return validation_result
        return {'valid_format': False, 'country': country, 'ruc_number': ruc_number, 'error': f'Formato inválido para {country}'}

    def _validate_ecuador_ruc(self, ruc: str) -> Dict[str, Any]:
        ruc = ruc.strip()
        if len(ruc) not in [10, 13]:
            return {'ecuador_validation': False, 'error': 'Longitud inválida'}
        if len(ruc) == 10:
            # Cédula sola (no RUC): válida como base, pero sin sufijo
            return self._validate_ecuador_cedula(ruc)

        base_ruc, suffix = ruc[:10], ruc[10:]
        base_validation = self._validate_ecuador_cedula(base_ruc)
        if not base_validation.get('ecuador_validation', False):
            return base_validation

        third_digit = int(ruc[2])
        if third_digit in [0, 1, 2, 3, 4, 5]:
            entity_type, expected_suffix, valid_suffix = 'persona_natural', '001', (suffix == '001')
        elif third_digit == 6:
            entity_type, expected_suffix, valid_suffix = 'entidad_publica', '001', (suffix == '001')
        elif third_digit == 9:
            entity_type, expected_suffix = 'persona_juridica', '001'
            # Permite matriz 001 o sucursales 002–999
            valid_suffix = bool(re.fullmatch(r'00[1-9]|0[1-9]\d|[1-9]\d\d', suffix))
        else:
            return {'ecuador_validation': False, 'error': 'Tercer dígito inválido'}

        return {
            'ecuador_validation': True,
            'entity_type': entity_type,
            'base_ruc': base_ruc,
            'suffix': suffix,
            'expected_suffix': expected_suffix,
            'valid_suffix': valid_suffix
        }

    def _validate_ecuador_cedula(self, cedula: str) -> Dict[str, Any]:
        if len(cedula) != 10:
            return {'ecuador_validation': False, 'error': 'Cédula debe tener 10 dígitos'}
        try:
            provincia = int(cedula[:2])
            if provincia < 1 or provincia > 24:
                return {'ecuador_validation': False, 'error': 'Código de provincia inválido'}

            digits = [int(d) for d in cedula]
            check_digit = digits[9]
            coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2]

            total = 0
            for i in range(9):
                product = digits[i] * coefficients[i]
                if product >= 10:
                    product = product // 10 + product % 10
                total += product

            expected_check = (10 - (total % 10)) % 10
            if check_digit == expected_check:
                return {'ecuador_validation': True, 'provincia': provincia, 'check_digit_valid': True}
            else:
                return {
                    'ecuador_validation': False,
                    'error': 'Dígito verificador inválido',
                    'expected_check': expected_check,
                    'provided_check': check_digit
                }
        except ValueError:
            return {'ecuador_validation': False, 'error': 'Cédula contiene caracteres no numéricos'}

    def validate_entity_compatibility(self, entity_data: Dict[str, Any], work_type: str = 'CONSTRUCCION') -> Dict[str, Any]:
        if work_type not in self.ENTITY_TYPES:
            return {'compatibility_validation': False, 'error': f'Tipo de trabajo {work_type} no reconocido'}
        work_config = self.ENTITY_TYPES[work_type]
        compatibility_score = 0
        compatibility_reasons: List[str] = []
        warnings: List[str] = []

        entity_activity = (entity_data.get('actividad_economica') or '').lower()
        ciiu_code = entity_data.get('ciiu_code', '')

        for activity in work_config['compatible_activities']:
            if activity.lower() in entity_activity:
                compatibility_score += 20
                compatibility_reasons.append(f"Actividad relacionada: {activity}")

        for code in work_config['ciiu_codes']:
            if ciiu_code.startswith(code):
                compatibility_score += 30
                compatibility_reasons.append(f"Código CIIU compatible: {code}")

        entity_qualifications = entity_data.get('qualifications', [])
        for required_qual in work_config['required_qualifications']:
            if any(required_qual.lower() in (qual or '').lower() for qual in entity_qualifications):
                compatibility_score += 25
                compatibility_reasons.append(f"Calificación requerida: {required_qual}")
            else:
                warnings.append(f"Calificación faltante: {required_qual}")

        if compatibility_score >= 70:
            compatibility_level = 'ALTA'
        elif compatibility_score >= 40:
            compatibility_level = 'MEDIA'
        else:
            compatibility_level = 'BAJA'
            warnings.append('Compatibilidad baja con el tipo de trabajo solicitado')

        return {
            'compatibility_validation': True,
            'work_type': work_type,
            'compatibility_score': compatibility_score,
            'compatibility_level': compatibility_level,
            'reasons': compatibility_reasons,
            'warnings': warnings,
            'is_compatible': compatibility_score >= 40,
            'recommendation': self._generate_compatibility_recommendation(
                compatibility_score, compatibility_level, warnings
            )
        }

    def _generate_compatibility_recommendation(self, score: int, level: str, warnings: List[str]) -> str:
        if level == 'ALTA':
            return "Entidad altamente compatible con el tipo de trabajo solicitado"
        elif level == 'MEDIA':
            return f"Entidad parcialmente compatible. Verificar: {', '.join(warnings[:2])}" if warnings else \
                   "Entidad parcialmente compatible."
        else:
            return f"Entidad con baja compatibilidad. Riesgos: {', '.join(warnings[:3])}" if warnings else \
                   "Entidad con baja compatibilidad."

    def validate_ruc_in_document(self, content: str, work_type: str = 'CONSTRUCCION') -> Dict[str, Any]:
        logger.info("Iniciando validación de RUC en documento")
        validation_report: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'work_type': work_type,
            'rucs_found': [],
            'validation_summary': {
                'total_rucs': 0,
                'valid_format': 0,
                'compatible_entities': 0,
                'critical_issues': []
            },
            'recommendations': []
        }

        found_rucs = self.extract_ruc_from_content(content)
        validation_report['validation_summary']['total_rucs'] = len(found_rucs)

        if not found_rucs:
            validation_report['validation_summary']['critical_issues'].append(
                "No se encontraron números de RUC en el documento"
            )
            validation_report['recommendations'].append(
                "Verificar que el documento contenga información de identificación del contratista"
            )
            return validation_report

        for ruc_data in found_rucs:
            ruc_number = ruc_data['ruc_number']
            country = ruc_data['country']

            format_validation = self.validate_ruc_format(ruc_number, country)
            ruc_data['format_validation'] = format_validation

            if format_validation.get('valid_format', False):
                validation_report['validation_summary']['valid_format'] += 1

                # Por ahora sin datos externos de la entidad
                entity_data = {
                    'ruc': ruc_number,
                    'actividad_economica': '',
                    'ciiu_code': '',
                    'qualifications': []
                }
                compatibility_validation = self.validate_entity_compatibility(entity_data, work_type)
                ruc_data['compatibility_validation'] = compatibility_validation
                if compatibility_validation.get('is_compatible', False):
                    validation_report['validation_summary']['compatible_entities'] += 1
            else:
                validation_report['validation_summary']['critical_issues'].append(
                    f"RUC {ruc_number}: Formato inválido"
                )

            validation_report['rucs_found'].append(ruc_data)

        validation_report['recommendations'] = self._generate_ruc_validation_recommendations(
            validation_report['validation_summary']
        )

        total_rucs = validation_report['validation_summary']['total_rucs']
        if total_rucs > 0:
            format_score = (validation_report['validation_summary']['valid_format'] / total_rucs) * 100
            compatibility_score = (validation_report['validation_summary']['compatible_entities'] / total_rucs) * 100
            overall_score = (format_score + compatibility_score) / 2
        else:
            overall_score = 0.0

        validation_report['overall_score'] = round(overall_score, 2)
        validation_report['validation_level'] = self._get_validation_level(overall_score)
        logger.info(f"Validación de RUC completada. Score: {overall_score:.1f}%")
        return validation_report

    def _generate_ruc_validation_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        recommendations: List[str] = []
        if summary['total_rucs'] == 0:
            recommendations.append("Solicitar documentación que contenga RUC del contratista")
        if summary['valid_format'] < summary['total_rucs']:
            recommendations.append("Verificar formato correcto de números de RUC")
        if summary['compatible_entities'] < summary['valid_format']:
            recommendations.append("Evaluar compatibilidad de actividad económica con trabajo solicitado")
        if len(summary['critical_issues']) > 0:
            recommendations.append("Resolver issues críticos antes de continuar evaluación")
        return recommendations

    # --------------------------
    # Pipeline principal
    # --------------------------
    def validate_document(self, document_path: Optional[str] = None, content: Optional[str] = None, document_type: str = "RFP") -> Dict[str, Any]:
        if not content and not document_path:
            raise ValueError("Debe proporcionar content o document_path")

        if document_path and not content:
            try:
                # Ajusta el import a tu estructura real
                from .document_extraction import DocumentExtractionAgent  # type: ignore
                extractor = DocumentExtractionAgent(document_path)
                content = extractor.extract_text()
            except Exception as e:
                logger.error(f"Error extrayendo contenido de {document_path}: {e}")
                return {"error": f"No se pudo extraer contenido: {e}"}

        assert content is not None
        logger.info(f"Iniciando validación de documento tipo {document_type}")

        # Validaciones
        structural_validation = self.validate_document_structure(content, document_type)
        compliance_validation = self.validate_compliance_rules(content)
        dates_validation = self.validate_dates_and_deadlines(content)
        ruc_validation = self.validate_ruc_in_document(content)

        # Scoring
        structural_score = structural_validation["completion_percentage"]
        compliance_score = self.compliance_validation_score(compliance_validation)
        dates_score = 100 if dates_validation["has_adequate_dates"] else 50
        ruc_score = ruc_validation.get("overall_score", 0.0)

        overall_score = (structural_score + compliance_score + dates_score + ruc_score) / 4

        # Recomendaciones
        recommendations = self._generate_recommendations(
            structural_validation, compliance_validation, dates_validation
        ) + ruc_validation.get("recommendations", [])

        validation_report: Dict[str, Any] = {
            "document_type": document_type,
            "validation_timestamp": datetime.now().isoformat(),
            "overall_score": round(overall_score, 2),
            "validation_level": self._get_validation_level(overall_score),
            "structural_validation": structural_validation,
            "compliance_validation": compliance_validation,
            "dates_validation": dates_validation,
            "ruc_validation": ruc_validation,
            "recommendations": recommendations,
            "summary": {
                "total_issues": len(structural_validation.get("structural_issues", [])) +
                                compliance_validation["failed_rules"] +
                                len(dates_validation.get("date_issues", [])) +
                                len(ruc_validation.get("validation_summary", {}).get("critical_issues", [])),
                "critical_issues": self._count_critical_issues(
                    structural_validation,
                    compliance_validation,
                    ruc_validation.get("overall_score"),
                    ruc_validation.get("validation_summary", {}).get("total_rucs")
                ),
                "document_length": len(content),
                "validation_success": overall_score >= 70
            }
        }

        self.validation_results = validation_report
        logger.info(f"Validación completada. Score: {overall_score:.1f}%")
        return validation_report

    def compliance_validation_score(self, comp: Dict[str, Any]) -> float:
        """Permite ajustar cómo computamos el score de cumplimiento (por si un día cambian pesos)."""
        return float(comp.get("overall_compliance_percentage", 0.0))

    # --------------------------
    # Export / batch
    # --------------------------
    def export_validation_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
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
        results: List[Dict[str, Any]] = []

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

        scores = [r['overall_score'] for r in results if 'overall_score' in r]

        comparative_report = {
            "validation_timestamp": datetime.now().isoformat(),
            "total_documents": len(documents),
            "successful_validations": len([r for r in results if 'error' not in r]),
            "failed_validations": len([r for r in results if 'error' in r]),
            "average_score": (sum(scores) / len(scores)) if scores else 0,
            "best_score": max(scores) if scores else 0,
            "worst_score": min(scores) if scores else 0,
            "documents_results": results
        }

        return comparative_report
