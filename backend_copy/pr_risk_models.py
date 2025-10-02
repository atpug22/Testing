"""
Comprehensive PR Risk Metrics Models
This module defines all the data structures for the PR risk analysis system.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PRState(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


# === Stuckness Score Models ===

class StucknessMetrics(BaseModel):
    """Sub-metrics for the Stuckness Score"""
    time_since_last_activity_hours: float = Field(description="Hours since last activity")
    unresolved_review_threads: int = Field(description="Number of open comment threads")
    failed_ci_checks: int = Field(description="Number of failed CI checks")
    time_waiting_for_reviewer_hours: float = Field(description="Hours waiting for required reviewer")
    pr_age_days: float = Field(description="Days since PR was opened")
    rebase_force_push_count: int = Field(description="Number of rebases/force pushes")
    comment_velocity_decay: float = Field(description="Rate of comment decay (0-1)")
    linked_issue_stale_time_hours: float = Field(description="Average stale time of linked issues")

    def calculate_score(self) -> float:
        """Calculate weighted stuckness score (0-100)"""
        score = 0.0
        
        # Time since last activity (25% weight)
        if self.time_since_last_activity_hours > 72:
            score += 25
        elif self.time_since_last_activity_hours > 24:
            score += 15
        
        # Unresolved threads (20% weight)
        score += min(self.unresolved_review_threads * 4, 20)
        
        # Failed CI (15% weight)
        score += min(self.failed_ci_checks * 5, 15)
        
        # Waiting for reviewer (15% weight)
        if self.time_waiting_for_reviewer_hours > 48:
            score += 15
        elif self.time_waiting_for_reviewer_hours > 24:
            score += 10
        
        # PR age (10% weight)
        if self.pr_age_days > 14:
            score += 10
        elif self.pr_age_days > 7:
            score += 5
        
        # Rebase frequency (8% weight)
        score += min(self.rebase_force_push_count * 2, 8)
        
        # Comment velocity decay (4% weight)
        score += self.comment_velocity_decay * 4
        
        # Linked issue stale time (3% weight)
        if self.linked_issue_stale_time_hours > 168:  # 1 week
            score += 3
        
        return min(score, 100)


# === Blast Radius Score Models ===

class BlastRadiusMetrics(BaseModel):
    """Sub-metrics for the Blast Radius Score"""
    downstream_dependencies: int = Field(description="Number of downstream dependencies")
    critical_path_touched: bool = Field(description="Whether critical paths are modified")
    lines_added: int = Field(description="Lines of code added")
    lines_removed: int = Field(description="Lines of code removed")
    files_changed: int = Field(description="Number of files changed")
    test_coverage_delta: float = Field(description="Change in test coverage percentage")
    historical_regression_risk: float = Field(description="Similarity to past buggy changes (0-1)")
    
    def calculate_score(self) -> float:
        """Calculate weighted blast radius score (0-100)"""
        score = 0.0
        
        # Downstream dependencies (30% weight)
        score += min(self.downstream_dependencies * 3, 30)
        
        # Critical path (25% weight)
        if self.critical_path_touched:
            score += 25
        
        # Change size (20% weight)
        total_changes = self.lines_added + self.lines_removed
        if total_changes > 1000:
            score += 20
        elif total_changes > 500:
            score += 15
        elif total_changes > 100:
            score += 10
        
        # Files changed (10% weight)
        score += min(self.files_changed * 2, 10)
        
        # Test coverage delta (8% weight)
        if self.test_coverage_delta < -5:
            score += 8
        elif self.test_coverage_delta < 0:
            score += 4
        
        # Historical regression risk (7% weight)
        score += self.historical_regression_risk * 7
        
        return min(score, 100)


# === Author/Reviewer Dynamics Models ===

class DynamicsMetrics(BaseModel):
    """Sub-metrics for Author/Reviewer Dynamics Score"""
    author_experience_score: float = Field(description="Author experience in repo (0-100)")
    reviewer_load: int = Field(description="Number of PRs assigned to reviewers")
    approval_ratio: float = Field(description="Ratio of approvals vs change requests")
    author_merge_history: int = Field(description="Number of past merges by author")
    avg_review_time_hours: float = Field(description="Average time for reviews")
    
    def calculate_score(self) -> float:
        """Calculate weighted dynamics score (0-100)"""
        score = 0.0
        
        # Author experience (40% weight)
        if self.author_experience_score < 20:
            score += 40
        elif self.author_experience_score < 50:
            score += 25
        elif self.author_experience_score < 70:
            score += 10
        
        # Reviewer load (30% weight)
        if self.reviewer_load > 10:
            score += 30
        elif self.reviewer_load > 5:
            score += 20
        elif self.reviewer_load > 3:
            score += 10
        
        # Approval ratio (20% weight)
        if self.approval_ratio < 0.5:
            score += 20
        elif self.approval_ratio < 0.7:
            score += 15
        elif self.approval_ratio < 0.9:
            score += 5
        
        # Review time (10% weight)
        if self.avg_review_time_hours > 72:
            score += 10
        elif self.avg_review_time_hours > 48:
            score += 6
        
        return min(score, 100)


# === Business Impact Models ===

class BusinessImpactMetrics(BaseModel):
    """Sub-metrics for Business Impact Score"""
    linked_to_release: bool = Field(description="Whether PR is linked to release milestone")
    external_dependencies: int = Field(description="Number of external API/service dependencies")
    priority_label: Optional[str] = Field(description="Priority label from PR")
    affects_core_functionality: bool = Field(description="Whether it affects core features")
    
    def calculate_score(self) -> float:
        """Calculate weighted business impact score (0-100)"""
        score = 0.0
        
        # Release link (40% weight)
        if self.linked_to_release:
            score += 40
        
        # External dependencies (25% weight)
        score += min(self.external_dependencies * 8, 25)
        
        # Priority label (20% weight)
        if self.priority_label:
            priority_scores = {
                "critical": 20,
                "high": 15,
                "medium": 10,
                "low": 5
            }
            score += priority_scores.get(self.priority_label.lower(), 0)
        
        # Core functionality (15% weight)
        if self.affects_core_functionality:
            score += 15
        
        return min(score, 100)


# === Composite Models ===

class CompositeRiskScore(BaseModel):
    """Composite risk scores for a PR"""
    stuckness_score: float = Field(description="Stuckness score (0-100)")
    blast_radius_score: float = Field(description="Blast radius score (0-100)")
    dynamics_score: float = Field(description="Dynamics score (0-100)")
    business_impact_score: float = Field(description="Business impact score (0-100)")
    
    @property
    def delivery_risk_score(self) -> float:
        """Calculate overall delivery risk score with weights:
        40% Stuckness + 30% Blast Radius + 20% Dynamics + 10% Business Impact"""
        return (
            self.stuckness_score * 0.4 +
            self.blast_radius_score * 0.3 +
            self.dynamics_score * 0.2 +
            self.business_impact_score * 0.1
        )
    
    @property
    def risk_level(self) -> RiskLevel:
        """Determine risk level based on delivery risk score"""
        score = self.delivery_risk_score
        if score >= 80:
            return RiskLevel.CRITICAL
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW


# === New Detailed PR Information Models ===

class FileChange(BaseModel):
    """Information about a single file changed in the PR"""
    filename: str
    status: str  # added, removed, modified, renamed
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None  # The actual diff
    blob_url: Optional[str] = None
    previous_filename: Optional[str] = None  # For renamed files


class CICheckRun(BaseModel):
    """CI/CD check run information"""
    name: str
    status: str  # queued, in_progress, completed
    conclusion: Optional[str] = None  # success, failure, neutral, cancelled, skipped, timed_out, action_required
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    html_url: Optional[str] = None
    details_url: Optional[str] = None


class PRComment(BaseModel):
    """Comment on a PR (issue comment or review comment)"""
    id: int
    author: str
    body: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    comment_type: str  # issue_comment, review_comment, review
    in_reply_to_id: Optional[int] = None
    path: Optional[str] = None  # For review comments
    line: Optional[int] = None  # For review comments


class PRLabel(BaseModel):
    """Label on a PR"""
    name: str
    color: str
    description: Optional[str] = None


class LinkedIssue(BaseModel):
    """Issue linked to the PR"""
    number: int
    title: str
    state: str  # open, closed
    url: str
    created_at: datetime
    closed_at: Optional[datetime] = None
    labels: List[str] = Field(default_factory=list)


class PRTimelineMetrics(BaseModel):
    """Detailed timeline metrics for a PR"""
    time_to_first_review_hours: Optional[float] = None
    time_to_first_approval_hours: Optional[float] = None
    time_to_merge_hours: Optional[float] = None
    first_commit_at: Optional[datetime] = None
    last_commit_at: Optional[datetime] = None
    time_from_first_to_last_commit_hours: Optional[float] = None
    total_review_time_hours: Optional[float] = None
    total_wait_time_hours: Optional[float] = None
    number_of_review_cycles: int = 0


class PRReviewSummary(BaseModel):
    """Summary of PR reviews"""
    total_reviews: int = 0
    approved_count: int = 0
    changes_requested_count: int = 0
    commented_count: int = 0
    reviewers: List[str] = Field(default_factory=list)
    review_comments: List[PRComment] = Field(default_factory=list)


class PRDetailedInfo(BaseModel):
    """Comprehensive detailed information about a PR"""
    # Basic info
    description: Optional[str] = None
    body_text: Optional[str] = None  # Plain text version
    
    # Files and changes
    files: List[FileChange] = Field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    total_changes: int = 0
    
    # CI/CD
    ci_checks: List[CICheckRun] = Field(default_factory=list)
    ci_status: str = "unknown"  # pending, success, failure, error
    
    # Timeline
    timeline_metrics: PRTimelineMetrics
    
    # Comments and discussions
    comments: List[PRComment] = Field(default_factory=list)
    total_comments: int = 0
    
    # Labels
    labels: List[PRLabel] = Field(default_factory=list)
    
    # Linked issues
    linked_issues: List[LinkedIssue] = Field(default_factory=list)
    
    # Reviews
    review_summary: PRReviewSummary
    
    # Commits
    commit_count: int = 0
    commits_authors: List[str] = Field(default_factory=list)  # All authors who contributed
    
    # Additional metadata
    mergeable: Optional[bool] = None
    mergeable_state: Optional[str] = None
    draft: bool = False
    requested_reviewers: List[str] = Field(default_factory=list)
    assignees: List[str] = Field(default_factory=list)


# === PR Analysis Models ===

class PRRiskAnalysis(BaseModel):
    """Complete risk analysis for a single PR"""
    pr_number: int
    title: str
    author: str
    state: PRState
    created_at: datetime
    updated_at: datetime
    url: str
    
    # Sub-metrics
    stuckness_metrics: StucknessMetrics
    blast_radius_metrics: BlastRadiusMetrics
    dynamics_metrics: DynamicsMetrics
    business_impact_metrics: BusinessImpactMetrics
    
    # Composite scores
    composite_scores: CompositeRiskScore
    
    # Detailed PR information
    detailed_info: Optional[PRDetailedInfo] = None
    
    # LLM-generated insights
    ai_summary: Optional[str] = Field(description="AI-generated summary of risks")
    
    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def risk_level(self) -> RiskLevel:
        return self.composite_scores.risk_level
    
    @property
    def delivery_risk_score(self) -> float:
        return self.composite_scores.delivery_risk_score


class RepositoryRiskReport(BaseModel):
    """Complete risk report for a repository"""
    owner: str
    repo: str
    analyzed_at: datetime
    total_prs_analyzed: int
    
    # Individual PR analyses
    pr_analyses: List[PRRiskAnalysis]
    
    # Aggregate metrics
    avg_delivery_risk_score: float
    high_risk_pr_count: int
    critical_risk_pr_count: int
    
    # Team-level insights
    team_velocity_impact: float = Field(description="Impact on team velocity (0-100)")
    release_risk_assessment: str = Field(description="Overall release risk assessment")


# === Database Models (File-based temporary storage) ===

class PRRiskDatabase(BaseModel):
    """Temporary file-based database for PR risk data"""
    repositories: Dict[str, RepositoryRiskReport] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    def get_repo_key(self, owner: str, repo: str) -> str:
        """Generate key for repository"""
        return f"{owner}/{repo}"
    
    def add_or_update_repo(self, report: RepositoryRiskReport):
        """Add or update repository risk report"""
        key = self.get_repo_key(report.owner, report.repo)
        self.repositories[key] = report
        self.last_updated = datetime.now()
    
    def get_repo_report(self, owner: str, repo: str) -> Optional[RepositoryRiskReport]:
        """Get repository risk report"""
        key = self.get_repo_key(owner, repo)
        return self.repositories.get(key)


# === API Request/Response Models ===

class PRRiskAnalysisRequest(BaseModel):
    """Request model for PR risk analysis"""
    owner: str
    repo: str
    force_refresh: bool = False
    include_closed_prs: bool = False
    max_prs: Optional[int] = 50
    

class PRRiskAnalysisResponse(BaseModel):
    """Response model for PR risk analysis"""
    success: bool
    repository_report: Optional[RepositoryRiskReport] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    api_requests_made: Optional[int] = None


class PRListItem(BaseModel):
    """Simplified PR item for list views"""
    pr_number: int
    title: str
    author: str
    state: PRState
    delivery_risk_score: float
    risk_level: RiskLevel
    created_at: datetime
    updated_at: datetime
    url: str
    ai_summary: Optional[str] = None


class DashboardSummary(BaseModel):
    """Summary data for dashboard"""
    total_prs: int
    high_risk_count: int
    critical_risk_count: int
    avg_risk_score: float
    team_velocity_impact: float
    top_risk_prs: List[PRListItem]
    risk_distribution: Dict[str, int]  # risk level -> count