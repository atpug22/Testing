from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from statistics import mean
from typing import Dict, Iterable, List, Optional, Tuple

try:
    from .models import (
        ContributorMetrics,
        GitHubUser,
        Metrics,
        PullRequest,
        RepoDataset,
        TeamSummary,
    )
except ImportError:
    # Fallback for direct import
    from models import (
        ContributorMetrics,
        GitHubUser,
        Metrics,
        PullRequest,
        RepoDataset,
        TeamSummary,
    )


def _week_start(dt: datetime) -> str:
    # Normalize to Monday week start ISO, return YYYY-MM-DD string in UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    iso_weekday = (dt.weekday() + 1) % 7  # Monday=0; keep Monday start
    week_start = dt.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        days=iso_weekday
    )
    return week_start.date().isoformat()


from datetime import timedelta  # placed after function to avoid shadowing


def _hours_between(a: Optional[datetime], b: Optional[datetime]) -> Optional[float]:
    if not a or not b:
        return None
    if a.tzinfo is None:
        a = a.replace(tzinfo=timezone.utc)
    if b.tzinfo is None:
        b = b.replace(tzinfo=timezone.utc)
    delta = (b - a).total_seconds() / 3600.0
    if delta < 0:
        return None
    return delta


def compute_metrics(dataset: RepoDataset) -> Metrics:
    prs: List[PullRequest] = dataset.prs

    # Index PRs by author
    author_to_prs: Dict[str, List[PullRequest]] = defaultdict(list)
    for pr in prs:
        author_to_prs[pr.user.login].append(pr)

    # Team-level aggregates
    all_time_to_merge: List[float] = []
    all_time_in_review: List[float] = []
    all_review_to_merge: List[float] = []
    all_pr_sizes: List[float] = []
    all_pr_files: List[float] = []

    # Contributor metrics
    contributors: List[ContributorMetrics] = []

    # Build commit frequency per user per week from dataset.commits
    commit_week_counts_by_user: Dict[str, Dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for c in dataset.commits:
        if not c.author or not c.author.login:
            continue
        w = _week_start(c.date)
        commit_week_counts_by_user[c.author.login][w] += 1

    # WIP time by PR author
    wip_times_by_author: Dict[str, List[float]] = defaultdict(list)

    for author, author_prs in author_to_prs.items():
        # Per-user accumulators
        created_counts_by_week: Dict[str, int] = defaultdict(int)
        merged_counts_by_week: Dict[str, int] = defaultdict(int)

        time_to_merge_values: List[float] = []
        time_in_review_values: List[float] = []
        review_to_merge_values: List[float] = []
        pr_size_values: List[float] = []
        pr_files_values: List[float] = []
        review_cycles_values: List[float] = []

        for pr in author_prs:
            created_week = _week_start(pr.created_at)
            created_counts_by_week[created_week] += 1
            if pr.merged_at:
                merged_week = _week_start(pr.merged_at)
                merged_counts_by_week[merged_week] += 1

            # Sizes
            size_lines = (pr.additions or 0) + (pr.deletions or 0)
            if size_lines > 0:
                pr_size_values.append(float(size_lines))
            if pr.changed_files:
                pr_files_values.append(float(pr.changed_files))

            # Times
            ttm = _hours_between(pr.created_at, pr.merged_at)
            if ttm is not None:
                time_to_merge_values.append(ttm)
                all_time_to_merge.append(ttm)

            tir = _hours_between(pr.created_at, pr.first_review_at)
            if tir is not None:
                time_in_review_values.append(tir)
                all_time_in_review.append(tir)

            rtm = _hours_between(pr.first_review_at, pr.merged_at)
            if rtm is not None:
                review_to_merge_values.append(rtm)
                all_review_to_merge.append(rtm)

            # Review cycles approximation using review + issue comments counts
            cycles = float((pr.review_comments or 0) + (pr.comments or 0))
            if cycles > 0:
                review_cycles_values.append(cycles)

            # WIP time
            wip = _hours_between(pr.first_commit_at, pr.created_at)
            if wip is not None:
                wip_times_by_author[author].append(wip)

        contributor = ContributorMetrics(
            user=author_prs[0].user,
            pr_throughput_by_week={
                w: {
                    "created": created_counts_by_week.get(w, 0),
                    "merged": merged_counts_by_week.get(w, 0),
                }
                for w in sorted(
                    set(
                        list(created_counts_by_week.keys())
                        + list(merged_counts_by_week.keys())
                    )
                )
            },
            avg_time_to_merge_hours=mean(time_to_merge_values)
            if time_to_merge_values
            else None,
            avg_time_in_review_hours=mean(time_in_review_values)
            if time_in_review_values
            else None,
            avg_review_to_merge_hours=mean(review_to_merge_values)
            if review_to_merge_values
            else None,
            avg_pr_size_lines=mean(pr_size_values) if pr_size_values else None,
            avg_pr_files_changed=mean(pr_files_values) if pr_files_values else None,
            avg_review_cycles=mean(review_cycles_values)
            if review_cycles_values
            else None,
            commit_frequency_by_week=dict(
                sorted(commit_week_counts_by_user.get(author, {}).items())
            ),
            avg_wip_time_hours=mean(wip_times_by_author.get(author, []))
            if wip_times_by_author.get(author)
            else None,
        )
        contributors.append(contributor)

        all_pr_sizes.extend(pr_size_values)
        all_pr_files.extend(pr_files_values)

    team_summary = TeamSummary(
        total_prs=len(prs),
        total_merged_prs=sum(1 for pr in prs if pr.merged_at is not None),
        total_commits=len(dataset.commits),
        avg_time_to_merge_hours=mean(all_time_to_merge) if all_time_to_merge else None,
        avg_time_in_review_hours=mean(all_time_in_review)
        if all_time_in_review
        else None,
        avg_review_to_merge_hours=mean(all_review_to_merge)
        if all_review_to_merge
        else None,
        avg_pr_size_lines=mean(all_pr_sizes) if all_pr_sizes else None,
        avg_pr_files_changed=mean(all_pr_files) if all_pr_files else None,
    )

    return Metrics(
        generated_at=datetime.now(timezone.utc),
        repo=dataset.repo,
        owner=dataset.owner,
        team_summary=team_summary,
        contributors=sorted(contributors, key=lambda c: c.user.login.lower()),
    )
