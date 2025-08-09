import React from 'react';
import { AnalysisResult } from '@/types/dashboard';

interface FileUploaderProps {
  uploadedFiles: File[];
  setUploadedFiles: React.Dispatch<React.SetStateAction<File[]>>;
  isProcessing: boolean;
  processingError: string | null;
  isDragOver: boolean;
  setIsDragOver: React.Dispatch<React.SetStateAction<boolean>>;
  fileInputRef: React.RefObject<HTMLInputElement | null>;
  isPolling: boolean;
  analysisResult: AnalysisResult | null;
  onProcessFiles: () => void;
  onClearAll: () => void;
  onFileUpload: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onDragEnter: (event: React.DragEvent<HTMLDivElement>) => void;
  onDragOver: (event: React.DragEvent<HTMLDivElement>) => void;
  onDragLeave: (event: React.DragEvent<HTMLDivElement>) => void;
  onDrop: (event: React.DragEvent<HTMLDivElement>) => void;
  onRemoveFile: (index: number) => void;
}

export default function FileUploader({
  uploadedFiles,
  isProcessing,
  processingError,
  isDragOver,
  fileInputRef,
  isPolling,
  analysisResult,
  onProcessFiles,
  onClearAll,
  onFileUpload,
  onDragEnter,
  onDragOver,
  onDragLeave,
  onDrop,
  onRemoveFile
}: FileUploaderProps) {
  return (
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
        onDragEnter={onDragEnter}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
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
          onChange={onFileUpload}
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
              onClick={onClearAll}
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
                  onClick={() => onRemoveFile(index)}
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
        <div className="space-y-4">
          {processingError && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <svg className="w-5 h-5 text-red-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h4 className="text-sm font-medium text-red-800 dark:text-red-200">Error en el procesamiento</h4>
                  <p className="text-sm text-red-700 dark:text-red-300 mt-1">{processingError}</p>
                </div>
              </div>
            </div>
          )}
          
          <button
            onClick={onProcessFiles}
            disabled={isProcessing || isPolling}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white py-4 rounded-lg font-semibold text-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isProcessing || isPolling ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
                <span>{isProcessing ? 'Subiendo archivos...' : 'Procesando con IA...'}</span>
              </div>
            ) : (
              'Procesar Documentos con IA'
            )}
          </button>
          
          {(isProcessing || isPolling) && analysisResult && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <div className="animate-pulse w-3 h-3 bg-blue-500 rounded-full"></div>
                <div>
                  <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                    Estado: {analysisResult.status === 'processing' ? 'Procesando' : 'Completando'}
                  </p>
                  {analysisResult.progress && (
                    <div className="mt-2">
                      <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                          style={{width: `${analysisResult.progress}%`}}
                        ></div>
                      </div>
                      <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">{analysisResult.progress}% completado</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
