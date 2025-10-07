"""
AI Analysis Models for storing AI-generated insights and analysis results.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import relationship

from core.database import Base


class AnalysisType(str, Enum):
    """Types of AI analysis that can be performed."""

    PR_SUMMARY = "pr_summary"
    CODE_REVIEW = "code_review"
    RISK_ASSESSMENT = "risk_assessment"
    TECHNICAL_DEBT = "technical_debt"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    SECURITY_ANALYSIS = "security_analysis"
    DOCUMENTATION = "documentation"
    CUSTOM = "custom"
    # New PR analysis types
    PR_RISK_FLAGS = "pr_risk_flags"
    PR_BLOCKER_FLAGS = "pr_blocker_flags"
    COPILOT_INSIGHTS = "copilot_insights"
    NARRATIVE_TIMELINE = "narrative_timeline"
    AI_ROI = "ai_roi"


class AnalysisStatus(str, Enum):
    """Status of AI analysis."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AIModel(str, Enum):
    """Supported AI models."""

    AZURE_OPENAI_GPT4O_MINI = "azure_openai_gpt4o_mini"
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT35_TURBO = "openai_gpt35_turbo"
    ANTHROPIC_CLAUDE = "anthropic_claude"


class AIAnalysis(Base):
    """Model for storing AI analysis results."""

    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)

    # Analysis metadata
    analysis_type = Column(SQLEnum(AnalysisType, values_callable=lambda x: [
                           e.value for e in x]), nullable=False, index=True)
    status = Column(SQLEnum(AnalysisStatus, values_callable=lambda x: [e.value for e in x]),
                    default=AnalysisStatus.PENDING, index=True)
    ai_model = Column(SQLEnum(AIModel, values_callable=lambda x: [
                      e.value for e in x]), nullable=False, index=True)

    # Input data
    input_data = Column(JSON, nullable=False)  # Structured input data
    input_text = Column(Text)  # Raw text input for analysis

    # Output data
    output_data = Column(JSON)  # Structured output data
    output_text = Column(Text)  # Raw text output from AI
    confidence_score = Column(Integer)  # 0-100 confidence score

    # Metadata
    prompt_template = Column(String(255))  # Name of prompt template used
    processing_time_ms = Column(Integer)  # Processing time in milliseconds
    token_usage = Column(JSON)  # Token usage statistics

    # Relationships
    # User who requested analysis
    user_id = Column(Integer, nullable=True, index=True)
    team_id = Column(Integer, nullable=True, index=True)  # Team context
    pull_request_id = Column(Integer, nullable=True, index=True)  # Related PR

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    def __repr__(self):
        return f"<AIAnalysis(id={self.id}, type={self.analysis_type}, status={self.status})>"


class AIPromptTemplate(Base):
    """Model for storing AI prompt templates."""

    __tablename__ = "ai_prompt_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template metadata
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    analysis_type = Column(SQLEnum(AnalysisType, values_callable=lambda x: [
                           e.value for e in x]), nullable=False, index=True)
    ai_model = Column(SQLEnum(AIModel, values_callable=lambda x: [
                      e.value for e in x]), nullable=False, index=True)

    # Template content
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    output_schema = Column(JSON)  # Expected output structure

    # Configuration
    temperature = Column(Integer, default=70)  # 0-100 scale
    max_tokens = Column(Integer, default=4000)
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive

    # Metadata
    version = Column(String(50), default="1.0")
    # User who created the template
    created_by = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AIPromptTemplate(id={self.id}, name={self.name}, type={self.analysis_type})>"


class AIUsageMetrics(Base):
    """Model for tracking AI usage and costs."""

    __tablename__ = "ai_usage_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # Usage metadata
    ai_model = Column(SQLEnum(AIModel, values_callable=lambda x: [
                      e.value for e in x]), nullable=False, index=True)
    analysis_type = Column(SQLEnum(AnalysisType, values_callable=lambda x: [
                           e.value for e in x]), nullable=False, index=True)

    # Token usage
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Cost tracking
    input_cost = Column(Integer, default=0)  # Cost in cents
    output_cost = Column(Integer, default=0)  # Cost in cents
    total_cost = Column(Integer, default=0)  # Cost in cents

    # Performance metrics
    processing_time_ms = Column(Integer, default=0)
    success = Column(Integer, default=1)  # 1 for success, 0 for failure

    # Context
    user_id = Column(Integer, nullable=True, index=True)
    team_id = Column(Integer, nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AIUsageMetrics(id={self.id}, model={self.ai_model}, tokens={self.total_tokens})>"
