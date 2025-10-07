"""
Response schemas for AI analysis endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalysisStatusResponse(str, Enum):
    """Response enum for analysis status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BaseAIAnalysisResponse(BaseModel):
    """Base response for AI analysis."""

    id: int = Field(..., description="Analysis ID")
    analysis_type: str = Field(..., description="Type of analysis")
    status: AnalysisStatusResponse = Field(..., description="Analysis status")
    ai_model: str = Field(..., description="AI model used")

    # Output data
    output_data: Optional[Dict[str, Any]] = Field(
        None, description="Structured output data"
    )
    output_text: Optional[str] = Field(None, description="Raw text output")
    confidence_score: Optional[int] = Field(
        None, ge=0, le=100, description="Confidence score (0-100)"
    )

    # Metadata
    processing_time_ms: Optional[int] = Field(
        None, description="Processing time in milliseconds"
    )
    token_usage: Optional[Dict[str, int]] = Field(
        None, description="Token usage statistics"
    )

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        use_enum_values = True


class PRSummaryResponse(BaseAIAnalysisResponse):
    """Response for PR summary analysis."""

    # Structured output
    summary: Optional[str] = Field(None, description="PR summary")
    key_changes: Optional[List[str]] = Field(None, description="Key changes identified")
    risk_level: Optional[str] = Field(None, description="Risk level assessment")
    code_quality_score: Optional[int] = Field(
        None, ge=0, le=100, description="Code quality score"
    )
    performance_impact: Optional[str] = Field(
        None, description="Performance impact assessment"
    )

    # Recommendations
    recommendations: Optional[List[str]] = Field(None, description="AI recommendations")
    suggested_reviewers: Optional[List[str]] = Field(
        None, description="Suggested reviewers"
    )

    # Metadata
    files_analyzed: Optional[int] = Field(None, description="Number of files analyzed")
    lines_changed: Optional[int] = Field(None, description="Lines changed")


class CodeReviewResponse(BaseAIAnalysisResponse):
    """Response for code review analysis."""

    # Review findings
    security_issues: Optional[List[Dict[str, Any]]] = Field(
        None, description="Security issues found"
    )
    performance_issues: Optional[List[Dict[str, Any]]] = Field(
        None, description="Performance issues found"
    )
    best_practice_violations: Optional[List[Dict[str, Any]]] = Field(
        None, description="Best practice violations"
    )
    readability_issues: Optional[List[Dict[str, Any]]] = Field(
        None, description="Readability issues found"
    )

    # Overall assessment
    overall_score: Optional[int] = Field(
        None, ge=0, le=100, description="Overall code quality score"
    )
    severity_level: Optional[str] = Field(None, description="Overall severity level")

    # Recommendations
    improvement_suggestions: Optional[List[str]] = Field(
        None, description="Improvement suggestions"
    )
    refactoring_opportunities: Optional[List[str]] = Field(
        None, description="Refactoring opportunities"
    )


class RiskAssessmentResponse(BaseAIAnalysisResponse):
    """Response for risk assessment analysis."""

    # Risk scores
    overall_risk_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Overall risk score"
    )
    blast_radius_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Blast radius score"
    )
    author_experience_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Author experience score"
    )
    reviewer_load_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Reviewer load score"
    )
    ci_status_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="CI status score"
    )

    # Risk level
    risk_level: Optional[str] = Field(
        None, description="Risk level (LOW, MEDIUM, HIGH, CRITICAL)"
    )

    # Risk factors
    risk_factors: Optional[List[Dict[str, Any]]] = Field(
        None, description="Identified risk factors"
    )
    mitigation_strategies: Optional[List[str]] = Field(
        None, description="Mitigation strategies"
    )

    # Recommendations
    recommended_actions: Optional[List[str]] = Field(
        None, description="Recommended actions"
    )


class TechnicalDebtResponse(BaseAIAnalysisResponse):
    """Response for technical debt analysis."""

    # Debt metrics
    overall_debt_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Overall technical debt score"
    )
    complexity_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Code complexity score"
    )
    duplication_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Code duplication score"
    )
    test_coverage_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Test coverage score"
    )
    documentation_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Documentation score"
    )

    # Debt areas
    debt_areas: Optional[List[Dict[str, Any]]] = Field(
        None, description="Areas with technical debt"
    )
    critical_issues: Optional[List[Dict[str, Any]]] = Field(
        None, description="Critical technical debt issues"
    )

    # Recommendations
    refactoring_priorities: Optional[List[str]] = Field(
        None, description="Refactoring priorities"
    )
    improvement_roadmap: Optional[List[Dict[str, Any]]] = Field(
        None, description="Improvement roadmap"
    )


