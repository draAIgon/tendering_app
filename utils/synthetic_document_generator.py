#!/usr/bin/env python3
"""
Synthetic Document Generator for Tendering Applications

This utility script generates synthetic documents based on the PLIEGO PDF
using OpenAI's GPT models. It extracts structure and content patterns from
the source document and creates variations for testing and development.

Usage:
    python synthetic_document_generator.py --input_pdf path/to/pliego.pdf --output_dir ./generated_docs --count 5

Author: draAIgon Team - Hackathon 2025
"""

import os
import sys
import argparse
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from datetime import datetime, timedelta
import random

try:
    from dotenv import load_dotenv
    # Load environment variables from parent directory's .env file
    parent_dir = Path(__file__).parent.parent
    env_path = parent_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        print(f"Warning: .env file not found at {env_path}")
except ImportError:
    print("Warning: python-dotenv not available. Install with: pip install python-dotenv")

try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI package not found. Please install it with: pip install openai")
    sys.exit(1)

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
except ImportError:
    print("Warning: LangChain not available. Using basic text splitting.")
    RecursiveCharacterTextSplitter = None
    Document = None


class PliegoPDFExtractor:
    """Extracts and analyzes content from PLIEGO PDF documents."""

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self.logger = logging.getLogger(__name__)
        self.document_structure = {}
        self.content_sections = []

    def extract_text_and_structure(self) -> Dict[str, Any]:
        """Extract text content and analyze document structure."""
        doc = None
        try:
            doc = fitz.open(self.pdf_path)
            full_text = ""
            sections = []
            total_pages = doc.page_count

            self.logger.debug(f"Processing PDF with {total_pages} pages")

            for page_num in range(total_pages):
                try:
                    page = doc[page_num]
                    text = page.get_text()

                    if text.strip():  # Only process pages with content
                        full_text += text + "\n\n"

                        # Basic structure detection
                        lines = text.split("\n")
                        current_section = {
                            "page": page_num + 1,
                            "content": (
                                text[:500] + "..." if len(text) > 500 else text
                            ),  # Truncate for storage
                            "lines": len(
                                [line for line in lines if line.strip()]
                            ),  # Count non-empty lines
                            "headers": self._detect_headers(lines),
                        }
                        sections.append(current_section)

                except Exception as e:
                    self.logger.warning(f"Error processing page {page_num + 1}: {e}")
                    continue

            result = {
                "full_text": full_text,
                "total_pages": total_pages,
                "sections": sections,
                "structure": self._analyze_structure(full_text),
            }

            return result

        except Exception as e:
            self.logger.error(f"Error extracting PDF content: {e}")
            raise
        finally:
            if doc:
                try:
                    doc.close()
                except:
                    pass

    def _detect_headers(self, lines: List[str]) -> List[str]:
        """Detect potential headers in text lines."""
        headers = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Simple heuristics for header detection
            if len(line) < 100 and (
                line.isupper()
                or line.startswith(
                    (
                        "CAPÍTULO",
                        "ARTÍCULO",
                        "SECCIÓN",
                        "ANEXO",
                        "PLIEGO",
                        "CONDICIONES",
                        "ESPECIFICACIONES",
                    )
                )
                or any(c.isdigit() for c in line[:10])
            ):
                headers.append(line)

        return headers

    def _analyze_structure(self, text: str) -> Dict[str, Any]:
        """Analyze document structure and extract patterns."""
        structure = {
            "document_type": "PLIEGO_LICITACION",
            "key_sections": [],
            "technical_specs": [],
            "legal_requirements": [],
            "dates_and_deadlines": [],
            "financial_info": [],
        }

        # Pattern matching for different types of content
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Technical specifications
            if any(
                keyword in line.lower()
                for keyword in [
                    "especificación",
                    "técnico",
                    "material",
                    "calidad",
                    "norma",
                ]
            ):
                structure["technical_specs"].append(line)

            # Legal requirements
            if any(
                keyword in line.lower()
                for keyword in ["legal", "normativo", "ley", "decreto", "reglamento"]
            ):
                structure["legal_requirements"].append(line)

            # Dates and deadlines
            if any(
                keyword in line.lower()
                for keyword in ["fecha", "plazo", "entrega", "término", "vencimiento"]
            ):
                structure["dates_and_deadlines"].append(line)

            # Financial information
            if any(
                keyword in line.lower()
                for keyword in ["precio", "costo", "presupuesto", "pago", "facturación"]
            ):
                structure["financial_info"].append(line)

        return structure


