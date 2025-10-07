"""
AI Controller for handling AI analysis API endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis import AIAnalysis, AIModel, AnalysisStatus, AnalysisType
from app.repositories.ai_analysis import (
    AIAnalysisRepository,
    AIPromptTemplateRepository,
    AIUsageMetricsRepository,
)
from app.schemas.requests.ai_requests import (
    BatchAnalysisRequest,
    CodeReviewRequest,
    CustomAnalysisRequest,
    PromptTemplateRequest,
    PRSummaryRequest,
    RiskAssessmentRequest,
    TechnicalDebtRequest,
)
from app.schemas.responses.ai_responses import (
    AIHealthResponse,
    AIUsageMetricsResponse,
    BaseAIAnalysisResponse,
    BatchAnalysisResponse,
    CodeReviewResponse,
    CustomAnalysisResponse,
    PromptTemplateResponse,
    PRSummaryResponse,
    RiskAssessmentResponse,
    TechnicalDebtResponse,
)
from app.services.ai_service import ai_service
from app.services.pr_analysis_service import pr_analysis_service
from core.controller import BaseController
from core.database import Propagation, Transactional
from core.database.session import get_session

logger = logging.getLogger(__name__)


class AIController(BaseController):
    """Controller for AI analysis operations."""

    def __init__(self, db_session: AsyncSession):
        # Initialize with a primary repository (we'll use AIAnalysisRepository as the main one)
        ai_analysis_repo = AIAnalysisRepository(db_session)
        super().__init__(AIAnalysis, ai_analysis_repo)

        # Set up additional repositories
        self.ai_analysis_repo = ai_analysis_repo
        self.prompt_template_repo = AIPromptTemplateRepository(db_session)
        self.usage_metrics_repo = AIUsageMetricsRepository(db_session)

    async def analyze_pr_summary(
        self,
        request: PRSummaryRequest,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        pull_request_id: Optional[int] = None,
    ) -> PRSummaryResponse:
        """Analyze PR summary."""
        try:
            return await ai_service.analyze_pr_summary(
                request=request,
                user_id=user_id,
                team_id=team_id,
                pull_request_id=pull_request_id,
                db_session=self.db_session,
            )
        except Exception as e:
            logger.error(f"PR summary analysis failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PR summary analysis failed: {str(e)}",
            )

    async def analyze_code_review(
        self,
        request: CodeReviewRequest,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> CodeReviewResponse:
        """Analyze code review."""
        try:
            return await ai_service.analyze_code_review(
                request=request,
                user_id=user_id,
                team_id=team_id,
                db_session=self.db_session,
            )
        except Exception as e:
            logger.error(f"Code review analysis failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Code review analysis failed: {str(e)}",
            )

    async def analyze_risk_assessment(
        self,
        request: RiskAssessmentRequest,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        pull_request_id: Optional[int] = None,
    ) -> RiskAssessmentResponse:
        """Analyze risk assessment."""
        try:
            return await ai_service.analyze_risk_assessment(
                request=request,
                user_id=user_id,
                team_id=team_id,
                pull_request_id=pull_request_id,
                db_session=self.db_session,
            )
        except Exception as e:
            logger.error(f"Risk assessment analysis failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Risk assessment analysis failed: {str(e)}",
            )

    async def analyze_technical_debt(
        self,
        request: TechnicalDebtRequest,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> TechnicalDebtResponse:
        """Analyze technical debt."""
        try:
            # For now, use custom analysis for technical debt
            custom_request = CustomAnalysisRequest(
                analysis_type=request.analysis_type,
                ai_model=request.ai_model,
                custom_prompt=f"Analyze technical debt for the following codebase data: {request.codebase_data}",
                input_data=request.dict(),
                output_format="json",
                include_confidence=True,
            )

            custom_response = await ai_service.analyze_custom(
                request=custom_request,
                user_id=user_id,
                team_id=team_id,
                db_session=self.db_session,
            )

            # Convert to technical debt response
            return TechnicalDebtResponse(
                id=custom_response.id,
                analysis_type=custom_response.analysis_type,
                status=custom_response.status,
                ai_model=custom_response.ai_model,
                output_data=custom_response.output_data,
                output_text=custom_response.output_text,
                confidence_score=custom_response.confidence_score,
                processing_time_ms=custom_response.processing_time_ms,
                token_usage=custom_response.token_usage,
                created_at=custom_response.created_at,
                updated_at=custom_response.updated_at,
                completed_at=custom_response.completed_at,
                overall_debt_score=(
                    custom_response.output_data.get("overall_debt_score")
                    if custom_response.output_data
                    else None
                ),
                complexity_score=(
                    custom_response.output_data.get("complexity_score")
                    if custom_response.output_data
                    else None
                ),
                duplication_score=(
                    custom_response.output_data.get("duplication_score")
                    if custom_response.output_data
                    else None
                ),
                test_coverage_score=(
                    custom_response.output_data.get("test_coverage_score")
                    if custom_response.output_data
                    else None
                ),
                documentation_score=(
                    custom_response.output_data.get("documentation_score")
                    if custom_response.output_data
                    else None
                ),
                debt_areas=(
                    custom_response.output_data.get("debt_areas", [])
                    if custom_response.output_data
                    else []
                ),
                critical_issues=(
                    custom_response.output_data.get("critical_issues", [])
                    if custom_response.output_data
                    else []
                ),
                refactoring_priorities=(
                    custom_response.output_data.get(
                        "refactoring_priorities", [])
                    if custom_response.output_data
                    else []
                ),
                improvement_roadmap=(
                    custom_response.output_data.get("improvement_roadmap", [])
                    if custom_response.output_data
                    else []
                ),
            )
        except Exception as e:
            logger.error(f"Technical debt analysis failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Technical debt analysis failed: {str(e)}",
            )

    async def analyze_custom(
        self,
        request: CustomAnalysisRequest,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> CustomAnalysisResponse:
        """Analyze custom analysis."""
        try:
            return await ai_service.analyze_custom(
                request=request,
                user_id=user_id,
                team_id=team_id,
                db_session=self.db_session,
            )
        except Exception as e:
            logger.error(f"Custom analysis failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Custom analysis failed: {str(e)}",
            )

    async def analyze_batch(
        self,
        request: BatchAnalysisRequest,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> BatchAnalysisResponse:
        """Analyze batch analysis."""
        try:
            return await ai_service.analyze_batch(
                request=request,
                user_id=user_id,
                team_id=team_id,
                db_session=self.db_session,
            )
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Batch analysis failed: {str(e)}",
            )

    async def get_analysis_by_id(self, analysis_id: int) -> BaseAIAnalysisResponse:
        """Get analysis by ID."""
        analysis = await self.ai_analysis_repo.get_by_id(analysis_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found"
            )

        return BaseAIAnalysisResponse(
            id=analysis.id,
            analysis_type=analysis.analysis_type.value,
            status=analysis.status.value,
            ai_model=analysis.ai_model.value,
            output_data=analysis.output_data,
            output_text=analysis.output_text,
            confidence_score=analysis.confidence_score,
            processing_time_ms=analysis.processing_time_ms,
            token_usage=analysis.token_usage,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
            completed_at=analysis.completed_at,
            error_message=analysis.error_message,
        )

    async def get_user_analyses(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        analysis_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[BaseAIAnalysisResponse]:
        """Get analyses by user."""
        from app.models.ai_analysis import AnalysisStatus, AnalysisType

        analysis_type_enum = None
        if analysis_type:
            try:
                analysis_type_enum = AnalysisType(analysis_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid analysis type: {analysis_type}",
                )

        status_enum = None
        if status:
            try:
                status_enum = AnalysisStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}",
                )

        analyses = await self.ai_analysis_repo.get_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            analysis_type=analysis_type_enum,
            status=status_enum,
        )

        return [
            BaseAIAnalysisResponse(
                id=analysis.id,
                analysis_type=analysis.analysis_type.value,
                status=analysis.status.value,
                ai_model=analysis.ai_model.value,
                output_data=analysis.output_data,
                output_text=analysis.output_text,
                confidence_score=analysis.confidence_score,
                processing_time_ms=analysis.processing_time_ms,
                token_usage=analysis.token_usage,
                created_at=analysis.created_at,
                updated_at=analysis.updated_at,
                completed_at=analysis.completed_at,
                error_message=analysis.error_message,
            )
            for analysis in analyses
        ]

    async def get_team_analyses(
        self,
        team_id: int,
        limit: int = 50,
        offset: int = 0,
        analysis_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[BaseAIAnalysisResponse]:
        """Get analyses by team."""
        from app.models.ai_analysis import AnalysisStatus, AnalysisType

        analysis_type_enum = None
        if analysis_type:
            try:
                analysis_type_enum = AnalysisType(analysis_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid analysis type: {analysis_type}",
                )

        status_enum = None
        if status:
            try:
                status_enum = AnalysisStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}",
                )

        analyses = await self.ai_analysis_repo.get_by_team(
            team_id=team_id,
            limit=limit,
            offset=offset,
            analysis_type=analysis_type_enum,
            status=status_enum,
        )

        return [
            BaseAIAnalysisResponse(
                id=analysis.id,
                analysis_type=analysis.analysis_type.value,
                status=analysis.status.value,
                ai_model=analysis.ai_model.value,
                output_data=analysis.output_data,
                output_text=analysis.output_text,
                confidence_score=analysis.confidence_score,
                processing_time_ms=analysis.processing_time_ms,
                token_usage=analysis.token_usage,
                created_at=analysis.created_at,
                updated_at=analysis.updated_at,
                completed_at=analysis.completed_at,
                error_message=analysis.error_message,
            )
            for analysis in analyses
        ]

    async def get_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        analysis_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get analytics data."""
        from app.models.ai_analysis import AnalysisType

        analysis_type_enum = None
        if analysis_type:
            try:
                analysis_type_enum = AnalysisType(analysis_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid analysis type: {analysis_type}",
                )

        return await self.ai_analysis_repo.get_analytics(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            team_id=team_id,
            analysis_type=analysis_type_enum,
        )

    async def get_usage_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        ai_model: Optional[str] = None,
        analysis_type: Optional[str] = None,
    ) -> AIUsageMetricsResponse:
        """Get usage metrics."""
        from app.models.ai_analysis import AIModel, AnalysisType

        # Set default date range if not provided
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        ai_model_enum = None
        if ai_model:
            try:
                ai_model_enum = AIModel(ai_model)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid AI model: {ai_model}",
                )

        analysis_type_enum = None
        if analysis_type:
            try:
                analysis_type_enum = AnalysisType(analysis_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid analysis type: {analysis_type}",
                )

        metrics = await self.usage_metrics_repo.get_usage_metrics(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            team_id=team_id,
            ai_model=ai_model_enum,
            analysis_type=analysis_type_enum,
        )

        return AIUsageMetricsResponse(**metrics)

    async def get_health_status(self) -> AIHealthResponse:
        """Get AI service health status."""
        try:
            from app.integrations.ai_providers import AIProviderFactory

            # Check available models
            available_models = AIProviderFactory.get_available_models()

            # Test each provider
            provider_status = {}
            for model in available_models:
                try:
                    provider = AIProviderFactory.get_provider(model)
                    provider_status[model.value] = "healthy"
                except Exception as e:
                    provider_status[model.value] = f"unhealthy: {str(e)}"

            # Get recent error rate
            recent_analyses = await self.ai_analysis_repo.get_recent_analyses(
                hours=1, limit=100
            )
            total_recent = len(recent_analyses)
            failed_recent = len(
                [a for a in recent_analyses if a.status.value == "failed"]
            )
            success_rate = (
                ((total_recent - failed_recent) / total_recent * 100)
                if total_recent > 0
                else 100
            )

            # Calculate average response time
            completed_recent = [
                a for a in recent_analyses if a.status.value == "completed"
            ]
            avg_response_time = 0
            if completed_recent:
                total_time = sum(
                    a.processing_time_ms or 0 for a in completed_recent)
                avg_response_time = total_time / len(completed_recent)

            # Determine overall status
            overall_status = "healthy"
            if any("unhealthy" in status for status in provider_status.values()):
                overall_status = "degraded"
            if success_rate < 80:
                overall_status = "unhealthy"

            return AIHealthResponse(
                status=overall_status,
                timestamp=datetime.utcnow(),
                azure_openai_status=provider_status.get(
                    "azure_openai_gpt4o_mini", "not_configured"
                ),
                openai_status=provider_status.get(
                    "openai_gpt4", "not_configured"),
                anthropic_status=provider_status.get(
                    "anthropic_claude", "not_configured"
                ),
                average_response_time_ms=avg_response_time,
                success_rate=success_rate,
                active_connections=len(available_models),
                queue_size=0,  # TODO: Implement queue monitoring
                recent_errors=None,  # TODO: Implement error tracking
            )

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return AIHealthResponse(
                status="unhealthy",
                timestamp=datetime.utcnow(),
                azure_openai_status="error",
                openai_status="error",
                anthropic_status="error",
                average_response_time_ms=0,
                success_rate=0,
                active_connections=0,
                queue_size=0,
                recent_errors=[
                    {"error": str(
                        e), "timestamp": datetime.utcnow().isoformat()}
                ],
            )

    # New PR Analysis Methods with Structured Output

    @Transactional(propagation=Propagation.REQUIRED)
    async def analyze_pr_risk_flags(
        self,
        request: "PRRiskFlagsRequest",
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> "PRRiskFlagsResponse":
        """Analyze PR for risk flags using structured output."""
        try:
            # Store analysis metadata
            analysis = await self.ai_analysis_repo.create(
                {
                    "analysis_type": AnalysisType.PR_RISK_FLAGS,
                    "user_id": user_id,
                    "team_id": team_id,
                    "input_data": request.model_dump(),
                    "status": AnalysisStatus.IN_PROGRESS,
                    "ai_model": AIModel.AZURE_OPENAI_GPT4O_MINI,
                    "created_at": datetime.utcnow(),
                }
            )
            # Flush to get the ID
            await self.ai_analysis_repo.session.flush()

            # Generate structured analysis
            response = await pr_analysis_service.analyze_pr_risk_flags(request)

            # Update analysis with results
            analysis.output_data = response.model_dump()
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.utcnow()
            self.ai_analysis_repo.session.add(analysis)

            return response

        except Exception as e:
            logger.error(f"PR risk flags analysis failed: {e}")
            if "analysis" in locals():
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                analysis.completed_at = datetime.utcnow()
                self.ai_analysis_repo.session.add(analysis)
            raise

    @Transactional(propagation=Propagation.REQUIRED)
    async def analyze_pr_blocker_flags(
        self,
        request: "PRBlockerFlagsRequest",
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> "PRBlockerFlagsResponse":
        """Analyze PR for blocker flags using structured output."""
        try:
            analysis = await self.ai_analysis_repo.create(
                {
                    "analysis_type": AnalysisType.PR_BLOCKER_FLAGS,
                    "user_id": user_id,
                    "team_id": team_id,
                    "input_data": request.model_dump(),
                    "status": AnalysisStatus.IN_PROGRESS,
                    "ai_model": AIModel.AZURE_OPENAI_GPT4O_MINI,
                    "created_at": datetime.utcnow(),
                }
            )
            # Flush to get the ID
            await self.ai_analysis_repo.session.flush()

            response = await pr_analysis_service.analyze_pr_blocker_flags(request)

            analysis.output_data = response.model_dump()
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.utcnow()
            self.ai_analysis_repo.session.add(analysis)

            return response

        except Exception as e:
            logger.error(f"PR blocker flags analysis failed: {e}")
            if "analysis" in locals():
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                analysis.completed_at = datetime.utcnow()
                self.ai_analysis_repo.session.add(analysis)
            raise

    @Transactional(propagation=Propagation.REQUIRED)
    async def generate_copilot_insights(
        self,
        request: "CopilotInsightsRequest",
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> "CopilotInsightsResponse":
        """Generate copilot insights using structured output."""
        try:
            analysis = await self.ai_analysis_repo.create(
                {
                    "analysis_type": AnalysisType.COPILOT_INSIGHTS,
                    "user_id": user_id,
                    "team_id": team_id,
                    "input_data": request.model_dump(),
                    "status": AnalysisStatus.IN_PROGRESS,
                    "ai_model": AIModel.AZURE_OPENAI_GPT4O_MINI,
                    "created_at": datetime.utcnow(),
                }
            )
            # Flush to get the ID
            await self.ai_analysis_repo.session.flush()

            response = await pr_analysis_service.generate_copilot_insights(request)

            analysis.output_data = response.model_dump()
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.utcnow()
            self.ai_analysis_repo.session.add(analysis)

            return response

        except Exception as e:
            logger.error(f"Copilot insights generation failed: {e}")
            if "analysis" in locals():
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                analysis.completed_at = datetime.utcnow()
                self.ai_analysis_repo.session.add(analysis)
            raise

    @Transactional(propagation=Propagation.REQUIRED)
    async def generate_narrative_timeline(
        self,
        request: "NarrativeTimelineRequest",
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> "NarrativeTimelineResponse":
        """Generate narrative timeline using structured output."""
        try:
            analysis = await self.ai_analysis_repo.create(
                {
                    "analysis_type": AnalysisType.NARRATIVE_TIMELINE,
                    "user_id": user_id,
                    "team_id": team_id,
                    "input_data": request.model_dump(),
                    "status": AnalysisStatus.IN_PROGRESS,
                    "ai_model": AIModel.AZURE_OPENAI_GPT4O_MINI,
                    "created_at": datetime.utcnow(),
                }
            )
            # Flush to get the ID
            await self.ai_analysis_repo.session.flush()

            response = await pr_analysis_service.generate_narrative_timeline(request)

            analysis.output_data = response.model_dump()
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.utcnow()
            self.ai_analysis_repo.session.add(analysis)

            return response

        except Exception as e:
            logger.error(f"Narrative timeline generation failed: {e}")
            if "analysis" in locals():
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                analysis.completed_at = datetime.utcnow()
                self.ai_analysis_repo.session.add(analysis)
            raise

    @Transactional(propagation=Propagation.REQUIRED)
    async def analyze_ai_roi(
        self,
        request: "AIROIRequest",
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> "AIROIResponse":
        """Analyze AI ROI metrics using structured output."""
        try:
            analysis = await self.ai_analysis_repo.create(
                {
                    "analysis_type": AnalysisType.AI_ROI,
                    "user_id": user_id,
                    "team_id": team_id,
                    "input_data": request.model_dump(),
                    "status": AnalysisStatus.IN_PROGRESS,
                    "ai_model": AIModel.AZURE_OPENAI_GPT4O_MINI,
                    "created_at": datetime.utcnow(),
                }
            )
            # Flush to get the ID
            await self.ai_analysis_repo.session.flush()

            response = await pr_analysis_service.analyze_ai_roi(request)

            analysis.output_data = response.model_dump()
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.utcnow()
            self.ai_analysis_repo.session.add(analysis)

            return response

        except Exception as e:
            logger.error(f"AI ROI analysis failed: {e}")
            if "analysis" in locals():
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                analysis.completed_at = datetime.utcnow()
                self.ai_analysis_repo.session.add(analysis)
            raise

    @Transactional(propagation=Propagation.REQUIRED)
    async def generate_pr_summary_enhanced(
        self,
        request: "PRSummaryRequest",
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
    ) -> "PRSummaryResponse":
        """Generate enhanced PR summary using structured output."""
        try:
            analysis = await self.ai_analysis_repo.create(
                {
                    "analysis_type": AnalysisType.PR_SUMMARY,
                    "user_id": user_id,
                    "team_id": team_id,
                    "input_data": request.model_dump(),
                    "status": AnalysisStatus.IN_PROGRESS,
                    "ai_model": AIModel.AZURE_OPENAI_GPT4O_MINI,
                    "created_at": datetime.utcnow(),
                }
            )
            # Flush to get the ID
            await self.ai_analysis_repo.session.flush()

            response = await pr_analysis_service.generate_pr_summary(request)

            analysis.output_data = response.model_dump()
            analysis.status = AnalysisStatus.COMPLETED
            analysis.completed_at = datetime.utcnow()
            self.ai_analysis_repo.session.add(analysis)

            return response

        except Exception as e:
            logger.error(f"Enhanced PR summary generation failed: {e}")
            if "analysis" in locals():
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                analysis.completed_at = datetime.utcnow()
                self.ai_analysis_repo.session.add(analysis)
            raise
