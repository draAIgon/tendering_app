export interface AnalysisResult {
  document_id?: string;
  comparison_id?: string;
  status: 'processing' | 'success' | 'error' | 'pending';
  progress?: number;
  error?: string;
  results?: {
    technical_analysis?: Record<string, unknown>;
    financial_analysis?: Record<string, unknown>;
    legal_analysis?: Record<string, unknown>;
    risk_analysis?: Record<string, unknown>;
    comparison_analysis?: Record<string, unknown>;
    recommendations?: string[];
    summary?: Record<string, unknown>;
    analysis?: AnalysisData;
  };
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
          data: ExtractionData;
        };
        classification?: {
          status: string;
          data: ClassificationData;
        };
        validation?: {
          status: string;
          data: ValidationData;
        };
        risk_analysis?: {
          status: string;
          data: RiskAnalysisData;
        };
      };
      summary: AnalysisSummary;
      errors: string[];
    }>;
  };
}

export interface AnalysisData {
  document_id?: string;
  document_path?: string;
  document_type?: string;
  analysis_level?: string;
  timestamp?: string;
  summary?: AnalysisSummary;
  stages?: {
    extraction?: {
      status?: string;
      data?: ExtractionData;
    };
    validation?: {
      status?: string;
      data?: ValidationData;
    };
    risk_analysis?: {
      status?: string;
      data?: RiskAnalysisData;
    };
    classification?: {
      status?: string;
      data?: ClassificationData;
    };
  };
  errors?: string[];
}

export interface ExtractionData {
  content?: string;
  text?: string;
}

export interface AnalysisSummary {
  total_stages: number;
  completed_stages: number;
  failed_stages: number;
  overall_status: string;
  key_findings: string[];
  recommendations: string[];
}

export interface ValidationData {
  document_type?: string;
  validation_timestamp?: string;
  overall_score: number;
  validation_level: string;
  structural_validation?: {
    document_type?: string;
    total_sections_required?: number;
    sections_found?: number;
    sections_missing?: number;
    missing_sections?: string[];
    structural_issues?: string[];
    completion_percentage?: number;
    has_adequate_length?: boolean;
    has_dates?: boolean;
  };
  compliance_validation?: {
    overall_compliance_percentage: number;
    total_rules?: number;
    passed_rules?: number;
    failed_rules?: number;
    compliance_level?: string;
  };
  recommendations: string[];
}

export interface RiskAnalysisData {
  document_type?: string;
  analysis_timestamp?: string;
  content_length?: number;
  overall_assessment?: {
    total_risk_score: number;
    risk_level: string;
    risk_distribution?: Record<string, number>;
    assessment_summary?: string;
  };
  category_risks?: Record<string, {
    category?: string;
    description?: string;
    risk_score?: number;
    risk_level: string;
    indicators_detected?: number;
    total_mentions?: number;
    detected_indicators?: string[];
    risk_mentions?: string[];
    semantic_risks?: string[];
    weight?: number;
  }>;
  critical_risks?: string[];
  mitigation_recommendations?: string[];
}

export interface ClassificationData {
  document_info?: {
    source?: string;
    total_sections: number;
    total_fragments: number;
    classification_timestamp?: string;
  };
  sections?: Record<string, {
    section_name?: string;
    document_count?: number;
    total_characters?: number;
    content_preview?: string;
    sources?: string[];
    taxonomy_info?: {
      keywords?: string[];
      priority?: number;
      description?: string;
    };
  }>;
  confidence_scores?: Record<string, number>;
  key_requirements?: Record<string, string[]>;
}

export interface ProcessedData {
  documentId: string;
  totalDocuments: number;
  analysisComplete: boolean;
  keyInsights: string[];
  recommendedActions: string[];
  apiData?: AnalysisResult;
}