class SyntheticDocumentGenerator:
    """Generates synthetic documents based on PLIEGO structure using OpenAI."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.use_openai = bool(self.api_key)

        if self.use_openai:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.model = model
                self.logger = logging.getLogger(__name__)
                self.logger.info(f"OpenAI client initialized with model: {model}")
            except Exception as e:
                self.logger.warning(
                    f"OpenAI initialization failed: {e}. Will use fallback generation."
                )
                self.use_openai = False
        else:
            self.logger = logging.getLogger(__name__)
            self.logger.info(
                "No OpenAI API key provided. Will use fallback content generation."
            )

        # Templates for different types of construction projects
        project_types_env = os.getenv("PROJECT_TYPES", "")
        if project_types_env:
            self.project_types = [pt.strip() for pt in project_types_env.split(",")]
        else:
            self.project_types = [
                "Construcción de Edificio de Oficinas",
                "Construcción de Centro Comercial",
                "Construcción de Complejo Residencial",
                "Construcción de Infraestructura Vial",
                "Construcción de Centro Educativo",
                "Construcción de Centro de Salud",
                "Rehabilitación de Edificio Histórico",
                "Construcción de Parque Recreativo",
            ]

        # Locations for realistic context
        locations_env = os.getenv("LOCATIONS", "")
        if locations_env:
            self.locations = [loc.strip() for loc in locations_env.split(",")]
        else:
            self.locations = [
                "Quito",
                "Guayaquil",
                "Cuenca",
                "Santo Domingo",
                "Ambato",
                "Manta",
                "Portoviejo",
                "Machala",
                "Loja",
                "Riobamba",
            ]

    def generate_synthetic_documents(
        self,
        source_structure: Dict[str, Any],
        count: int = 5,
        output_dir: str = "./generated_docs",
    ) -> List[str]:
        """Generate multiple synthetic documents based on source structure."""

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        generated_files = []

        for i in range(count):
            try:
                # Generate variation parameters
                project_type = random.choice(self.project_types)
                location = random.choice(self.locations)
                project_id = f"LICIT-{datetime.now().year}-{random.randint(100, 999)}"

                # Generate document content
                synthetic_content = self._generate_document_content(
                    source_structure, project_type, location, project_id
                )

                # Save to file
                filename = f"pliego_sintetico_{i+1:03d}_{project_type.replace(' ', '_').lower()}.md"
                file_path = output_path / filename

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(synthetic_content)

                generated_files.append(str(file_path))
                self.logger.info(f"Generated synthetic document: {filename}")

            except Exception as e:
                self.logger.error(f"Error generating document {i+1}: {e}")
                continue

        return generated_files

    def _generate_document_content(
        self,
        source_structure: Dict[str, Any],
        project_type: str,
        location: str,
        project_id: str,
    ) -> str:
        """Generate content for a single synthetic document."""

        if self.use_openai:
            try:
                # Create prompt for OpenAI
                prompt = self._create_generation_prompt(
                    source_structure, project_type, location, project_id
                )

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": """Eres un experto en la elaboración de pliegos de condiciones para licitaciones públicas en el sector de la construcción en Ecuador. 
                            Tu tarea es generar documentos sintéticos realistas basados en la estructura y contenido de documentos reales,
                            manteniendo el formato, terminología legal y técnica apropiada. Los documentos deben ser extremadamente detallados
                            y profesionales, con el mismo nivel de complejidad que los pliegos reales utilizados en licitaciones públicas.""",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=16384,
                    temperature=0.7,
                )

                return response.choices[0].message.content

            except Exception as e:
                self.logger.error(f"Error calling OpenAI API: {e}")
                self.logger.info("Falling back to template-based generation")

        # Use fallback content if OpenAI is not available or fails
        return self._create_fallback_content(project_type, location, project_id)

    def _create_generation_prompt(
        self,
        source_structure: Dict[str, Any],
        project_type: str,
        location: str,
        project_id: str,
    ) -> str:
        """Create a detailed prompt for document generation."""

        structure_summary = self._summarize_structure(source_structure)

        prompt = f"""
        En base a la siguiente estructura de un pliego de licitación real, genera un documento sintético completo 
        para el siguiente proyecto:

        **PROYECTO:** {project_type}
        **UBICACIÓN:** {location}
        **ID LICITACIÓN:** {project_id}

        **ESTRUCTURA DE REFERENCIA:**
        {structure_summary}

        **INSTRUCCIONES - GENERAR CON EL MISMO NIVEL DE DETALLE QUE EL PLIEGO ORIGINAL:**
        1. Mantén la estructura formal COMPLETA y legal típica de un pliego de condiciones ecuatoriano
        2. Incluye TODAS las secciones principales con subsecciones detalladas
        3. Especificaciones técnicas MUY DETALLADAS
        4. Criterios de evaluación COMPLETOS
        5. Condiciones contractuales COMPREHENSIVAS
        6. Usa terminología técnica y legal ecuatoriana EXACTA para el tipo de proyecto
        7. Incluye fechas realistas (próximos 6 meses) y presupuestos detallados con desglose
        8. Incluye requisitos normativos ecuatorianos específicos y códigos de construcción
        9. Formato en Markdown con numeración y estructura profesional exacta
        10. Longitud mínima: 4000-6000 palabras (MISMO NIVEL DE DETALLE que el pliego original)

        IMPORTANTE: El documento debe tener el MISMO NIVEL DE COMPLEJIDAD, DETALLE TÉCNICO y ESTRUCTURA PROFESIONAL 
        que un pliego real utilizado en licitaciones públicas ecuatorianas. Debe ser completamente comprehensivo y detallado.
        """

        return prompt

    def _summarize_structure(self, structure: Dict[str, Any]) -> str:
        """Create a summary of the source document structure."""
        summary_parts = []

        if structure.get("structure", {}).get("technical_specs"):
            summary_parts.append("Especificaciones técnicas detalladas")

        if structure.get("structure", {}).get("legal_requirements"):
            summary_parts.append("Requisitos legales y normativos")

        if structure.get("structure", {}).get("financial_info"):
            summary_parts.append("Información financiera y presupuestaria")

        if structure.get("structure", {}).get("dates_and_deadlines"):
            summary_parts.append("Fechas y plazos de ejecución")

        summary_parts.extend(
            [
                f"Documento de {structure.get('total_pages', 'N/A')} páginas",
                "Estructura formal de pliego de licitación",
                "Terminología técnica especializada",
            ]
        )

        return "\n- " + "\n- ".join(summary_parts)

    def _create_fallback_content(
        self, project_type: str, location: str, project_id: str
    ) -> str:
        """Create comprehensive fallback content if OpenAI API is not available."""

        base_date = datetime.now()
        submission_deadline = base_date + timedelta(days=30)
        project_start = base_date + timedelta(days=45)
        project_end = base_date + timedelta(days=365)

        # Generate realistic budget based on project type
        budget_ranges = {
            "Construcción de Edificio de Oficinas": (2_000_000, 5_000_000),
            "Construcción de Centro Comercial": (3_000_000, 8_000_000),
            "Construcción de Complejo Residencial": (1_500_000, 4_000_000),
            "Construcción de Infraestructura Vial": (5_000_000, 15_000_000),
            "Construcción de Centro Educativo": (1_000_000, 3_000_000),
            "Construcción de Centro de Salud": (2_500_000, 6_000_000),
            "Rehabilitación de Edificio Histórico": (800_000, 2_500_000),
            "Construcción de Parque Recreativo": (500_000, 1_500_000),
        }

        min_budget, max_budget = budget_ranges.get(project_type, (1_000_000, 5_000_000))
        estimated_budget = random.randint(min_budget, max_budget)

        return f"""
