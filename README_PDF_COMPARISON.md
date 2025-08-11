# Funcionalidad de Comparación y Generación de Reportes

## Descripción

Este documento describe la implementación de la funcionalidad de comparación de documentos y generación de reportes diferenciados según el tipo de análisis (individual vs comparación).

## Implementación

### 1. Frontend (React/TypeScript)

#### API Client (`frontend/src/lib/api.ts`)

Se agregó la función `generateComparisonReportAsFile()` para manejar específicamente reportes de comparación:

```typescript
async generateComparisonReportAsFile(comparisonId: string, options: ReportRequest = {}): Promise<Blob>
```

Esta función utiliza el endpoint específico `/api/v1/reports/comparison/{comparison_id}` para generar reportes de comparación.

#### Dashboard (`frontend/src/app/dashboard/page.tsx`)

Se modificó la función `handleGenerateReport()` para usar el endpoint correcto dependiendo del tipo de análisis:

- **Análisis Individual**: Usa `/api/v1/reports/generate/{document_id}`
- **Comparación**: Usa `/api/v1/reports/comparison/{comparison_id}`

```typescript
if (isComparison) {
  // Usar endpoint de comparación para múltiples documentos
  pdfReportBlob = await apiClient.generateComparisonReportAsFile(processedData.documentId, {
    report_type: 'comparison',
    include_charts: true,
    format: 'pdf'
  });
} else {
  // Usar endpoint regular para documento individual
  pdfReportBlob = await apiClient.generateReportAsFile(processedData.documentId, {
    report_type: 'comprehensive',
    include_charts: true,
    format: 'pdf'
  });
}
```

### 2. Backend (FastAPI/Python)

#### Endpoint de Comparación (`backend/api/main.py`)

El endpoint `/api/v1/reports/comparison/{comparison_id}` ya estaba implementado, pero se mejoró para:

1. **Soporte de caché y disco**: Primero intenta cargar desde caché en memoria, si no encuentra los datos, los carga desde disco.

2. **Mejor manejo de errores**: Incluye mensajes de error más descriptivos.

3. **Formatos múltiples**: Soporta PDF, HTML y JSON según el parámetro `format`.

```python
@app.post("/api/v1/reports/comparison/{comparison_id}")
async def generate_comparison_report(
    comparison_id: str,
    report_request: ReportRequest
):
    # Lógica mejorada para cargar desde caché o disco
    # Generación de reportes en múltiples formatos
```

## Flujo de Funcionamiento

### Análisis Individual (1 archivo)
1. Usuario sube 1 archivo
2. Se establece `isComparison = false`
3. Al generar reporte: `generateReportAsFile()` → `/api/v1/reports/generate/{document_id}`

### Comparación (2+ archivos)
1. Usuario sube 2 o más archivos
2. Se establece `isComparison = true`
3. Al generar reporte: `generateComparisonReportAsFile()` → `/api/v1/reports/comparison/{comparison_id}`

## Ventajas de la Implementación

1. **Separación clara**: Endpoints específicos para cada tipo de análisis
2. **Flexibilidad**: El backend puede manejar datos desde caché o disco
3. **Escalabilidad**: Fácil agregar nuevos tipos de reportes
4. **Mantenibilidad**: Código bien organizado y documentado

## Testing

Se incluye un script de prueba `test_comparison_report.py` que verifica:
- Funcionamiento del endpoint de comparación
- Lógica del frontend
- Generación de archivos PDF

## Archivos Modificados

### Frontend
- `frontend/src/lib/api.ts`: Nueva función `generateComparisonReportAsFile()`
- `frontend/src/app/dashboard/page.tsx`: Lógica condicional en `handleGenerateReport()`

### Backend
- `backend/api/main.py`: Mejorado endpoint `/api/v1/reports/comparison/{comparison_id}`

### Testing
- `test_comparison_report.py`: Script de pruebas (nuevo)

## Estado Actual

✅ **Implementado y funcional**

La funcionalidad está completa y lista para ser utilizada. Cuando un usuario sube 2 o más archivos y genera un reporte, automáticamente se usa el endpoint de comparación `/api/v1/reports/comparison/{comparison_id}`.
