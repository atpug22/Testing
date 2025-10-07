"""
AI Impact Analysis API Endpoints
Provides REST API endpoints for AI impact analysis functionality.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ai_impact_analyzer import AIImpactAnalyzer
from ai_impact_models import AIImpactRequest, AIImpactResponse
from fastapi import APIRouter, BackgroundTasks, Cookie, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from github_oauth import get_session
from models import RepoDataset

router = APIRouter(prefix="/api/ai-impact", tags=["AI Impact Analysis"])


@router.post("/analyze", response_model=AIImpactResponse)
async def analyze_ai_impact(
    request: AIImpactRequest,
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None),
) -> AIImpactResponse:
    """
    Analyze AI impact for a repository

    This endpoint performs comprehensive AI impact analysis including:
    - AI authorship detection
    - Performance comparison (AI vs human code)
    - Adoption trends over time
    - Quality assessment
    """
    try:
        # Get session for GitHub API access
        sid = x_session_id or session_id
        if not sid:
            raise HTTPException(status_code=401, detail="Authentication required")

        session = get_session(sid)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid session")

        # Define data path and fetch functions locally to avoid circular imports
        import json
        from pathlib import Path

        DATA_DIR = Path(__file__).parent / "storage" / "data"
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        def _dataset_path(owner: str, repo: str) -> Path:
            safe = f"{owner}__{repo}.json".replace("/", "_")
            return DATA_DIR / safe

        # Check if we have cached data or need to fetch fresh
        path = _dataset_path(request.owner, request.repo)

        if path.exists() and not request.force_refresh:
            # Load cached data
            with path.open("r", encoding="utf-8") as f:
                raw_data = json.load(f)
            dataset = RepoDataset.model_validate(raw_data)
        else:
            # For now, return error if no cached data - user needs to fetch via main API first
            raise HTTPException(
                status_code=400,
                detail="No cached data found. Please fetch repository data first via /api/fetch endpoint.",
            )

        # Prepare data for AI analysis
        repo_data = {
            "owner": request.owner,
            "repo": request.repo,
            "dataset": dataset.model_dump(),
        }

        # Perform AI impact analysis
        analyzer = AIImpactAnalyzer()
        analysis = analyzer.analyze_repository(repo_data, days=request.days)

        return AIImpactResponse(
            success=True,
            repository=f"{request.owner}/{request.repo}",
            analysis_date=datetime.now(),
            analysis=analysis,
        )

    except Exception as e:
        return AIImpactResponse(
            success=False,
            repository=f"{request.owner}/{request.repo}",
            analysis_date=datetime.now(),
            error_message=str(e),
        )


@router.get("/summary")
async def get_ai_impact_summary(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None),
):
    """
    Get a quick summary of AI impact metrics for a repository
    """
    try:
        # Check for existing analysis
        analyzer = AIImpactAnalyzer()

        # For now, redirect to full analysis
        # In production, you might want to cache summaries separately
        request = AIImpactRequest(owner=owner, repo=repo, days=90)
        response = await analyze_ai_impact(request, session_id, x_session_id)

        if not response.success or not response.analysis:
            return JSONResponse(
                status_code=400,
                content={"error": response.error_message or "Analysis failed"},
            )

        # Extract summary metrics
        analysis = response.analysis
        summary = {
            "repository": response.repository,
            "ai_adoption_rate": analysis.metrics.ai_adoption_rate,
            "total_prs_analyzed": analysis.metrics.total_prs_analyzed,
            "ai_authored_prs": analysis.metrics.ai_authored_prs,
            "impact_score": analysis.impact_score,
            "confidence_level": analysis.confidence_level,
            "trend_direction": analysis.trends.trend_direction,
            "quality_score": analysis.quality.quality_score,
            "key_insights": analysis.summary_insights[:3],  # Top 3 insights
        }

        return JSONResponse(content=summary)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get AI impact summary: {str(e)}"},
        )


@router.get("/trends")
async def get_ai_trends(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    days: int = Query(90, description="Number of days to analyze"),
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None),
):
    """
    Get AI adoption trends over time for a repository
    """
    try:
        request = AIImpactRequest(owner=owner, repo=repo, days=days)
        response = await analyze_ai_impact(request, session_id, x_session_id)

        if not response.success or not response.analysis:
            return JSONResponse(
                status_code=400,
                content={"error": response.error_message or "Analysis failed"},
            )

        trends_data = {
            "repository": response.repository,
            "trend_direction": response.analysis.trends.trend_direction,
            "weekly_ai_adoption": response.analysis.trends.weekly_ai_adoption,
            "weekly_ai_prs": response.analysis.trends.weekly_ai_prs,
            "weekly_total_prs": response.analysis.trends.weekly_total_prs,
            "analysis_period_days": days,
        }

        return JSONResponse(content=trends_data)

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Failed to get AI trends: {str(e)}"}
        )


@router.get("/quality")
async def get_ai_quality_assessment(
    owner: str = Query(..., description="Repository owner"),
    repo: str = Query(..., description="Repository name"),
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None),
):
    """
    Get AI code quality assessment for a repository
    """
    try:
        request = AIImpactRequest(owner=owner, repo=repo, days=90)
        response = await analyze_ai_impact(request, session_id, x_session_id)

        if not response.success or not response.analysis:
            return JSONResponse(
                status_code=400,
                content={"error": response.error_message or "Analysis failed"},
            )

        quality_data = {
            "repository": response.repository,
            "quality_score": response.analysis.quality.quality_score,
            "high_risk_prs": response.analysis.quality.high_risk_ai_prs,
            "common_issues": response.analysis.quality.common_issues,
            "recommendations": response.analysis.quality.recommendations,
            "total_ai_prs": response.analysis.metrics.ai_authored_prs,
        }

        return JSONResponse(content=quality_data)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get AI quality assessment: {str(e)}"},
        )
