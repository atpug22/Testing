"""
PR Risk Analysis API Endpoints
This module provides FastAPI endpoints for the PR risk analysis system.
"""

from datetime import datetime
from typing import Optional, List
import asyncio
import os

from fastapi import APIRouter, HTTPException, BackgroundTasks, Header, Cookie
from pydantic import BaseModel

from .pr_risk_models import (
    PRRiskAnalysisRequest,
    PRRiskAnalysisResponse,
    RepositoryRiskReport,
    PRListItem,
    DashboardSummary,
    PRRiskDatabase,
    RiskLevel
)
from .pr_risk_analyzer import PRRiskAnalyzer
from .github_oauth import get_session

router = APIRouter(prefix="/api/pr-risk", tags=["PR Risk Analysis"])


class PRRiskService:
    """Service class for PR risk analysis operations"""
    
    def __init__(self):
        self.analyzer = None
    
    def get_analyzer(self, token: Optional[str] = None) -> PRRiskAnalyzer:
        """Get or create analyzer instance"""
        if self.analyzer is None or token:
            self.analyzer = PRRiskAnalyzer(token=token)
        return self.analyzer


# Global service instance
pr_risk_service = PRRiskService()


async def _get_github_token(session_id: Optional[str] = None) -> Optional[str]:
    """Get GitHub token from session"""
    if not session_id:
        return None
    
    session = get_session(session_id)
    if session and "access_token" in session:
        return session["access_token"]
    
    # Fallback to environment variable
    return os.getenv("GITHUB_TOKEN")


@router.post("/analyze", response_model=PRRiskAnalysisResponse)
async def analyze_repository_risks(
    request: PRRiskAnalysisRequest,
    background_tasks: BackgroundTasks,
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None)
):
    """
    Analyze PR risks for a repository
    
    This endpoint performs comprehensive risk analysis on all open PRs
    in the specified repository and returns detailed metrics.
    """
    sid = x_session_id or session_id
    
    try:
        start_time = datetime.now()
        
        # Get GitHub token
        token = await _get_github_token(sid)
        analyzer = pr_risk_service.get_analyzer(token)
        
        # Perform analysis
        report = await analyzer.analyze_repository(
            owner=request.owner,
            repo=request.repo,
            include_closed_prs=request.include_closed_prs,
            max_prs=request.max_prs or 50,
            force_refresh=request.force_refresh
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return PRRiskAnalysisResponse(
            success=True,
            repository_report=report,
            processing_time_seconds=processing_time,
            api_requests_made=analyzer.client.requests_made
        )
        
    except Exception as e:
        return PRRiskAnalysisResponse(
            success=False,
            error_message=str(e)
        )


@router.get("/repositories/{owner}/{repo}/summary", response_model=DashboardSummary)
async def get_repository_risk_summary(
    owner: str,
    repo: str,
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None)
):
    """
    Get risk summary for a repository
    
    Returns high-level metrics and top risky PRs for dashboard display.
    """
    sid = x_session_id or session_id
    
    try:
        token = await _get_github_token(sid)
        analyzer = pr_risk_service.get_analyzer(token)
        
        # Load existing analysis or perform quick analysis
        db = analyzer._load_database()
        report = db.get_repo_report(owner, repo)
        
        if not report:
            # Perform quick analysis with limited PRs
            report = await analyzer.analyze_repository(
                owner=owner,
                repo=repo,
                max_prs=20,
                force_refresh=False
            )
        
        # Build summary
        risk_distribution = {
            "low": len([p for p in report.pr_analyses if p.risk_level == RiskLevel.LOW]),
            "medium": len([p for p in report.pr_analyses if p.risk_level == RiskLevel.MEDIUM]),
            "high": len([p for p in report.pr_analyses if p.risk_level == RiskLevel.HIGH]),
            "critical": len([p for p in report.pr_analyses if p.risk_level == RiskLevel.CRITICAL])
        }
        
        # Top 5 riskiest PRs
        sorted_prs = sorted(report.pr_analyses, key=lambda x: x.delivery_risk_score, reverse=True)
        top_risk_prs = [
            PRListItem(
                pr_number=pr.pr_number,
                title=pr.title,
                author=pr.author,
                state=pr.state,
                delivery_risk_score=pr.delivery_risk_score,
                risk_level=pr.risk_level,
                created_at=pr.created_at,
                updated_at=pr.updated_at,
                url=pr.url,
                ai_summary=pr.ai_summary
            )
            for pr in sorted_prs[:5]
        ]
        
        return DashboardSummary(
            total_prs=report.total_prs_analyzed,
            high_risk_count=report.high_risk_pr_count,
            critical_risk_count=report.critical_risk_pr_count,
            avg_risk_score=report.avg_delivery_risk_score,
            team_velocity_impact=report.team_velocity_impact,
            top_risk_prs=top_risk_prs,
            risk_distribution=risk_distribution
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repositories/{owner}/{repo}/prs", response_model=List[PRListItem])
async def get_repository_pr_risks(
    owner: str,
    repo: str,
    risk_level: Optional[RiskLevel] = None,
    limit: int = 50,
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None)
):
    """
    Get list of PRs with risk analysis
    
    Returns all analyzed PRs, optionally filtered by risk level.
    """
    sid = x_session_id or session_id
    
    try:
        token = await _get_github_token(sid)
        analyzer = pr_risk_service.get_analyzer(token)
        
        db = analyzer._load_database()
        report = db.get_repo_report(owner, repo)
        
        if not report:
            raise HTTPException(status_code=404, detail="No analysis found for this repository")
        
        pr_items = [
            PRListItem(
                pr_number=pr.pr_number,
                title=pr.title,
                author=pr.author,
                state=pr.state,
                delivery_risk_score=pr.delivery_risk_score,
                risk_level=pr.risk_level,
                created_at=pr.created_at,
                updated_at=pr.updated_at,
                url=pr.url,
                ai_summary=pr.ai_summary
            )
            for pr in report.pr_analyses
        ]
        
        # Filter by risk level if specified
        if risk_level:
            pr_items = [pr for pr in pr_items if pr.risk_level == risk_level]
        
        # Sort by risk score (highest first) and limit
        pr_items.sort(key=lambda x: x.delivery_risk_score, reverse=True)
        return pr_items[:limit]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repositories/{owner}/{repo}/prs/{pr_number}")
