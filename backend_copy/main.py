from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv
from fastapi import Body, Cookie, FastAPI, Header, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from .github_oauth import (
    FRONTEND_URL,
    GITHUB_API_BASE,
    build_oauth_login_url,
    clear_session,
    exchange_code_for_token,
    fetch_github_user,
    generate_session_id,
    generate_state,
    get_session,
    set_session,
)
from .metrics import compute_metrics
from .models import FetchRequest, MetricsResponse, RepoDataset
from .pr_risk_api import router as pr_risk_router

load_dotenv()

DATA_DIR = Path(__file__).parent / "storage" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="GitHub Analytics MVP")

# Include PR Risk Analysis router
app.include_router(pr_risk_router)

origins = [FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/auth/login")
async def auth_login(response: Response) -> RedirectResponse:
    state = generate_state()
    # Store state in a non-HTTPOnly cookie for the simple flow. In production, use server-side store.
    response = RedirectResponse(url=build_oauth_login_url(state))
    response.set_cookie(
        "oauth_state", state, httponly=False, max_age=300, samesite="lax"
    )
    return response


@app.get("/auth/callback")
async def auth_callback(
    code: str, state: str, oauth_state: Optional[str] = Cookie(None)
) -> RedirectResponse:
    if not oauth_state or oauth_state != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    try:
        access_token = await exchange_code_for_token(code)
        gh_user = await fetch_github_user(access_token)
        session_id = generate_session_id()
        set_session(session_id, access_token, gh_user)
        response = RedirectResponse(url=f"{FRONTEND_URL}/#session_id={session_id}")
        response.set_cookie(
            "session_id",
            session_id,
            httponly=True,
            samesite="lax",
            max_age=60 * 60 * 24,
        )
        response.delete_cookie("oauth_state")
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth failed: {e}")


@app.post("/auth/logout")
async def logout(session_id: Optional[str] = Cookie(None)) -> Dict[str, str]:
    clear_session(session_id)
    resp = {"status": "ok"}
    return resp


async def _gh_get(
    session_id: Optional[str], url: str, params: Optional[Dict[str, Any]] = None
) -> httpx.Response:
    sess = get_session(session_id)
    if not sess:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token: str = sess["access_token"]  # type: ignore
    client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )
    resp = await client.get(url, params=params, timeout=60.0)
    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="GitHub auth expired")
    resp.raise_for_status()
    return resp


async def _gh_paginated(
    session_id: Optional[str], url: str, params: Optional[Dict[str, Any]] = None
) -> List[dict]:
    items: List[dict] = []
    page = 1
    per_page = 100
    params = params.copy() if params else {}
    while True:
        params.update({"per_page": per_page, "page": page})
        resp = await _gh_get(session_id, url, params=params)
        chunk = resp.json()
        if not isinstance(chunk, list):
            break
        items.extend(chunk)
        link = resp.headers.get("link")
        if link and 'rel="next"' in link:
            page += 1
        else:
            break
    return items


@app.get("/api/me")
async def api_me(
    session_id: Optional[str] = Cookie(None), x_session_id: Optional[str] = Header(None)
) -> dict:
    sid = x_session_id or session_id
    sess = get_session(sid)
    if not sess:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return sess["user"]  # type: ignore


@app.get("/api/repos")
async def api_repos(
    session_id: Optional[str] = Cookie(None), x_session_id: Optional[str] = Header(None)
) -> List[dict]:
    sid = x_session_id or session_id
    # List repositories the user has access to (affiliations owner, collaborator, organization_member)
    repos = await _gh_paginated(
        sid,
        f"{GITHUB_API_BASE}/user/repos",
        params={
            "affiliation": "owner,collaborator,organization_member",
            "sort": "pushed",
        },
    )
    # Simplify payload
    slim = [
        {
            "id": r.get("id"),
            "name": r.get("name"),
            "full_name": r.get("full_name"),
            "private": r.get("private"),
            "owner": {
                "login": r.get("owner", {}).get("login"),
                "id": r.get("owner", {}).get("id"),
                "avatar_url": r.get("owner", {}).get("avatar_url"),
                "html_url": r.get("owner", {}).get("html_url"),
            },
        }
        for r in repos
    ]
    return slim


def _dataset_path(owner: str, repo: str) -> Path:
    safe = f"{owner}__{repo}.json".replace("/", "_")
    return DATA_DIR / safe


