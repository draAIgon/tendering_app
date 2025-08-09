# Dashboard Components

Esta carpeta contiene los componentes refactorizados del Dashboard de TenderAI para hacer el código más modular y mantenible.

## Estructura de Componentes

### `Header.tsx`
- **Propósito**: Cabecera de la aplicación con el logo y navegación
- **Props**: Ninguna
- **Responsabilidad**: Mostrar el branding y título de la aplicación

### `FileUploader.tsx`
- **Propósito**: Maneja la subida de archivos con drag & drop
- **Props**:
  - `uploadedFiles`: Array de archivos subidos
  - `isProcessing`: Estado de procesamiento
  - `processingError`: Errores de procesamiento
  - `isDragOver`: Estado de drag over
  - `fileInputRef`: Referencia al input de archivo
  - `isPolling`: Estado de polling
  - `analysisResult`: Resultado del análisis
  - Múltiples handlers para eventos de drag & drop, upload, etc.
- **Responsabilidad**: UI de subida de archivos, validación, y progreso

### `Sidebar.tsx`
- **Propósito**: Panel lateral con estadísticas y actividad reciente
- **Props**:
  - `uploadedFiles`: Array de archivos subidos
  - `processedData`: Datos procesados
- **Responsabilidad**: Mostrar estadísticas del proyecto, actividad reciente y consejos

### `ResultsSection.tsx`
- **Propósito**: Muestra los resultados del análisis
- **Props**:
  - `processedData`: Datos procesados con insights y recomendaciones
  - `onExportReport`: Función para exportar reporte
  - `onDetailedAnalysis`: Función para mostrar análisis detallado
- **Responsabilidad**: Presentar insights y recomendaciones del análisis

### `DetailedAnalysisModal.tsx`
- **Propósito**: Modal con análisis detallado en pestañas
- **Props**:
  - `showModal`: Estado de visibilidad del modal
  - `onClose`: Función para cerrar el modal
  - `activeTab`: Pestaña activa
  - `setActiveTab`: Función para cambiar pestaña
  - `uploadedFiles`: Array de archivos
  - `onExportReport`: Función para exportar
- **Responsabilidad**: Mostrar análisis detallado en categorías (técnico, financiero, legal, etc.)

## Tipos Compartidos

Los tipos están definidos en `@/types/dashboard.ts`:

- `AnalysisResult`: Resultado del análisis de la API
- `ProcessedData`: Datos procesados para el UI

## Ventajas de esta Refactorización

1. **Separación de Responsabilidades**: Cada componente tiene una responsabilidad específica
2. **Reutilización**: Los componentes pueden ser reutilizados en otras partes de la aplicación
3. **Mantenibilidad**: Es más fácil encontrar y modificar funcionalidad específica
4. **Testing**: Cada componente puede ser testado de forma independiente
5. **Legibilidad**: El código es más fácil de leer y entender
6. **Tipado**: Mejor tipado con TypeScript para prevenir errores

## Uso

```tsx
import {
  Header,
  FileUploader,
  Sidebar,
  ResultsSection,
  DetailedAnalysisModal
} from '@/components/dashboard';

// Usar los componentes en tu página
```

## Estructura del Archivo Principal

El componente `Dashboard` en `page.tsx` ahora es mucho más limpio y actúa como un coordinador entre los componentes, manejando el estado global y pasando props a los componentes hijos.
