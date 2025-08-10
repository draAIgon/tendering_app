import React from 'react';

// Interfaces para el análisis
interface AnalysisData {
  status: string;
  document_id: string;
  analysis: {
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
        }
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
          sections: Record<string, {
            section_name: string;
            document_count: number;
            total_characters: number;
            content_preview: string;
            sources: string[];
            taxonomy_info: {
              keywords: string[];
              priority: number;
              description: string;
            }
          }>;
          confidence_scores: Record<string, number>;
          key_requirements: Record<string, string[]>;
        }
      };
      validation?: {
        status: string;
        data: {
          document_type: string;
          validation_timestamp: string;
          overall_score: number;
          validation_level: string;
          structural_validation: {
            document_type: string;
            total_sections_required: number;
            sections_found: number;
            sections_missing: number;
            missing_sections: string[];
            structural_issues: string[];
            completion_percentage: number;
            has_adequate_length: boolean;
            has_dates: boolean;
          };
          compliance_validation: {
            overall_compliance_percentage: number;
            total_rules: number;
            passed_rules: number;
            failed_rules: number;
            category_results: Record<string, {
              description: string;
              rules_checked: number;
              rules_passed: number;
              missing_rules: string[];
              found_rules: string[];
              compliance_percentage: number;
            }>;
            compliance_level: string;
          };
          dates_validation: {
            dates_found: number;
            deadlines_found: number;
            sample_dates: string[];
            sample_deadlines: string[][];
            date_issues: string[];
            has_adequate_dates: boolean;
          };
          recommendations: string[];
          summary: {
            total_issues: number;
            critical_issues: number;
            document_length: number;
            validation_success: boolean;
          }
        }
      };
      risk_analysis?: {
        status: string;
        data: {
          document_type: string;
          analysis_timestamp: string;
          content_length: number;
          category_risks: Record<string, {
            category: string;
            description: string;
            risk_score: number;
            risk_level: string;
            indicators_detected: number;
            total_mentions: number;
            detected_indicators: string[];
            risk_mentions: string[];
            semantic_risks: string[];
            weight: number;
          }>;
          overall_assessment: {
            total_risk_score: number;
            risk_level: string;
            risk_distribution: Record<string, number>;
            assessment_summary: string;
          };
          critical_risks: string[];
          mitigation_recommendations: string[];
          risk_matrix: {
            low_impact: Array<{
              category: string;
              score: number;
              level: string;
              indicators: number;
            }>;
            medium_impact: Array<{
              category: string;
              score: number;
              level: string;
              indicators: number;
            }>;
            high_impact: Array<{
              category: string;
              score: number;
              level: string;
              indicators: number;
            }>;
          }
        }
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
  };
  source: string;
}

interface DetailedAnalysisModalProps {
  showModal: boolean;
  onClose: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  uploadedFiles: File[];
  analysisData?: AnalysisData; // Datos del análisis del backend
  onExportReport: () => void;
}

