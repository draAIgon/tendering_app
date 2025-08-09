export interface AnalysisResult {
  document_id: string;
  status: 'processing' | 'completed' | 'error' | 'pending';
  progress?: number;
  error?: string;
  results?: {
    recommendations?: string[];
    analysis?: Record<string, unknown>;
  };
}

export interface ProcessedData {
  documentId: string;
  totalDocuments: number;
  analysisComplete: boolean;
  keyInsights: string[];
  recommendedActions: string[];
  apiData?: AnalysisResult;
}