async def get_pr_risk_details(
    owner: str,
    repo: str,
    pr_number: int,
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None)
):
    """
    Get detailed risk analysis for a specific PR
    """
    sid = x_session_id or session_id
    
    try:
        token = await _get_github_token(sid)
        analyzer = pr_risk_service.get_analyzer(token)
        
        db = analyzer._load_database()
        report = db.get_repo_report(owner, repo)
        
        if not report:
            raise HTTPException(status_code=404, detail="No analysis found for this repository")
        
        # Find the specific PR
        pr_analysis = None
        for pr in report.pr_analyses:
            if pr.pr_number == pr_number:
                pr_analysis = pr
                break
        
        if not pr_analysis:
            raise HTTPException(status_code=404, detail="PR analysis not found")
        
        return pr_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repositories")
async def list_analyzed_repositories(
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None)
):
    """
    List all repositories that have been analyzed
    """
    try:
        analyzer = pr_risk_service.get_analyzer()
        db = analyzer._load_database()
        
        repositories = []
        for repo_key, report in db.repositories.items():
            repositories.append({
                "owner": report.owner,
                "repo": report.repo,
                "analyzed_at": report.analyzed_at,
                "total_prs": report.total_prs_analyzed,
                "avg_risk_score": report.avg_delivery_risk_score,
                "high_risk_count": report.high_risk_pr_count,
                "critical_risk_count": report.critical_risk_pr_count
            })
        
        # Sort by most recently analyzed
        repositories.sort(key=lambda x: x["analyzed_at"], reverse=True)
        return repositories
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/repositories/{owner}/{repo}/cache")
async def clear_repository_cache(
    owner: str,
    repo: str,
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None)
):
    """
    Clear cached analysis for a repository
    """
    try:
        analyzer = pr_risk_service.get_analyzer()
        db = analyzer._load_database()
        
        repo_key = db.get_repo_key(owner, repo)
        if repo_key in db.repositories:
            del db.repositories[repo_key]
            analyzer._save_database(db)
            return {"message": "Cache cleared successfully"}
        else:
            raise HTTPException(status_code=404, detail="Repository not found in cache")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RefreshRequest(BaseModel):
    repositories: List[str]  # List of "owner/repo" strings


@router.post("/refresh")
async def refresh_multiple_repositories(
    request: RefreshRequest,
    background_tasks: BackgroundTasks,
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None)
):
    """
    Refresh analysis for multiple repositories in background
    """
    sid = x_session_id or session_id
    
    async def refresh_repos():
        token = await _get_github_token(sid)
        analyzer = pr_risk_service.get_analyzer(token)
        
        for repo_str in request.repositories:
            try:
                owner, repo = repo_str.split("/", 1)
                await analyzer.analyze_repository(
                    owner=owner,
                    repo=repo,
                    force_refresh=True,
                    max_prs=30
                )
            except Exception as e:
                print(f"Error refreshing {repo_str}: {e}")
    
    background_tasks.add_task(refresh_repos)
    
    return {
        "message": f"Background refresh started for {len(request.repositories)} repositories",
        "repositories": request.repositories
    }