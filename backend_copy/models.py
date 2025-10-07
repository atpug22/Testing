from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class GitHubUser(BaseModel):
    login: str
    id: int
    avatar_url: Optional[str] = None
    html_url: Optional[str] = None
    name: Optional[str] = None


class Repository(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool
    owner: GitHubUser


class PullRequest(BaseModel):
    number: int
    title: str
    user: GitHubUser
    state: str
    created_at: datetime
    merged_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    additions: Optional[int] = 0
    deletions: Optional[int] = 0
    changed_files: Optional[int] = 0
    comments: Optional[int] = 0
    review_comments: Optional[int] = 0
    first_review_at: Optional[datetime] = None
    first_commit_at: Optional[datetime] = None


class Commit(BaseModel):
    sha: str
    author: Optional[GitHubUser] = None
    commit_author_name: Optional[str] = None
    commit_author_email: Optional[str] = None
    date: datetime


class RepoDataset(BaseModel):
    repo: str
    owner: str
    fetched_at: datetime
    prs: List[PullRequest]
    commits: List[Commit]


class ContributorMetrics(BaseModel):
    user: GitHubUser
    pr_throughput_by_week: Dict[str, Dict[str, int]]
    avg_time_to_merge_hours: Optional[float]
    avg_time_in_review_hours: Optional[float]
    avg_review_to_merge_hours: Optional[float]
    avg_pr_size_lines: Optional[float]
    avg_pr_files_changed: Optional[float]
    avg_review_cycles: Optional[float]
    commit_frequency_by_week: Dict[str, int]
    avg_wip_time_hours: Optional[float]


class TeamSummary(BaseModel):
    total_prs: int
    total_merged_prs: int
    total_commits: int
    avg_time_to_merge_hours: Optional[float]
    avg_time_in_review_hours: Optional[float]
    avg_review_to_merge_hours: Optional[float]
    avg_pr_size_lines: Optional[float]
    avg_pr_files_changed: Optional[float]


class Metrics(BaseModel):
    generated_at: datetime
    repo: str
    owner: str
    team_summary: TeamSummary
    contributors: List[ContributorMetrics]


class FetchRequest(BaseModel):
    owner: str
    repo: str
    force_refresh: Optional[bool] = False
    days: Optional[int] = 90


class MetricsResponse(BaseModel):
    dataset: RepoDataset
    metrics: Metrics
