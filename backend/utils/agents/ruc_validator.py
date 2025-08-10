"""
RUC Validation Agent
Agente especializado en validación de RUC y verificación de entidades legales
"""

import re
import requests
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
from pathlib import Path
import time

# Importar sistema de embeddings
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.embedding import get_embeddings_provider
from langchain_chroma import Chroma
from langchain.schema import Document

# Importar database manager
from ..db_manager import get_standard_db_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RUCValidationAgent:
    """
    Agente especializado en validar RUC y verificar la legitimidad de entidades contratistas.
    Incluye detección automática, verificación en línea y validación de compatibilidad.
    """
    
    # Patrones de RUC para diferentes países
    RUC_PATTERNS = {
        'ECUADOR': {
            'pattern': r'\b\d{10}001\b|\b\d{13}\b',
            'description': 'RUC Ecuador: 10 dígitos + 001 o 13 dígitos',
            'validation_url': 'https://srienlinea.sri.gob.ec/sri-catastro-sujeto-servicio-internet/rest/ConsolidadoContribuyente/existePorNumeroRuc',
            'headers': {'Content-Type': 'application/json'}
        },
        'COLOMBIA': {
            'pattern': r'\b\d{9,10}\b',
            'description': 'NIT Colombia: 9-10 dígitos',
            'validation_url': None,  # Implementar según disponibilidad
            'headers': {}
        },
        'PERU': {
            'pattern': r'\b\d{11}\b',
            'description': 'RUC Perú: 11 dígitos',
            'validation_url': None,  # Implementar según disponibilidad
            'headers': {}
        }
    }
    
    # Tipos de empresas y su compatibilidad con trabajos de construcción
    ENTITY_TYPES = {
        'CONSTRUCCION': {
            'compatible_activities': [
                'construcción', 'edificación', 'obra civil', 'ingeniería civil',
                'arquitectura', 'consultoría técnica', 'supervisión de obras',
                'construcción de edificios', 'obras de ingeniería civil',
                'actividades especializadas de construcción'
            ],
            'ciiu_codes': ['F41', 'F42', 'F43', 'M71', 'M74'],  # Códigos CIIU de construcción
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
    
    def __init__(self, vector_db_path: Optional[Path] = None, use_embeddings: bool = True, use_real_api: bool = False):
        # Usar base de datos estandarizada
        if vector_db_path:
            self.vector_db_path = vector_db_path
        else:
            self.vector_db_path = get_standard_db_path('ruc_validation', 'global')
            
        self.use_embeddings = use_embeddings
        self.use_real_api = use_real_api
        self.embeddings_provider = None
        self.vector_db = None
        self.validation_cache = {}
        
        # Cache de validaciones para evitar llamadas repetitivas a la API
        self.cache_ttl = 3600  # 1 hora
        self.last_cache_cleanup = datetime.now()
        
        logger.info(f"RUCValidationAgent iniciado con DB: {self.vector_db_path}")
        logger.info(f"Modo API real: {'ACTIVADO' if use_real_api else 'DESACTIVADO (simulación)'}")
    
    def set_api_mode(self, use_real_api: bool):
        """Cambia el modo de validación entre API real y simulación"""
        self.use_real_api = use_real_api
        logger.info(f"Modo API cambiado a: {'REAL' if use_real_api else 'SIMULACION'}")
        # Limpiar cache al cambiar modo
        self.validation_cache.clear()
    
    def initialize_embeddings(self, provider="auto", model=None):
        """Inicializa el sistema de embeddings para análisis semántico"""
        try:
            self.embeddings_provider = get_embeddings_provider(provider, model)
            if self.embeddings_provider:
                logger.info(f"Embeddings inicializados: {provider}")
                return True
            else:
                logger.warning("No se pudo inicializar embeddings")
                return False
        except Exception as e:
            logger.error(f"Error inicializando embeddings: {e}")
            return False
    
    def setup_vector_db(self, documents: List[Document]):
        """Configura la base de datos vectorial con documentos"""
        if not self.embeddings_provider:
            logger.warning("Embeddings no inicializados")
            return False
        
        try:
            self.vector_db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings_provider,
                persist_directory=str(self.vector_db_path),
                collection_name="ruc_validation"
            )
            return True
        except Exception as e:
            logger.error(f"Error configurando vector DB: {e}")
            return False
    
    def extract_ruc_from_content(self, content: str) -> List[Dict[str, Any]]:
        """
        Extrae números de RUC del contenido del documento
        
        Args:
            content: Contenido del documento
            
        Returns:
            Lista de RUCs encontrados con metadata
        """
        found_rucs = []
        
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
        """
        Valida el formato de un RUC según el país
        
        Args:
            ruc_number: Número de RUC a validar
            country: País para validación
            
        Returns:
            Resultado de validación de formato
        """
        if country not in self.RUC_PATTERNS:
            return {
                'valid_format': False,
                'error': f'País {country} no soportado'
            }
        
        config = self.RUC_PATTERNS[country]
        pattern = config['pattern']
        
        if re.match(pattern, ruc_number.strip()):
            validation_result = {
                'valid_format': True,
                'country': country,
                'ruc_number': ruc_number.strip(),
                'description': config['description']
            }
            
            # Validación específica para Ecuador
            if country == 'ECUADOR':
                validation_result.update(self._validate_ecuador_ruc(ruc_number))
                
            return validation_result
        else:
            return {
                'valid_format': False,
                'country': country,
                'ruc_number': ruc_number,
                'error': f'Formato inválido para {country}'
            }
    
    def _validate_ecuador_ruc(self, ruc: str) -> Dict[str, Any]:
        """Validación específica para RUC de Ecuador"""
        ruc = ruc.strip()
        
        if len(ruc) not in [10, 13]:
            return {'ecuador_validation': False, 'error': 'Longitud inválida'}
        
        # Validar dígito verificador para personas naturales (10 dígitos)
        if len(ruc) == 10:
            return self._validate_ecuador_cedula(ruc)
        
        # Validar RUC completo (13 dígitos)
        if len(ruc) == 13:
            base_ruc = ruc[:10]
            suffix = ruc[10:]
            
            base_validation = self._validate_ecuador_cedula(base_ruc)
            if not base_validation.get('ecuador_validation', False):
                return base_validation
            
            # Determinar tipo de contribuyente
            third_digit = int(ruc[2])
            if third_digit in [0, 1, 2, 3, 4, 5]:
                entity_type = 'persona_natural'
                expected_suffix = '001'
            elif third_digit == 6:
                entity_type = 'entidad_publica'
                expected_suffix = '001'
            elif third_digit == 9:
                entity_type = 'persona_juridica'
                # Para personas jurídicas, el sufijo puede variar
                expected_suffix = suffix  # Aceptar cualquier sufijo válido
            else:
                return {'ecuador_validation': False, 'error': 'Tercer dígito inválido'}
            
            return {
                'ecuador_validation': True,
                'entity_type': entity_type,
                'base_ruc': base_ruc,
                'suffix': suffix,
                'expected_suffix': expected_suffix,
                'valid_suffix': suffix == expected_suffix or entity_type == 'persona_juridica'
            }
    
    def _validate_ecuador_cedula(self, cedula: str) -> Dict[str, Any]:
        """Validar cédula ecuatoriana (algoritmo oficial)"""
        if len(cedula) != 10:
            return {'ecuador_validation': False, 'error': 'Cédula debe tener 10 dígitos'}
        
        try:
            # Validar provincia (primeros 2 dígitos)
            provincia = int(cedula[:2])
            if provincia < 1 or provincia > 24:
                return {'ecuador_validation': False, 'error': 'Código de provincia inválido'}
            
            # Validar dígito verificador
            digits = [int(d) for d in cedula]
            check_digit = digits[9]
            
            # Algoritmo de validación
            coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2]
            total = 0
            
            for i in range(9):
                product = digits[i] * coefficients[i]
                if product >= 10:
                    product = product // 10 + product % 10
                total += product
            
            expected_check = (10 - (total % 10)) % 10
            
            if check_digit == expected_check:
                return {
                    'ecuador_validation': True,
                    'provincia': provincia,
                    'check_digit_valid': True
                }
            else:
                return {
                    'ecuador_validation': False,
                    'error': 'Dígito verificador inválido',
                    'expected_check': expected_check,
                    'provided_check': check_digit
                }
                
        except ValueError:
            return {'ecuador_validation': False, 'error': 'RUC contiene caracteres no numéricos'}
    
    def verify_ruc_online(self, ruc_number: str, country: str = 'ECUADOR') -> Dict[str, Any]:
        """
        Verifica un RUC en línea contra bases de datos oficiales
        
        Args:
            ruc_number: Número de RUC
            country: País del RUC
            
        Returns:
            Resultado de verificación en línea
        """
        # Limpiar cache antiguo periódicamente
        self._cleanup_cache()
        
        # Verificar cache primero
        cache_key = f"{country}_{ruc_number}"
        if cache_key in self.validation_cache:
            cached_result = self.validation_cache[cache_key]
            if (datetime.now() - cached_result['timestamp']).seconds < self.cache_ttl:
                logger.info(f"Usando resultado cached para RUC {ruc_number}")
                cached_result['data']['from_cache'] = True
                return cached_result['data']
        
        if country not in self.RUC_PATTERNS:
            return {'online_validation': False, 'error': f'País {country} no soportado'}
        
        config = self.RUC_PATTERNS[country]
        validation_url = config.get('validation_url')
        
        if not validation_url:
            return {
                'online_validation': False,
                'error': f'Validación en línea no disponible para {country}',
                'suggestion': 'Implementar integración con API oficial'
            }
        
        try:
            # Preparar request según el país
            if country == 'ECUADOR':
                if self.use_real_api:
                    result = self._verify_ecuador_ruc_online(ruc_number, validation_url, config['headers'])
                else:
                    result = self._simulate_ecuador_validation(ruc_number)
                
                # Guardar en cache
                self.validation_cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                
                return result
            else:
                return {'online_validation': False, 'error': 'Implementación pendiente para este país'}
                
        except Exception as e:
            logger.error(f"Error en verificación en línea: {e}")
            return {
                'online_validation': False,
                'error': f'Error de conectividad: {str(e)}',
                'offline_validation': True
            }
    
    def _cleanup_cache(self):
        """Limpia entradas antigas del cache"""
        now = datetime.now()
        if (now - self.last_cache_cleanup).seconds > 1800:  # Limpiar cada 30 minutos
            expired_keys = []
            for key, value in self.validation_cache.items():
                if (now - value['timestamp']).seconds > self.cache_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.validation_cache[key]
            
            self.last_cache_cleanup = now
            logger.info(f"Cache limpiado: {len(expired_keys)} entradas eliminadas")
    
    def _simulate_ecuador_validation(self, ruc: str) -> Dict[str, Any]:
        """Simulación mejorada para validación de RUC cuando la API real no está habilitada"""
        format_validation = self.validate_ruc_format(ruc, 'ECUADOR')
        
        if not format_validation.get('valid_format', False):
            return {
                'online_validation': False,
                'error': 'Formato de RUC inválido',
                'details': format_validation
            }
        
        # Simular latencia de red
        time.sleep(0.1)
        
        return {
            'online_validation': True,
            'simulation_mode': True,
            'found': True,
            'ruc_number': ruc,
            'status': 'ACTIVO',
            'razon_social': f'EMPRESA SIMULADA RUC {ruc}',
            'tipo_contribuyente': format_validation.get('entity_type', 'PERSONA JURIDICA'),
            'estado_contribuyente': 'ACTIVO',
            'actividad_economica': 'ACTIVIDADES DE CONSTRUCCION',
            'fecha_consulta': datetime.now().isoformat(),
            'source': 'SRI_SIMULATION',
            'nota': 'Validación simulada - Habilitar use_real_api=True para usar API real'
        }
    
    def _verify_ecuador_ruc_online(self, ruc: str, url: str, headers: dict) -> Dict[str, Any]:
        """Verificación específica para RUC de Ecuador con API real del SRI"""
        try:
            # Primero validar formato offline
            format_validation = self.validate_ruc_format(ruc, 'ECUADOR')
            if not format_validation.get('valid_format', False):
                return {
                    'online_validation': False,
                    'error': 'Formato de RUC inválido',
                    'details': format_validation
                }
            
            # Intentar validación real con SRI
            return self._call_sri_api(ruc, format_validation)
            
        except Exception as e:
            logger.error(f"Error en verificación SRI: {e}")
            # Fallback a validación offline si falla la API
            return self._fallback_validation(ruc, format_validation, str(e))
    
    def _call_sri_api(self, ruc: str, format_validation: Dict) -> Dict[str, Any]:
        """Llamada real a la API del SRI"""
        try:
            # URL actual del SRI para consulta de contribuyentes
            sri_url = "https://srienlinea.sri.gob.ec/sri-catastro-sujeto-servicio-internet/rest/ConsolidadoContribuyente/existePorNumeroRuc"
            
            # Headers necesarios para la API del SRI
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Origin': 'https://srienlinea.sri.gob.ec'
            }
            
            # Payload para la consulta
            payload = {
                "numeroRuc": ruc
            }
            
            # Hacer la consulta con timeout
            logger.info(f"Consultando RUC {ruc} en API del SRI...")
            response = requests.post(
                sri_url, 
                json=payload, 
                headers=headers, 
                timeout=10,
                verify=True
            )
            
            if response.status_code == 200:
                return self._process_sri_response(response.json(), ruc)
            elif response.status_code == 404:
                return {
                    'online_validation': True,
                    'found': False,
                    'ruc_number': ruc,
                    'status': 'NO_ENCONTRADO',
                    'message': 'RUC no registrado en el SRI',
                    'fecha_consulta': datetime.now().isoformat(),
                    'source': 'SRI_OFICIAL'
                }
            else:
                raise Exception(f"Error HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            logger.warning("Timeout en consulta SRI, usando validación offline")
            return self._fallback_validation(ruc, format_validation, "Timeout en API del SRI")
        except requests.exceptions.ConnectionError:
            logger.warning("Error de conexión SRI, usando validación offline")
            return self._fallback_validation(ruc, format_validation, "Error de conexión con SRI")
        except Exception as e:
            logger.error(f"Error inesperado en API SRI: {e}")
            return self._fallback_validation(ruc, format_validation, str(e))
    
    def _process_sri_response(self, sri_data: Dict, ruc: str) -> Dict[str, Any]:
        """Procesar respuesta exitosa del SRI"""
        try:
            # El SRI puede devolver diferentes estructuras, adaptamos según la respuesta
            if isinstance(sri_data, dict):
                return {
                    'online_validation': True,
                    'found': True,
                    'ruc_number': ruc,
                    'status': 'ACTIVO',
                    'razon_social': sri_data.get('razonSocial', '').strip(),
                    'nombre_comercial': sri_data.get('nombreComercial', '').strip(),
                    'tipo_contribuyente': sri_data.get('tipoContribuyente', ''),
                    'estado_contribuyente': sri_data.get('estadoContribuyente', ''),
                    'clase_contribuyente': sri_data.get('claseContribuyente', ''),
                    'fecha_actualizacion': sri_data.get('fechaActualizacion', ''),
                    'actividad_economica': sri_data.get('actividadEconomica', ''),
                    'provincia': sri_data.get('provincia', ''),
                    'canton': sri_data.get('canton', ''),
                    'fecha_consulta': datetime.now().isoformat(),
                    'source': 'SRI_OFICIAL',
                    'raw_data': sri_data  # Guardar datos originales para debugging
                }
            else:
                raise Exception(f"Formato de respuesta SRI inesperado: {type(sri_data)}")
                
        except Exception as e:
            logger.error(f"Error procesando respuesta SRI: {e}")
            return {
                'online_validation': False,
                'error': f'Error procesando respuesta del SRI: {str(e)}',
                'raw_response': sri_data
            }
    
    def _fallback_validation(self, ruc: str, format_validation: Dict, error_msg: str) -> Dict[str, Any]:
        """Validación fallback cuando la API del SRI no está disponible"""
        return {
            'online_validation': False,
            'fallback_mode': True,
            'ruc_number': ruc,
            'format_validation': format_validation,
            'error': error_msg,
            'status': 'FORMATO_VALIDO' if format_validation.get('valid_format') else 'FORMATO_INVALIDO',
            'nota': 'Validación offline - API del SRI no disponible',
            'fecha_consulta': datetime.now().isoformat(),
            'source': 'VALIDACION_OFFLINE',
            'recomendacion': 'Verificar manualmente en https://srienlinea.sri.gob.ec/'
        }
    
    def validate_entity_compatibility(self, entity_data: Dict[str, Any], 
                                    work_type: str = 'CONSTRUCCION') -> Dict[str, Any]:
        """
        Valida si una entidad es compatible con el tipo de trabajo solicitado
        
        Args:
            entity_data: Datos de la entidad (incluyendo actividad económica)
            work_type: Tipo de trabajo (CONSTRUCCION, SERVICIOS, SUMINISTROS)
            
        Returns:
            Resultado de validación de compatibilidad
        """
        if work_type not in self.ENTITY_TYPES:
            return {
                'compatibility_validation': False,
                'error': f'Tipo de trabajo {work_type} no reconocido'
            }
        
        work_config = self.ENTITY_TYPES[work_type]
        compatibility_score = 0
        compatibility_reasons = []
        warnings = []
        
        # Extraer actividad económica de los datos
        entity_activity = entity_data.get('actividad_economica', '').lower()
        ciiu_code = entity_data.get('ciiu_code', '')
        
        # Verificar actividades compatibles
        for activity in work_config['compatible_activities']:
            if activity.lower() in entity_activity:
                compatibility_score += 20
                compatibility_reasons.append(f"Actividad relacionada: {activity}")
        
        # Verificar códigos CIIU
        for code in work_config['ciiu_codes']:
            if ciiu_code.startswith(code):
                compatibility_score += 30
                compatibility_reasons.append(f"Código CIIU compatible: {code}")
        
        # Verificar calificaciones requeridas
        entity_qualifications = entity_data.get('qualifications', [])
        for required_qual in work_config['required_qualifications']:
            if any(required_qual.lower() in qual.lower() for qual in entity_qualifications):
                compatibility_score += 25
                compatibility_reasons.append(f"Calificación requerida: {required_qual}")
            else:
                warnings.append(f"Calificación faltante: {required_qual}")
        
        # Determinar nivel de compatibilidad
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
        """Genera recomendación basada en compatibilidad"""
        if level == 'ALTA':
            return "Entidad altamente compatible con el tipo de trabajo solicitado"
        elif level == 'MEDIA':
            return f"Entidad parcialmente compatible. Verificar: {', '.join(warnings[:2])}"
        else:
            return f"Entidad con baja compatibilidad. Riesgos: {', '.join(warnings[:3])}"
    
    def comprehensive_ruc_validation(self, content: str, 
                                   work_type: str = 'CONSTRUCCION') -> Dict[str, Any]:
        """
        Validación comprehensiva de RUC: extracción, formato, verificación y compatibilidad
        
        Args:
            content: Contenido del documento
            work_type: Tipo de trabajo para validar compatibilidad
            
        Returns:
            Reporte completo de validación de RUC
        """
        logger.info("Iniciando validación comprehensiva de RUC")
        
        validation_report = {
            'timestamp': datetime.now().isoformat(),
            'work_type': work_type,
            'rucs_found': [],
            'validation_summary': {
                'total_rucs': 0,
                'valid_format': 0,
                'verified_online': 0,
                'compatible_entities': 0,
                'critical_issues': []
            },
            'recommendations': []
        }
        
        # 1. Extraer RUCs del contenido
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
        
        # 2. Validar cada RUC encontrado
        for ruc_data in found_rucs:
            ruc_number = ruc_data['ruc_number']
            country = ruc_data['country']
            
            # Validación de formato
            format_validation = self.validate_ruc_format(ruc_number, country)
            ruc_data['format_validation'] = format_validation
            
            if format_validation.get('valid_format', False):
                validation_report['validation_summary']['valid_format'] += 1
                
                # Verificación en línea
                online_validation = self.verify_ruc_online(ruc_number, country)
                ruc_data['online_validation'] = online_validation
                
                if online_validation.get('online_validation', False):
                    validation_report['validation_summary']['verified_online'] += 1
                    
                    # Validación de compatibilidad
                    entity_data = {
                        'ruc': ruc_number,
                        'actividad_economica': online_validation.get('razon_social', ''),
                        'ciiu_code': '',  # Extraer si está disponible
                        'qualifications': []  # Extraer del contexto
                    }
                    
                    compatibility_validation = self.validate_entity_compatibility(
                        entity_data, work_type
                    )
                    ruc_data['compatibility_validation'] = compatibility_validation
                    
                    if compatibility_validation.get('is_compatible', False):
                        validation_report['validation_summary']['compatible_entities'] += 1
                    else:
                        validation_report['validation_summary']['critical_issues'].append(
                            f"RUC {ruc_number}: Baja compatibilidad con {work_type}"
                        )
                else:
                    validation_report['validation_summary']['critical_issues'].append(
                        f"RUC {ruc_number}: No se pudo verificar en línea"
                    )
            else:
                validation_report['validation_summary']['critical_issues'].append(
                    f"RUC {ruc_number}: Formato inválido"
                )
            
            validation_report['rucs_found'].append(ruc_data)
        
        # 3. Generar recomendaciones
        validation_report['recommendations'] = self._generate_validation_recommendations(
            validation_report['validation_summary']
        )
        
        # 4. Calcular score general
        total_rucs = validation_report['validation_summary']['total_rucs']
        if total_rucs > 0:
            format_score = (validation_report['validation_summary']['valid_format'] / total_rucs) * 100
            online_score = (validation_report['validation_summary']['verified_online'] / total_rucs) * 100
            compatibility_score = (validation_report['validation_summary']['compatible_entities'] / total_rucs) * 100
            
            overall_score = (format_score + online_score + compatibility_score) / 3
        else:
            overall_score = 0
        
        validation_report['overall_score'] = round(overall_score, 2)
        validation_report['validation_level'] = self._get_validation_level(overall_score)
        
        logger.info(f"Validación de RUC completada. Score: {overall_score:.1f}%")
        return validation_report
    
    def _generate_validation_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en el resumen de validación"""
        recommendations = []
        
        if summary['total_rucs'] == 0:
            recommendations.append("Solicitar documentación que contenga RUC del contratista")
        
        if summary['valid_format'] < summary['total_rucs']:
            recommendations.append("Verificar formato correcto de números de RUC")
        
        if summary['verified_online'] < summary['valid_format']:
            recommendations.append("Realizar verificación manual en portales oficiales")
        
        if summary['compatible_entities'] < summary['verified_online']:
            recommendations.append("Evaluar compatibilidad de actividad económica con trabajo solicitado")
        
        if len(summary['critical_issues']) > 0:
            recommendations.append("Resolver issues críticos antes de continuar evaluación")
        
        return recommendations
    
    def _get_validation_level(self, score: float) -> str:
        """Determina el nivel de validación basado en el score"""
        if score >= 90:
            return "EXCELENTE"
        elif score >= 80:
            return "BUENO"
        elif score >= 70:
            return "ACEPTABLE"
        elif score >= 50:
            return "DEFICIENTE"
        else:
            return "CRITICO"
    
    def export_validation_report(self, validation_data: Dict[str, Any], 
                               output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Exporta reporte de validación en formato JSON"""
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(validation_data, f, ensure_ascii=False, indent=2)
            
            return {
                'export_status': 'success',
                'file_path': str(output_path),
                'export_timestamp': datetime.now().isoformat()
            }
        
        return validation_data
