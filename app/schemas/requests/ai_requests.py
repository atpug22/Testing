"""
Request schemas for AI analysis endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class AnalysisTypeRequest(str, Enum):
    """Request enum for analysis types."""

    PR_SUMMARY = "pr_summary"
    CODE_REVIEW = "code_review"
    RISK_ASSESSMENT = "risk_assessment"
    TECHNICAL_DEBT = "technical_debt"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    SECURITY_ANALYSIS = "security_analysis"
    DOCUMENTATION = "documentation"
    CUSTOM = "custom"


class AIModelRequest(str, Enum):
    """Request enum for AI models."""

    AZURE_OPENAI_GPT4O_MINI = "azure_openai_gpt4o_mini"
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT35_TURBO = "openai_gpt35_turbo"
    ANTHROPIC_CLAUDE = "anthropic_claude"


class BaseAIAnalysisRequest(BaseModel):
    """Base request for AI analysis."""

    analysis_type: AnalysisTypeRequest = Field(
        ..., description="Type of analysis to perform"
    )
    ai_model: Optional[AIModelRequest] = Field(
        None, description="AI model to use (defaults to configured model)"
    )
    custom_prompt: Optional[str] = Field(None, description="Custom prompt for analysis")
    temperature: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Temperature for AI generation"
    )
    max_tokens: Optional[int] = Field(
        None, ge=1, le=8000, description="Maximum tokens to generate"
    )

    class Config:
        use_enum_values = True


class PRSummaryRequest(BaseAIAnalysisRequest):
    """Request for PR summary analysis."""

    analysis_type: AnalysisTypeRequest = Field(default=AnalysisTypeRequest.PR_SUMMARY)

    # PR data
    pr_title: str = Field(..., description="Pull request title")
    pr_description: str = Field(..., description="Pull request description")
    changed_files: List[str] = Field(..., description="List of changed files")
    diff_content: Optional[str] = Field(None, description="Diff content")
    commit_messages: List[str] = Field(
        default_factory=list, description="Commit messages"
    )

    # Context
    repository_name: str = Field(..., description="Repository name")
    author: str = Field(..., description="PR author")
    reviewers: List[str] = Field(default_factory=list, description="List of reviewers")

    # Analysis preferences
    include_risk_assessment: bool = Field(
        default=True, description="Include risk assessment"
    )
    include_code_quality: bool = Field(
        default=True, description="Include code quality analysis"
    )
    include_performance_impact: bool = Field(
        default=False, description="Include performance impact analysis"
    )


class CodeReviewRequest(BaseAIAnalysisRequest):
    """Request for code review analysis."""

    analysis_type: AnalysisTypeRequest = Field(default=AnalysisTypeRequest.CODE_REVIEW)

    # Code data
    code_content: str = Field(..., description="Code content to review")
    file_path: str = Field(..., description="File path")
    language: str = Field(..., description="Programming language")

    # Context
    pr_context: Optional[str] = Field(None, description="PR context")
    coding_standards: Optional[str] = Field(
        None, description="Coding standards to follow"
    )

    # Review focus areas
    check_security: bool = Field(default=True, description="Check for security issues")
    check_performance: bool = Field(
        default=True, description="Check for performance issues"
    )
    check_best_practices: bool = Field(
        default=True, description="Check for best practices"
    )
    check_readability: bool = Field(default=True, description="Check for readability")


class RiskAssessmentRequest(BaseAIAnalysisRequest):
    """Request for risk assessment analysis."""

    analysis_type: AnalysisTypeRequest = Field(
        default=AnalysisTypeRequest.RISK_ASSESSMENT
    )

    # PR data
    pr_data: Dict[str, Any] = Field(..., description="PR data for risk assessment")

    # Risk factors to consider
    consider_blast_radius: bool = Field(
        default=True, description="Consider blast radius"
    )
    consider_author_experience: bool = Field(
        default=True, description="Consider author experience"
    )
    consider_reviewer_load: bool = Field(
        default=True, description="Consider reviewer load"
    )
    consider_ci_status: bool = Field(default=True, description="Consider CI status")

    # Risk thresholds
    high_risk_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="High risk threshold"
    )
    medium_risk_threshold: float = Field(
        default=0.4, ge=0.0, le=1.0, description="Medium risk threshold"
    )


class TechnicalDebtRequest(BaseAIAnalysisRequest):
    """Request for technical debt analysis."""

    analysis_type: AnalysisTypeRequest = Field(
        default=AnalysisTypeRequest.TECHNICAL_DEBT
    )

    # Codebase data
    codebase_data: Dict[str, Any] = Field(..., description="Codebase data for analysis")

    # Analysis scope
    analyze_complexity: bool = Field(
        default=True, description="Analyze code complexity"
    )
    analyze_duplication: bool = Field(
        default=True, description="Analyze code duplication"
    )
    analyze_test_coverage: bool = Field(
        default=True, description="Analyze test coverage"
    )
    analyze_documentation: bool = Field(
        default=True, description="Analyze documentation"
    )


class CustomAnalysisRequest(BaseAIAnalysisRequest):
    """Request for custom analysis."""

    analysis_type: AnalysisTypeRequest = Field(default=AnalysisTypeRequest.CUSTOM)

    # Custom data
    input_data: Dict[str, Any] = Field(..., description="Custom input data")
    custom_prompt: str = Field(..., description="Custom prompt for analysis")

    # Output preferences
    output_format: str = Field(default="json", description="Desired output format")
    include_confidence: bool = Field(
        default=True, description="Include confidence scores"
    )


class BatchAnalysisRequest(BaseModel):
    """Request for batch analysis."""

    analyses: List[BaseAIAnalysisRequest] = Field(
        ..., min_items=1, max_items=10, description="List of analyses to perform"
    )
    parallel: bool = Field(default=True, description="Run analyses in parallel")
    priority: int = Field(
        default=5, ge=1, le=10, description="Priority level (1=highest, 10=lowest)"
    )


class PromptTemplateRequest(BaseModel):
    """Request for creating/updating prompt templates."""

    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    analysis_type: AnalysisTypeRequest = Field(..., description="Analysis type")
    ai_model: AIModelRequest = Field(..., description="AI model")

    system_prompt: str = Field(..., min_length=1, description="System prompt")
    user_prompt_template: str = Field(
        ..., min_length=1, description="User prompt template"
    )
    output_schema: Optional[Dict[str, Any]] = Field(
        None, description="Expected output schema"
    )

    temperature: int = Field(
        default=70, ge=0, le=100, description="Temperature (0-100)"
    )
    max_tokens: int = Field(default=4000, ge=1, le=8000, description="Maximum tokens")
    is_active: bool = Field(default=True, description="Whether template is active")

    version: str = Field(default="1.0", description="Template version")

    class Config:
        use_enum_values = True
