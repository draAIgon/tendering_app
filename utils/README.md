# Synthetic Document Generator

A Python utility to generate synthetic tendering documents based on PLIEGO PDFs using OpenAI's GPT models.

## Overview

This tool extracts structure and content patterns from source PLIEGO (tendering specification) documents and generates realistic variations for testing, development, and training purposes.

## Features

- **PDF Text Extraction**: Uses PyMuPDF to extract text and analyze document structure
- **AI-Powered Generation**: Leverages OpenAI GPT models to create realistic synthetic documents
- **Structure Analysis**: Identifies key sections like technical specifications, legal requirements, and financial information
- **Multiple Project Types**: Generates documents for various construction project types
- **Configurable Output**: Supports multiple output formats and customizable generation parameters

## Installation

### Prerequisites

- Python 3.10+
- OpenAI API key

### Dependencies

All required dependencies are already available in the hackathon environment:
- `openai` - OpenAI API client
- `PyMuPDF` - PDF processing
- `langchain` - Text processing utilities (optional)

## Usage

### Basic Usage

```bash
# Generate 5 synthetic documents from a PLIEGO PDF
python synthetic_document_generator.py --input_pdf /path/to/pliego.pdf

# Specify custom output directory and count
python synthetic_document_generator.py \
    --input_pdf /path/to/pliego.pdf \
    --output_dir ./my_generated_docs \
    --count 10

# Use different OpenAI model
python synthetic_document_generator.py \
    --input_pdf /path/to/pliego.pdf \
    --model gpt-3.5-turbo \
    --count 3
```

### Advanced Usage

```bash
# With custom API key and detailed logging
python synthetic_document_generator.py \
    --input_pdf /path/to/pliego.pdf \
    --api_key your_openai_api_key \
    --log_level DEBUG \
    --count 5
```

### Environment Variables

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

Or copy the example configuration:

```bash
cp .env.example .env
# Edit .env with your actual API key
```

## Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--input_pdf` | Path to the source PLIEGO PDF file | *Required* |
| `--output_dir` | Output directory for generated documents | `./generated_docs` |
| `--count` | Number of synthetic documents to generate | `5` |
| `--model` | OpenAI model to use | `gpt-4` |
| `--api_key` | OpenAI API key | From `OPENAI_API_KEY` env var |
| `--log_level` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` |

## Output

The tool generates:

1. **Synthetic Documents**: Markdown files with realistic tendering document content
2. **Metadata File**: JSON file with generation details and statistics
3. **Log Output**: Detailed information about the generation process

### Example Output Structure

```
generated_docs/
├── pliego_sintetico_001_construcción_de_edificio_de_oficinas.md
├── pliego_sintetico_002_construcción_de_centro_comercial.md
├── pliego_sintetico_003_construcción_de_complejo_residencial.md
├── pliego_sintetico_004_construcción_de_infraestructura_vial.md
├── pliego_sintetico_005_construcción_de_centro_educativo.md
└── generation_metadata.json
```

## Features in Detail

### PDF Structure Analysis

The tool analyzes the source PDF to identify:
- Document sections and headers
- Technical specifications
- Legal requirements
- Financial information
- Dates and deadlines

### Synthetic Content Generation

Generated documents include:
- Realistic project descriptions
- Technical specifications appropriate to project type
- Legal and regulatory compliance sections
- Financial terms and conditions
- Realistic timelines and deadlines
- Spanish construction industry terminology

### Project Types Supported

- Construcción de Edificio de Oficinas
- Construcción de Centro Comercial
- Construcción de Complejo Residencial
- Construcción de Infraestructura Vial
- Construcción de Centro Educativo
- Construcción de Centro de Salud
- Rehabilitación de Edificio Histórico
- Construcción de Parque Recreativo

## Integration with Tendering App

This utility integrates with the larger tendering application by:

1. **Testing Data Generation**: Creating diverse test documents for system validation
2. **Development Support**: Providing realistic data for feature development
3. **Training Data**: Generating examples for machine learning model training

### Usage in Backend

```python
from utils.synthetic_document_generator import SyntheticDocumentGenerator, PliegoPDFExtractor

# Extract structure from existing document
extractor = PliegoPDFExtractor("path/to/pliego.pdf")
structure = extractor.extract_text_and_structure()

# Generate synthetic variants
generator = SyntheticDocumentGenerator()
documents = generator.generate_synthetic_documents(structure, count=10)
```

## Error Handling

The tool includes robust error handling:
- PDF reading errors
- OpenAI API failures (with fallback content)
- File system permissions
- Invalid input parameters

## Logging

Comprehensive logging provides insights into:
- PDF processing progress
- Structure analysis results
- API call status
- Generation success/failure
- Output file creation

## Configuration

Key configuration options:
- OpenAI model selection
- Generation parameters
- Output formats
- Project type variations
- Location settings

## Troubleshooting

### Common Issues

1. **Missing API Key**
   ```
   Error: OpenAI API key is required
   ```
   Solution: Set `OPENAI_API_KEY` environment variable or use `--api_key` argument

2. **PDF Not Found**
   ```
   Error: PDF file not found: path/to/file.pdf
   ```
   Solution: Verify the PDF file path is correct and accessible

3. **API Rate Limits**
   ```
   Error calling OpenAI API: Rate limit exceeded
   ```
   Solution: Reduce generation count or wait before retrying

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
python synthetic_document_generator.py \
    --input_pdf pliego.pdf \
    --log_level DEBUG
```

## Performance Considerations

- Processing time scales with document size and generation count
- OpenAI API calls may take 10-30 seconds per document
- Generated documents are approximately 2000-3000 words each
- Memory usage is minimal for typical document sizes

## Future Enhancements

Planned improvements:
- Support for multiple input document formats
- Template-based generation options
- Integration with ChromaDB for content vectorization
- Batch processing capabilities
- Custom output formats (PDF, DOCX)

## License

This tool is part of the draAIgon team hackathon submission for intelligent tendering process optimization.
