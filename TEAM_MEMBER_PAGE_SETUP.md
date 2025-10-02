
# Team Member Page MVP - Setup & Run Guide

## 🎉 What's Been Built

A complete **Team Member Page** MVP with:

### Backend (FastAPI)
- ✅ **New Models**:
  - `TeamMember` - Extended profile with all metrics (separate from User for modularity)
  - `Event` - Timeline activity tracking
  - Enhanced `PullRequest` - With flow blockers, risk flags, and detailed metadata
  
- ✅ **5 API Endpoints** (as specified):
  - `GET /api/v1/member/{id}/summary` - Primary Status + KPI tiles
  - `GET /api/v1/member/{id}/insights` - Copilot Insights (Recognition, Risk, Health, Collaboration)
  - `GET /api/v1/member/{id}/metrics` - All 4 quadrants (Velocity, Work Focus, Quality, Collaboration)
  - `GET /api/v1/member/{id}/prs` - PR cards (authored + assigned)
  - `GET /api/v1/member/{id}/timeline` - Chronological activity feed

- ✅ **Business Logic**:
  - Primary Status calculation (Balanced, Overloaded, Blocked, Firefighting, Mentoring)
  - KPI tile computation with hover details
  - Copilot Insights generation with icons and priorities
  - Metrics computation for all 4 quadrants
  
- ✅ **Mock Data**:
  - 1 Manager + 2 Engineers
  - ~10 PRs with realistic flow blockers & risk flags
  - Timeline events

---

## 🚀 Quick Start

### 1. Run Database Migrations

```bash
# From project root
make migrate

# Or manually:
poetry run alembic upgrade head
```

This creates:
- `team_members` table
- `events` table
- `pr_reviewers` association table
- Enhanced `pull_requests` table with new fields

### 2. Seed Demo Data

```bash
poetry run python scripts/seed_team_member_data.py
```

This creates:
- Team "Engineering Team Alpha"
- 3 users (1 manager, 2 engineers)
- 3 team member profiles with computed metrics
- 9 PRs with flow blockers and risk flags
- 8 timeline events

**Demo Credentials:**
- Manager: `alice_manager` / `demo123`
- Engineer 1: `bob_engineer` / `demo123` (Overloaded status)
- Engineer 2: `carol_engineer` / `demo123` (Firefighting status)

### 3. Start Backend

```bash
make run

# Or manually:
poetry run python main.py
```

Server runs at: **http://localhost:8000**

### 4. Test API Endpoints

Visit: **http://localhost:8000/docs**

