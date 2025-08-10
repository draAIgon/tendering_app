import React from 'react';

// Interface específica para datos de comparación
interface ComparisonData {
  document_id?: string;
  comparison_id?: string;
  status: string;
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
}

interface ComparisonModalProps {
  showModal: boolean;
  onClose: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  uploadedFiles: File[];
  comparisonData?: ComparisonData;
  onExportReport: () => void;
}

export default function ComparisonModal({
  showModal,
  onClose,
  activeTab,
  setActiveTab,
  uploadedFiles,
  comparisonData,
  onExportReport
}: ComparisonModalProps) {
  if (!showModal) return null;

  const tabs = [
    { id: 'overview', label: '📊 Resumen', icon: '📊' },
    { id: 'comparison', label: '🔄 Comparación', icon: '🔄' },
    { id: 'documents', label: '📄 Documentos', icon: '📄' },
    { id: 'risks', label: '⚠️ Riesgos', icon: '⚠️' },
    { id: 'recommendations', label: '💡 Recomendaciones', icon: '💡' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header del Modal */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            🔄 Comparación Detallada de Documentos
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs Navigation */}
        <div className="flex border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-white dark:bg-gray-800'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Contenido del Modal */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {activeTab === 'overview' && (
            <ComparisonOverviewTab uploadedFiles={uploadedFiles} comparisonData={comparisonData} />
          )}

          {activeTab === 'comparison' && (
            <ComparisonDetailsTab comparisonData={comparisonData} />
          )}

          {activeTab === 'documents' && (
            <DocumentsTab comparisonData={comparisonData} />
          )}

          {activeTab === 'risks' && (
            <ComparisonRisksTab comparisonData={comparisonData} />
          )}

          {activeTab === 'recommendations' && (
            <RecommendationsTab comparisonData={comparisonData} />
          )}
        </div>

        {/* Footer del Modal */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Comparación generada el {new Date().toLocaleDateString('es-ES')} a las {new Date().toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'})}
          </span>
          <div className="flex space-x-3">
            <button
              onClick={onExportReport}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              📋 Exportar Comparación
            </button>
            <button
              onClick={onClose}
              className="border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Componentes para cada tab de comparación
function ComparisonOverviewTab({ uploadedFiles, comparisonData }: { uploadedFiles: File[]; comparisonData?: ComparisonData }) {
  const comparison = comparisonData?.comparison;
  const systemStatus = comparison?.system_status;
  const analysisResults = comparison?.analysis_results || {};
  const documentsAnalyzed = Object.keys(analysisResults).length;

  return (
    <div className="space-y-6">
      <div className="grid md:grid-cols-4 gap-6">
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">📄 Documentos</h3>
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{uploadedFiles.length}</p>
          <p className="text-sm text-blue-700 dark:text-blue-300">Subidos</p>
        </div>
        <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
          <h3 className="font-semibold text-green-800 dark:text-green-200 mb-2">✅ Procesados</h3>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">{systemStatus?.documents_processed || documentsAnalyzed}</p>
          <p className="text-sm text-green-700 dark:text-green-300">Completados</p>
        </div>
        <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
          <h3 className="font-semibold text-orange-800 dark:text-orange-200 mb-2">📊 Análisis</h3>
          <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{systemStatus?.analyses_completed || 0}</p>
          <p className="text-sm text-orange-700 dark:text-orange-300">Realizados</p>
        </div>
        <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
          <h3 className="font-semibold text-purple-800 dark:text-purple-200 mb-2">🤖 Agentes</h3>
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{systemStatus?.agents_available?.length || 0}</p>
          <p className="text-sm text-purple-700 dark:text-purple-300">Disponibles</p>
        </div>
      </div>

      {/* Estado del sistema */}
      {systemStatus && (
        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-3">🖥️ Estado del Sistema</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Inicializado:</p>
              <p className={`font-medium ${systemStatus.initialized ? 'text-green-600' : 'text-red-600'}`}>
                {systemStatus.initialized ? '✅ Sí' : '❌ No'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Timestamp:</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {new Date(systemStatus.timestamp).toLocaleString('es-ES')}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Directorio de datos:</p>
              <p className="font-medium text-gray-900 dark:text-white text-xs">{systemStatus.data_directory}</p>
            </div>
          </div>
        </div>
      )}

      {/* Resumen de documentos analizados */}
      {Object.keys(analysisResults).length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-3">📋 Resumen de Análisis</h3>
          <div className="space-y-3">
            {Object.entries(analysisResults).map(([docId, result]) => (
              <div key={docId} className="bg-white dark:bg-gray-700 p-3 rounded border">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-medium text-gray-900 dark:text-white">{result.document_type}</h4>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    result.summary.overall_status === 'completed' ? 'bg-green-100 text-green-800' :
                    result.summary.overall_status === 'failed' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {result.summary.overall_status}
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  Etapas: {result.summary.completed_stages}/{result.summary.total_stages}
                </p>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Análisis: {result.analysis_level} | {new Date(result.timestamp).toLocaleString('es-ES')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ComparisonDetailsTab({ comparisonData }: { comparisonData?: ComparisonData }) {
  const analysisResults = comparisonData?.comparison?.analysis_results || {};
  
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">🔄 Detalles de Comparación</h3>
      
      {Object.keys(analysisResults).length > 0 && (
        <div className="grid md:grid-cols-2 gap-6">
          {Object.entries(analysisResults).map(([docId, result]) => (
            <div key={docId} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-3">{result.document_type}</h4>
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Estado:</span>
                  <span className="text-sm font-medium">{result.summary.overall_status}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Progreso:</span>
                  <span className="text-sm font-medium">
                    {Math.round((result.summary.completed_stages / result.summary.total_stages) * 100)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Errores:</span>
                  <span className="text-sm font-medium text-red-600">{result.errors.length}</span>
                </div>
              </div>

              {result.summary.key_findings.length > 0 && (
                <div className="mt-3">
                  <h5 className="text-sm font-medium text-gray-900 dark:text-white mb-2">🔍 Hallazgos:</h5>
                  <ul className="space-y-1">
                    {result.summary.key_findings.slice(0, 3).map((finding, idx) => (
                      <li key={idx} className="text-xs text-gray-600 dark:text-gray-400 flex items-start">
                        <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                        {finding}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function DocumentsTab({ comparisonData }: { comparisonData?: ComparisonData }) {
  const analysisResults = comparisonData?.comparison?.analysis_results || {};
  
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">📄 Análisis Individual de Documentos</h3>
      
      {Object.keys(analysisResults).length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-500 dark:text-gray-400">No hay documentos analizados disponibles</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(analysisResults).map(([docId, result]) => (
            <div key={docId} className="border border-gray-200 dark:border-gray-600 rounded-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white">{result.document_type}</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{result.document_path}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  result.summary.overall_status === 'completed' ? 'bg-green-100 text-green-800' :
                  result.summary.overall_status === 'failed' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {result.summary.overall_status}
                </span>
              </div>

              {/* Progreso de etapas */}
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-1">
                  <span>Progreso de análisis</span>
                  <span>{result.summary.completed_stages}/{result.summary.total_stages}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{width: `${(result.summary.completed_stages / result.summary.total_stages) * 100}%`}}
                  ></div>
                </div>
              </div>

              {/* Hallazgos clave */}
              {result.summary.key_findings.length > 0 && (
                <div className="mb-4">
                  <h5 className="font-medium text-gray-900 dark:text-white mb-2">🔍 Hallazgos Clave</h5>
                  <ul className="space-y-1">
                    {result.summary.key_findings.map((finding, idx) => (
                      <li key={idx} className="text-sm text-gray-600 dark:text-gray-400 flex items-start">
                        <span className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                        {finding}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recomendaciones */}
              {result.summary.recommendations.length > 0 && (
                <div className="mb-4">
                  <h5 className="font-medium text-gray-900 dark:text-white mb-2">💡 Recomendaciones</h5>
                  <ul className="space-y-1">
                    {result.summary.recommendations.map((rec, idx) => (
                      <li key={idx} className="text-sm text-gray-600 dark:text-gray-400 flex items-start">
                        <span className="w-2 h-2 bg-green-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Errores */}
              {result.errors.length > 0 && (
                <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                  <h5 className="font-medium text-red-800 dark:text-red-200 mb-2">❌ Errores ({result.errors.length})</h5>
                  <ul className="space-y-1">
                    {result.errors.map((error, idx) => (
                      <li key={idx} className="text-sm text-red-700 dark:text-red-300 flex items-start">
                        <span className="w-2 h-2 bg-red-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                        {error}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ComparisonRisksTab({ comparisonData }: { comparisonData?: ComparisonData }) {
  const analysisResults = comparisonData?.comparison?.analysis_results || {};
  
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">⚠️ Análisis de Riesgos Comparativo</h3>
      
      {Object.keys(analysisResults).length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-500 dark:text-gray-400">No hay análisis de riesgos disponibles</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(analysisResults).map(([docId, result]) => {
            const riskData = result.stages.risk_analysis?.data;
            if (!riskData) return null;

            const overallAssessment = riskData.overall_assessment as {
              total_risk_score?: number;
              risk_level?: string;
              assessment_summary?: string;
            };

            return (
              <div key={docId} className="border border-gray-200 dark:border-gray-600 rounded-lg p-6">
                <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  {result.document_type} - Análisis de Riesgos
                </h4>

                {overallAssessment && (
                  <div className="grid md:grid-cols-3 gap-4 mb-4">
                    <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg text-center">
                      <p className="text-2xl font-bold text-gray-700 dark:text-gray-300">
                        {overallAssessment.total_risk_score?.toFixed(1) || 'N/A'}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Puntuación de Riesgo</p>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg text-center">
                      <p className={`text-2xl font-bold ${
                        overallAssessment.risk_level === 'HIGH' ? 'text-red-600' :
                        overallAssessment.risk_level === 'MEDIUM' ? 'text-yellow-600' :
                        'text-green-600'
                      }`}>
                        {overallAssessment.risk_level || 'N/A'}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Nivel de Riesgo</p>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg text-center">
                      <p className="text-2xl font-bold text-gray-700 dark:text-gray-300">
                        {riskData.critical_risks?.length || 0}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Riesgos Críticos</p>
                    </div>
                  </div>
                )}

                {riskData.critical_risks && riskData.critical_risks.length > 0 && (
                  <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg mb-4">
                    <h5 className="font-semibold text-red-800 dark:text-red-200 mb-2">🚨 Riesgos Críticos</h5>
                    <ul className="space-y-1">
                      {riskData.critical_risks.map((risk, idx) => (
                        <li key={idx} className="text-sm text-red-700 dark:text-red-300 flex items-start">
                          <span className="w-2 h-2 bg-red-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                          {risk}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {riskData.mitigation_recommendations && riskData.mitigation_recommendations.length > 0 && (
                  <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                    <h5 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">💡 Recomendaciones de Mitigación</h5>
                    <ul className="space-y-1">
                      {riskData.mitigation_recommendations.map((rec, idx) => (
                        <li key={idx} className="text-sm text-blue-700 dark:text-blue-300 flex items-start">
                          <span className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function RecommendationsTab({ comparisonData }: { comparisonData?: ComparisonData }) {
  const analysisResults = comparisonData?.comparison?.analysis_results || {};
  
  // Usar un Map para evitar duplicados y consolidar recomendaciones
  const recommendationsMap = new Map<string, { 
    docType: string; 
    category: string;
    recommendations: Set<string>;
  }>();
  
  Object.entries(analysisResults).forEach(([, result]) => {
    const docType = result.document_type;
    
    // Función helper para agregar recomendaciones al map
    const addRecommendations = (category: string, recs: string[]) => {
      const key = `${docType}-${category}`;
      if (!recommendationsMap.has(key)) {
        recommendationsMap.set(key, {
          docType,
          category,
          recommendations: new Set()
        });
      }
      recs.forEach(rec => {
        if (rec && rec.trim()) { // Solo agregar recomendaciones no vacías
          recommendationsMap.get(key)!.recommendations.add(rec.trim());
        }
      });
    };
    
    // Recomendaciones del resumen general
    if (result.summary.recommendations && Array.isArray(result.summary.recommendations)) {
      addRecommendations('Resumen General', result.summary.recommendations);
    }
    
    // Recomendaciones de validación
    if (result.stages.validation?.data?.recommendations && 
        Array.isArray(result.stages.validation.data.recommendations)) {
      addRecommendations('Validación', result.stages.validation.data.recommendations as string[]);
    }
    
    // Recomendaciones de análisis de riesgos
    if (result.stages.risk_analysis?.data?.mitigation_recommendations && 
        Array.isArray(result.stages.risk_analysis.data.mitigation_recommendations)) {
      addRecommendations('Mitigación de Riesgos', result.stages.risk_analysis.data.mitigation_recommendations as string[]);
    }
    
    // Revisar si hay recomendaciones en clasificación
    if (result.stages.classification?.data && 
        typeof result.stages.classification.data === 'object') {
      const classData = result.stages.classification.data as Record<string, unknown>;
      
      // Buscar recomendaciones en diferentes posibles ubicaciones
      if (classData.recommendations && Array.isArray(classData.recommendations)) {
        addRecommendations('Clasificación', classData.recommendations as string[]);
      }
      
      // Revisar si hay recomendaciones en key_requirements
      if (classData.key_requirements && typeof classData.key_requirements === 'object') {
        const keyReqs = classData.key_requirements as Record<string, string[]>;
        Object.entries(keyReqs).forEach(([section, reqs]) => {
          if (Array.isArray(reqs) && reqs.length > 0) {
            addRecommendations(`Requisitos - ${section}`, reqs);
          }
        });
      }
    }
  });

  // Convertir el Map a array y filtrar solo los que tienen recomendaciones
  const allRecommendations = Array.from(recommendationsMap.values())
    .filter(section => section.recommendations.size > 0)
    .map(section => ({
      ...section,
      recommendations: Array.from(section.recommendations)
    }));

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">💡 Recomendaciones Consolidadas</h3>
      
      {allRecommendations.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-500 dark:text-gray-400">No hay recomendaciones disponibles</p>
        </div>
      ) : (
        <div className="space-y-6">
          {allRecommendations.map((section, index) => (
            <div key={index} className="bg-blue-50 dark:bg-blue-900/20 p-6 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-semibold text-blue-800 dark:text-blue-200">
                  📄 {section.docType}
                </h4>
                <span className="px-3 py-1 bg-blue-200 dark:bg-blue-700 text-blue-800 dark:text-blue-200 text-xs font-medium rounded-full">
                  {section.category}
                </span>
              </div>
              <ul className="space-y-3">
                {section.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start space-x-3">
                    <span className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <span className="text-sm text-blue-700 dark:text-blue-300">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
          
          {/* Resumen general */}
          <div className="bg-gray-50 dark:bg-gray-700/50 p-6 rounded-lg">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3">📊 Resumen de Recomendaciones</h4>
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Documentos analizados:</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {new Set(allRecommendations.map(r => r.docType)).size}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Categorías de recomendaciones:</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {new Set(allRecommendations.map(r => r.category)).size}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total de recomendaciones:</p>
                <p className="font-medium text-gray-900 dark:text-white">
                  {allRecommendations.reduce((total, section) => total + section.recommendations.length, 0)}
                </p>
              </div>
            </div>
            
            {/* Lista de categorías encontradas */}
            <div className="mt-4">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Categorías encontradas:</p>
              <div className="flex flex-wrap gap-2">
                {Array.from(new Set(allRecommendations.map(r => r.category))).map((category, idx) => (
                  <span key={idx} className="px-2 py-1 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 text-xs rounded">
                    {category}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
