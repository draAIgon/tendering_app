// API Client para TenderAI
import React from 'react';

const API_BASE_URL = 'https://hackiathon-api.nimblersoft.org';

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
  document_id: string;
  status: 'processing' | 'completed' | 'error';
  progress?: number;
  results?: {
    technical_analysis?: Record<string, unknown>;
    financial_analysis?: Record<string, unknown>;
    legal_analysis?: Record<string, unknown>;
    risk_analysis?: Record<string, unknown>;
    recommendations?: string[];
    summary?: Record<string, unknown>;
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
  report_id: string;
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
}

export const apiClient = new TenderAIApi();

// Función para testear que los logs funcionan
export const testDebugLogs = () => {
  debugLog('Test de logs de debug', { mensaje: 'Los logs están funcionando correctamente' });
  debugError('Test de logs de error', new Error('Este es un error de prueba'));
  console.log('Si ves los mensajes de arriba con emojis, los logs están funcionando');
};

// Hook personalizado para polling de resultados
export const useAnalysisPolling = (documentId: string | null, interval: number = 3000) => {
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
        const data = await apiClient.getAnalysisResult(documentId);
        setResult(data);
        
        // Si está completado o hay error, dejar de hacer polling
        if (data.status === 'completed' || data.status === 'error') {
          if (intervalId) clearInterval(intervalId);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
        debugError('Error en polling de análisis', {
          documentId: documentId,
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
  }, [documentId, interval]);

  return { result, isLoading, error };
};
