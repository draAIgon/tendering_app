'use client';

import React, { useState, useRef } from 'react';
import { apiClient, useAnalysisPolling } from '@/lib/api';
import { ProcessedData } from '@/types/dashboard';
import {
  Header,
  FileUploader,
  Sidebar,
  ResultsSection,
  DetailedAnalysisModal,
  ComparisonModal
} from '@/components/dashboard';

export default function Dashboard() {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedData, setProcessedData] = useState<ProcessedData | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [showDetailedModal, setShowDetailedModal] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [currentDocumentId, setCurrentDocumentId] = useState<string | null>(null);
  const [isComparison, setIsComparison] = useState(false);
  const [processingError, setProcessingError] = useState<string | null>(null);
  const [notification, setNotification] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
    visible: boolean;
  }>({ type: 'info', message: '', visible: false });
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Hook para polling de resultados
  const { result: analysisResult, isLoading: isPolling, error: pollingError } = useAnalysisPolling(currentDocumentId, isComparison);

  // Función para mostrar notificaciones
  const showNotification = (type: 'success' | 'error' | 'info', message: string) => {
    setNotification({ type, message, visible: true });
    setTimeout(() => {
      setNotification(prev => ({ ...prev, visible: false }));
    }, 4000); // Se oculta después de 4 segundos
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      setUploadedFiles(prev => [...prev, ...Array.from(files)]);
    }
  };

  const handleDragEnter = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    // Solo cambiar el estado si realmente salimos del contenedor
    if (!event.currentTarget.contains(event.relatedTarget as Node)) {
      setIsDragOver(false);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragOver(false);
    
    const droppedFiles = Array.from(event.dataTransfer.files);
    const validFiles = droppedFiles.filter(file => {
      const validTypes = ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx'];
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      return validTypes.includes(fileExtension);
    });
    
    if (validFiles.length > 0) {
      setUploadedFiles(prev => [...prev, ...validFiles]);
    }
    
    if (droppedFiles.length > validFiles.length) {
      showNotification('error', 'Algunos archivos no son compatibles. Solo se aceptan: PDF, DOC, DOCX, TXT, XLS, XLSX');
    }
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const processFiles = async () => {
    if (uploadedFiles.length === 0) return;
    
    setIsProcessing(true);
    setProcessingError(null);
    
    try {
      // Si hay múltiples archivos, usar upload múltiple
      if (uploadedFiles.length > 1) {
        const result = await apiClient.uploadMultipleDocuments(uploadedFiles);
        setCurrentDocumentId(result.comparison_id);
        setIsComparison(true);
      } else {
        // Un solo archivo
        const result = await apiClient.uploadAndAnalyzeDocument(uploadedFiles[0], {
          analysis_level: 'comprehensive',
          document_type: 'tender_document'
        });
        setCurrentDocumentId(result.document_id);
        setIsComparison(false);
      }
    } catch (error) {
      console.error('Error al procesar archivos:', error);
      setProcessingError(error instanceof Error ? error.message : 'Error desconocido');
      setIsProcessing(false);
    }
  };

  // Efecto para manejar los resultados del polling
  React.useEffect(() => {
    if (analysisResult && analysisResult.status === 'success') {
      // Manejar estructura diferente para comparación vs análisis individual
      let results: Record<string, unknown> | null = null;
      let summary: Record<string, unknown> | null = null;
      let riskAnalysis: Record<string, unknown> | null = null;
      let validation: Record<string, unknown> | null = null;
      let classification: Record<string, unknown> | null = null;
      let extraction: Record<string, unknown> | null = null;

      if (isComparison && analysisResult.comparison) {
        // Estructura de comparación
        const comparison = analysisResult.comparison;
        const analysisResults = comparison.analysis_results;
        
        // Tomar el primer documento como referencia para mostrar datos
        const firstDocKey = Object.keys(analysisResults)[0];
        if (firstDocKey) {
          const firstDoc = analysisResults[firstDocKey];
          results = firstDoc as Record<string, unknown>;
          summary = firstDoc.summary as Record<string, unknown>;
          
          // Extraer datos de las etapas
          const stages = firstDoc.stages;
          if (stages) {
            validation = stages.validation?.data as Record<string, unknown>;
            classification = stages.classification?.data as Record<string, unknown>;
            extraction = stages.extraction?.data as Record<string, unknown>;
            riskAnalysis = stages.risk_analysis?.data as Record<string, unknown>;
          }
        }
      } else {
        // Estructura de análisis individual (formato anterior)
        results = analysisResult.results || null;
        summary = results?.summary as Record<string, unknown>;
        riskAnalysis = results?.risk_analysis as Record<string, unknown>;

        // Si los resultados contienen análisis detallado en el formato esperado
        if (summary && typeof summary === 'object' && 'stages' in summary) {
          const stages = (summary as Record<string, unknown>).stages as Record<string, unknown>;
          if (stages) {
            validation = (stages.validation as Record<string, unknown>)?.data as Record<string, unknown>;
            classification = (stages.classification as Record<string, unknown>)?.data as Record<string, unknown>;
            extraction = (stages.extraction as Record<string, unknown>)?.data as Record<string, unknown>;
          }
        }
      }

      // Generar insights dinámicos basados en los datos reales
      const generateKeyInsights = () => {
        const insights: string[] = [];
        
        // Insights del resumen
        if (summary?.completed_stages && summary?.total_stages) {
          insights.push(`✅ Análisis completado: ${summary.completed_stages}/${summary.total_stages} etapas`);
        }
        
        // Insights específicos para comparación
        if (isComparison && analysisResult.comparison) {
          const comparison = analysisResult.comparison;
          const docsProcessed = comparison.system_status.documents_processed;
          const analysesCompleted = comparison.system_status.analyses_completed;
          insights.push(`📊 Comparación: ${docsProcessed} documentos procesados`);
          insights.push(`✅ Análisis completados: ${analysesCompleted}`);
        }
        
        // Insights de clasificación - con verificaciones de tipo seguras
        if (classification?.document_info && typeof classification.document_info === 'object') {
          const docInfo = classification.document_info as { total_sections?: number; total_fragments?: number };
          if (typeof docInfo.total_sections === 'number' && typeof docInfo.total_fragments === 'number') {
            insights.push(`📝 Documento clasificado: ${docInfo.total_sections} secciones y ${docInfo.total_fragments} fragmentos identificados`);
          }
        }
        
        // Insights de validación - con verificaciones de tipo seguras
        if (validation?.overall_score !== undefined && typeof validation.overall_score === 'number') {
          const score = validation.overall_score;
          const level = validation.validation_level;
          const levelStr = typeof level === 'string' ? level.replace('_', ' ') : 'desconocido';
          insights.push(`📋 Validación: ${score.toFixed(1)}/100 - ${levelStr}`);
        }
        
        // Insights de cumplimiento normativo - con verificaciones de tipo seguras
        if (validation?.compliance_validation && 
            typeof validation.compliance_validation === 'object' &&
            validation.compliance_validation !== null) {
          const complianceValidation = validation.compliance_validation as Record<string, unknown>;
          if (typeof complianceValidation.overall_compliance_percentage === 'number') {
            const compliance = complianceValidation.overall_compliance_percentage.toFixed(3);
            insights.push(`⚖️ Cumplimiento normativo: ${compliance}%`);
          }
        }
        
        // Insights de riesgos - con verificaciones de tipo seguras
        if (riskAnalysis?.overall_assessment && typeof riskAnalysis.overall_assessment === 'object') {
          const assessment = riskAnalysis.overall_assessment as Record<string, unknown>;
          if (typeof assessment.risk_level === 'string' && typeof assessment.total_risk_score === 'number') {
            const riskLevel = assessment.risk_level.replace('_', ' ');
            const riskScore = assessment.total_risk_score;
            insights.push(`⚠️ Nivel de riesgo: ${riskLevel} (${riskScore}/100)`);
          }
        }
        
        // Insights del contenido extraído - con verificaciones de tipo seguras
        if (extraction?.content && typeof extraction.content === 'string') {
          const contentLength = extraction.content.length;
          insights.push(`📄 Contenido extraído: ${Math.round(contentLength / 1000)}k caracteres procesados`);
        }
        
        // Insights por defecto si no hay datos específicos
        if (insights.length === 0) {
          insights.push(
            `📄 Documentos procesados: ${uploadedFiles.length}`,
            `🎯 Análisis completado con IA`,
            `📊 Resultados disponibles para revisión`
          );
        }
        
        return insights;
      };

      // Generar recomendaciones dinámicas - con verificaciones de tipo seguras
      const generateRecommendations = () => {
        const recommendations: string[] = [];
        
        // Recomendaciones del resumen
        if (summary?.recommendations && Array.isArray(summary.recommendations)) {
          recommendations.push(...summary.recommendations.slice(0, 3).map((rec: unknown) => 
            typeof rec === 'string' ? `💡 ${rec}` : '💡 Revisar recomendación'
          ));
        }
        
        // Recomendaciones de validación
        if (validation?.recommendations && Array.isArray(validation.recommendations)) {
          recommendations.push(...validation.recommendations.slice(0, 2).map((rec: unknown) => 
            typeof rec === 'string' ? `🔍 ${rec}` : '🔍 Revisar recomendación'
          ));
        }
        
        // Recomendaciones de riesgos
        if (riskAnalysis?.overall_assessment && typeof riskAnalysis.overall_assessment === 'object') {
          const assessment = riskAnalysis.overall_assessment as Record<string, unknown>;
          if (assessment.risk_level === 'HIGH' || assessment.risk_level === 'VERY_HIGH') {
            recommendations.push('⚠️ Revisar análisis de riesgos detallado - Nivel de riesgo elevado');
          }
        }
        
        // Recomendaciones basadas en cumplimiento
        if (validation?.compliance_validation && 
            typeof validation.compliance_validation === 'object' &&
            validation.compliance_validation !== null) {
          const complianceValidation = validation.compliance_validation as Record<string, unknown>;
          if (typeof complianceValidation.overall_compliance_percentage === 'number' &&
              complianceValidation.overall_compliance_percentage < 50) {
            recommendations.push('📋 Mejorar cumplimiento normativo - Puntuación baja detectada');
          }
        }
        
        // Recomendaciones por defecto
        if (recommendations.length === 0) {
          recommendations.push(
            '🔍 Revisar análisis técnico detallado',
            '📋 Consultar recomendaciones de mejora',
            '📈 Analizar resultados del análisis de riesgos'
          );
        }
        
        return recommendations;
      };

      // Convertir datos de la API al formato esperado por el UI
      const transformedData: ProcessedData = {
        documentId: analysisResult.document_id || analysisResult.comparison?.comparison_id || '',
        totalDocuments: uploadedFiles.length,
        analysisComplete: true,
        keyInsights: generateKeyInsights(),
        recommendedActions: generateRecommendations(),
        apiData: analysisResult as import('@/types/dashboard').AnalysisResult
      };
      
      setProcessedData(transformedData);
      setIsProcessing(false);
    } else if (analysisResult && analysisResult.status === 'error') {
      setProcessingError(analysisResult.error || 'Error en el análisis');
      setIsProcessing(false);
    }
  }, [analysisResult, uploadedFiles.length, isComparison]);

  // Efecto para manejar errores de polling
  React.useEffect(() => {
    if (pollingError) {
      setProcessingError(pollingError);
      setIsProcessing(false);
    }
  }, [pollingError]);

  const clearAll = () => {
    setUploadedFiles([]);
    setProcessedData(null);
    setCurrentDocumentId(null);
    setIsComparison(false);
    setProcessingError(null);
    setIsProcessing(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDetailedAnalysis = () => {
    setShowDetailedModal(true);
    setActiveTab('overview');
  };

  const handleExportReport = async () => {
    if (!processedData?.documentId) {
      showNotification('error', 'No hay datos para exportar');
      return;
    }

    try {
      const reportBlob = await apiClient.exportDocument(processedData.documentId, 'pdf');
      
      // Crear URL para descarga
      const url = window.URL.createObjectURL(reportBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reporte_licitacion_${processedData.documentId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      showNotification('success', '✅ Reporte exportado exitosamente');
    } catch (error) {
      console.error('Error al exportar:', error);
      showNotification('error', '❌ Error al exportar el reporte: ' + (error instanceof Error ? error.message : 'Error desconocido'));
    }
  };

  const handleGenerateReport = async () => {
    if (!processedData?.documentId) {
      showNotification('error', 'No hay datos para generar reporte');
      return;
    }

    try {
      showNotification('info', '🔄 Generando reporte PDF...');
      
      // Generar reporte en formato PDF
      const pdfReportBlob = await apiClient.generateReportAsFile(processedData.documentId, {
        report_type: 'comprehensive',
        include_charts: true,
        format: 'pdf'
      });
      
      // Crear URL para descarga del archivo PDF
      const url = window.URL.createObjectURL(pdfReportBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `reporte_licitacion_${processedData.documentId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      showNotification('success', '✅ Reporte PDF descargado exitosamente');
      
    } catch (error) {
      console.error('Error al generar reporte PDF:', error);
      showNotification('error', '❌ Error al generar el reporte PDF: ' + (error instanceof Error ? error.message : 'Error desconocido'));
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <Header />

      <div className="container mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-2">
            <FileUploader
              uploadedFiles={uploadedFiles}
              setUploadedFiles={setUploadedFiles}
              isProcessing={isProcessing}
              processingError={processingError}
              isDragOver={isDragOver}
              setIsDragOver={setIsDragOver}
              fileInputRef={fileInputRef}
              isPolling={isPolling}
              analysisResult={analysisResult as import('@/types/dashboard').AnalysisResult | null}
              onProcessFiles={processFiles}
              onClearAll={clearAll}
              onFileUpload={handleFileUpload}
              onDragEnter={handleDragEnter}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onRemoveFile={removeFile}
            />
          </div>

          {/* Sidebar */}
          <Sidebar
            uploadedFiles={uploadedFiles}
            processedData={processedData}
          />
        </div>

        {/* Results Section */}
        {processedData && (
          <ResultsSection
            processedData={processedData}
            onExportReport={handleExportReport}
            onGenerateReport={handleGenerateReport}
            onDetailedAnalysis={handleDetailedAnalysis}
          />
        )}
      </div>

      {/* Modal de Análisis Detallado - Condicional */}
      {!isComparison && (
        <DetailedAnalysisModal
          showModal={showDetailedModal}
          onClose={() => setShowDetailedModal(false)}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          uploadedFiles={uploadedFiles}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          analysisData={processedData?.apiData && !isComparison ? processedData.apiData as any : undefined}
          onExportReport={handleExportReport}
        />
      )}

      {/* Modal de Comparación - Condicional */}
      {isComparison && (
        <ComparisonModal
          showModal={showDetailedModal}
          onClose={() => setShowDetailedModal(false)}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          uploadedFiles={uploadedFiles}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          comparisonData={processedData?.apiData && isComparison ? processedData.apiData as any : undefined}
          onExportReport={handleExportReport}
        />
      )}

      {/* Componente de Notificación */}
      {notification.visible && (
        <div 
          className={`fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg border transform transition-all duration-300 ease-in-out ${
            notification.type === 'success' 
              ? 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900 dark:border-green-700 dark:text-green-100' 
              : notification.type === 'error'
              ? 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900 dark:border-red-700 dark:text-red-100'
              : 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900 dark:border-blue-700 dark:text-blue-100'
          } ${notification.visible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}`}
        >
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              {notification.type === 'success' && (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              )}
              {notification.type === 'error' && (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              )}
              {notification.type === 'info' && (
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium">
                {notification.message}
              </p>
            </div>
            <button
              onClick={() => setNotification(prev => ({ ...prev, visible: false }))}
              className="flex-shrink-0 ml-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