# PLIEGO DE CONDICIONES TÉCNICAS Y ADMINISTRATIVAS

## LICITACIÓN: {project_id}

---

### DATOS GENERALES DE LA LICITACIÓN

**Denominación del proyecto:** {project_type}  
**Ubicación:** {location}  
**Tipo de contrato:** Obra pública  
**Procedimiento:** Abierto  
**Presupuesto base de licitación:** {estimated_budget:,} € (IVA excluido)  

---

### 1. OBJETO DEL CONTRATO

#### 1.1. Descripción
El presente pliego tiene por objeto regular la contratación de las obras correspondientes al proyecto de {project_type.lower()} situado en {location}.

#### 1.2. Alcance de los trabajos
Las obras comprenden la ejecución completa del proyecto según especificaciones técnicas, incluyendo:
- Trabajos de preparación del terreno
- Estructura y cimentación
- Instalaciones (eléctricas, fontanería, climatización)
- Acabados interiores y exteriores
- Urbanización y paisajismo

---

### 2. CARACTERÍSTICAS Y CONDICIONES GENERALES

#### 2.1. Plazos
- **Fecha límite de presentación de ofertas:** {submission_deadline.strftime('%d de %B de %Y')}
- **Fecha prevista de inicio de obras:** {project_start.strftime('%d de %B de %Y')}
- **Plazo de ejecución:** 12 meses
- **Fecha prevista de finalización:** {project_end.strftime('%d de %B de %Y')}

