// API Client para TenderAI
import React from 'react';

const API_BASE_URL = 'https://tenderai-dev-api.nimblersoft.org';

// Flag de debug - cambiar a false en producción
const DEBUG_MODE = true;

const debugLog = (message: string, data: unknown ) => {
  if (DEBUG_MODE) {
    console.group(`🔍 [API DEBUG] ${message}`);
    if (data !== null && data !== undefined) {
      console.log(data);
    }
    console.groupEnd();
  }
};

const debugError = (message: string, error?: unknown) => {
  if (DEBUG_MODE) {
    console.group(`❌ [API ERROR] ${message}`);
    if (error !== null && error !== undefined) {
      console.error(error);
    }
    console.groupEnd();
  }
};

export interface AnalysisRequest {
  document_type?: string;
  analysis_level?: string;
  provider?: string;
  force_rebuild?: boolean;
}

export interface UploadResponse {
  status: string;
  document_id: string;
  filename: string;
  analysis_level: string;
  provider_used: string;
  analysis_result: Record<string, unknown>;
  processing_time: string;
  api_version: string;
}

export interface AnalysisResult {
  document_id?: string;
  comparison_id?: string;
  status: 'processing' | 'success' | 'error';
  progress?: number;
  results?: {
    technical_analysis?: Record<string, unknown>;
    financial_analysis?: Record<string, unknown>;
    legal_analysis?: Record<string, unknown>;
    risk_analysis?: Record<string, unknown>;
    comparison_analysis?: Record<string, unknown>;
    recommendations?: string[];
    summary?: Record<string, unknown>;
  };
  comparison?: {
    comparison_id: string;
    system_status: {
      initialized: boolean;
      documents_processed: number;
      analyses_completed: number;
      agents_available: string[];
      data_directory: string;
      timestamp: string;
    };
    analysis_results: Record<string, {
      document_id: string;
      document_path: string;
      document_type: string;
      analysis_level: string;
      timestamp: string;
      stages: {
        extraction?: {
          status: string;
          data: {
            content: string;
            text: string;
          };
        };
        classification?: {
          status: string;
          data: {
            document_info: {
              source: string;
              total_sections: number;
              total_fragments: number;
              classification_timestamp: string;
            };
            sections: Record<string, unknown>;
            confidence_scores: Record<string, number>;
            key_requirements: Record<string, string[]>;
          };
        };
        validation?: {
          status: string;
          data: {
            document_type: string;
            validation_timestamp: string;
            overall_score: number;
            validation_level: string;
            structural_validation: Record<string, unknown>;
            compliance_validation: Record<string, unknown>;
            dates_validation: Record<string, unknown>;
            recommendations: string[];
            summary: Record<string, unknown>;
          };
        };
        risk_analysis?: {
          status: string;
          data: {
            document_type: string;
            analysis_timestamp: string;
            content_length: number;
            category_risks: Record<string, unknown>;
            overall_assessment: Record<string, unknown>;
            critical_risks: string[];
            mitigation_recommendations: string[];
            risk_matrix: Record<string, unknown>;
          };
        };
      };
      summary: {
        total_stages: number;
        completed_stages: number;
        failed_stages: number;
        overall_status: string;
        key_findings: string[];
        recommendations: string[];
      };
      errors: string[];
    }>;
  };
  error?: string;
}

export interface ComparisonRequest {
  comparison_criteria?: Record<string, unknown>;
  weights?: Record<string, number>;
}

export interface ComparisonResponse {
  status: string;
  comparison_id: string;
  files_compared: string[];
  comparison_result: Record<string, unknown>;
  processing_time: string;
}

export interface ReportRequest {
  report_type?: string;
  include_charts?: boolean;
  format?: string;
}

export interface ReportResponse {
  status?: string;
  document_id?: string;
  report_type?: string;
  report?: Record<string, unknown>;
  generated_at?: string;
  report_id?: string;
  download_url?: string;
  content?: Record<string, unknown>;
}

export interface SystemStatus {
  status: string;
  version: string;
  uptime: number;
  active_analyses: number;
}

