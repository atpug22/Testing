"""
AI Impact Analyzer
Main module for analyzing AI impact on development workflows.
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_authorship_detector import AIAuthorshipDetector
from ai_impact_models import (
    AIAuthorshipResult,
    AIConfidenceLevel,
    AIImpactAnalysis,
    AIImpactMetrics,
    AIQualityAssessment,
    AITrendAnalysis,
)


class AIImpactAnalyzer:
    """Analyzes AI impact on development workflows"""

    def __init__(self, storage_dir: Optional[str] = None):
        self.detector = AIAuthorshipDetector()
        self.storage_dir = (
            Path(storage_dir)
            if storage_dir
            else Path(__file__).parent / "ai_impact_data"
        )
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def analyze_repository(
        self, repo_data: Dict[str, Any], days: int = 90
    ) -> AIImpactAnalysis:
        """Perform complete AI impact analysis on repository data"""

        # Extract repository info
        owner = repo_data.get("owner", "")
        repo = repo_data.get("repo", "")
        repository = f"{owner}/{repo}"

        # Get PRs from the dataset
        prs = repo_data.get("dataset", {}).get("prs", [])

        # Filter PRs by date if needed
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        recent_prs = []

        for pr in prs:
            created_at = pr.get("created_at")
            if created_at:
                if isinstance(created_at, str):
                    pr_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                else:
                    pr_date = created_at

                if pr_date >= cutoff_date:
                    recent_prs.append(pr)

        # Analyze AI authorship for all PRs
        pr_analyses = self.detector.batch_analyze_prs(recent_prs)

        # Calculate core metrics
        metrics = self._calculate_metrics(recent_prs, pr_analyses)

        # Analyze trends
        trends = self._analyze_trends(recent_prs, pr_analyses, days)

        # Quality assessment
        quality = self._assess_quality(recent_prs, pr_analyses)

        # Calculate overall impact score
        impact_score = self._calculate_impact_score(metrics, trends, quality)

        # Determine confidence level
        confidence_level = self._determine_overall_confidence(pr_analyses)

        # Generate insights
        insights = self._generate_insights(metrics, trends, quality)

        return AIImpactAnalysis(
            repository=repository,
            analysis_date=datetime.now(timezone.utc),
            days_analyzed=days,
            metrics=metrics,
            trends=trends,
            quality=quality,
            pr_analyses=pr_analyses,
            impact_score=impact_score,
            confidence_level=confidence_level,
            summary_insights=insights,
        )

    def _calculate_metrics(
        self, prs: List[Dict[str, Any]], analyses: List[AIAuthorshipResult]
    ) -> AIImpactMetrics:
        """Calculate core AI impact metrics"""

        # Categorize PRs by AI confidence
        ai_prs = []
        human_prs = []

        for pr, analysis in zip(prs, analyses):
            if analysis.confidence in [
                AIConfidenceLevel.HIGH,
                AIConfidenceLevel.MEDIUM,
            ]:
                ai_prs.append(pr)
            elif analysis.confidence == AIConfidenceLevel.LOW:
                # For low confidence, use probability threshold
                if analysis.ai_probability >= 0.3:
                    ai_prs.append(pr)
                else:
                    human_prs.append(pr)
            else:
                human_prs.append(pr)

        total_prs = len(prs)
        ai_count = len(ai_prs)
        human_count = len(human_prs)

        # Calculate adoption rate
        adoption_rate = ai_count / total_prs if total_prs > 0 else 0.0

        # Calculate performance metrics
        ai_metrics = self._calculate_pr_performance(ai_prs)
        human_metrics = self._calculate_pr_performance(human_prs)

        return AIImpactMetrics(
            total_prs_analyzed=total_prs,
            ai_authored_prs=ai_count,
            human_authored_prs=human_count,
            ai_adoption_rate=adoption_rate,
            ai_avg_merge_time_hours=ai_metrics.get("avg_merge_time"),
            human_avg_merge_time_hours=human_metrics.get("avg_merge_time"),
            ai_avg_review_cycles=ai_metrics.get("avg_review_cycles"),
            human_avg_review_cycles=human_metrics.get("avg_review_cycles"),
            ai_avg_files_changed=ai_metrics.get("avg_files_changed"),
            human_avg_files_changed=human_metrics.get("avg_files_changed"),
            ai_avg_lines_changed=ai_metrics.get("avg_lines_changed"),
            human_avg_lines_changed=human_metrics.get("avg_lines_changed"),
        )

    def _calculate_pr_performance(
        self, prs: List[Dict[str, Any]]
    ) -> Dict[str, Optional[float]]:
        """Calculate performance metrics for a set of PRs"""
        if not prs:
            return {
                "avg_merge_time": None,
                "avg_review_cycles": None,
                "avg_files_changed": None,
                "avg_lines_changed": None,
            }

        merge_times = []
        files_changed = []
        lines_changed = []

        for pr in prs:
            # Calculate merge time
            created_at = pr.get("created_at")
            merged_at = pr.get("merged_at")

            if created_at and merged_at:
                if isinstance(created_at, str):
                    created_dt = datetime.fromisoformat(
                        created_at.replace("Z", "+00:00")
                    )
                else:
                    created_dt = created_at

                if isinstance(merged_at, str):
                    merged_dt = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
                else:
                    merged_dt = merged_at

                merge_time_hours = (merged_dt - created_dt).total_seconds() / 3600
                merge_times.append(merge_time_hours)

            # Files changed
            changed_files = pr.get("changed_files", 0)
            if changed_files:
                files_changed.append(changed_files)

            # Lines changed
            additions = pr.get("additions", 0) or 0
            deletions = pr.get("deletions", 0) or 0
            total_lines = additions + deletions
            if total_lines > 0:
                lines_changed.append(total_lines)

        return {
            "avg_merge_time": sum(merge_times) / len(merge_times)
            if merge_times
            else None,
            "avg_review_cycles": None,  # Would need review data to calculate
            "avg_files_changed": sum(files_changed) / len(files_changed)
            if files_changed
            else None,
            "avg_lines_changed": sum(lines_changed) / len(lines_changed)
            if lines_changed
            else None,
        }

    def _analyze_trends(
        self, prs: List[Dict[str, Any]], analyses: List[AIAuthorshipResult], days: int
    ) -> AITrendAnalysis:
        """Analyze AI adoption trends over time"""

        # Group PRs by week
        weekly_data = defaultdict(lambda: {"ai": 0, "total": 0})

        for pr, analysis in zip(prs, analyses):
            created_at = pr.get("created_at")
            if not created_at:
                continue

            if isinstance(created_at, str):
                pr_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                pr_date = created_at

            # Get week start (Monday)
            week_start = pr_date - timedelta(days=pr_date.weekday())
            week_key = week_start.strftime("%Y-%m-%d")

            weekly_data[week_key]["total"] += 1

            # Count as AI if high/medium confidence or low confidence with high probability
            if analysis.confidence in [
                AIConfidenceLevel.HIGH,
                AIConfidenceLevel.MEDIUM,
            ] or (
                analysis.confidence == AIConfidenceLevel.LOW
                and analysis.ai_probability >= 0.3
            ):
                weekly_data[week_key]["ai"] += 1

        # Calculate adoption rates and extract data
        weekly_ai_adoption = {}
        weekly_ai_prs = {}
        weekly_total_prs = {}

        for week, data in weekly_data.items():
            weekly_total_prs[week] = data["total"]
            weekly_ai_prs[week] = data["ai"]
            weekly_ai_adoption[week] = (
                data["ai"] / data["total"] if data["total"] > 0 else 0.0
            )

        # Determine trend direction
        trend_direction = self._calculate_trend_direction(weekly_ai_adoption)

        return AITrendAnalysis(
            weekly_ai_adoption=weekly_ai_adoption,
            weekly_ai_prs=weekly_ai_prs,
            weekly_total_prs=weekly_total_prs,
            trend_direction=trend_direction,
        )

    def _calculate_trend_direction(self, weekly_adoption: Dict[str, float]) -> str:
        """Calculate trend direction from weekly adoption rates"""
        if len(weekly_adoption) < 2:
            return "stable"

        # Get sorted weeks and their adoption rates
        sorted_weeks = sorted(weekly_adoption.keys())
        rates = [weekly_adoption[week] for week in sorted_weeks]

        # Simple trend calculation: compare first half to second half
        mid_point = len(rates) // 2
        if mid_point == 0:
            return "stable"

        first_half_avg = sum(rates[:mid_point]) / mid_point
        second_half_avg = sum(rates[mid_point:]) / (len(rates) - mid_point)

        if second_half_avg > first_half_avg + 0.1:
            return "increasing"
        elif second_half_avg < first_half_avg - 0.1:
            return "decreasing"
        else:
            return "stable"

    def _assess_quality(
        self, prs: List[Dict[str, Any]], analyses: List[AIAuthorshipResult]
    ) -> AIQualityAssessment:
        """Assess quality of AI-generated code"""

        high_risk_prs = []
        issues = []
        recommendations = []

        ai_prs_count = 0
        quality_indicators = []

        for pr, analysis in zip(prs, analyses):
            # Skip if not AI-authored
            if analysis.confidence == AIConfidenceLevel.UNKNOWN:
                continue

            ai_prs_count += 1
            pr_number = pr.get("number", 0)

            # Check for risk indicators
            risk_score = 0

            # Large changes without tests
            additions = pr.get("additions", 0) or 0
            if additions > 500:
                risk_score += 0.3
                if pr_number not in high_risk_prs:
                    high_risk_prs.append(pr_number)

            # Multiple file types (potential over-engineering)
            if "files" in pr and pr["files"]:
                file_types = set()
                for file_data in pr["files"]:
                    filename = file_data.get("filename", "")
                    if "." in filename:
                        file_types.add(filename.split(".")[-1])

                if len(file_types) > 5:
                    risk_score += 0.2
                    if pr_number not in high_risk_prs:
                        high_risk_prs.append(pr_number)

            # High AI confidence with many indicators (potential over-detection)
            if (
                analysis.confidence == AIConfidenceLevel.HIGH
                and len(analysis.indicators) > 5
            ):
                risk_score += 0.1

            quality_indicators.append(1.0 - risk_score)  # Higher is better

        # Calculate overall quality score
        if quality_indicators:
            quality_score = (sum(quality_indicators) / len(quality_indicators)) * 100
        else:
            quality_score = 50.0  # Neutral score if no AI PRs

        # Generate common issues and recommendations
        if len(high_risk_prs) > 0:
            issues.append(f"{len(high_risk_prs)} AI PRs flagged as high-risk")
            recommendations.append("Review large AI-generated changes more carefully")

        if ai_prs_count > 0:
            ai_ratio = len(high_risk_prs) / ai_prs_count
            if ai_ratio > 0.3:
                issues.append("High proportion of risky AI-generated code")
                recommendations.append("Consider additional AI code review processes")

        return AIQualityAssessment(
            high_risk_ai_prs=high_risk_prs,
            quality_score=quality_score,
            common_issues=issues,
            recommendations=recommendations,
        )

    def _calculate_impact_score(
        self,
        metrics: AIImpactMetrics,
        trends: AITrendAnalysis,
        quality: AIQualityAssessment,
    ) -> float:
        """Calculate overall AI impact score (0-100)"""

        score = 0.0

        # Adoption component (0-40 points)
        adoption_score = min(metrics.ai_adoption_rate * 40, 40)
        score += adoption_score

        # Performance component (0-30 points)
        performance_score = 15  # Neutral baseline

        if (
            metrics.ai_avg_merge_time_hours is not None
            and metrics.human_avg_merge_time_hours is not None
        ):
            # AI faster = positive, AI slower = negative
            if metrics.human_avg_merge_time_hours > 0:
                time_ratio = (
                    metrics.ai_avg_merge_time_hours / metrics.human_avg_merge_time_hours
                )
                if time_ratio < 0.8:  # AI 20% faster
                    performance_score += 15
                elif time_ratio > 1.2:  # AI 20% slower
                    performance_score -= 10

        score += performance_score

        # Quality component (0-20 points)
        quality_score = (quality.quality_score / 100) * 20
        score += quality_score

        # Trend component (0-10 points)
        if trends.trend_direction == "increasing":
            score += 10
        elif trends.trend_direction == "stable":
            score += 5
        # decreasing gets 0 points

        return min(max(score, 0), 100)  # Clamp to 0-100

    def _determine_overall_confidence(
        self, analyses: List[AIAuthorshipResult]
    ) -> AIConfidenceLevel:
        """Determine overall confidence level for the analysis"""
        if not analyses:
            return AIConfidenceLevel.UNKNOWN

        # Count confidence levels
        confidence_counts = {
            AIConfidenceLevel.HIGH: 0,
            AIConfidenceLevel.MEDIUM: 0,
            AIConfidenceLevel.LOW: 0,
            AIConfidenceLevel.UNKNOWN: 0,
        }

        for analysis in analyses:
            confidence_counts[analysis.confidence] += 1

        total = len(analyses)
        high_ratio = confidence_counts[AIConfidenceLevel.HIGH] / total
        medium_ratio = confidence_counts[AIConfidenceLevel.MEDIUM] / total

        if high_ratio >= 0.3 or (high_ratio + medium_ratio) >= 0.5:
            return AIConfidenceLevel.HIGH
        elif (
            medium_ratio >= 0.3
            or confidence_counts[AIConfidenceLevel.LOW] / total >= 0.4
        ):
            return AIConfidenceLevel.MEDIUM
        elif confidence_counts[AIConfidenceLevel.UNKNOWN] / total < 0.7:
            return AIConfidenceLevel.LOW
        else:
            return AIConfidenceLevel.UNKNOWN

    def _generate_insights(
        self,
        metrics: AIImpactMetrics,
        trends: AITrendAnalysis,
        quality: AIQualityAssessment,
    ) -> List[str]:
        """Generate summary insights from the analysis"""
        insights = []

        # Adoption insights
        if metrics.ai_adoption_rate >= 0.5:
            insights.append(
                f"High AI adoption: {metrics.ai_adoption_rate:.1%} of PRs are AI-generated"
            )
        elif metrics.ai_adoption_rate >= 0.2:
            insights.append(
                f"Moderate AI adoption: {metrics.ai_adoption_rate:.1%} of PRs are AI-generated"
            )
        else:
            insights.append(
                f"Low AI adoption: {metrics.ai_adoption_rate:.1%} of PRs are AI-generated"
            )

        # Performance insights
        if (
            metrics.ai_avg_merge_time_hours
            and metrics.human_avg_merge_time_hours
            and metrics.ai_avg_merge_time_hours
            < metrics.human_avg_merge_time_hours * 0.8
        ):
            insights.append(
                "AI-generated PRs merge significantly faster than human PRs"
            )
        elif (
            metrics.ai_avg_merge_time_hours
            and metrics.human_avg_merge_time_hours
            and metrics.ai_avg_merge_time_hours
            > metrics.human_avg_merge_time_hours * 1.2
        ):
            insights.append("AI-generated PRs take longer to merge than human PRs")

        # Trend insights
        if trends.trend_direction == "increasing":
            insights.append("AI adoption is trending upward")
        elif trends.trend_direction == "decreasing":
            insights.append("AI adoption is declining")

        # Quality insights
        if quality.quality_score >= 80:
            insights.append("AI-generated code shows high quality indicators")
        elif quality.quality_score <= 40:
            insights.append("AI-generated code shows quality concerns")

        if quality.high_risk_ai_prs:
            insights.append(
                f"{len(quality.high_risk_ai_prs)} AI PRs flagged for additional review"
            )

        return insights