#### 2.2. Lugar de ejecución
Las obras se ejecutarán en {location}, según la ubicación especificada en los planos del proyecto.

---

### 3. ESPECIFICACIONES TÉCNICAS

#### 3.1. Normativa aplicable
Las obras se ejecutarán conforme a:
- Código Técnico de la Edificación (CTE)
- Instrucción de Hormigón Estructural (EHE-08)
- Normativas UNE correspondientes a cada especialidad
- Reglamento Electrotécnico de Baja Tensión (REBT)
- Código de la Edificación local de {location}

#### 3.2. Materiales y sistemas constructivos
- **Estructura:** Hormigón armado o estructura metálica según proyecto
- **Cerramientos:** Cumplimiento de exigencias térmicas del CTE-HE
- **Cubiertas:** Impermeabilización según CTE-HS
- **Instalaciones:** Cumplimiento de normativas específicas de cada instalación

#### 3.3. Control de calidad
- Plan de control de calidad según normativa vigente
- Ensayos de materiales por laboratorio acreditado
- Certificaciones de conformidad CE cuando proceda
- Control de ejecución por dirección facultativa

---

### 4. CONDICIONES ECONÓMICAS

#### 4.1. Presupuesto
- **Presupuesto base de licitación:** {estimated_budget:,} € (IVA excluido)
- **IVA aplicable:** 21%
- **Presupuesto total:** {int(estimated_budget * 1.21):,} € (IVA incluido)

#### 4.2. Forma de pago
- Certificaciones mensuales según obra ejecutada
- Retención del 5% hasta recepción definitiva
- Abono en un plazo máximo de 30 días desde certificación

#### 4.3. Revisión de precios
No procede revisión de precios dado el plazo de ejecución inferior a 24 meses.

---

### 5. GARANTÍAS

#### 5.1. Garantía provisional
- Importe: {int(estimated_budget * 0.03):,} € (3% del presupuesto base)
- Modalidades: Aval bancario, seguro de caución o depósito en efectivo

#### 5.2. Garantía definitiva
- Importe: {int(estimated_budget * 0.05):,} € (5% del precio del contrato)
- Constitución: Antes de la firma del contrato
- Liberación: Tras recepción definitiva de las obras

---

### 6. CRITERIOS DE ADJUDICACIÓN

#### 6.1. Criterios evaluables mediante fórmulas (70 puntos)
- **Oferta económica:** 60 puntos
  - Fórmula: (Presupuesto base / Oferta) × 60
  - Ofertas anormalmente bajas: aplicación art. 149 LCSP

- **Plazo de ejecución:** 10 puntos
  - Plazo base: 12 meses
  - Reducción máxima admisible: 2 meses
  - Fórmula: (Reducción en días / 60) × 10

#### 6.2. Criterios evaluables mediante juicio de valor (30 puntos)
- **Propuesta técnica:** 20 puntos
  - Soluciones técnicas innovadoras
  - Mejoras en materiales y sistemas constructivos
  - Plan de obra y organización

- **Medidas ambientales y sociales:** 10 puntos
  - Sostenibilidad y eficiencia energética
  - Gestión de residuos
  - Integración de trabajadores locales

---

### 7. CONDICIONES DE EJECUCIÓN

#### 7.1. Dirección facultativa
- Director de obra: Arquitecto colegiado
- Director de ejecución: Arquitecto técnico colegiado
- Coordinador de seguridad y salud

#### 7.2. Seguimiento y control
- Reuniones de seguimiento quincenales
- Informes mensuales de avance
- Certificaciones mensuales de obra ejecutada

#### 7.3. Subcontratación
- Permitida hasta el 60% del importe del contrato
- Comunicación previa obligatoria
- Cumplimiento de requisitos del subcontratista

---

### 8. DOCUMENTACIÓN TÉCNICA REQUERIDA

#### 8.1. Con la oferta
- Propuesta técnica detallada
- Plan de obra y cronograma
- Plan de seguridad y salud
- Certificados de clasificación empresarial

