import React from 'react';

interface DetailedAnalysisModalProps {
  showModal: boolean;
  onClose: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  uploadedFiles: File[];
  onExportReport: () => void;
}

export default function DetailedAnalysisModal({
  showModal,
  onClose,
  activeTab,
  setActiveTab,
  uploadedFiles,
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
            <OverviewTab uploadedFiles={uploadedFiles} />
          )}

          {activeTab === 'technical' && (
            <TechnicalTab />
          )}

          {activeTab === 'financial' && (
            <FinancialTab />
          )}

          {activeTab === 'legal' && (
            <LegalTab />
          )}

          {activeTab === 'timeline' && (
            <TimelineTab />
          )}

          {activeTab === 'risks' && (
            <RisksTab />
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
function OverviewTab({ uploadedFiles }: { uploadedFiles: File[] }) {
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
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">87%</p>
          <p className="text-sm text-green-700 dark:text-green-300">Documentos requeridos</p>
        </div>
        <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
          <h3 className="font-semibold text-orange-800 dark:text-orange-200 mb-2">🎯 Éxito Est.</h3>
          <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">78%</p>
          <p className="text-sm text-orange-700 dark:text-orange-300">Probabilidad</p>
        </div>
      </div>
      
      <div className="bg-gray-50 dark:bg-gray-700/50 p-4 rounded-lg">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-3">📈 Distribución de Documentos</h3>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600 dark:text-gray-400">Técnicos</span>
            <div className="flex items-center space-x-2">
              <div className="w-32 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full" style={{width: '60%'}}></div>
              </div>
              <span className="text-sm font-medium text-gray-900 dark:text-white">60%</span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600 dark:text-gray-400">Financieros</span>
            <div className="flex items-center space-x-2">
              <div className="w-32 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                <div className="bg-green-600 h-2 rounded-full" style={{width: '30%'}}></div>
              </div>
              <span className="text-sm font-medium text-gray-900 dark:text-white">30%</span>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600 dark:text-gray-400">Legales</span>
            <div className="flex items-center space-x-2">
              <div className="w-32 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                <div className="bg-purple-600 h-2 rounded-full" style={{width: '10%'}}></div>
              </div>
              <span className="text-sm font-medium text-gray-900 dark:text-white">10%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TechnicalTab() {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">🔧 Análisis Técnico</h3>
      <div className="grid md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h4 className="font-semibold text-gray-900 dark:text-white">📋 Especificaciones Encontradas</h4>
          <ul className="space-y-2">
            <li className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span className="text-sm text-gray-700 dark:text-gray-300">Planos arquitectónicos (15 archivos)</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span className="text-sm text-gray-700 dark:text-gray-300">Memorias de cálculo estructural</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
              <span className="text-sm text-gray-700 dark:text-gray-300">Especificaciones climatización (Revisar Sección 4.2)</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span className="text-sm text-gray-700 dark:text-gray-300">Sistemas eléctricos y domótica</span>
            </li>
          </ul>
        </div>
        <div className="space-y-4">
          <h4 className="font-semibold text-gray-900 dark:text-white">⚡ Puntos de Atención</h4>
          <div className="space-y-3">
            <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg border-l-4 border-yellow-400">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                <strong>Climatización:</strong> Verificar compatibilidad con normativa europea EN 14825
              </p>
            </div>
            <div className="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg border-l-4 border-blue-400">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                <strong>Estructural:</strong> Considerar análisis sísmico actualizado
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function FinancialTab() {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">💰 Análisis Financiero</h3>
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-green-800 dark:text-green-200 mb-3">💹 Resumen Económico</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-green-700 dark:text-green-300">Presupuesto Base:</span>
              <span className="font-medium text-green-800 dark:text-green-200">€2,450,000</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-green-700 dark:text-green-300">Oferta Propuesta:</span>
              <span className="font-medium text-green-800 dark:text-green-200">€2,280,000</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-green-700 dark:text-green-300">Margen:</span>
              <span className="font-medium text-green-800 dark:text-green-200">12.5%</span>
            </div>
          </div>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-3">📊 Competitividad</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-blue-700 dark:text-blue-300">Posición estimada:</span>
              <span className="font-medium text-blue-800 dark:text-blue-200">2º-3º lugar</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-blue-700 dark:text-blue-300">Diferencia promedio:</span>
              <span className="font-medium text-blue-800 dark:text-blue-200">-6.9%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function LegalTab() {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">⚖️ Análisis Legal</h3>
      <div className="space-y-4">
        <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
          <h4 className="font-semibold text-green-800 dark:text-green-200 mb-3">✅ Cumplimiento Normativo</h4>
          <ul className="space-y-2">
            <li className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span className="text-sm text-green-700 dark:text-green-300">Ley de Contratos del Sector Público</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span className="text-sm text-green-700 dark:text-green-300">Normativa de Seguridad Laboral</span>
            </li>
            <li className="flex items-center space-x-2">
              <span className="w-2 h-2 bg-yellow-500 rounded-full"></span>
              <span className="text-sm text-green-700 dark:text-green-300">ISO 14001 (Pendiente certificación)</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

function TimelineTab() {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">⏱️ Cronograma del Proyecto</h3>
      <div className="space-y-4">
        <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg border-l-4 border-yellow-400">
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            <strong>⚠️ Alerta:</strong> Posible conflicto temporal en el mes 8 (instalaciones vs acabados)
          </p>
        </div>
        <div className="space-y-3">
          {[
            { fase: 'Preparación del terreno', duracion: '2 meses', estado: 'planificado' },
            { fase: 'Estructura y cimentación', duracion: '4 meses', estado: 'planificado' },
            { fase: 'Instalaciones', duracion: '3 meses', estado: 'revision' },
            { fase: 'Acabados', duracion: '2 meses', estado: 'planificado' }
          ].map((item, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <span className="text-sm text-gray-900 dark:text-white">{item.fase}</span>
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-600 dark:text-gray-400">{item.duracion}</span>
                <span className={`px-2 py-1 rounded-full text-xs ${
                  item.estado === 'revision' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                }`}>
                  {item.estado === 'revision' ? 'Revisar' : 'OK'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function RisksTab() {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-bold text-gray-900 dark:text-white">⚠️ Matriz de Riesgos</h3>
      <div className="space-y-4">
        {[
          { riesgo: 'Retraso en suministros de materiales', probabilidad: 'Media', impacto: 'Alto', mitigacion: 'Contratos marco con proveedores alternativos' },
          { riesgo: 'Cambios normativos durante ejecución', probabilidad: 'Baja', impacto: 'Medio', mitigacion: 'Clausulas de revisión de precios' },
          { riesgo: 'Condiciones meteorológicas adversas', probabilidad: 'Media', impacto: 'Medio', mitigacion: 'Planificación estacional flexible' }
        ].map((item, index) => (
          <div key={index} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-2">{item.riesgo}</h4>
            <div className="grid md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">Probabilidad: </span>
                <span className={`font-medium ${
                  item.probabilidad === 'Alta' ? 'text-red-600' :
                  item.probabilidad === 'Media' ? 'text-yellow-600' : 'text-green-600'
                }`}>{item.probabilidad}</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Impacto: </span>
                <span className={`font-medium ${
                  item.impacto === 'Alto' ? 'text-red-600' :
                  item.impacto === 'Medio' ? 'text-yellow-600' : 'text-green-600'
                }`}>{item.impacto}</span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Mitigación: </span>
                <span className="text-gray-900 dark:text-white">{item.mitigacion}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