class CustomAnalysisResponse(BaseAIAnalysisResponse):
    """Response for custom analysis."""

    # Custom output
    custom_output: Optional[Dict[str, Any]] = Field(
        None, description="Custom analysis output"
    )
    formatted_output: Optional[str] = Field(None, description="Formatted output text")

    # Metadata
    output_format: Optional[str] = Field(None, description="Output format used")
    processing_notes: Optional[List[str]] = Field(None, description="Processing notes")


class BatchAnalysisResponse(BaseModel):
    """Response for batch analysis."""

    batch_id: str = Field(..., description="Batch analysis ID")
    total_analyses: int = Field(..., description="Total number of analyses")
    completed_analyses: int = Field(..., description="Number of completed analyses")
    failed_analyses: int = Field(..., description="Number of failed analyses")

    # Results
    results: List[BaseAIAnalysisResponse] = Field(..., description="Analysis results")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Error details")

    # Performance
    total_processing_time_ms: int = Field(
        ..., description="Total processing time in milliseconds"
    )
    parallel_execution: bool = Field(
        ..., description="Whether analyses ran in parallel"
    )

    # Timestamps
    started_at: datetime = Field(..., description="Batch start timestamp")
    completed_at: Optional[datetime] = Field(
        None, description="Batch completion timestamp"
    )


class PromptTemplateResponse(BaseModel):
    """Response for prompt template operations."""

    id: int = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    analysis_type: str = Field(..., description="Analysis type")
    ai_model: str = Field(..., description="AI model")

    # Template content
    system_prompt: str = Field(..., description="System prompt")
    user_prompt_template: str = Field(..., description="User prompt template")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="Output schema")

    # Configuration
    temperature: int = Field(..., description="Temperature setting")
    max_tokens: int = Field(..., description="Maximum tokens")
    is_active: bool = Field(..., description="Whether template is active")

    # Metadata
    version: str = Field(..., description="Template version")
    created_by: Optional[int] = Field(None, description="Creator user ID")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        use_enum_values = True


class AIUsageMetricsResponse(BaseModel):
    """Response for AI usage metrics."""

    # Time period
    start_date: datetime = Field(..., description="Start date of metrics")
    end_date: datetime = Field(..., description="End date of metrics")

    # Usage statistics
    total_analyses: int = Field(..., description="Total number of analyses")
    successful_analyses: int = Field(..., description="Number of successful analyses")
    failed_analyses: int = Field(..., description="Number of failed analyses")

    # Token usage
    total_tokens: int = Field(..., description="Total tokens used")
    input_tokens: int = Field(..., description="Input tokens used")
    output_tokens: int = Field(..., description="Output tokens used")

    # Cost tracking
    total_cost_cents: int = Field(..., description="Total cost in cents")
    average_cost_per_analysis: float = Field(
        ..., description="Average cost per analysis"
    )

    # Performance metrics
    average_processing_time_ms: float = Field(
        ..., description="Average processing time in milliseconds"
    )

    # Model breakdown
    model_usage: Dict[str, Dict[str, Any]] = Field(
        ..., description="Usage breakdown by model"
    )

    # Analysis type breakdown
    analysis_type_usage: Dict[str, Dict[str, Any]] = Field(
        ..., description="Usage breakdown by analysis type"
    )


class AIHealthResponse(BaseModel):
    """Response for AI service health check."""

    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")

    # Service status
    azure_openai_status: str = Field(..., description="Azure OpenAI service status")
    openai_status: str = Field(..., description="OpenAI service status")
    anthropic_status: str = Field(..., description="Anthropic service status")

    # Performance metrics
    average_response_time_ms: float = Field(..., description="Average response time")
    success_rate: float = Field(..., description="Success rate percentage")

    # Resource usage
    active_connections: int = Field(..., description="Active connections")
    queue_size: int = Field(..., description="Queue size")

    # Error details
    recent_errors: Optional[List[Dict[str, Any]]] = Field(
        None, description="Recent errors"
    )