class TenderAIApi {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async uploadAndAnalyzeDocument(
    file: File, 
    options: AnalysisRequest = {}
  ): Promise<UploadResponse> {
    debugLog('Iniciando upload de documento', { 
      fileName: file.name, 
      fileSize: file.size,
      fileType: file.type,
      options 
    });

    const formData = new FormData();
    formData.append('file', file);
    
    // Agregar parámetros opcionales como form data (no como query params)
    // El backend usa Depends() que espera form data
    if (options.document_type) {
      formData.append('document_type', options.document_type);
    }
    if (options.analysis_level) {
      formData.append('analysis_level', options.analysis_level || 'comprehensive');
    }
    if (options.provider) {
      formData.append('provider', options.provider || 'auto');
    }
    if (options.force_rebuild !== undefined) {
      formData.append('force_rebuild', options.force_rebuild.toString());
    }

    const url = `${this.baseUrl}/api/v1/analysis/upload`;
    debugLog('URL completa:', url);
    debugLog('FormData contents:', Object.fromEntries(formData.entries()));

    try {
      debugLog('Enviando petición POST con FormData', null);
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      debugLog('Respuesta recibida', { 
        status: response.status, 
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries())
      });

      if (!response.ok) {
        debugError('Respuesta HTTP no exitosa', {
          status: response.status,
          statusText: response.statusText,
          url: url
        });
        
        let errorMessage = `Error HTTP: ${response.status} ${response.statusText}`;
        
        try {
          const errorData = await response.json();
          debugError('Detalles del error del servidor', errorData);
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (parseError) {
          debugError('No se pudo parsear respuesta de error como JSON', parseError);
          // Intentar obtener como texto
          try {
            const errorText = await response.text();
            debugError('Respuesta de error como texto', errorText);
            if (errorText) {
              errorMessage = errorText;
            }
          } catch (textError) {
            debugError('No se pudo obtener respuesta como texto', textError);
          }
        }
        
        throw new Error(errorMessage);
      }

      const result = await response.json();
      debugLog('Upload exitoso', result);
      return result;
    } catch (error) {
      debugError('Error en uploadAndAnalyzeDocument', {
        error: error,
        errorMessage: error instanceof Error ? error.message : 'Error desconocido',
        errorStack: error instanceof Error ? error.stack : undefined,
        fileName: file.name,
        fileSize: file.size,
        options: options
      });
      throw error;
    }
  }

  async getAnalysisResult(documentId: string): Promise<AnalysisResult> {
    debugLog('Obteniendo resultado de análisis', { documentId });
    
    try {
      const url = `${this.baseUrl}/api/v1/analysis/${documentId}`;
      debugLog('URL de consulta:', url);
      
      const response = await fetch(url);
      
      debugLog('Respuesta de análisis recibida', { 
        status: response.status, 
        statusText: response.statusText 
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
        throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
      }

      const result = await response.json();
      debugLog('Resultado de análisis obtenido', result);
      return result;
    } catch (error) {
      debugError('Error en getAnalysisResult', error);
      throw error;
    }
  }

  async generateReport(documentId: string, options: ReportRequest = {}): Promise<ReportResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/reports/generate/${documentId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(options),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
      throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
    }

    return await response.json();
  }

