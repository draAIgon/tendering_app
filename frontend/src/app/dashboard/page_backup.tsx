'use client';

import React, { useState, useRef } from 'react';
import { apiClient, useAnalysisPolling } from '@/lib/api';
import { Pro        // Insights de clasificación
        if (classification?.document_info && typeof classification.document_info === 'object') {
          const docInfo = classification.document_info as { total_sections?: number; total_fragments?: number };
          if (docInfo.total_sections && docInfo.total_fragments) {
            insights.push(`📝 Documento clasificado: ${docInfo.total_sections} secciones y ${docInfo.total_fragments} fragmentos identificados`);
          }
        }dData } from '@/types/dashboard';
import {
  Header,
  FileUploader,
  Sidebar,
  ResultsSection,
  DetailedAnalysisModal
} from '@/components/dashboard';

export default function Dashboard() {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedData, setProcessedData] = useState<ProcessedData | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [showDetailedModal, setShowDetailedModal] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [currentDocumentId, setCurrentDocumentId] = useState<string | null>(null);
  const [processingError, setProcessingError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

  // Hook para polling de resultados
  const { result: analysisResult, isLoading: isPolling, error: pollingError } = useAnalysisPolling(currentDocumentId);

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
      alert('Algunos archivos no son compatibles. Solo se aceptan: PDF, DOC, DOCX, TXT, XLS, XLSX');
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
      } else {
        // Un solo archivo
        const result = await apiClient.uploadAndAnalyzeDocument(uploadedFiles[0], {
          analysis_level: 'comprehensive',
          document_type: 'tender_document'
        });
        setCurrentDocumentId(result.document_id);
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
      // Extraer datos específicos del análisis desde la estructura real de la API
      const results = analysisResult.results;
      const summary = results?.summary as Record<string, unknown>;
      const riskAnalysis = results?.risk_analysis as Record<string, unknown>;

      // Intentar extraer datos más específicos si están estructurados como el JSON de ejemplo
      let detailedAnalysis: Record<string, unknown> | null = null;
      let validation: Record<string, unknown> | null = null;
      let classification: Record<string, unknown> | null = null;
      let extraction: Record<string, unknown> | null = null;

      // Si los resultados contienen análisis detallado en el formato esperado
      if (summary && typeof summary === 'object' && 'stages' in summary) {
        detailedAnalysis = summary;
        const stages = (detailedAnalysis as Record<string, unknown>).stages as Record<string, unknown>;
        if (stages) {
          validation = (stages.validation as Record<string, unknown>)?.data as Record<string, unknown>;
          classification = (stages.classification as Record<string, unknown>)?.data as Record<string, unknown>;
          extraction = (stages.extraction as Record<string, unknown>)?.data as Record<string, unknown>;
        }
      }

      // Generar insights dinámicos basados en los datos reales
      const generateKeyInsights = () => {
        const insights: string[] = [];
        
        // Insights del resumen
        if (summary?.completed_stages && summary?.total_stages) {
          insights.push(`✅ Análisis completado: ${summary.completed_stages}/${summary.total_stages} etapas`);
        }
        
        // Insights de clasificación
        if (classification?.document_info) {
          const { total_sections, total_fragments } = classification.document_info;
          insights.push(`� Documento clasificado: ${total_sections} secciones y ${total_fragments} fragmentos identificados`);
        }
        
        // Insights de validación
        if (validation?.overall_score !== undefined) {
          const score = validation.overall_score;
          const level = validation.validation_level;
          insights.push(`📋 Validación: ${score.toFixed(1)}/100 - ${level?.replace('_', ' ')}`);
        }
        
        if (validation?.compliance_validation?.overall_compliance_percentage !== undefined) {
          const compliance = validation.compliance_validation.overall_compliance_percentage;
          insights.push(`⚖️ Cumplimiento normativo: ${compliance.toFixed(1)}%`);
        }
        
        // Insights de riesgos
        if (riskAnalysis?.overall_assessment) {
          const riskLevel = riskAnalysis.overall_assessment.risk_level;
          const riskScore = riskAnalysis.overall_assessment.total_risk_score;
          insights.push(`⚠️ Nivel de riesgo: ${riskLevel?.replace('_', ' ')} (${riskScore}/100)`);
        }
        
        // Insights del contenido extraído
        if (extraction?.content) {
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

      // Generar recomendaciones dinámicas
      const generateRecommendations = () => {
        const recommendations: string[] = [];
        
        // Recomendaciones del resumen
        if (summary?.recommendations && summary.recommendations.length > 0) {
          recommendations.push(...summary.recommendations.slice(0, 3).map((rec: string) => `💡 ${rec}`));
        }
        
        // Recomendaciones de validación
        if (validation?.recommendations && validation.recommendations.length > 0) {
          recommendations.push(...validation.recommendations.slice(0, 2).map((rec: string) => `🔍 ${rec}`));
        }
        
        // Recomendaciones de riesgos
        if (riskAnalysis?.overall_assessment?.risk_level === 'HIGH' || riskAnalysis?.overall_assessment?.risk_level === 'VERY_HIGH') {
          recommendations.push('⚠️ Revisar análisis de riesgos detallado - Nivel de riesgo elevado');
        }
        
        // Recomendaciones basadas en cumplimiento
        if (validation?.compliance_validation?.overall_compliance_percentage && validation.compliance_validation.overall_compliance_percentage < 50) {
          recommendations.push('📋 Mejorar cumplimiento normativo - Puntuación baja detectada');
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
        documentId: analysisResult.document_id,
        totalDocuments: uploadedFiles.length,
        analysisComplete: true,
        keyInsights: generateKeyInsights(),
        recommendedActions: generateRecommendations(),
        apiData: analysisResult
      };
      
      setProcessedData(transformedData);
      setIsProcessing(false);
    } else if (analysisResult && analysisResult.status === 'error') {
      setProcessingError(analysisResult.error || 'Error en el análisis');
      setIsProcessing(false);
    }
  }, [analysisResult, uploadedFiles.length]);

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
      alert('No hay datos para exportar');
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
      
      alert('✅ Reporte exportado exitosamente');
    } catch (error) {
      console.error('Error al exportar:', error);
      alert('❌ Error al exportar el reporte: ' + (error instanceof Error ? error.message : 'Error desconocido'));
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
              analysisResult={analysisResult}
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
            onDetailedAnalysis={handleDetailedAnalysis}
          />
        )}
      </div>

      {/* Modal de Análisis Detallado */}
      <DetailedAnalysisModal
        showModal={showDetailedModal}
        onClose={() => setShowDetailedModal(false)}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        uploadedFiles={uploadedFiles}
        onExportReport={handleExportReport}
      />
    </div>
  );
}