import React from 'react';
import { ProcessedData } from '@/types/dashboard';

interface ResultsSectionProps {
  processedData: ProcessedData;
  onGenerateReport: () => void;
  onDetailedAnalysis: () => void;
}

// Helper function to get validation level color
const getValidationLevelColor = (level: string) => {
  switch (level) {
    case 'APROBADO':
      return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
    case 'APROBADO_CON_OBSERVACIONES':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
    case 'RECHAZADO':
      return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
  }
};

// Helper function to get risk level color
const getRiskLevelColor = (level: string) => {
  switch (level) {
    case 'VERY_LOW':
      return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
    case 'LOW':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
    case 'MEDIUM':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
    case 'HIGH':
      return 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400';
    case 'VERY_HIGH':
      return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
  }
};

export default function ResultsSection({
  processedData,
  onGenerateReport,
  onDetailedAnalysis
}: ResultsSectionProps) {
  const analysisData = processedData.apiData?.results?.analysis;
  const summary = analysisData?.summary;
  const validation = analysisData?.stages?.validation?.data;
  const riskAnalysis = analysisData?.stages?.risk_analysis?.data;
  const classification = analysisData?.stages?.classification?.data;

  return (
    <div className="mt-8 bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Resultados del Análisis</h2>
      
      {/* Analysis Status Overview */}
      {summary && (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Estado del Análisis</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              summary.overall_status === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' : 'bg-gray-100 text-gray-800'
            }`}>
              {summary.overall_status === 'success' ? 'Completado' : summary.overall_status}
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-600 dark:text-gray-400">Etapas Totales</p>
              <p className="font-semibold text-gray-900 dark:text-white">{summary.total_stages}</p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Completadas</p>
              <p className="font-semibold text-green-600">{summary.completed_stages}</p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Fallidas</p>
              <p className="font-semibold text-red-600">{summary.failed_stages}</p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Progreso</p>
              <p className="font-semibold text-blue-600">{Math.round((summary.completed_stages / summary.total_stages) * 100)}%</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Validation Results */}
        {validation && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">� Validación de Cumplimiento</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <span className="text-gray-700 dark:text-gray-300">Nivel de Validación</span>
                <span className={`px-2 py-1 rounded text-sm font-medium ${getValidationLevelColor(validation.validation_level)}`}>
                  {validation.validation_level?.replace('_', ' ')}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <span className="text-gray-700 dark:text-gray-300">Puntuación General</span>
                <span className="font-semibold text-blue-600">{validation.overall_score?.toFixed(1)}/100</span>
              </div>
              {validation.compliance_validation && (
                <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <span className="text-gray-700 dark:text-gray-300">Cumplimiento Normativo</span>
                  <span className="font-semibold text-orange-600">
                    {validation.compliance_validation.overall_compliance_percentage?.toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Risk Analysis */}
        {riskAnalysis && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">⚠️ Análisis de Riesgos</h3>
            <div className="space-y-4">
              {riskAnalysis.overall_assessment && (
                <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-700 dark:text-gray-300">Nivel de Riesgo General</span>
                    <span className={`px-2 py-1 rounded text-sm font-medium ${getRiskLevelColor(riskAnalysis.overall_assessment.risk_level)}`}>
                      {riskAnalysis.overall_assessment.risk_level?.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Puntuación: {riskAnalysis.overall_assessment.total_risk_score}/100
                  </div>
                </div>
              )}
              
              {riskAnalysis.category_risks && Object.entries(riskAnalysis.category_risks).slice(0, 3).map(([category, risk]) => {
                const riskData = risk as { risk_level?: string };
                return (
                <div key={category} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                  <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">
                    {category.replace('_', ' ').toLowerCase()}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskLevelColor(riskData.risk_level || 'UNKNOWN')}`}>
                    {riskData.risk_level?.replace('_', ' ') || 'N/A'}
                  </span>
                </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Document Classification */}
        {classification && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">📑 Clasificación de Documentos</h3>
            <div className="space-y-3">
              {classification.document_info && (
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600 dark:text-gray-400">Secciones Totales</p>
                    <p className="font-semibold text-gray-900 dark:text-white">{classification.document_info.total_sections}</p>
                  </div>
                  <div>
                    <p className="text-gray-600 dark:text-gray-400">Fragmentos</p>
                    <p className="font-semibold text-gray-900 dark:text-white">{classification.document_info.total_fragments}</p>
                  </div>
                </div>
              )}
              
              {classification.sections && Object.keys(classification.sections).length > 0 && (
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Secciones Identificadas:</p>
                  <div className="flex flex-wrap gap-2">
                    {Object.keys(classification.sections).slice(0, 6).map((section) => (
                      <span key={section} className="px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400 rounded text-xs">
                        {section.replace('_', ' ')}
                      </span>
                    ))}
                    {Object.keys(classification.sections).length > 6 && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                        +{Object.keys(classification.sections).length - 6} más
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Key Findings */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">🔍 Hallazgos Principales</h3>
          <div className="space-y-3">
            {summary?.key_findings?.map((finding: string, index: number) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                <p className="text-gray-700 dark:text-gray-300 text-sm">{finding}</p>
              </div>
            )) || processedData.keyInsights.map((insight: string, index: number) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                <p className="text-gray-700 dark:text-gray-300 text-sm">{insight}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recommendations Section */}
      {(summary?.recommendations || validation?.recommendations || processedData.recommendedActions) && (
        <div className="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/10 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">💡 Recomendaciones</h3>
          <div className="space-y-2">
            {(summary?.recommendations || validation?.recommendations || processedData.recommendedActions).map((recommendation: string, index: number) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-yellow-600 rounded-full mt-2"></div>
                <p className="text-gray-700 dark:text-gray-300 text-sm">{recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-4">
          <button 
            onClick={onGenerateReport}
            className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            📋 Generar Reporte PDF
          </button>
          <button 
            onClick={onDetailedAnalysis}
            className="border-2 border-blue-600 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            🔍 Ver Análisis Detallado
          </button>
        </div>
      </div>
    </div>
  );
}
