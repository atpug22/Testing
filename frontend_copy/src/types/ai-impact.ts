/**
 * TypeScript type definitions for AI Impact Analysis
 */

export type AIConfidenceLevel = 'high' | 'medium' | 'low' | 'unknown';

export interface AIAuthorshipResult {
  pr_number: number;
  confidence: AIConfidenceLevel;
  ai_probability: number;
  indicators: string[];
  file_analysis: Record<string, any>;
  commit_patterns: Record<string, any>;
}

export interface AIImpactMetrics {
  total_prs_analyzed: number;
  ai_authored_prs: number;
  human_authored_prs: number;
  ai_adoption_rate: number;
  ai_avg_merge_time_hours?: number;
  human_avg_merge_time_hours?: number;
  ai_avg_review_cycles?: number;
  human_avg_review_cycles?: number;
  ai_avg_files_changed?: number;
  human_avg_files_changed?: number;
  ai_avg_lines_changed?: number;
  human_avg_lines_changed?: number;
}

export interface AITrendAnalysis {
  weekly_ai_adoption: Record<string, number>;
  weekly_ai_prs: Record<string, number>;
  weekly_total_prs: Record<string, number>;
  trend_direction: 'increasing' | 'decreasing' | 'stable';
}

export interface AIQualityAssessment {
  high_risk_ai_prs: number[];
  quality_score: number;
  common_issues: string[];
  recommendations: string[];
}

export interface AIImpactAnalysis {
  repository: string;
  analysis_date: string;
  days_analyzed: number;
  metrics: AIImpactMetrics;
  trends: AITrendAnalysis;
  quality: AIQualityAssessment;
  pr_analyses: AIAuthorshipResult[];
  impact_score: number;
  confidence_level: AIConfidenceLevel;
  summary_insights: string[];
}

export interface AIImpactResponse {
  success: boolean;
  repository: string;
  analysis_date: string;
  analysis?: AIImpactAnalysis;
  error_message?: string;
}

export interface AIImpactRequest {
  owner: string;
  repo: string;
  days?: number;
  force_refresh?: boolean;
  include_detailed_analysis?: boolean;
}