async def _fetch_repo_dataset(
    session_id: Optional[str], owner: str, repo: str, days: int = 90
) -> RepoDataset:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    # Fetch PRs (state=all) since; we will stop once created_at < since
    prs: List[dict] = []
    page = 1
    per_page = 100
    while True:
        resp = await _gh_get(
            session_id,
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls",
            params={
                "state": "all",
                "sort": "created",
                "direction": "desc",
                "per_page": per_page,
                "page": page,
            },
        )
        chunk: List[dict] = (
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else []
        )
        if not chunk:
            break
        prs.extend(chunk)
        # Early stop: if the last PR in this page is older than 'since', we can stop
        last_created = chunk[-1].get("created_at")
        if last_created and last_created < since:
            break
        link = resp.headers.get("link")
        if link and 'rel="next"' in link:
            page += 1
        else:
            break

    filtered_prs = [pr for pr in prs if pr.get("created_at") >= since]

    # For each PR, fetch reviews and commits (first commit date)
    logging.info(f"Fetching details for {len(filtered_prs)} PRs in parallel")

    sem = asyncio.Semaphore(100)

    async def build_pr(pr: Dict[str, Any]) -> Dict[str, Any]:
        number = pr.get("number")
        async with sem:
            reviews_task = _gh_paginated(
                session_id,
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}/reviews",
                params={},
            )
            commits_task = _gh_paginated(
                session_id,
                f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{number}/commits",
                params={},
            )
            reviews, commits = await asyncio.gather(reviews_task, commits_task)

        first_review_at: Optional[str] = None
        if reviews:
            try:
                first_review_at = min(
                    r.get("submitted_at") for r in reviews if r.get("submitted_at")
                )
            except ValueError:
                first_review_at = None

        first_commit_at: Optional[str] = None
        if commits:
            dates = [
                c.get("commit", {}).get("author", {}).get("date")
                for c in commits
                if c.get("commit")
            ]
            dates = [d for d in dates if d]
            if dates:
                first_commit_at = min(dates)

        return {
            "number": pr.get("number"),
            "title": pr.get("title"),
            "user": {
                "login": pr.get("user", {}).get("login"),
                "id": pr.get("user", {}).get("id"),
                "avatar_url": pr.get("user", {}).get("avatar_url"),
                "html_url": pr.get("user", {}).get("html_url"),
            },
            "state": pr.get("state"),
            "created_at": pr.get("created_at"),
            "merged_at": pr.get("merged_at"),
            "closed_at": pr.get("closed_at"),
            "additions": pr.get("additions"),
            "deletions": pr.get("deletions"),
            "changed_files": pr.get("changed_files"),
            "comments": pr.get("comments"),
            "review_comments": pr.get("review_comments"),
            "first_review_at": first_review_at,
            "first_commit_at": first_commit_at,
        }

    result_prs: List[Dict[str, Any]] = await asyncio.gather(
        *(build_pr(pr) for pr in filtered_prs)
    )

    commits = await _gh_paginated(
        session_id,
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits",
        params={"since": since},
    )
    result_commits: List[Dict[str, Any]] = []
    for c in commits:
        author = c.get("author")
        commit_info = c.get("commit", {})
        date = commit_info.get("author", {}).get("date")
        if not date:
            continue
        result_commits.append(
            {
                "sha": c.get("sha"),
                "author": {
                    "login": author.get("login") if author else None,
                    "id": author.get("id") if author else None,
                    "avatar_url": author.get("avatar_url") if author else None,
                    "html_url": author.get("html_url") if author else None,
                }
                if author
                else None,
                "commit_author_name": commit_info.get("author", {}).get("name"),
                "commit_author_email": commit_info.get("author", {}).get("email"),
                "date": date,
            }
        )

    dataset = RepoDataset.model_validate(
        {
            "repo": repo,
            "owner": owner,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "prs": result_prs,
            "commits": result_commits,
        }
    )
    return dataset


@app.post("/api/fetch", response_model=MetricsResponse)
async def api_fetch(
    payload: FetchRequest = Body(...),
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None),
) -> MetricsResponse:
    owner = payload.owner
    repo = payload.repo
    force = bool(payload.force_refresh)
    days = int(payload.days or 90)
    path = _dataset_path(owner, repo)

    sid = x_session_id or session_id

    if path.exists() and not force:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        dataset = RepoDataset.model_validate(raw)
    else:
        dataset = await _fetch_repo_dataset(sid, owner, repo, days=days)
        with path.open("w", encoding="utf-8") as f:
            json.dump(json.loads(dataset.model_dump_json()), f, indent=2)

    metrics = compute_metrics(dataset)
    return MetricsResponse(dataset=dataset, metrics=metrics)


@app.get("/api/metrics", response_model=MetricsResponse)
async def api_metrics(
    owner: str = Query(...),
    repo: str = Query(...),
    days: int = Query(90),
    session_id: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None),
) -> MetricsResponse:
    sid = x_session_id or session_id
    path = _dataset_path(owner, repo)
    if not path.exists():
        dataset = await _fetch_repo_dataset(sid, owner, repo, days=days)
        with path.open("w", encoding="utf-8") as f:
            json.dump(json.loads(dataset.model_dump_json()), f, indent=2)
    else:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        dataset = RepoDataset.model_validate(raw)

    metrics = compute_metrics(dataset)
    return MetricsResponse(dataset=dataset, metrics=metrics)
