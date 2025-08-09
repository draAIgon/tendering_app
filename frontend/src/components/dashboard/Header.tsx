import React from 'react';

export default function Header() {
  return (
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
  );
}
