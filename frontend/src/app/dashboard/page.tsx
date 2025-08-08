'use client';

import React, { useState, useRef } from 'react';

interface ProcessedData {
  totalDocuments: number;
  analysisComplete: boolean;
  keyInsights: string[];
  recommendedActions: string[];
}

export default function Dashboard() {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedData, setProcessedData] = useState<ProcessedData | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [showDetailedModal, setShowDetailedModal] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    setIsProcessing(true);
    // Simular procesamiento
    setTimeout(() => {
      setProcessedData({
        totalDocuments: uploadedFiles.length,
        analysisComplete: true,
        keyInsights: [
          `📄 Documentos técnicos identificados: ${Math.floor(uploadedFiles.length * 0.6)} (Especificaciones, planos, memorias técnicas)`,
          `💰 Documentos financieros encontrados: ${Math.floor(uploadedFiles.length * 0.3)} (Presupuestos, garantías, estados financieros)`,
          `⚖️ Documentos legales detectados: ${Math.floor(uploadedFiles.length * 0.1)} (Contratos marco, certificaciones, avales)`,
          `🎯 Nivel de completitud: 87% - Faltan algunos documentos opcionales`,
          `⚠️ Riesgos identificados: 3 elementos requieren atención especial`,
          `📊 Probabilidad de éxito estimada: 78% basada en criterios históricos`
        ],
        recommendedActions: [
          '🔍 Revisar especificaciones técnicas del sistema de climatización (Sección 4.2)',
          '💵 Verificar coherencia entre presupuesto base y oferta económica',
          '📋 Completar certificación ISO 14001 para mejorar puntuación ambiental',
          '⏰ Ajustar cronograma de obra - posible conflicto en mes 8',
          '🤝 Considerar alianza estratégica para fortalecer propuesta técnica',
          '📈 Optimizar margen de beneficio manteniendo competitividad'
        ]
      });
      setIsProcessing(false);
    }, 3000);
  };

  const clearAll = () => {
    setUploadedFiles([]);
    setProcessedData(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDetailedAnalysis = () => {
    setShowDetailedModal(true);
    setActiveTab('overview');
  };

  const handleExportReport = () => {
    // Simular exportación de reporte
    const reportData = {
      fecha: new Date().toLocaleDateString('es-ES'),
      proyecto: 'Construcción Centro Comercial Plaza Norte',
      documentos: uploadedFiles.length,
      ...processedData
    };
    
    alert('📋 Reporte Exportado:\n\n' +
          `📅 Fecha: ${reportData.fecha}\n` +
          `🏗️ Proyecto: ${reportData.proyecto}\n` +
          `📄 Documentos analizados: ${reportData.documentos}\n` +
          `✅ Estado: Análisis completado\n\n` +
          'El reporte incluye:\n' +
          '• Resumen ejecutivo\n' +
          '• Análisis detallado por categorías\n' +
          '• Recomendaciones priorizadas\n' +
          '• Matriz de riesgos\n' +
          '• Anexos con documentos procesados');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">T</span>
                </div>
                <span className="text-xl font-bold text-gray-900 dark:text-white">TenderAI</span>
              </div>
              <span className="text-gray-400 dark:text-gray-500">|</span>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600 dark:text-gray-400">Procesamiento Inteligente de Licitaciones</span>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Upload Section */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                Subir Documentos de Licitación
              </h2>
              
              {/* Upload Area */}
              <div 
                className={`border-2 border-dashed rounded-lg p-8 text-center mb-6 transition-all duration-300 transform ${
                  isDragOver 
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 scale-105 shadow-lg border-solid animate-pulse' 
                    : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                }`}
                onDragEnter={handleDragEnter}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                <div className={`space-y-4 transition-all duration-300 ${isDragOver ? 'transform scale-110' : ''}`}>
                  <div className={`mx-auto w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 ${
                    isDragOver 
                      ? 'bg-blue-500 animate-bounce' 
                      : 'bg-blue-100 dark:bg-blue-900'
                  }`}>
                    <svg className={`w-8 h-8 transition-all duration-300 ${
                      isDragOver 
                        ? 'text-white animate-pulse' 
                        : 'text-blue-600 dark:text-blue-400'
                    }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <div>
                    <p className={`mb-4 transition-all duration-300 ${
                      isDragOver 
                        ? 'text-blue-700 dark:text-blue-300 font-semibold text-lg' 
                        : 'text-gray-600 dark:text-gray-400'
                    }`}>
                      {isDragOver ? '¡Suelta los archivos aquí!' : 'Arrastra y suelta tus archivos aquí, o usa los botones para seleccionar'}
                    </p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
                      >
                        Seleccionar Archivos
                      </button>
                    </div>
                  </div>
                </div>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  className="hidden"
                  onChange={handleFileUpload}
                  accept=".pdf,.doc,.docx,.txt,.xls,.xlsx"
                />
              </div>

              {/* Uploaded Files List */}
              {uploadedFiles.length > 0 && (
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Archivos Subidos ({uploadedFiles.length})
                    </h3>
                    <button
                      onClick={clearAll}
                      className="text-red-600 hover:text-red-700 text-sm font-medium"
                    >
                      Limpiar Todo
                    </button>
                  </div>
                  <div className="max-h-64 overflow-y-auto space-y-2">
                    {uploadedFiles.map((file, index) => (
                      <div key={index} className="flex items-center justify-between bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded flex items-center justify-center">
                            <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">{file.name}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                          </div>
                        </div>
                        <button
                          onClick={() => removeFile(index)}
                          className="text-red-500 hover:text-red-700 p-1"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Process Button */}
              {uploadedFiles.length > 0 && (
                <button
                  onClick={processFiles}
                  disabled={isProcessing}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-4 rounded-lg font-semibold text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? (
                    <div className="flex items-center justify-center space-x-2">
                      <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
                      <span>Procesando con IA...</span>
                    </div>
                  ) : (
                    'Procesar Documentos'
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Sidebar */}
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
              </div>            {/* Recent Activity */}
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
        </div>

        {/* Results Section */}
        {processedData && (
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
                  onClick={handleExportReport}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
                >
                  📋 Exportar Reporte
                </button>
                <button 
                  onClick={handleDetailedAnalysis}
                  className="border-2 border-blue-600 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 px-6 py-3 rounded-lg font-semibold transition-colors"
                >
                  🔍 Ver Análisis Detallado
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modal de Análisis Detallado */}
      {showDetailedModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
            {/* Header del Modal */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                🔍 Análisis Detallado de Licitación
              </h2>
              <button
                onClick={() => setShowDetailedModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Tabs Navigation */}
            <div className="flex border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
              {[
                { id: 'overview', label: '📊 Resumen', icon: '📊' },
                { id: 'technical', label: '🔧 Técnico', icon: '🔧' },
                { id: 'financial', label: '💰 Financiero', icon: '💰' },
                { id: 'legal', label: '⚖️ Legal', icon: '⚖️' },
                { id: 'timeline', label: '⏱️ Cronograma', icon: '⏱️' },
                { id: 'risks', label: '⚠️ Riesgos', icon: '⚠️' }
              ].map((tab) => (
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
              )}

              {activeTab === 'technical' && (
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
              )}

              {activeTab === 'financial' && (
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
              )}

              {activeTab === 'legal' && (
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
              )}

              {activeTab === 'timeline' && (
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
              )}

              {activeTab === 'risks' && (
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
              )}
            </div>

            {/* Footer del Modal */}
            <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Análisis generado el {new Date().toLocaleDateString('es-ES')} a las {new Date().toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'})}
              </span>
              <div className="flex space-x-3">
                <button
                  onClick={handleExportReport}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  📋 Exportar
                </button>
                <button
                  onClick={() => setShowDetailedModal(false)}
                  className="border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}