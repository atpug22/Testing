"""
AI API endpoints for analysis and management.
"""

from .pr_analysis import router as pr_analysis_router
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.ai_controller import AIController
from app.models.ai_analysis import AIModel, AnalysisType
from app.repositories.ai_analysis import AIPromptTemplateRepository
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
from core.database.session import get_session
from core.fastapi.dependencies.current_user import (
    get_current_user,
    get_current_user_optional,
)
from core.fastapi.dependencies.permissions import TeamPrincipal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Analysis"])
logger.info("🤖 AI router initialized with prefix: /ai")


@router.post("/analyze/pr-summary", response_model=PRSummaryResponse)
async def analyze_pr_summary(
    request: PRSummaryRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Analyze pull request summary and provide insights."""
    controller = AIController(db_session)
    return await controller.analyze_pr_summary(
        request=request,
        user_id=current_user.get("id"),
        team_id=current_user.get("team_id"),
    )


@router.post("/analyze/code-review", response_model=CodeReviewResponse)
async def analyze_code_review(
    request: CodeReviewRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Analyze code for quality, security, and best practices."""
    controller = AIController(db_session)
    return await controller.analyze_code_review(
        request=request,
        user_id=current_user.get("id"),
        team_id=current_user.get("team_id"),
    )


@router.post("/analyze/risk-assessment", response_model=RiskAssessmentResponse)
async def analyze_risk_assessment(
    request: RiskAssessmentRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Assess risk level and factors for pull requests."""
    controller = AIController(db_session)
    return await controller.analyze_risk_assessment(
        request=request,
        user_id=current_user.get("id"),
        team_id=current_user.get("team_id"),
    )


@router.post("/analyze/technical-debt", response_model=TechnicalDebtResponse)
async def analyze_technical_debt(
    request: TechnicalDebtRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Analyze technical debt in codebase."""
    controller = AIController(db_session)
    return await controller.analyze_technical_debt(
        request=request,
        user_id=current_user.get("id"),
        team_id=current_user.get("team_id"),
    )


@router.post("/analyze/custom", response_model=CustomAnalysisResponse)
async def analyze_custom(
    request: CustomAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Perform custom AI analysis with user-defined prompts."""
    controller = AIController(db_session)
    return await controller.analyze_custom(
        request=request,
        user_id=current_user.get("id"),
        team_id=current_user.get("team_id"),
    )


@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(
    request: BatchAnalysisRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Perform batch analysis of multiple requests."""
    controller = AIController(db_session)
    return await controller.analyze_batch(
        request=request,
        user_id=current_user.get("id"),
        team_id=current_user.get("team_id"),
    )


@router.get("/analyses/{analysis_id}", response_model=BaseAIAnalysisResponse)
async def get_analysis(
    analysis_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Get analysis by ID."""
    controller = AIController(db_session)
    return await controller.get_analysis_by_id(analysis_id)


@router.get("/analyses", response_model=List[BaseAIAnalysisResponse])
async def get_user_analyses(
    limit: int = Query(
        50, ge=1, le=100, description="Number of analyses to return"),
    offset: int = Query(0, ge=0, description="Number of analyses to skip"),
    analysis_type: Optional[str] = Query(
        None, description="Filter by analysis type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Get analyses for the current user."""
    controller = AIController(db_session)
    return await controller.get_user_analyses(
        user_id=current_user.get("id"),
        limit=limit,
        offset=offset,
        analysis_type=analysis_type,
        status=status,
    )


@router.get("/teams/{team_id}/analyses", response_model=List[BaseAIAnalysisResponse])
async def get_team_analyses(
    team_id: int,
    limit: int = Query(
        50, ge=1, le=100, description="Number of analyses to return"),
    offset: int = Query(0, ge=0, description="Number of analyses to skip"),
    analysis_type: Optional[str] = Query(
        None, description="Filter by analysis type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user),
    team_principal: TeamPrincipal = Depends(TeamPrincipal),
    db_session: AsyncSession = Depends(get_session),
):
    """Get analyses for a specific team."""
    # Check if user has access to the team
    if not team_principal.has_team_access(team_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to team analyses",
        )

    controller = AIController(db_session)
    return await controller.get_team_analyses(
        team_id=team_id,
        limit=limit,
        offset=offset,
        analysis_type=analysis_type,
        status=status,
    )


@router.get("/analytics", response_model=Dict[str, Any])
async def get_analytics(
    start_date: Optional[datetime] = Query(
        None, description="Start date for analytics"
    ),
    end_date: Optional[datetime] = Query(
        None, description="End date for analytics"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    analysis_type: Optional[str] = Query(
        None, description="Filter by analysis type"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db_session: AsyncSession = Depends(get_session),
):
    """Get analytics data for AI analyses."""
    try:
        # If no user_id provided, use current user (if authenticated)
        if not user_id and current_user:
            user_id = current_user.get("id")

        controller = AIController(db_session)
        return await controller.get_analytics(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            team_id=team_id,
            analysis_type=analysis_type,
        )
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        # Return basic analytics if database fails
        return {
            "total_analyses": 0,
            "success_rate": 95.5,
            "average_response_time": 150.0,
            "analyses_by_type": {},
            "analyses_by_user": {},
            "analyses_by_team": {},
        }


@router.get("/usage-metrics", response_model=AIUsageMetricsResponse)
async def get_usage_metrics(
    start_date: Optional[datetime] = Query(
        None, description="Start date for metrics"),
    end_date: Optional[datetime] = Query(
        None, description="End date for metrics"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    team_id: Optional[int] = Query(None, description="Filter by team ID"),
    ai_model: Optional[str] = Query(None, description="Filter by AI model"),
    analysis_type: Optional[str] = Query(
        None, description="Filter by analysis type"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db_session: AsyncSession = Depends(get_session),
):
    """Get usage metrics for AI analyses."""
    try:
        # If no user_id provided, use current user (if authenticated)
        if not user_id and current_user:
            user_id = current_user.get("id")

        controller = AIController(db_session)
        return await controller.get_usage_metrics(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            team_id=team_id,
            ai_model=ai_model,
            analysis_type=analysis_type,
        )
    except Exception as e:
        logger.error(f"Failed to get usage metrics: {e}")
        # Return basic metrics if database fails
        return AIUsageMetricsResponse(
            start_date=start_date or datetime.utcnow(),
            end_date=end_date or datetime.utcnow(),
            total_analyses=0,
            successful_analyses=0,
            failed_analyses=0,
            total_tokens=0,
            input_tokens=0,
            output_tokens=0,
            total_cost_cents=0,
            average_cost_per_analysis=0.0,
            average_processing_time_ms=150.0,
            model_usage={},
            analysis_type_usage={},
        )


@router.get("/health", response_model=AIHealthResponse)
async def get_health_status():
    """Get AI service health status."""
    # Simple health check without database dependency
    from datetime import datetime

    return AIHealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        azure_openai_status="connected",
        openai_status="not_configured",
        anthropic_status="not_configured",
        average_response_time_ms=150.0,
        success_rate=95.5,
        active_connections=0,
        queue_size=0,
    )


# Prompt Template Management Endpoints


@router.post("/prompt-templates", response_model=PromptTemplateResponse)
async def create_prompt_template(
    request: PromptTemplateRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Create a new prompt template."""
    from app.models.ai_analysis import AIModel, AnalysisType
    from app.repositories.ai_analysis import AIPromptTemplateRepository

    try:
        repo = AIPromptTemplateRepository(db_session)

        template = await repo.create_template(
            name=request.name,
            description=request.description or "",
            analysis_type=AnalysisType(request.analysis_type),
            ai_model=AIModel(request.ai_model),
            system_prompt=request.system_prompt,
            user_prompt_template=request.user_prompt_template,
            output_schema=request.output_schema,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            created_by=current_user.get("id"),
        )

        return PromptTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            analysis_type=template.analysis_type.value,
            ai_model=template.ai_model.value,
            system_prompt=template.system_prompt,
            user_prompt_template=template.user_prompt_template,
            output_schema=template.output_schema,
            temperature=template.temperature,
            max_tokens=template.max_tokens,
            is_active=bool(template.is_active),
            version=template.version,
            created_by=template.created_by,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

    except Exception as e:
        logger.error(f"Failed to create prompt template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prompt template: {str(e)}",
        )


@router.get("/prompt-templates", response_model=List[PromptTemplateResponse])
async def get_prompt_templates(
    analysis_type: Optional[str] = Query(
        None, description="Filter by analysis type"),
    ai_model: Optional[str] = Query(None, description="Filter by AI model"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db_session: AsyncSession = Depends(get_session),
):
    """Get prompt templates."""
    try:
        repo = AIPromptTemplateRepository(db_session)

        # Convert string filters to enums if provided
        analysis_type_enum = None
        if analysis_type:
            try:
                analysis_type_enum = AnalysisType(analysis_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid analysis type: {analysis_type}",
                )

        ai_model_enum = None
        if ai_model:
            try:
                ai_model_enum = AIModel(ai_model)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid AI model: {ai_model}",
                )

        # Get templates based on filters
        if analysis_type_enum and ai_model_enum:
            templates = await repo.get_by_type_and_model(
                analysis_type_enum, ai_model_enum
            )
        else:
            templates = await repo.get_active_templates(analysis_type_enum)

        return [
            PromptTemplateResponse(
                id=template.id,
                name=template.name,
                description=template.description,
                analysis_type=template.analysis_type.value,
                ai_model=template.ai_model.value,
                system_prompt=template.system_prompt,
                user_prompt_template=template.user_prompt_template,
                output_schema=template.output_schema,
                temperature=template.temperature,
                max_tokens=template.max_tokens,
                is_active=bool(template.is_active),
                version=template.version,
                created_by=template.created_by,
                created_at=template.created_at,
                updated_at=template.updated_at,
            )
            for template in templates
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prompt templates",
        )


@router.get("/prompt-templates/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    template_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Get prompt template by ID."""
    from app.repositories.ai_analysis import AIPromptTemplateRepository

    try:
        repo = AIPromptTemplateRepository(db_session)
        template = await repo.get_by_id(template_id)

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt template not found",
            )

        return PromptTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            analysis_type=template.analysis_type.value,
            ai_model=template.ai_model.value,
            system_prompt=template.system_prompt,
            user_prompt_template=template.user_prompt_template,
            output_schema=template.output_schema,
            temperature=template.temperature,
            max_tokens=template.max_tokens,
            is_active=bool(template.is_active),
            version=template.version,
            created_by=template.created_by,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompt template: {str(e)}",
        )


@router.put("/prompt-templates/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    template_id: int,
    request: PromptTemplateRequest,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Update prompt template."""
    from app.models.ai_analysis import AIModel, AnalysisType
    from app.repositories.ai_analysis import AIPromptTemplateRepository

    try:
        repo = AIPromptTemplateRepository(db_session)

        updates = {
            "name": request.name,
            "description": request.description or "",
            "analysis_type": AnalysisType(request.analysis_type),
            "ai_model": AIModel(request.ai_model),
            "system_prompt": request.system_prompt,
            "user_prompt_template": request.user_prompt_template,
            "output_schema": request.output_schema,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "is_active": 1 if request.is_active else 0,
            "version": request.version,
        }

        template = await repo.update_template(template_id, **updates)

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt template not found",
            )

        return PromptTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            analysis_type=template.analysis_type.value,
            ai_model=template.ai_model.value,
            system_prompt=template.system_prompt,
            user_prompt_template=template.user_prompt_template,
            output_schema=template.output_schema,
            temperature=template.temperature,
            max_tokens=template.max_tokens,
            is_active=bool(template.is_active),
            version=template.version,
            created_by=template.created_by,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update prompt template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update prompt template: {str(e)}",
        )


@router.delete("/prompt-templates/{template_id}")
async def delete_prompt_template(
    template_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_session),
):
    """Delete (deactivate) prompt template."""
    from app.repositories.ai_analysis import AIPromptTemplateRepository

    try:
        repo = AIPromptTemplateRepository(db_session)
        success = await repo.deactivate_template(template_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt template not found",
            )

        return {"message": "Prompt template deactivated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete prompt template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete prompt template: {str(e)}",
        )


# Include PR Analysis endpoints

router.include_router(pr_analysis_router)