export default function DetailedAnalysisModal({
  showModal,
  onClose,
  activeTab,
  setActiveTab,
  uploadedFiles,
  analysisData,
  onExportReport
}: DetailedAnalysisModalProps) {
  if (!showModal) return null;

  const tabs = [
    { id: 'overview', label: '📊 Resumen', icon: '📊' },
    { id: 'technical', label: '🔧 Técnico', icon: '🔧' },
    { id: 'financial', label: '💰 Financiero', icon: '💰' },
    { id: 'legal', label: '⚖️ Legal', icon: '⚖️' },
    { id: 'timeline', label: '⏱️ Cronograma', icon: '⏱️' },
    { id: 'risks', label: '⚠️ Riesgos', icon: '⚠️' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header del Modal */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            🔍 Análisis Detallado de Licitación
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
            <OverviewTab uploadedFiles={uploadedFiles} analysisData={analysisData} />
          )}

          {activeTab === 'technical' && (
            <TechnicalTab analysisData={analysisData} />
          )}

          {activeTab === 'financial' && (
            <FinancialTab analysisData={analysisData} />
          )}

          {activeTab === 'legal' && (
            <LegalTab analysisData={analysisData} />
          )}

          {activeTab === 'timeline' && (
            <TimelineTab analysisData={analysisData} />
          )}

          {activeTab === 'risks' && (
            <RisksTab analysisData={analysisData} />
          )}
        </div>

        {/* Footer del Modal */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Análisis generado el {new Date().toLocaleDateString('es-ES')} a las {new Date().toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'})}
          </span>
          <div className="flex space-x-3">
            <button
              onClick={onExportReport}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              📋 Exportar
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

// Componentes para cada tab
function OverviewTab({ uploadedFiles, analysisData }: { uploadedFiles: File[]; analysisData?: AnalysisData }) {
  const analysis = analysisData?.analysis;
  const completedStages = analysis?.summary?.completed_stages || 0;
  const totalStages = analysis?.summary?.total_stages || 4;
  const completionPercentage = totalStages > 0 ? Math.round((completedStages / totalStages) * 100) : 0;
  
  // Calcular distribución de tipos de documentos basado en classification
  const sections = analysis?.stages?.classification?.data?.sections || {};
  const totalSections = Object.keys(sections).length;
  
  return (
    <div className="space-y-6">
      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">📄 Documentos</h3>
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{uploadedFiles.length}</p>
          <p className="text-sm text-blue-700 dark:text-blue-300">Total analizados</p>
        </div>
        <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
          <h3 className="font-semibold text-green-800 dark:text-green-200 mb-2">✅ Completitud</h3>
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">{completionPercentage}%</p>
          <p className="text-sm text-green-700 dark:text-green-300">Etapas completadas</p>
        </div>
        <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
          <h3 className="font-semibold text-orange-800 dark:text-orange-200 mb-2">📊 Estado</h3>
          <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">{analysis?.summary?.overall_status || 'N/A'}</p>
          <p className="text-sm text-orange-700 dark:text-orange-300">Estado general</p>
        </div>
      </div>
      
      {/* Información del documento */}
      {analysis && (
        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-3">� Información del Análisis</h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Tipo de documento:</p>
              <p className="font-medium text-gray-900 dark:text-white">{analysis.document_type}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Nivel de análisis:</p>
              <p className="font-medium text-gray-900 dark:text-white">{analysis.analysis_level}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Timestamp:</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {new Date(analysis.timestamp).toLocaleString('es-ES')}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Secciones identificadas:</p>
              <p className="font-medium text-gray-900 dark:text-white">{totalSections}</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Resumen de hallazgos clave */}
      {analysis?.summary?.key_findings && analysis.summary.key_findings.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-3">🔍 Hallazgos Clave</h3>
          <ul className="space-y-2">
            {analysis.summary.key_findings.map((finding, index) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></span>
                <span className="text-sm text-blue-700 dark:text-blue-300">{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Errores si los hay */}
      {analysis?.errors && analysis.errors.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
          <h3 className="font-semibold text-red-800 dark:text-red-200 mb-3">❌ Errores Detectados</h3>
          <ul className="space-y-2">
            {analysis.errors.map((error, index) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></span>
                <span className="text-sm text-red-700 dark:text-red-300">{error}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function TechnicalTab({ analysisData }: { analysisData?: AnalysisData }) {
  const classification = analysisData?.analysis?.stages?.classification?.data;
  const sections = classification?.sections || {};
  const extraction = analysisData?.analysis?.stages?.extraction?.data;
  
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">🔧 Análisis Técnico</h3>
      
      {/* Información de extracción */}
      {extraction && (
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-3">📄 Extracción de Contenido</h4>
          <div className="space-y-2">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              <strong>Estado:</strong> {analysisData?.analysis?.stages?.extraction?.status}
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              <strong>Longitud del contenido:</strong> {extraction.content?.length || 0} caracteres
            </p>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h4 className="font-semibold text-gray-900 dark:text-white">📋 Secciones Identificadas</h4>
          {Object.keys(sections).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(sections).map(([key, section]) => (
                <div key={key} className="bg-white dark:bg-gray-700 p-3 rounded-lg border">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="font-medium text-gray-900 dark:text-white">{section.section_name}</h5>
                    <span className="text-xs bg-gray-100 dark:bg-gray-600 px-2 py-1 rounded">
                      {section.document_count} docs
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {section.total_characters} caracteres
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
                    {section.content_preview}
                  </p>
                  {section.taxonomy_info && (
                    <div className="mt-2">
                      <div className="flex flex-wrap gap-1">
                        {section.taxonomy_info.keywords?.slice(0, 3).map((keyword, idx) => (
                          <span key={idx} className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
                            {keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">No hay secciones clasificadas disponibles</p>
          )}
        </div>
        
        <div className="space-y-4">
          <h4 className="font-semibold text-gray-900 dark:text-white">📊 Métricas de Clasificación</h4>
          {classification?.document_info && (
            <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-green-700 dark:text-green-300">Total secciones:</span>
                  <span className="font-medium text-green-800 dark:text-green-200">
                    {classification.document_info.total_sections}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-green-700 dark:text-green-300">Total fragmentos:</span>
                  <span className="font-medium text-green-800 dark:text-green-200">
                    {classification.document_info.total_fragments}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-green-700 dark:text-green-300">Fuente:</span>
                  <span className="font-medium text-green-800 dark:text-green-200">
                    {classification.document_info.source}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Puntuaciones de confianza */}
          {classification?.confidence_scores && Object.keys(classification.confidence_scores).length > 0 && (
            <div className="space-y-3">
              <h5 className="font-medium text-gray-900 dark:text-white">🎯 Puntuaciones de Confianza</h5>
              {Object.entries(classification.confidence_scores).map(([section, score]) => (
                <div key={section} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400 truncate flex-1">{section}</span>
                  <div className="flex items-center space-x-2 ml-2">
                    <div className="w-16 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{width: `${Math.min(score, 100)}%`}}
                      ></div>
                    </div>
                    <span className="text-xs font-medium text-gray-900 dark:text-white w-10 text-right">
                      {Math.round(score )}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Requisitos clave */}
      {classification?.key_requirements && Object.keys(classification.key_requirements).length > 0 && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-3">📝 Requisitos Clave Identificados</h4>
          <div className="grid md:grid-cols-2 gap-4">
            {Object.entries(classification.key_requirements).map(([category, requirements]) => (
              <div key={category}>
                <h5 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">{category}</h5>
                <ul className="space-y-1">
                  {requirements.map((req, idx) => (
                    <li key={idx} className="text-sm text-yellow-700 dark:text-yellow-300 flex items-start">
                      <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                      {req}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function FinancialTab({ analysisData }: { analysisData?: AnalysisData }) {
  // Los datos financieros no están directamente en el JSON de análisis
  // pero podemos mostrar información relacionada con costos de análisis
  const analysis = analysisData?.analysis;
  const contentLength = analysisData?.analysis?.stages?.risk_analysis?.data?.content_length;
  
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">💰 Análisis Financiero</h3>
      
      <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
        <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-3">📊 Métricas del Análisis</h4>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-blue-700 dark:text-blue-300">Longitud del contenido:</p>
            <p className="font-medium text-blue-800 dark:text-blue-200">
              {contentLength ? `${contentLength.toLocaleString()} caracteres` : 'N/A'}
            </p>
          </div>
          <div>
            <p className="text-sm text-blue-700 dark:text-blue-300">Etapas completadas:</p>
            <p className="font-medium text-blue-800 dark:text-blue-200">
              {analysis?.summary?.completed_stages || 0} de {analysis?.summary?.total_stages || 0}
            </p>
          </div>
        </div>
      </div>

      {/* Placeholder para datos financieros reales */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-green-800 dark:text-green-200 mb-3">💹 Resumen Económico</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-green-700 dark:text-green-300">Estado del análisis:</span>
              <span className="font-medium text-green-800 dark:text-green-200">
                {analysis?.summary?.overall_status || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-green-700 dark:text-green-300">Documento analizado:</span>
              <span className="font-medium text-green-800 dark:text-green-200">
                {analysis?.document_type || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-green-700 dark:text-green-300">Nivel de análisis:</span>
              <span className="font-medium text-green-800 dark:text-green-200">
                {analysis?.analysis_level || 'N/A'}
              </span>
            </div>
          </div>
        </div>
        
        <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-3">⚠️ Nota</h4>
          <p className="text-sm text-yellow-700 dark:text-yellow-300">
            Los datos financieros específicos (presupuestos, costos, márgenes) necesitan ser 
            extraídos e integrados desde documentos financieros específicos. El análisis actual 
            se enfoca en la estructura y clasificación del documento.
          </p>
        </div>
      </div>

      {/* Recomendaciones relacionadas con finanzas */}
      {analysis?.summary?.recommendations && analysis.summary.recommendations.length > 0 && (
        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-3">💡 Recomendaciones</h4>
          <ul className="space-y-2">
            {analysis.summary.recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="w-2 h-2 bg-gray-500 rounded-full mt-2 flex-shrink-0"></span>
                <span className="text-sm text-gray-700 dark:text-gray-300">{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function LegalTab({ analysisData }: { analysisData?: AnalysisData }) {
  const validation = analysisData?.analysis?.stages?.validation?.data;
  const compliance = validation?.compliance_validation;
  const structural = validation?.structural_validation;
  const dates = validation?.dates_validation;
  
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">⚖️ Análisis Legal y Validación</h3>
      
      {/* Validación estructural */}
      {structural && (
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-3">🏗️ Validación Estructural</h4>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-blue-700 dark:text-blue-300">Tipo de documento:</p>
              <p className="font-medium text-blue-800 dark:text-blue-200">{structural.document_type}</p>
            </div>
            <div>
              <p className="text-sm text-blue-700 dark:text-blue-300">Porcentaje de completitud:</p>
              <p className="font-medium text-blue-800 dark:text-blue-200">{structural.completion_percentage}%</p>
            </div>
            <div>
              <p className="text-sm text-blue-700 dark:text-blue-300">Secciones encontradas:</p>
              <p className="font-medium text-blue-800 dark:text-blue-200">
                {structural.sections_found} de {structural.total_sections_required}
              </p>
            </div>
            <div>
              <p className="text-sm text-blue-700 dark:text-blue-300">Longitud adecuada:</p>
              <p className={`font-medium ${structural.has_adequate_length ? 'text-green-600' : 'text-red-600'}`}>
                {structural.has_adequate_length ? '✅ Sí' : '❌ No'}
              </p>
            </div>
          </div>
          
          {structural.missing_sections && structural.missing_sections.length > 0 && (
            <div className="mt-4">
              <h5 className="font-medium text-blue-800 dark:text-blue-200 mb-2">❌ Secciones faltantes:</h5>
              <ul className="space-y-1">
                {structural.missing_sections.map((section, index) => (
                  <li key={index} className="text-sm text-blue-700 dark:text-blue-300 flex items-center">
                    <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                    {section}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {structural.structural_issues && structural.structural_issues.length > 0 && (
            <div className="mt-4">
              <h5 className="font-medium text-blue-800 dark:text-blue-200 mb-2">⚠️ Problemas estructurales:</h5>
              <ul className="space-y-1">
                {structural.structural_issues.map((issue, index) => (
                  <li key={index} className="text-sm text-blue-700 dark:text-blue-300 flex items-start">
                    <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2 mt-1.5 flex-shrink-0"></span>
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Validación de cumplimiento */}
      {compliance && (
        <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-green-800 dark:text-green-200 mb-3">✅ Cumplimiento Normativo</h4>
          <div className="grid md:grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{compliance.overall_compliance_percentage.toFixed(1)}%</p>
              <p className="text-sm text-green-700 dark:text-green-300">Cumplimiento general</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{compliance.passed_rules}</p>
              <p className="text-sm text-green-700 dark:text-green-300">Reglas cumplidas</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600">{compliance.failed_rules}</p>
              <p className="text-sm text-green-700 dark:text-green-300">Reglas no cumplidas</p>
            </div>
          </div>
          
          <div className="mb-3">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              compliance.compliance_level === 'high' ? 'bg-green-100 text-green-800' :
              compliance.compliance_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              Nivel: {compliance.compliance_level}
            </span>
          </div>

          {compliance.category_results && Object.keys(compliance.category_results).length > 0 && (
            <div>
              <h5 className="font-medium text-green-800 dark:text-green-200 mb-3">📋 Resultados por categoría:</h5>
              <div className="space-y-3">
                {Object.entries(compliance.category_results).map(([category, result]) => (
                  <div key={category} className="bg-white dark:bg-gray-700 p-3 rounded border">
                    <div className="flex justify-between items-center mb-2">
                      <h6 className="font-medium text-gray-900 dark:text-white">{category}</h6>
                      <span className="text-sm font-medium text-green-600">
                        {result.compliance_percentage}%
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{result.description}</p>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {result.rules_passed} de {result.rules_checked} reglas cumplidas
                    </div>
                    
                    {result.missing_rules && result.missing_rules.length > 0 && (
                      <div className="mt-2">
                        <details className="text-sm">
                          <summary className="cursor-pointer text-red-600 hover:text-red-700">
                            Reglas faltantes ({result.missing_rules.length})
                          </summary>
                          <ul className="mt-1 ml-4 space-y-1">
                            {result.missing_rules.map((rule, idx) => (
                              <li key={idx} className="text-red-600">• {rule}</li>
                            ))}
                          </ul>
                        </details>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Validación de fechas */}
      {dates && (
        <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-purple-800 dark:text-purple-200 mb-3">📅 Validación de Fechas</h4>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-purple-700 dark:text-purple-300">Fechas encontradas:</p>
              <p className="font-medium text-purple-800 dark:text-purple-200">{dates.dates_found}</p>
            </div>
            <div>
              <p className="text-sm text-purple-700 dark:text-purple-300">Plazos encontrados:</p>
              <p className="font-medium text-purple-800 dark:text-purple-200">{dates.deadlines_found}</p>
            </div>
            <div>
              <p className="text-sm text-purple-700 dark:text-purple-300">Fechas adecuadas:</p>
              <p className={`font-medium ${dates.has_adequate_dates ? 'text-green-600' : 'text-red-600'}`}>
                {dates.has_adequate_dates ? '✅ Sí' : '❌ No'}
              </p>
            </div>
          </div>

          {dates.sample_dates && dates.sample_dates.length > 0 && (
            <div className="mt-4">
              <h5 className="font-medium text-purple-800 dark:text-purple-200 mb-2">📋 Fechas de muestra:</h5>
              <div className="flex flex-wrap gap-2">
                {dates.sample_dates.slice(0, 5).map((date, index) => (
                  <span key={index} className="text-xs bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 px-2 py-1 rounded">
                    {date}
                  </span>
                ))}
              </div>
            </div>
          )}

          {dates.date_issues && dates.date_issues.length > 0 && (
            <div className="mt-4">
              <h5 className="font-medium text-purple-800 dark:text-purple-200 mb-2">⚠️ Problemas con fechas:</h5>
              <ul className="space-y-1">
                {dates.date_issues.map((issue, index) => (
                  <li key={index} className="text-sm text-purple-700 dark:text-purple-300 flex items-start">
                    <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2 mt-1.5 flex-shrink-0"></span>
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Recomendaciones */}
      {validation?.recommendations && validation.recommendations.length > 0 && (
        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-3">💡 Recomendaciones Legales</h4>
          <ul className="space-y-2">
            {validation.recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></span>
                <span className="text-sm text-gray-700 dark:text-gray-300">{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Resumen de validación */}
      {validation?.summary && (
        <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-3">📊 Resumen de Validación</h4>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total de problemas:</p>
              <p className="font-medium text-gray-900 dark:text-white">{validation.summary.total_issues}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Problemas críticos:</p>
              <p className="font-medium text-red-600">{validation.summary.critical_issues}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Longitud del documento:</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {validation.summary.document_length?.toLocaleString()} caracteres
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Validación exitosa:</p>
              <p className={`font-medium ${validation.summary.validation_success ? 'text-green-600' : 'text-red-600'}`}>
                {validation.summary.validation_success ? '✅ Sí' : '❌ No'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function TimelineTab({ analysisData }: { analysisData?: AnalysisData }) {
  const validation = analysisData?.analysis?.stages?.validation?.data;
  const dates = validation?.dates_validation;
  const analysis = analysisData?.analysis;
  
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">⏱️ Cronograma y Fechas</h3>
      
      {/* Información del análisis */}
      {analysis && (
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-3">📅 Información del Análisis</h4>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-blue-700 dark:text-blue-300">Fecha del análisis:</p>
              <p className="font-medium text-blue-800 dark:text-blue-200">
                {new Date(analysis.timestamp).toLocaleString('es-ES')}
              </p>
            </div>
            <div>
              <p className="text-sm text-blue-700 dark:text-blue-300">Tipo de documento:</p>
              <p className="font-medium text-blue-800 dark:text-blue-200">{analysis.document_type}</p>
            </div>
          </div>
        </div>
      )}

      {/* Validación de fechas */}
      {dates && (
        <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-green-800 dark:text-green-200 mb-3">📋 Fechas Identificadas en el Documento</h4>
          <div className="grid md:grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{dates.dates_found}</p>
              <p className="text-sm text-green-700 dark:text-green-300">Fechas encontradas</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">{dates.deadlines_found}</p>
              <p className="text-sm text-green-700 dark:text-green-300">Plazos identificados</p>
            </div>
            <div className="text-center">
              <p className={`text-2xl font-bold ${dates.has_adequate_dates ? 'text-green-600' : 'text-red-600'}`}>
                {dates.has_adequate_dates ? '✅' : '❌'}
              </p>
              <p className="text-sm text-green-700 dark:text-green-300">Fechas adecuadas</p>
            </div>
          </div>

          {dates.sample_dates && dates.sample_dates.length > 0 && (
            <div className="mb-4">
              <h5 className="font-medium text-green-800 dark:text-green-200 mb-2">📅 Fechas de ejemplo:</h5>
              <div className="grid md:grid-cols-2 gap-2">
                {dates.sample_dates.map((date, index) => (
                  <div key={index} className="bg-white dark:bg-gray-700 p-2 rounded border">
                    <span className="text-sm text-gray-900 dark:text-white">{date}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {dates.sample_deadlines && dates.sample_deadlines.length > 0 && (
            <div className="mb-4">
              <h5 className="font-medium text-green-800 dark:text-green-200 mb-2">⏰ Plazos identificados:</h5>
              <div className="space-y-2">
                {dates.sample_deadlines.map((deadline, index) => (
                  <div key={index} className="bg-white dark:bg-gray-700 p-2 rounded border">
                    <span className="text-sm text-gray-900 dark:text-white">
                      {Array.isArray(deadline) ? deadline.join(' - ') : deadline}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {dates.date_issues && dates.date_issues.length > 0 && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg border-l-4 border-yellow-400">
              <h5 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">⚠️ Problemas con fechas:</h5>
              <ul className="space-y-1">
                {dates.date_issues.map((issue, index) => (
                  <li key={index} className="text-sm text-yellow-700 dark:text-yellow-300 flex items-start">
                    <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2 mt-1.5 flex-shrink-0"></span>
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Cronograma de las etapas del análisis */}
      <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg">
        <h4 className="font-semibold text-gray-900 dark:text-white mb-3">🔄 Progreso del Análisis</h4>
        <div className="space-y-3">
          {[
            { 
              etapa: 'Extracción', 
              estado: analysis?.stages?.extraction?.status || 'pendiente',
              descripcion: 'Extracción del contenido del documento'
            },
            { 
              etapa: 'Clasificación', 
              estado: analysis?.stages?.classification?.status || 'pendiente',
              descripcion: 'Clasificación y segmentación del contenido'
            },
            { 
              etapa: 'Validación', 
              estado: analysis?.stages?.validation?.status || 'pendiente',
              descripcion: 'Validación estructural y de cumplimiento'
            },
            { 
              etapa: 'Análisis de Riesgos', 
              estado: analysis?.stages?.risk_analysis?.status || 'pendiente',
              descripcion: 'Identificación y evaluación de riesgos'
            }
          ].map((item, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-white dark:bg-gray-700 rounded-lg border">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{item.etapa}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    item.estado === 'completed' || item.estado === 'success' ? 
                      'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                    item.estado === 'failed' || item.estado === 'error' ? 
                      'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                    item.estado === 'in_progress' || item.estado === 'processing' ?
                      'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                      'bg-gray-100 text-gray-800 dark:bg-gray-600 dark:text-gray-200'
                  }`}>
                    {item.estado}
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{item.descripcion}</p>
              </div>
              <div className="text-sm text-gray-400">
                {index + 1}/4
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Resumen temporal */}
      {analysis?.summary && (
        <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-purple-800 dark:text-purple-200 mb-3">📊 Resumen Temporal</h4>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-purple-700 dark:text-purple-300">Etapas completadas:</p>
              <p className="font-medium text-purple-800 dark:text-purple-200">
                {analysis.summary.completed_stages} de {analysis.summary.total_stages}
              </p>
            </div>
            <div>
              <p className="text-sm text-purple-700 dark:text-purple-300">Estado general:</p>
              <p className="font-medium text-purple-800 dark:text-purple-200">
                {analysis.summary.overall_status}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function RisksTab({ analysisData }: { analysisData?: AnalysisData }) {
  const riskAnalysis = analysisData?.analysis?.stages?.risk_analysis?.data;
  const categoryRisks = riskAnalysis?.category_risks || {};
  const overallAssessment = riskAnalysis?.overall_assessment;
  const riskMatrix = riskAnalysis?.risk_matrix;
  
  // Función para obtener color basado en el nivel de riesgo
  const getRiskColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'high': return 'text-red-600 bg-red-50 dark:bg-red-900/20';
      case 'medium': return 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20';
      case 'low': return 'text-green-600 bg-green-50 dark:bg-green-900/20';
      default: return 'text-gray-600 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">⚠️ Análisis de Riesgos</h3>
      
      {/* Resumen general */}
      {overallAssessment && (
        <div className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-3">📊 Evaluación General</h4>
          <div className="grid md:grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-700 dark:text-gray-300">
                {overallAssessment.total_risk_score?.toFixed(1) || 'N/A'}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Puntuación total</p>
            </div>
            <div className="text-center">
              <p className={`text-2xl font-bold ${
                overallAssessment.risk_level === 'high' ? 'text-red-600' :
                overallAssessment.risk_level === 'medium' ? 'text-yellow-600' :
                'text-green-600'
              }`}>
                {overallAssessment.risk_level?.toUpperCase() || 'N/A'}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Nivel de riesgo</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-700 dark:text-gray-300">
                {Object.keys(categoryRisks).length}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">Categorías analizadas</p>
            </div>
          </div>
          
          {overallAssessment.assessment_summary && (
            <div className="bg-white dark:bg-gray-600 p-3 rounded">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <strong>Resumen:</strong> {overallAssessment.assessment_summary}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Riesgos por categoría */}
      {Object.keys(categoryRisks).length > 0 && (
        <div className="space-y-4">
          <h4 className="font-semibold text-gray-900 dark:text-white">🎯 Riesgos por Categoría</h4>
          {Object.entries(categoryRisks).map(([category, risk]) => (
            <div key={category} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <h5 className="font-semibold text-gray-900 dark:text-white">{risk.category}</h5>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(risk.risk_level)}`}>
                    {risk.risk_level}
                  </span>
                  <span className="text-sm font-bold text-gray-700 dark:text-gray-300">
                    {risk.risk_score?.toFixed(1)}
                  </span>
                </div>
              </div>
              
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{risk.description}</p>
              
              <div className="grid md:grid-cols-2 gap-4 mb-3">
                <div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">Indicadores detectados:</span>
                  <span className="ml-2 text-sm font-medium text-gray-900 dark:text-white">
                    {risk.indicators_detected}
                  </span>
                </div>
                <div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">Total menciones:</span>
                  <span className="ml-2 text-sm font-medium text-gray-900 dark:text-white">
                    {risk.total_mentions}
                  </span>
                </div>
              </div>

              {risk.detected_indicators && risk.detected_indicators.length > 0 && (
                <div className="mb-3">
                  <h6 className="text-sm font-medium text-gray-900 dark:text-white mb-2">🔍 Indicadores:</h6>
                  <div className="flex flex-wrap gap-1">
                    {risk.detected_indicators.slice(0, 5).map((indicator, idx) => (
                      <span key={idx} className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
                        {indicator}
                      </span>
                    ))}
                    {risk.detected_indicators.length > 5 && (
                      <span className="text-xs text-gray-500">+{risk.detected_indicators.length - 5} más</span>
                    )}
                  </div>
                </div>
              )}

              {risk.risk_mentions && risk.risk_mentions.length > 0 && (
                <details className="mb-3">
                  <summary className="text-sm font-medium text-gray-900 dark:text-white cursor-pointer hover:text-blue-600">
                    Ver menciones de riesgo ({risk.risk_mentions.length})
                  </summary>
                  <div className="mt-2 space-y-1 max-h-32 overflow-y-auto">
                    {risk.risk_mentions.map((mention, idx) => (
                      <p key={idx} className="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700 p-2 rounded">
                        &ldquo;{mention}&rdquo;
                      </p>
                    ))}
                  </div>
                </details>
              )}

              {risk.semantic_risks && risk.semantic_risks.length > 0 && (
                <div>
                  <h6 className="text-sm font-medium text-gray-900 dark:text-white mb-2">🧠 Riesgos semánticos:</h6>
                  <ul className="space-y-1">
                    {risk.semantic_risks.map((semanticRisk, idx) => (
                      <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start">
                        <span className="w-1.5 h-1.5 bg-orange-500 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                        {semanticRisk}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Riesgos críticos */}
      {riskAnalysis?.critical_risks && riskAnalysis.critical_risks.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg border-l-4 border-red-500">
          <h4 className="font-semibold text-red-800 dark:text-red-200 mb-3">🚨 Riesgos Críticos</h4>
          <ul className="space-y-2">
            {riskAnalysis.critical_risks.map((risk, index) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></span>
                <span className="text-sm text-red-700 dark:text-red-300">{risk}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recomendaciones de mitigación */}
      {riskAnalysis?.mitigation_recommendations && riskAnalysis.mitigation_recommendations.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-3">💡 Recomendaciones de Mitigación</h4>
          <ul className="space-y-2">
            {riskAnalysis.mitigation_recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start space-x-2">
                <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></span>
                <span className="text-sm text-blue-700 dark:text-blue-300">{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Matriz de riesgos */}
      {riskMatrix && (
        <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-purple-800 dark:text-purple-200 mb-3">📋 Matriz de Riesgos por Impacto</h4>
          <div className="grid md:grid-cols-3 gap-4">
            {(['low_impact', 'medium_impact', 'high_impact'] as const).map((impactLevel) => {
              const risks = riskMatrix[impactLevel] || [];
              const impactLabel = impactLevel === 'low_impact' ? 'Bajo Impacto' : 
                                impactLevel === 'medium_impact' ? 'Impacto Medio' : 'Alto Impacto';
              const colorClass = impactLevel === 'low_impact' ? 'border-green-200' : 
                               impactLevel === 'medium_impact' ? 'border-yellow-200' : 'border-red-200';
              
              return (
                <div key={impactLevel} className={`border-2 ${colorClass} rounded-lg p-3`}>
                  <h5 className="font-medium text-gray-900 dark:text-white mb-2">{impactLabel}</h5>
                  {risks.length > 0 ? (
                    <div className="space-y-2">
                      {risks.map((risk, idx) => (
                        <div key={idx} className="text-sm bg-white dark:bg-gray-700 p-2 rounded">
                          <div className="font-medium text-gray-900 dark:text-white">{risk.category}</div>
                          <div className="text-xs text-gray-600 dark:text-gray-400">
                            Score: {risk.score?.toFixed(1)} | {risk.indicators} indicadores
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 dark:text-gray-400">No hay riesgos en esta categoría</p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Distribución de riesgos */}
      {overallAssessment?.risk_distribution && Object.keys(overallAssessment.risk_distribution).length > 0 && (
        <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-3">📈 Distribución de Riesgos</h4>
          <div className="space-y-2">
            {Object.entries(overallAssessment.risk_distribution).map(([category, percentage]) => (
              <div key={category} className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">{category}</span>
                <div className="flex items-center space-x-2">
                  <div className="w-32 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                    <div 
                      className="bg-gradient-to-r from-green-500 to-red-500 h-2 rounded-full" 
                      style={{width: `${Math.min(percentage * 100, 100)}%`}}
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-gray-900 dark:text-white w-12 text-right">
                    {(percentage * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
