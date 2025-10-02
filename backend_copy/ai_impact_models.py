"""
AI Impact Analysis Data Models
Defines the data structures for AI authorship detection and impact analysis.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class AIConfidenceLevel(str, Enum):
    """AI detection confidence levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class AIAuthorshipResult(BaseModel):
    """Result of AI authorship detection for a single PR"""
    pr_number: int
    confidence: AIConfidenceLevel
    ai_probability: float = Field(ge=0.0, le=1.0)
    indicators: List[str] = []
    file_analysis: Dict[str, Any] = {}
    commit_patterns: Dict[str, Any] = {}


class AIImpactMetrics(BaseModel):
    """Core AI impact metrics for a repository"""
    total_prs_analyzed: int
    ai_authored_prs: int
    human_authored_prs: int
    ai_adoption_rate: float = Field(ge=0.0, le=1.0)
    
    # Performance comparisons
    ai_avg_merge_time_hours: Optional[float] = None
    human_avg_merge_time_hours: Optional[float] = None
    ai_avg_review_cycles: Optional[float] = None
    human_avg_review_cycles: Optional[float] = None
    
    # Code quality indicators
    ai_avg_files_changed: Optional[float] = None
    human_avg_files_changed: Optional[float] = None
    ai_avg_lines_changed: Optional[float] = None
    human_avg_lines_changed: Optional[float] = None


class AITrendAnalysis(BaseModel):
    """AI adoption trends over time"""
    weekly_ai_adoption: Dict[str, float] = {}
    weekly_ai_prs: Dict[str, int] = {}
    weekly_total_prs: Dict[str, int] = {}
    trend_direction: str = "stable"  # "increasing", "decreasing", "stable"


class AIQualityAssessment(BaseModel):
    """Quality assessment of AI-generated code"""
    high_risk_ai_prs: List[int] = []
    quality_score: float = Field(ge=0.0, le=100.0, default=50.0)
    common_issues: List[str] = []
    recommendations: List[str] = []


class AIImpactAnalysis(BaseModel):
    """Complete AI impact analysis for a repository"""
    repository: str
    analysis_date: datetime
    days_analyzed: int
    
    # Core metrics
    metrics: AIImpactMetrics
    trends: AITrendAnalysis
    quality: AIQualityAssessment
    
    # Individual PR results
    pr_analyses: List[AIAuthorshipResult] = []
    
    # Summary
    impact_score: float = Field(ge=0.0, le=100.0)
    confidence_level: AIConfidenceLevel
    summary_insights: List[str] = []


class AIImpactRequest(BaseModel):
    """Request model for AI impact analysis"""
    owner: str
    repo: str
    days: int = 90
    force_refresh: bool = False
    include_detailed_analysis: bool = True


class AIImpactResponse(BaseModel):
    """Response model for AI impact analysis"""
    success: bool
    repository: str
    analysis_date: datetime
    analysis: Optional[AIImpactAnalysis] = None
    error_message: Optional[str] = None
