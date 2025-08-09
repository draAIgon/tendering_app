import React from 'react';
import { ProcessedData } from '@/types/dashboard';

interface SidebarProps {
  uploadedFiles: File[];
  processedData: ProcessedData | null;
}

export default function Sidebar({ uploadedFiles, processedData }: SidebarProps) {
  return (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Estado del Proyecto</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-gray-600 dark:text-gray-400">Documentos</span>
            <span className="font-semibold text-gray-900 dark:text-white">{uploadedFiles.length}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600 dark:text-gray-400">Estado</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              processedData ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 
              uploadedFiles.length > 0 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' : 
              'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
            }`}>
              {processedData ? 'Procesado' : uploadedFiles.length > 0 ? 'Listo' : 'Sin archivos'}
            </span>
          </div>
          {processedData && (
            <>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Éxito estimado</span>
                <span className="font-semibold text-green-600 dark:text-green-400">78%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Riesgos</span>
                <span className="font-semibold text-orange-600 dark:text-orange-400">3 elementos</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Actividad Reciente</h3>
        <div className="space-y-3">
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
            <div>
              <p className="text-sm text-gray-900 dark:text-white">Sistema iniciado</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Hace unos momentos</p>
            </div>
          </div>
          {uploadedFiles.length > 0 && (
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-green-600 rounded-full mt-2"></div>
              <div>
                <p className="text-sm text-gray-900 dark:text-white">Archivos cargados</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{uploadedFiles.length} documentos</p>
              </div>
            </div>
          )}
          {processedData && (
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 bg-purple-600 rounded-full mt-2"></div>
              <div>
                <p className="text-sm text-gray-900 dark:text-white">Análisis completado</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">IA aplicada exitosamente</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tips */}
      <div className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">💡 Consejos</h3>
        <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
          <li>• Sube archivos PDF, Word o Excel</li>
          <li>• Incluye documentos técnicos y financieros</li>
          <li>• La IA analizará automáticamente el contenido</li>
          <li>• Revisa las recomendaciones generadas</li>
        </ul>
      </div>
    </div>
  );
}
