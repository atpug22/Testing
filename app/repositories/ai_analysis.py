"""
Repository for AI analysis data operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_analysis import (
    AIAnalysis,
    AIModel,
    AIPromptTemplate,
    AIUsageMetrics,
    AnalysisStatus,
    AnalysisType,
)
from core.repository.base import BaseRepository

logger = logging.getLogger(__name__)


class AIAnalysisRepository(BaseRepository[AIAnalysis]):
    """Repository for AI analysis operations."""

    def __init__(self, db_session: AsyncSession):
        super().__init__(AIAnalysis, db_session)

    async def get_by_id(self, analysis_id: int) -> Optional[AIAnalysis]:
        """Get analysis by ID."""
        query = select(AIAnalysis).where(AIAnalysis.id == analysis_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        analysis_type: Optional[AnalysisType] = None,
        status: Optional[AnalysisStatus] = None,
    ) -> List[AIAnalysis]:
        """Get analyses by user with optional filtering."""
        query = select(AIAnalysis).where(AIAnalysis.user_id == user_id)

        if analysis_type:
            query = query.where(AIAnalysis.analysis_type == analysis_type)

        if status:
            query = query.where(AIAnalysis.status == status)

        query = query.order_by(desc(AIAnalysis.created_at)
                               ).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_team(
        self,
        team_id: int,
        limit: int = 50,
        offset: int = 0,
        analysis_type: Optional[AnalysisType] = None,
        status: Optional[AnalysisStatus] = None,
    ) -> List[AIAnalysis]:
        """Get analyses by team with optional filtering."""
        query = select(AIAnalysis).where(AIAnalysis.team_id == team_id)

        if analysis_type:
            query = query.where(AIAnalysis.analysis_type == analysis_type)

        if status:
            query = query.where(AIAnalysis.status == status)

        query = query.order_by(desc(AIAnalysis.created_at)
                               ).limit(limit).offset(offset)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_pull_request(
        self, pull_request_id: int, analysis_type: Optional[AnalysisType] = None
    ) -> List[AIAnalysis]:
        """Get analyses by pull request."""
        query = select(AIAnalysis).where(
            AIAnalysis.pull_request_id == pull_request_id)

        if analysis_type:
            query = query.where(AIAnalysis.analysis_type == analysis_type)

        query = query.order_by(desc(AIAnalysis.created_at))

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_recent_analyses(
        self, hours: int = 24, limit: int = 100
    ) -> List[AIAnalysis]:
        """Get recent analyses within specified hours."""
        since = datetime.utcnow() - timedelta(hours=hours)

        query = (
            select(AIAnalysis)
            .where(AIAnalysis.created_at >= since)
            .order_by(desc(AIAnalysis.created_at))
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_failed_analyses(
        self, limit: int = 50, retry_count_threshold: int = 3
    ) -> List[AIAnalysis]:
        """Get failed analyses that can be retried."""
        query = (
            select(AIAnalysis)
            .where(
                and_(
                    AIAnalysis.status == AnalysisStatus.FAILED,
                    AIAnalysis.retry_count < retry_count_threshold,
                )
            )
            .order_by(desc(AIAnalysis.created_at))
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_status(
        self,
        analysis_id: int,
        status: AnalysisStatus,
        error_message: Optional[str] = None,
        output_data: Optional[Dict[str, Any]] = None,
        output_text: Optional[str] = None,
        confidence_score: Optional[int] = None,
        processing_time_ms: Optional[int] = None,
        token_usage: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Update analysis status and results."""
        try:
            analysis = await self.get_by_id(analysis_id)
            if not analysis:
                return False

            analysis.status = status
            analysis.updated_at = datetime.utcnow()

            if error_message:
                analysis.error_message = error_message

            if output_data is not None:
                analysis.output_data = output_data

            if output_text is not None:
                analysis.output_text = output_text

            if confidence_score is not None:
                analysis.confidence_score = confidence_score

            if processing_time_ms is not None:
                analysis.processing_time_ms = processing_time_ms

            if token_usage is not None:
                analysis.token_usage = token_usage

            if status == AnalysisStatus.COMPLETED:
                analysis.completed_at = datetime.utcnow()

            await self.session.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to update analysis status: {e}")
            await self.session.rollback()
            return False

    async def increment_retry_count(self, analysis_id: int) -> bool:
        """Increment retry count for failed analysis."""
        try:
            analysis = await self.get_by_id(analysis_id)
            if not analysis:
                return False

            analysis.retry_count += 1
            analysis.updated_at = datetime.utcnow()

            await self.session.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to increment retry count: {e}")
            await self.session.rollback()
            return False

    async def get_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        analysis_type: Optional[AnalysisType] = None,
    ) -> Dict[str, Any]:
        """Get analytics data for AI analyses."""
        query = select(AIAnalysis)

        # Apply filters
        if start_date:
            query = query.where(AIAnalysis.created_at >= start_date)

        if end_date:
            query = query.where(AIAnalysis.created_at <= end_date)

        if user_id:
            query = query.where(AIAnalysis.user_id == user_id)

        if team_id:
            query = query.where(AIAnalysis.team_id == team_id)

        if analysis_type:
            query = query.where(AIAnalysis.analysis_type == analysis_type)

        # Execute query
        result = await self.session.execute(query)
        analyses = result.scalars().all()

        # Calculate analytics
        total_analyses = len(analyses)
        successful_analyses = len(
            [a for a in analyses if a.status == AnalysisStatus.COMPLETED]
        )
        failed_analyses = len(
            [a for a in analyses if a.status == AnalysisStatus.FAILED]
        )

        # Status breakdown
        status_breakdown = {}
        for status in AnalysisStatus:
            count = len([a for a in analyses if a.status == status])
            status_breakdown[status.value] = count

        # Analysis type breakdown
        type_breakdown = {}
        for analysis_type in AnalysisType:
            count = len(
                [a for a in analyses if a.analysis_type == analysis_type])
            type_breakdown[analysis_type.value] = count

        # Model breakdown
        model_breakdown = {}
        for model in AIModel:
            count = len([a for a in analyses if a.ai_model == model])
            model_breakdown[model.value] = count

        # Performance metrics
        completed_analyses = [
            a for a in analyses if a.status == AnalysisStatus.COMPLETED
        ]
        avg_processing_time = 0
        if completed_analyses:
            total_time = sum(
                a.processing_time_ms or 0 for a in completed_analyses)
            avg_processing_time = total_time / len(completed_analyses)

        # Token usage
        total_tokens = sum(
            (a.token_usage or {}).get("total_tokens", 0) for a in completed_analyses
        )

        return {
            "total_analyses": total_analyses,
            "successful_analyses": successful_analyses,
            "failed_analyses": failed_analyses,
            "success_rate": (
                (successful_analyses / total_analyses * 100)
                if total_analyses > 0
                else 0
            ),
            "status_breakdown": status_breakdown,
            "type_breakdown": type_breakdown,
            "model_breakdown": model_breakdown,
            "average_processing_time_ms": avg_processing_time,
            "total_tokens_used": total_tokens,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }


