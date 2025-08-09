import React from 'react';
import { ProcessedData } from '@/types/dashboard';

interface ResultsSectionProps {
  processedData: ProcessedData;
  onExportReport: () => void;
  onDetailedAnalysis: () => void;
}

export default function ResultsSection({
  processedData,
  onExportReport,
  onDetailedAnalysis
}: ResultsSectionProps) {
  return (
    <div className="mt-8 bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Resultados del Análisis</h2>
      
      <div className="grid md:grid-cols-2 gap-6">
        {/* Key Insights */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">📊 Análisis de Documentos</h3>
          <div className="space-y-3">
            {processedData.keyInsights.map((insight: string, index: number) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                <p className="text-gray-700 dark:text-gray-300">{insight}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Recommendations */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">🎯 Recomendaciones</h3>
          <div className="space-y-3">
            {processedData.recommendedActions.map((action: string, index: number) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-green-600 rounded-full mt-2"></div>
                <p className="text-gray-700 dark:text-gray-300">{action}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row gap-4">
          <button 
            onClick={onExportReport}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            📋 Exportar Reporte
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
