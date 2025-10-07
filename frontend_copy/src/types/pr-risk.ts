/**
 * TypeScript types for PR Risk Analysis
 */

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type PRState = 'open' | 'closed' | 'merged';

// === New Detailed PR Information Types ===

export interface FileChange {
  filename: string;
  status: string; // added, removed, modified, renamed
  additions: number;
  deletions: number;
  changes: number;
  patch?: string;
  blob_url?: string;
  previous_filename?: string;
}

export interface CICheckRun {
  name: string;
  status: string; // queued, in_progress, completed
  conclusion?: string; // success, failure, neutral, cancelled, skipped, timed_out, action_required
  started_at?: string;
  completed_at?: string;
  html_url?: string;
  details_url?: string;
}

export interface PRComment {
  id: number;
  author: string;
  body: string;
  created_at: string;
  updated_at?: string;
  comment_type: string; // issue_comment, review_comment, review
  in_reply_to_id?: number;
  path?: string;
  line?: number;
}

export interface PRLabel {
  name: string;
  color: string;
  description?: string;
}

export interface LinkedIssue {
  number: number;
  title: string;
  state: string;
  url: string;
  created_at: string;
  closed_at?: string;
  labels: string[];
}

export interface PRTimelineMetrics {
  time_to_first_review_hours?: number;
  time_to_first_approval_hours?: number;
  time_to_merge_hours?: number;
  first_commit_at?: string;
  last_commit_at?: string;
  time_from_first_to_last_commit_hours?: number;
  total_review_time_hours?: number;
  total_wait_time_hours?: number;
  number_of_review_cycles: number;
}

export interface PRReviewSummary {
  total_reviews: number;
  approved_count: number;
  changes_requested_count: number;
  commented_count: number;
  reviewers: string[];
  review_comments: PRComment[];
}

export interface PRDetailedInfo {
  // Basic info
  description?: string;
  body_text?: string;

  // Files and changes
  files: FileChange[];
  total_additions: number;
  total_deletions: number;
  total_changes: number;

  // CI/CD
  ci_checks: CICheckRun[];
  ci_status: string;

  // Timeline
  timeline_metrics: PRTimelineMetrics;

  // Comments and discussions
  comments: PRComment[];
  total_comments: number;

  // Labels
  labels: PRLabel[];

  // Linked issues
  linked_issues: LinkedIssue[];

  // Reviews
  review_summary: PRReviewSummary;

  // Commits
  commit_count: number;
  commits_authors: string[];

  // Additional metadata
  mergeable?: boolean;
  mergeable_state?: string;
  draft: boolean;
  requested_reviewers: string[];
  assignees: string[];
}

export interface StucknessMetrics {
  time_since_last_activity_hours: number;
  unresolved_review_threads: number;
  failed_ci_checks: number;
  time_waiting_for_reviewer_hours: number;
  pr_age_days: number;
  rebase_force_push_count: number;
  comment_velocity_decay: number;
  linked_issue_stale_time_hours: number;
}

export interface BlastRadiusMetrics {
  downstream_dependencies: number;
  critical_path_touched: boolean;
  lines_added: number;
  lines_removed: number;
  files_changed: number;
  test_coverage_delta: number;
  historical_regression_risk: number;
}

export interface DynamicsMetrics {
  author_experience_score: number;
  reviewer_load: number;
  approval_ratio: number;
  author_merge_history: number;
  avg_review_time_hours: number;
}

export interface BusinessImpactMetrics {
  linked_to_release: boolean;
  external_dependencies: number;
  priority_label?: string;
  affects_core_functionality: boolean;
}

export interface CompositeRiskScore {
  stuckness_score: number;
  blast_radius_score: number;
  dynamics_score: number;
  business_impact_score: number;
}

export interface PRRiskAnalysis {
  pr_number: number;
  title: string;
  author: string;
  state: PRState;
  created_at: string;
  updated_at: string;
  url: string;
  stuckness_metrics: StucknessMetrics;
  blast_radius_metrics: BlastRadiusMetrics;
  dynamics_metrics: DynamicsMetrics;
  business_impact_metrics: BusinessImpactMetrics;
  composite_scores: CompositeRiskScore;
  detailed_info?: PRDetailedInfo;
  ai_summary?: string;
  analyzed_at: string;
  delivery_risk_score: number;
  risk_level: RiskLevel;
}

export interface PRListItem {
  pr_number: number;
  title: string;
  author: string;
  state: PRState;
  delivery_risk_score: number;
  risk_level: RiskLevel;
  created_at: string;
  updated_at: string;
  url: string;
  ai_summary?: string;
}

export interface DashboardSummary {
  total_prs: number;
  high_risk_count: number;
  critical_risk_count: number;
  avg_risk_score: number;
  team_velocity_impact: number;
  top_risk_prs: PRListItem[];
  risk_distribution: Record<RiskLevel, number>;
}

export interface RepositoryRiskReport {
  owner: string;
  repo: string;
  analyzed_at: string;
  total_prs_analyzed: number;
  pr_analyses: PRRiskAnalysis[];
  avg_delivery_risk_score: number;
  high_risk_pr_count: number;
  critical_risk_pr_count: number;
  team_velocity_impact: number;
  release_risk_assessment: string;
}

export interface PRRiskAnalysisRequest {
  owner: string;
  repo: string;
  force_refresh?: boolean;
  include_closed_prs?: boolean;
  max_prs?: number;
}

export interface PRRiskAnalysisResponse {
  success: boolean;
  repository_report?: RepositoryRiskReport;
  error_message?: string;
  processing_time_seconds?: number;
  api_requests_made?: number;
}