Try these endpoints (you'll need to authenticate first):

```bash
# Get team member IDs from seed script output, then:

# Primary Status + KPI Tiles
GET /api/v1/member/1/summary

# Copilot Insights
GET /api/v1/member/1/insights

# All Quadrant Metrics
GET /api/v1/member/1/metrics

# PR Cards
GET /api/v1/member/1/prs

# Timeline
GET /api/v1/member/1/timeline?days=7
```

---

## 📁 What Was Created

### Models (`app/models/`)
```
team_member.py          # Extended profile with all LogPose metrics
event.py                # Timeline events
pull_request.py         # Enhanced with flow blockers, risk flags
```

### Repositories (`app/repositories/`)
```
team_member.py          # TeamMember data access
event.py                # Event queries (recent, by date range)
```

### Controllers (`app/controllers/`)
```
team_member.py          # Business logic:
                        # - calculate_primary_status()
                        # - compute_kpi_tiles()
                        # - generate_copilot_insights()
                        # - compute_velocity_metrics()
                        # - compute_work_focus_metrics()
                        # - compute_quality_metrics()
                        # - compute_collaboration_metrics()
```

### API Endpoints (`api/v1/member/`)
```
member.py               # 5 endpoints as per spec
```

### Schemas (`app/schemas/responses/`)
```
team_member.py          # Pydantic response models for all endpoints
```

### Database (`migrations/`)
```
20241002_team_member_page_models.py
```

### Scripts
```
scripts/seed_team_member_data.py
```

---

## 🎨 Frontend Setup (Next.js)

### Option 1: Create New Next.js App

```bash
# In project root
npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir
cd frontend
npm install recharts date-fns clsx
```

### Option 2: Setup Guide for Team Member Page UI

Create these components (structure provided, you can implement):

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Home/dashboard
│   └── member/
│       └── [id]/
│           └── page.tsx        # Team Member Page
│
├── components/
│   ├── TeamMemberPage/
│   │   ├── PrimaryStatus.tsx      # Status indicator (🟢🟠🔴🚀🔥🧑‍🏫)
│   │   ├── KPITiles.tsx           # WIP, Reviews, In Discussion, Last Active
│   │   ├── CopilotInsights.tsx    # 🎉⚠️🚩🤝 insights
│   │   ├── VelocityQuadrant.tsx   # Bar + line charts
│   │   ├── WorkFocusQuadrant.tsx  # Donut chart
│   │   ├── QualityQuadrant.tsx    # KPIs with trends
│   │   ├── CollaborationQuadrant.tsx
│   │   ├── PRCard.tsx             # Individual PR card
│   │   └── Timeline.tsx           # Activity feed
│   │
│   └── ui/
│       ├── Card.tsx
│       ├── Badge.tsx
│       └── ...
│
├── lib/
│   └── api-client.ts           # API calls to FastAPI backend
│
└── types/
    └── team-member.ts          # TypeScript types matching backend schemas
```

### API Client Example

```typescript
// lib/api-client.ts
const API_BASE = 'http://localhost:8000/api/v1';

export async function getTeamMemberSummary(memberId: number) {
  const res = await fetch(`${API_BASE}/member/${memberId}/summary`, {
    headers: {
      'Authorization': `Bearer ${getToken()}`,
    },
  });
  return res.json();
}

export async function getTeamMemberInsights(memberId: number) {
  const res = await fetch(`${API_BASE}/member/${memberId}/insights`, {
    headers: {
      'Authorization': `Bearer ${getToken()}`,
    },
  });
  return res.json();
}

export async function getTeamMemberMetrics(memberId: number) {
  const res = await fetch(`${API_BASE}/member/${memberId}/metrics`, {
    headers: {
      'Authorization': `Bearer ${getToken()}`,
    },
  });
  return res.json();
}

export async function getTeamMemberPRs(memberId: number) {
  const res = await fetch(`${API_BASE}/member/${memberId}/prs`, {
    headers: {
      'Authorization': `Bearer ${getToken()}`,
    },
  });
  return res.json();
}

export async function getTeamMemberTimeline(memberId: number, days: number = 7) {
  const res = await fetch(`${API_BASE}/member/${memberId}/timeline?days=${days}`, {
    headers: {
      'Authorization': `Bearer ${getToken()}`,
    },
  });
  return res.json();
}
```

---

## 📊 Data Model Overview

### TeamMember (Profile)
```python
# Separate from User - holds all LogPose-specific data
{
  primary_status: "balanced | overloaded | blocked | onboarding | firefighting | mentoring",
  last_active_at: datetime,
  
  # KPIs
  wip_count: int,
  reviews_pending_count: int,
  unresolved_discussions_count: int,
  
  # Velocity
  merged_prs_last_30_days: int,
  avg_cycle_time_hours: float,
  
  # Work Focus
  work_focus_distribution: {feature: %, bug: %, chore: %},
  codebase_familiarity_percentage: float,
  
  # Quality
  rework_rate_percentage: float,
  revert_count: int,
  churn_percentage: float,
  
  # Collaboration
  review_velocity_median_hours: float,
  collaboration_reach: int,
  top_collaborators: [{user_id, name, count}],
  
  # Future integrations (ready for Jira, Confluence, Slack)
  jira_metrics: JSON,
  confluence_metrics: JSON,
  chat_activity_metrics: JSON,
}
```

### PullRequest
```python
{
  title, description, status, author, team, reviewers,
  labels: ["feature", "bug", "priority: high"],
  flow_blockers: ["awaiting_review", "broken_build", "review_stalemate"],
  risk_flags: ["critical_file_change", "large_blast_radius", "scope_creep_detected"],
  unresolved_comments: int,
  lines_changed, additions, deletions, changed_files,
  created_at, merged_at, first_review_at,
}
```

### Event (Timeline)
```python
{
  type: "commit | pr_opened | pr_merged | review_submitted | issue_closed",
  timestamp, title, description,
  metadata: {blast_radius, issue_id, etc.}
}
```

---

## 🎯 Primary Status Logic

The system automatically calculates status based on workload:

| Status | Icon | Logic |
|--------|------|-------|
| **Overloaded** | 🟠 | > 5 reviews OR > 8 WIP PRs |
| **Blocked** | 🔴 | ≥ 3 PRs with flow blockers |
| **Firefighting** | 🔥 | > 60% of PRs are bugs |
| **Mentoring** | 🧑‍🏫 | Reviews > 1.5× authored PRs |
| **Balanced** | 🟢 | Everything looks good |

---

## 🔍 Copilot Insights

Auto-generated insights with icons:

| Type | Icon | Example Signal | Example Recommendation |
|------|------|----------------|----------------------|
| Recognition | 🎉 | "Merged 5 PRs this week" | "Celebrate high velocity in 1:1" |
| Risk | ⚠️ | "2 PRs open for >7 days" | "Review blockers, consider reassignment" |
| Health | 🚩 | "Review velocity at 48h" | "Check in on workload and bandwidth" |
| Collaboration | 🤝 | "Helping 5 teammates" | "Great collaboration! Consider knowledge sharing" |

---

## 🧪 Testing the MVP

1. **Start backend**: `make run`
2. **Seed data**: `python scripts/seed_team_member_data.py`
3. **Open Swagger UI**: http://localhost:8000/docs
4. **Authenticate** as `bob_engineer` / `demo123`
5. **Call endpoints**:
   - `/member/2/summary` → See Bob's overloaded status
   - `/member/2/insights` → See risk alerts about stale PRs
   - `/member/2/metrics` → See all quadrant data
   - `/member/2/timeline` → See recent activity

6. **Compare with Carol** (firefighting status):
   - `/member/3/summary` → 65% bug work
   - `/member/3/insights` → Different insights pattern

---

## 🎨 UI Reference (from prototype)

You can reference the prototype for UI inspiration:
- `backend_copy/` - API patterns
- `frontend_copy/src/ui/` - Component structure
- **Don't copy directly** - adapt to your clean boilerplate architecture

Key differences:
- ✅ Your backend uses **PostgreSQL** (not JSON files)
- ✅ Your backend has **proper auth** (JWT + RBAC)
- ✅ Your models are **modular** (TeamMember separate from User)
- ✅ Your structure is **extensible** (ready for Jira, Confluence, Slack)

---

## 🚀 Next Steps

1. ✅ **Backend is complete** and ready to demo
2. 🎨 **Build frontend** using Next.js + Tailwind + Recharts
3. 🔄 **Connect to GitHub** - Replace mock data with real PR data
4. 📊 **Add more metrics** - Expand quadrants as needed
5. 🔗 **Integrate Jira/Confluence** - Use reserved fields in TeamMember model

---

## 📚 Key Files to Understand

| File | Purpose |
|------|---------|
| `app/models/team_member.py` | **Core model** - All metrics live here |
| `app/controllers/team_member.py` | **Business logic** - Status calculation, insights generation |
| `api/v1/member/member.py` | **API endpoints** - 5 endpoints as per spec |
| `app/schemas/responses/team_member.py` | **Response models** - What frontend receives |
| `scripts/seed_team_member_data.py` | **Demo data** - Example of how data looks |

---

## 💡 Architecture Benefits

### Modularity
- `User` = Auth/RBAC only
- `TeamMember` = All LogPose metrics
- Easy to add new integrations (Jira, Confluence, etc.)

### Extensibility  
- JSON fields for flexible metrics
- Separate Event model for timeline
- Flow blockers & risk flags as arrays

### Production-Ready
- Proper migrations
- Repository pattern
- Controller business logic
- Pydantic validation
- Access control via existing ACL system

---

**You now have a working Team Member Page backend!** 🎉

The backend is complete and ready to demo. Build the Next.js frontend to visualize all this data!