class AIPromptTemplateRepository(BaseRepository[AIPromptTemplate]):
    """Repository for AI prompt template operations."""

    def __init__(self, db_session: AsyncSession):
        super().__init__(AIPromptTemplate, db_session)

    async def get_by_name(self, name: str) -> Optional[AIPromptTemplate]:
        """Get prompt template by name."""
        query = select(AIPromptTemplate).where(AIPromptTemplate.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_type_and_model(
        self, analysis_type: AnalysisType, ai_model: AIModel
    ) -> List[AIPromptTemplate]:
        """Get prompt templates by analysis type and AI model."""
        query = (
            select(AIPromptTemplate)
            .where(
                and_(
                    AIPromptTemplate.analysis_type == analysis_type,
                    AIPromptTemplate.ai_model == ai_model,
                    AIPromptTemplate.is_active == 1,
                )
            )
            .order_by(desc(AIPromptTemplate.created_at))
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_active_templates(
        self, analysis_type: Optional[AnalysisType] = None
    ) -> List[AIPromptTemplate]:
        """Get active prompt templates."""
        query = select(AIPromptTemplate).where(AIPromptTemplate.is_active == 1)

        if analysis_type:
            query = query.where(
                AIPromptTemplate.analysis_type == analysis_type)

        query = query.order_by(desc(AIPromptTemplate.created_at))

        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_template(
        self,
        name: str,
        description: str,
        analysis_type: AnalysisType,
        ai_model: AIModel,
        system_prompt: str,
        user_prompt_template: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: int = 70,
        max_tokens: int = 4000,
        created_by: Optional[int] = None,
    ) -> AIPromptTemplate:
        """Create a new prompt template."""
        template = AIPromptTemplate(
            name=name,
            description=description,
            analysis_type=analysis_type,
            ai_model=ai_model,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            output_schema=output_schema,
            temperature=temperature,
            max_tokens=max_tokens,
            created_by=created_by,
        )

        self.session.add(template)
        await self.session.flush()
        await self.session.refresh(template)

        return template

    async def update_template(
        self, template_id: int, **updates
    ) -> Optional[AIPromptTemplate]:
        """Update a prompt template."""
        template = await self.get_by_id(template_id)
        if not template:
            return None

        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        template.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(template)

        return template

    async def deactivate_template(self, template_id: int) -> bool:
        """Deactivate a prompt template."""
        template = await self.get_by_id(template_id)
        if not template:
            return False

        template.is_active = 0
        template.updated_at = datetime.utcnow()

        await self.session.commit()
        return True


class AIUsageMetricsRepository(BaseRepository[AIUsageMetrics]):
    """Repository for AI usage metrics operations."""

    def __init__(self, db_session: AsyncSession):
        super().__init__(AIUsageMetrics, db_session)

    async def get_usage_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        ai_model: Optional[AIModel] = None,
        analysis_type: Optional[AnalysisType] = None,
    ) -> Dict[str, Any]:
        """Get usage metrics for the specified period."""
        query = select(AIUsageMetrics).where(
            and_(
                AIUsageMetrics.created_at >= start_date,
                AIUsageMetrics.created_at <= end_date,
            )
        )

        if user_id:
            query = query.where(AIUsageMetrics.user_id == user_id)

        if team_id:
            query = query.where(AIUsageMetrics.team_id == team_id)

        if ai_model:
            query = query.where(AIUsageMetrics.ai_model == ai_model)

        if analysis_type:
            query = query.where(AIUsageMetrics.analysis_type == analysis_type)

        result = await self.session.execute(query)
        metrics = result.scalars().all()

        # Calculate aggregated metrics
        total_analyses = len(metrics)
        successful_analyses = len([m for m in metrics if m.success == 1])
        failed_analyses = total_analyses - successful_analyses

        total_tokens = sum(m.total_tokens for m in metrics)
        input_tokens = sum(m.input_tokens for m in metrics)
        output_tokens = sum(m.output_tokens for m in metrics)

        total_cost_cents = sum(m.total_cost for m in metrics)
        avg_cost_per_analysis = (
            total_cost_cents / total_analyses if total_analyses > 0 else 0
        )

        avg_processing_time = 0
        if successful_analyses > 0:
            total_time = sum(
                m.processing_time_ms for m in metrics if m.success == 1)
            avg_processing_time = total_time / successful_analyses

        # Model breakdown
        model_usage = {}
        for model in AIModel:
            model_metrics = [m for m in metrics if m.ai_model == model]
            if model_metrics:
                model_usage[model.value] = {
                    "analyses": len(model_metrics),
                    "tokens": sum(m.total_tokens for m in model_metrics),
                    "cost_cents": sum(m.total_cost for m in model_metrics),
                    "avg_processing_time_ms": sum(
                        m.processing_time_ms for m in model_metrics
                    )
                    / len(model_metrics),
                }

        # Analysis type breakdown
        type_usage = {}
        for analysis_type in AnalysisType:
            type_metrics = [
                m for m in metrics if m.analysis_type == analysis_type]
            if type_metrics:
                type_usage[analysis_type.value] = {
                    "analyses": len(type_metrics),
                    "tokens": sum(m.total_tokens for m in type_metrics),
                    "cost_cents": sum(m.total_cost for m in type_metrics),
                    "avg_processing_time_ms": sum(
                        m.processing_time_ms for m in type_metrics
                    )
                    / len(type_metrics),
                }

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_analyses": total_analyses,
            "successful_analyses": successful_analyses,
            "failed_analyses": failed_analyses,
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_cost_cents": total_cost_cents,
            "average_cost_per_analysis": avg_cost_per_analysis,
            "average_processing_time_ms": avg_processing_time,
            "model_usage": model_usage,
            "analysis_type_usage": type_usage,
        }

    async def get_daily_usage(
        self,
        days: int = 30,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get daily usage metrics for the last N days."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        query = (
            select(
                func.date(AIUsageMetrics.created_at).label("date"),
                func.count(AIUsageMetrics.id).label("analyses"),
                func.sum(AIUsageMetrics.total_tokens).label("tokens"),
                func.sum(AIUsageMetrics.total_cost).label("cost_cents"),
                func.avg(AIUsageMetrics.processing_time_ms).label(
                    "avg_processing_time"
                ),
            )
            .where(
                and_(
                    AIUsageMetrics.created_at >= start_date,
                    AIUsageMetrics.created_at <= end_date,
                )
            )
            .group_by(func.date(AIUsageMetrics.created_at))
            .order_by("date")
        )

        if user_id:
            query = query.where(AIUsageMetrics.user_id == user_id)

        if team_id:
            query = query.where(AIUsageMetrics.team_id == team_id)

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "date": row.date.isoformat(),
                "analyses": row.analyses or 0,
                "tokens": row.tokens or 0,
                "cost_cents": row.cost_cents or 0,
                "avg_processing_time_ms": float(row.avg_processing_time or 0),
            }
            for row in rows
        ]