  async generateReportAsFile(documentId: string, options: ReportRequest = {}): Promise<Blob> {
    debugLog('Generando reporte como archivo', { documentId, options });
    
    const response = await fetch(`${this.baseUrl}/api/v1/reports/generate/${documentId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(options),
    });

    debugLog('Respuesta de reporte recibida', { 
      status: response.status, 
      statusText: response.statusText,
      contentType: response.headers.get('content-type')
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
      throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
    }

    // Verificar si la respuesta es un archivo binario (PDF/HTML) o JSON
    const contentType = response.headers.get('content-type');
    if (contentType?.includes('application/pdf') || 
        contentType?.includes('text/html') || 
        contentType?.includes('application/octet-stream')) {
      // Es un archivo binario, devolver como blob
      const blob = await response.blob();
      debugLog('Reporte archivo recibido como blob', { 
        size: blob.size, 
        type: blob.type,
        contentType: contentType
      });
      return blob;
    } else {
      // Es JSON, no un archivo descargable
      const jsonResponse = await response.json();
      debugLog('Respuesta JSON recibida en lugar de archivo', jsonResponse);
      throw new Error('El servidor devolvió JSON en lugar de un archivo. Formato no soportado para descarga.');
    }
  }

  async exportDocument(documentId: string, format: string = 'pdf'): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/v1/documents/export/${documentId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ format }),
    });

    if (!response.ok) {
      throw new Error(`Error al exportar: ${response.status}`);
    }

    return await response.blob();
  }

  async getSystemStatus(): Promise<SystemStatus> {
    const response = await fetch(`${this.baseUrl}/api/v1/utils/system-status`);
    
    if (!response.ok) {
      throw new Error(`Error al obtener estado del sistema: ${response.status}`);
    }

    return await response.json();
  }

  async uploadMultipleDocuments(
    files: File[], 
    options: ComparisonRequest = {}
  ): Promise<ComparisonResponse> {
    debugLog('Iniciando upload de múltiples documentos', { 
      fileCount: files.length,
      fileNames: files.map(f => f.name),
      options
    });

    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    // Agregar parámetros opcionales como form data
    if (options.comparison_criteria) {
      formData.append('comparison_criteria', JSON.stringify(options.comparison_criteria));
    }
    if (options.weights) {
      formData.append('weights', JSON.stringify(options.weights));
    }

    const url = `${this.baseUrl}/api/v1/comparison/upload-multiple`;
    debugLog('URL de comparación:', url);

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      debugLog('Respuesta de comparación recibida', { 
        status: response.status, 
        statusText: response.statusText 
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
        throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
      }

      const result = await response.json();
      debugLog('Comparación exitosa', result);
      return result;
    } catch (error) {
      debugError('Error en uploadMultipleDocuments', error);
      throw error;
    }
  }

  async getComparisonResult(comparisonId: string): Promise<AnalysisResult> {
    debugLog('Obteniendo resultado de comparación', { comparisonId });
    
    try {
      const url = `${this.baseUrl}/api/v1/comparison/${comparisonId}`;
      debugLog('URL de consulta de comparación:', url);
      
      const response = await fetch(url);
      
      debugLog('Respuesta de comparación recibida', { 
        status: response.status, 
        statusText: response.statusText 
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Error desconocido' }));
        throw new Error(errorData.detail || `Error HTTP: ${response.status}`);
      }

      const result = await response.json();
      debugLog('Resultado de comparación obtenido', result);
      return result;
    } catch (error) {
      debugError('Error en getComparisonResult', error);
      throw error;
    }
  }
}

export const apiClient = new TenderAIApi();

// Función para testear que los logs funcionan
export const testDebugLogs = () => {
  debugLog('Test de logs de debug', { mensaje: 'Los logs están funcionando correctamente' });
  debugError('Test de logs de error', new Error('Este es un error de prueba'));
  console.log('Si ves los mensajes de arriba con emojis, los logs están funcionando');
};

// Hook personalizado para polling de resultados
export const useAnalysisPolling = (
  documentId: string | null, 
  isComparison: boolean = false,
  interval: number = 3000
) => {
  const [result, setResult] = React.useState<AnalysisResult | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!documentId) return;

    let intervalId: NodeJS.Timeout | null = null;
    
    const pollResult = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Usar el método correcto según el tipo de operación
        const data = isComparison 
          ? await apiClient.getComparisonResult(documentId)
          : await apiClient.getAnalysisResult(documentId);
          
        setResult(data);
        
        // Si está completado o hay error, dejar de hacer polling
        if (data.status === 'success' || data.status === 'error') {
          if (intervalId) clearInterval(intervalId);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
        debugError('Error en polling de análisis/comparación', {
          documentId: documentId,
          isComparison: isComparison,
          error: err,
          errorMessage: errorMessage
        });
        setError(errorMessage);
        if (intervalId) clearInterval(intervalId);
      } finally {
        setIsLoading(false);
      }
    };

    // Hacer polling inicial
    pollResult();
    
    // Configurar polling periódico
    intervalId = setInterval(pollResult, interval);

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [documentId, isComparison, interval]);

  return { result, isLoading, error };
};
