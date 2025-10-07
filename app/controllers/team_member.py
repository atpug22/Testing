from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.models import Event, PullRequest, TeamMember, User
from app.repositories import (
    EventRepository,
    PullRequestRepository,
    TeamMemberRepository,
)
from core.controller import BaseController


def make_aware(dt: datetime) -> datetime:
    """Convert naive datetime to timezone-aware UTC datetime"""
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class TeamMemberController(BaseController[TeamMember]):
    """Controller for TeamMember with business logic for metrics computation"""

    def __init__(
        self,
        team_member_repository: TeamMemberRepository,
        event_repository: EventRepository,
        pr_repository: PullRequestRepository,
    ):
        super().__init__(model=TeamMember, repository=team_member_repository)
        self.team_member_repository = team_member_repository
        self.event_repository = event_repository
        self.pr_repository = pr_repository

    async def get_by_user_id(
        self, user_id: int, join_: set[str] | None = None
    ) -> TeamMember:
        """Get team member by user ID"""
        return await self.team_member_repository.get_by_user_id(user_id, join_)

    # === Primary Status Computation ===
    def calculate_primary_status(
        self,
        wip_count: int,
        reviews_pending_count: int,
        unresolved_comments: int,
        recent_prs: List[PullRequest],
    ) -> tuple[str, str, str]:
        """
        Calculate primary status based on workload.
        Returns (status, icon, reasoning)
        """
        # Overloaded: > 5 reviews pending OR > 8 WIP PRs
        if reviews_pending_count > 5:
            return (
                "overloaded",
                "🟠",
                f"Handling {reviews_pending_count} review requests - potential bottleneck",
            )

        if wip_count > 8:
            return (
                "overloaded",
                "🟠",
                f"{wip_count} PRs in progress - may need support",
            )

        # Blocked: multiple PRs with flow blockers
        blocked_prs = [
            pr for pr in recent_prs if pr.flow_blockers and len(pr.flow_blockers) > 0
        ]
        if len(blocked_prs) >= 3:
            return (
                "blocked",
                "🔴",
                f"{len(blocked_prs)} PRs stuck with blockers - needs attention",
            )

        # Firefighting: > 60% of PRs are bugs
        if recent_prs:
            bug_prs = [
                pr
                for pr in recent_prs
                if pr.labels and "bug" in [l.lower() for l in pr.labels]
            ]
            if len(bug_prs) / len(recent_prs) > 0.6:
                return (
                    "firefighting",
                    "🔥",
                    f"Mostly handling bug fixes ({len(bug_prs)}/{len(recent_prs)} PRs)",
                )

        # Mentoring: > 50% of time spent reviewing
        if reviews_pending_count > 0 and wip_count > 0:
            if reviews_pending_count > wip_count * 1.5:
                return (
                    "mentoring",
                    "🧑‍🏫",
                    f"High review activity ({reviews_pending_count} reviews vs {wip_count} authored)",
                )

        # Balanced: everything looks good
        return ("balanced", "🟢", "Work is progressing smoothly")

    # === KPI Computation ===
    async def compute_kpi_tiles(
        self, team_member_id: int, user_id: int
    ) -> Dict[str, Any]:
        """Compute all KPI tiles"""
        # Get authored PRs
        authored_prs = await self.pr_repository.get_by_author(user_id, join_=None)
        wip_prs = [pr for pr in authored_prs if pr.status == "open"]

        # Get assigned reviews (would need to query pr_reviewers table)
        # For now, using mock data structure
        reviews_pending = []  # TODO: Query from pr_reviewers join

        # Unresolved comments
        unresolved_count = sum(pr.unresolved_comments or 0 for pr in wip_prs)

        return {
            "wip": {
                "label": "WIP",
                "value": len(wip_prs),
                "hover_details": [pr.title for pr in wip_prs[:3]],
            },
            "reviews": {
                "label": "Reviews",
                "value": len(reviews_pending),
                "hover_details": [],  # Top 3 waiting PRs
            },
            "in_discussion": {
                "label": "In Discussion",
                "value": unresolved_count,
                "hover_details": [
                    f"{pr.title}: {pr.unresolved_comments} threads"
                    for pr in wip_prs
                    if pr.unresolved_comments > 0
                ][:3],
            },
            "last_active": {
                "label": "Last Active",
                "value": "2h ago",  # TODO: Calculate from last_active_at
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

    # === Copilot Insights Generation ===
    def generate_copilot_insights(
        self,
        team_member: TeamMember,
        recent_prs: List[PullRequest],
        recent_events: List[Event],
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered insights.
        Returns list of {type, signal, recommendation, priority, icon}
        """
        insights = []

        # Recognition: High velocity
        merged_last_week = [
            pr
            for pr in recent_prs
            if pr.merged_at
            and make_aware(pr.merged_at)
            > datetime.now(timezone.utc) - timedelta(days=7)
        ]
        if len(merged_last_week) >= 5:
            insights.append(
                {
                    "type": "recognition",
                    "signal": f"Merged {len(merged_last_week)} PRs this week",
                    "recommendation": "Celebrate high velocity in 1:1",
                    "priority": "medium",
                    "icon": "🎉",
                    "pr_ids": [pr.id for pr in merged_last_week],
                }
            )

        # Risk: Stale PRs
        stale_prs = [
            pr
            for pr in recent_prs
            if pr.status == "open"
            and make_aware(pr.created_at)
            < datetime.now(timezone.utc) - timedelta(days=7)
        ]
        if len(stale_prs) >= 2:
            insights.append(
                {
                    "type": "risk",
                    "signal": f"{len(stale_prs)} PRs open for >7 days",
                    "recommendation": "Review blockers and consider reassignment",
                    "priority": "high",
                    "icon": "⚠️",
                    "pr_ids": [pr.id for pr in stale_prs],
                }
            )

        # Health: Low review velocity
        if (
            team_member.review_velocity_median_hours
            and team_member.review_velocity_median_hours > 48
        ):
            insights.append(
                {
                    "type": "health",
                    "signal": f"Review velocity at {team_member.review_velocity_median_hours:.0f}h",
                    "recommendation": "Check in on workload and bandwidth",
                    "priority": "medium",
                    "icon": "🚩",
                    "pr_ids": [],
                }
            )

        # Collaboration: Helping many teammates
        if team_member.collaboration_reach and team_member.collaboration_reach >= 5:
            insights.append(
                {
                    "type": "collaboration",
                    "signal": f"Helping {team_member.collaboration_reach} teammates",
                    "recommendation": "Great collaboration! Consider knowledge sharing session",
                    "priority": "low",
                    "icon": "🤝",
                    "pr_ids": [],
                }
            )

        return insights

    # === Metrics Computation ===
    async def compute_velocity_metrics(self, user_id: int) -> Dict[str, Any]:
        """Compute velocity quadrant metrics"""
        # Get PRs from last 30 days
        all_prs = await self.pr_repository.get_by_author(user_id)
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        recent_prs = [pr for pr in all_prs if make_aware(pr.created_at) >= cutoff]

        # Merged PRs by week
        merged_by_week = {}
        for pr in recent_prs:
            if pr.merged_at:
                week_key = pr.merged_at.strftime("%Y-W%U")
                merged_by_week[week_key] = merged_by_week.get(week_key, 0) + 1

        # Avg cycle time
        cycle_times = []
        for pr in recent_prs:
            if pr.merged_at and pr.created_at:
                delta = make_aware(pr.merged_at) - make_aware(pr.created_at)
                cycle_times.append(delta.total_seconds() / 3600)  # hours

        avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else None

        return {
            "merged_prs_by_week": [
                {"week": k, "count": v} for k, v in sorted(merged_by_week.items())
            ],
            "avg_cycle_time_trend": [],  # TODO: Historical trend
            "total_merged_last_30_days": len([pr for pr in recent_prs if pr.merged_at]),
            "avg_cycle_time_hours": avg_cycle_time,
        }

    async def compute_work_focus_metrics(self, user_id: int) -> Dict[str, Any]:
        """Compute work focus quadrant metrics"""
        all_prs = await self.pr_repository.get_by_author(user_id)

        # Categorize by labels
        categories = {"feature": 0, "bug": 0, "chore": 0, "refactor": 0}
        for pr in all_prs:
            if pr.labels:
                labels_lower = [l.lower() for l in pr.labels]
                if "bug" in labels_lower or "fix" in labels_lower:
                    categories["bug"] += 1
                elif "feature" in labels_lower or "enhancement" in labels_lower:
                    categories["feature"] += 1
                elif "chore" in labels_lower or "maintenance" in labels_lower:
                    categories["chore"] += 1
                elif "refactor" in labels_lower:
                    categories["refactor"] += 1
                else:
                    categories["feature"] += 1  # default
            else:
                categories["feature"] += 1

        total = sum(categories.values()) or 1
        distribution = {k: (v / total) * 100 for k, v in categories.items()}

        return {
            "distribution": distribution,
            "codebase_familiarity_percentage": 24.0,  # TODO: Calculate from file changes
            "new_modules_touched": 12,  # TODO: Count new directories
        }

    async def compute_quality_metrics(
        self, user_id: int, team_member: TeamMember
    ) -> Dict[str, Any]:
        """Compute quality quadrant metrics"""
        return {
            "rework_rate_percentage": team_member.rework_rate_percentage or 0.0,
            "rework_trend": "stable",  # TODO: Compare with historical data
            "revert_count": team_member.revert_count or 0,
            "revert_trend": "down",  # TODO: Historical comparison
            "churn_percentage": team_member.churn_percentage,
        }

    async def compute_collaboration_metrics(
        self, team_member: TeamMember
    ) -> Dict[str, Any]:
        """Compute collaboration quadrant metrics"""
        return {
            "review_velocity_median_hours": team_member.review_velocity_median_hours,
            "collaboration_reach": team_member.collaboration_reach or 0,
            "top_collaborators": team_member.top_collaborators or [],
        }