#### 8.2. Antes del inicio
- Proyecto de ejecución visado
- Plan de control de calidad
- Seguros de responsabilidad civil y decenal
- Designación de equipo técnico

---

### 9. PENALIZACIONES

#### 9.1. Por retraso
- 0,20 € por cada 1.000 € del precio del contrato por cada día de retraso
- Máximo: 5% del precio del contrato

#### 9.2. Por defectos de calidad
- Según gravedad y reincidencia
- Posible resolución del contrato por incumplimiento grave

---

### 10. RECEPCIÓN Y LIQUIDACIÓN

#### 10.1. Recepción provisional
- Comunicación de finalización por contratista
- Acto de recepción en plazo máximo de 30 días
- Inicio del plazo de garantía (12 meses)

#### 10.2. Recepción definitiva
- Transcurrido el plazo de garantía sin observaciones
- Liquidación definitiva del contrato
- Liberación de garantías

---

### 11. JURISDICCIÓN Y RÉGIMEN JURÍDICO

- **Legislación aplicable:** Ley 9/2017, de Contratos del Sector Público
- **Jurisdicción:** Contencioso-administrativa
- **Tribunal competente:** {location}

---

### ANEXOS

#### Anexo I: Modelo de proposición económica
#### Anexo II: Modelo de aval para garantía provisional  
#### Anexo III: Documentación acreditativa de solvencia
#### Anexo IV: Planos de situación y emplazamiento

---

**Fecha de elaboración:** {base_date.strftime('%d de %B de %Y')}  
**Órgano de contratación:** Ayuntamiento de {location}  
**Expediente:** {project_id}

---

*Documento generado sintéticamente para fines de desarrollo y testing del sistema de licitaciones inteligentes - draAIgon Team*
"""


def main():
    """Main function to run the synthetic document generator."""

    parser = argparse.ArgumentParser(
        description="Generate synthetic tendering documents based on PLIEGO PDF"
    )
    parser.add_argument(
        "--input_pdf",
        type=str,
        required=True,
        help="Path to the source PLIEGO PDF file",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=os.getenv("DEFAULT_OUTPUT_DIR", "./generated_docs"),
        help="Output directory for generated documents (default: ./generated_docs)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=int(os.getenv("DEFAULT_DOCUMENT_COUNT", "5")),
        help="Number of synthetic documents to generate (default: 5)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("OPENAI_MODEL", "gpt-4"),
        help="OpenAI model to use (default: gpt-4)",
    )
    parser.add_argument(
        "--api_key", type=str, help="OpenAI API key (or use OPENAI_API_KEY env var)"
    )
    parser.add_argument(
        "--log_level",
        type=str,
        default=os.getenv("DEFAULT_LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logger = logging.getLogger(__name__)

    try:
        # Extract structure from source PDF
        logger.info(f"Extracting structure from: {args.input_pdf}")
        extractor = PliegoPDFExtractor(args.input_pdf)
        source_structure = extractor.extract_text_and_structure()

        logger.info(f"Extracted document with {source_structure['total_pages']} pages")

        # Generate synthetic documents
        logger.info(f"Generating {args.count} synthetic documents...")
        generator = SyntheticDocumentGenerator(api_key=args.api_key, model=args.model)

        generated_files = generator.generate_synthetic_documents(
            source_structure=source_structure,
            count=args.count,
            output_dir=args.output_dir,
        )

        logger.info(f"Successfully generated {len(generated_files)} documents:")
        for file_path in generated_files:
            logger.info(f"  - {file_path}")

        # Save metadata
        metadata = {
            "source_pdf": args.input_pdf,
            "generation_date": datetime.now().isoformat(),
            "model_used": args.model,
            "documents_generated": len(generated_files),
            "output_directory": args.output_dir,
            "files": generated_files,
            "source_structure_summary": {
                "total_pages": source_structure["total_pages"],
                "sections_count": len(source_structure["sections"]),
                "has_technical_specs": bool(
                    source_structure["structure"]["technical_specs"]
                ),
                "has_legal_requirements": bool(
                    source_structure["structure"]["legal_requirements"]
                ),
                "has_financial_info": bool(
                    source_structure["structure"]["financial_info"]
                ),
            },
        }

        metadata_path = Path(args.output_dir) / "generation_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Metadata saved to: {metadata_path}")
        print(
            f"\n✅ Successfully generated {len(generated_files)} synthetic documents in '{args.output_dir}'"
        )

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
