# LogPose Integration Plan: Prototype → Production

## 📊 Current State Overview

You have **two separate implementations** that need to be merged:

### 1. **Boilerplate (Current Repo)** ✅ Production-Ready
Located in: `/Users/aryaman/Documents/Testing/`

**Tech Stack:**
- FastAPI with SQLAlchemy 2.0 ORM
- PostgreSQL database
- Alembic migrations
- Row-level access control (ACL)
- Redis caching
- Celery background tasks
- JWT authentication
- Layered architecture (Models → Repositories → Controllers → API)

**Already Implemented (by us today):**
- `Team` model with manager relationships
- `User` model with roles (CTO, Eng Head, Eng Manager, Engineer)
- `PullRequest` model (basic structure)
- `Role` hierarchy system
- Team-based access control with `TeamPrincipal`
- Database migrations ready

### 2. **Prototype (backend_copy + frontend_copy)** 🚀 Feature-Rich
Located in: `/Users/aryaman/Documents/Testing/backend_copy/` and `frontend_copy/`

**Backend Features:**
- ✅ GitHub OAuth integration
- ✅ GitHub API data fetching (PRs, commits, reviews)
- ✅ **PR Risk Analysis** - Advanced risk scoring:
  - Stuckness score (time stuck, unresolved threads, failed CI)
  - Blast radius (dependencies, critical paths, lines changed)
  - Dynamics score (author experience, reviewer load)
  - Business impact scoring
  - Composite risk levels (LOW, MEDIUM, HIGH, CRITICAL)
- ✅ **AI Impact Analysis**:
  - AI-generated code detection
  - Impact metrics on development velocity
  - Quality assessment
- ✅ Metrics computation (time to merge, review cycles, etc.)
- ✅ Data storage in JSON files

**Frontend Features:**
- ✅ React + TypeScript + Vite + Tailwind
- ✅ GitHub OAuth flow
- ✅ Repository picker
- ✅ Team/Contributor dashboard with charts
- ✅ PR Risk dashboard with filters
- ✅ AI Impact dashboard
- ✅ Expandable PR views
- ✅ Beautiful UI with Chart.js visualizations

---

## 🎯 Integration Strategy

### Phase 1: Backend Integration (Week 1)

#### Step 1.1: Enhance PullRequest Model
**What to do:** Extend the existing `PullRequest` model with fields from the prototype

```python
# app/models/pull_request.py (ENHANCED)

class PullRequest(Base, TimestampMixin):
    __tablename__ = "pull_requests"
    
    # Existing fields...
    github_pr_id = Column(BigInteger, nullable=False, unique=True)
    title = Column(Unicode(500), nullable=False)
    
    # ADD from prototype:
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    changed_files = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    review_comments_count = Column(Integer, default=0)
    
    # Review timing
    first_review_at = Column(DateTime(timezone=True), nullable=True)
    first_commit_at = Column(DateTime(timezone=True), nullable=True)
    merged_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Risk analysis fields (stored from computation)
    risk_level = Column(String(20), nullable=True)  # low, medium, high, critical
    stuckness_score = Column(Float, nullable=True)
    blast_radius_score = Column(Float, nullable=True)
    dynamics_score = Column(Float, nullable=True)
    composite_risk_score = Column(Float, nullable=True)
    
    # AI impact fields
    ai_probability = Column(Float, nullable=True)
    ai_confidence_level = Column(String(20), nullable=True)
```

#### Step 1.2: Create GitHub Integration Service
**Where:** `app/integrations/github_service.py`

```python
# Migrate code from backend_copy/github_fetcher.py
# This will handle:
# - GitHub API calls with proper authentication
# - PR data fetching
# - Commit data fetching
# - Review data fetching
```

#### Step 1.3: Create PR Risk Analysis Service
**Where:** `app/services/pr_risk_analyzer.py`

```python
# Migrate code from backend_copy/pr_risk_analyzer.py
# This will compute:
# - Stuckness metrics
# - Blast radius
# - Dynamics scoring
# - Store results in PullRequest model
```

#### Step 1.4: Create Background Tasks
**Where:** `worker/tasks/github_sync.py`

```python
@celery_app.task
def sync_repository_prs(owner: str, repo: str, team_id: int):
    """
    Background task to fetch and analyze PRs
    """
    # 1. Fetch PRs from GitHub
    # 2. Store in database
    # 3. Compute risk metrics
    # 4. Link to team
```

#### Step 1.5: Create API Endpoints
**Where:** `api/v1/pull_requests/` (new directory)

```python
# api/v1/pull_requests/pull_request.py
@router.get("/")
async def list_prs(
    team_id: Optional[int] = None,
    risk_level: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    pr_controller = Depends(Factory().get_pull_request_controller),
    assert_access = Depends(Permissions(PRPermission.READ))
):
    """List PRs with access control"""
    # Filter by team based on user's role
    # Apply risk level filter
    # Return with risk metrics
```

---

### Phase 2: Database Migration (Week 1)

#### Migration File
Create: `migrations/versions/20241002_enhance_pull_requests.py`

```python
def upgrade():
    # Add new columns to pull_requests table
    op.add_column('pull_requests', sa.Column('additions', sa.Integer()))
    op.add_column('pull_requests', sa.Column('deletions', sa.Integer()))
    op.add_column('pull_requests', sa.Column('changed_files', sa.Integer()))
    op.add_column('pull_requests', sa.Column('first_review_at', sa.DateTime(timezone=True)))
    op.add_column('pull_requests', sa.Column('first_commit_at', sa.DateTime(timezone=True)))
    op.add_column('pull_requests', sa.Column('merged_at', sa.DateTime(timezone=True)))
    op.add_column('pull_requests', sa.Column('closed_at', sa.DateTime(timezone=True)))
    op.add_column('pull_requests', sa.Column('risk_level', sa.String(20)))
    op.add_column('pull_requests', sa.Column('stuckness_score', sa.Float()))
    op.add_column('pull_requests', sa.Column('blast_radius_score', sa.Float()))
    op.add_column('pull_requests', sa.Column('dynamics_score', sa.Float()))
    op.add_column('pull_requests', sa.Column('composite_risk_score', sa.Float()))
    op.add_column('pull_requests', sa.Column('ai_probability', sa.Float()))
    op.add_column('pull_requests', sa.Column('ai_confidence_level', sa.String(20)))
```

---

### Phase 3: Frontend Integration (Week 2)

#### Step 3.1: Setup Frontend Structure
**Where:** Create `/Users/aryaman/Documents/Testing/frontend/` (new)

```bash
# Copy from frontend_copy and adapt
cp -r frontend_copy/* frontend/

# Update API base URL to point to FastAPI backend
# Update authentication to use JWT instead of session cookies
```

#### Step 3.2: Create TypeScript Types
**Where:** `frontend/src/types/`

```typescript
// types/logpose.ts
export interface PullRequest {
  id: number;
  github_pr_id: number;
  title: string;
  author: {
    id: number;
    username: string;
    role: string;
  };
  team: {
    id: number;
    name: string;
  };
  status: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  stuckness_score: number;
  blast_radius_score: number;
  dynamics_score: number;
  composite_risk_score: number;
  created_at: string;
  merged_at?: string;
}

export interface TeamMember {
  id: number;
  username: string;
  email: string;
  role: 'cto' | 'engineering_head' | 'engineering_manager' | 'engineer';
  primary_status: 'balanced' | 'overloaded' | 'blocked' | 'onboarding' | 'firefighting' | 'mentoring';
  teams: Team[];
  open_prs: PullRequest[];
}
```

#### Step 3.3: Create API Client
**Where:** `frontend/src/lib/api-client.ts`

```typescript
class LogPoseAPI {
  private baseURL = 'http://localhost:8000/api/v1';
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
  }

  async request(endpoint: string, options?: RequestInit) {
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
      ...options?.headers,
    };

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  }

  // Team endpoints
  async getTeam(teamId: number) {
    return this.request(`/teams/${teamId}`);
  }

  // PR endpoints
  async listPRs(params: { team_id?: number; risk_level?: string }) {
    const query = new URLSearchParams(params as any);
    return this.request(`/pull-requests?${query}`);
  }

  // User endpoints
  async getTeamMember(userId: number) {
    return this.request(`/users/${userId}`);
  }
}

export const api = new LogPoseAPI();
```

#### Step 3.4: Create Team Member Page
**Where:** `frontend/src/pages/TeamMemberPage.tsx`

This is the main LogPose V1 deliverable!

```tsx
// Team Member Page with 3 tabs: Snapshot, Analytics, Timeline
import { useState } from 'react';
import { SnapshotTab } from '../components/SnapshotTab';
import { AnalyticsTab } from '../components/AnalyticsTab';
import { TimelineTab } from '../components/TimelineTab';

export function TeamMemberPage({ userId }: { userId: number }) {
  const [activeTab, setActiveTab] = useState<'snapshot' | 'analytics' | 'timeline'>('snapshot');
  const { data: member, loading } = useTeamMember(userId);

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header with member info */}
      <MemberHeader member={member} />

      {/* Tab Navigation */}
      <TabNav active={activeTab} onChange={setActiveTab} />

      {/* Tab Content */}
      {activeTab === 'snapshot' && <SnapshotTab member={member} />}
      {activeTab === 'analytics' && <AnalyticsTab member={member} />}
      {activeTab === 'timeline' && <TimelineTab member={member} />}
    </div>
  );
}
```

---

## 📁 Final Directory Structure

```
Testing/
├── backend_copy/           # ARCHIVE (keep for reference)
├── frontend_copy/          # ARCHIVE (keep for reference)
│
├── frontend/               # 🆕 PRODUCTION FRONTEND
│   ├── src/
│   │   ├── pages/
│   │   │   ├── TeamMemberPage.tsx      # Main LogPose page
│   │   │   ├── TeamDashboard.tsx
│   │   │   ├── PRRiskDashboard.tsx
│   │   │   └── AIImpactDashboard.tsx
│   │   ├── components/
│   │   │   ├── SnapshotTab.tsx         # V1 Snapshot tab
│   │   │   ├── AnalyticsTab.tsx        # V1 Analytics tab
│   │   │   ├── TimelineTab.tsx         # V1 Timeline tab
│   │   │   ├── PRRiskCard.tsx
│   │   │   └── ...
│   │   ├── lib/
│   │   │   ├── api-client.ts           # JWT-based API client
│   │   │   └── types.ts
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── app/                    # ✅ PRODUCTION BACKEND
│   ├── models/
│   │   ├── pull_request.py             # Enhanced with risk fields
│   │   ├── team.py
│   │   ├── user.py
│   │   └── role.py
│   ├── repositories/
│   │   ├── pull_request.py
│   │   ├── team.py
│   │   └── user.py
│   ├── controllers/
│   │   ├── pull_request.py
│   │   ├── team.py
│   │   └── user.py
│   ├── integrations/
│   │   └── github_service.py           # 🆕 From prototype
│   ├── services/
│   │   ├── pr_risk_analyzer.py         # 🆕 From prototype
│   │   └── ai_impact_analyzer.py       # 🆕 From prototype
│   └── schemas/
│       ├── requests/
│       │   ├── pr_request.py
│       │   └── team_request.py
│       └── responses/
│           ├── pr_response.py
│           └── team_response.py
│
├── api/
│   └── v1/
│       ├── teams/                      # ✅ Team endpoints
│       ├── pull_requests/              # 🆕 PR endpoints
│       ├── users/                      # ✅ User endpoints
│       └── analytics/                  # 🆕 Analytics endpoints
│
├── worker/
│   └── tasks/
│       └── github_sync.py              # 🆕 Background PR sync
│
├── migrations/
│   └── versions/
│       ├── ...initial_models.py
│       ├── ...add_team_and_hierarchy.py
│       └── ...enhance_pull_requests.py # 🆕 Add risk fields
│
└── [core/, tests/, etc.] # Unchanged
```

---

## 🚀 Migration Checklist

### Week 1: Backend Integration

- [ ] **Day 1-2: Enhance Models**
  - [ ] Update `PullRequest` model with prototype fields
  - [ ] Create migration for new fields
  - [ ] Run migration
  - [ ] Update repositories and controllers

- [ ] **Day 3-4: Integrate Services**
  - [ ] Copy `github_fetcher.py` → `app/integrations/github_service.py`
  - [ ] Copy `pr_risk_analyzer.py` → `app/services/pr_risk_analyzer.py`
  - [ ] Copy `ai_impact_analyzer.py` → `app/services/ai_impact_analyzer.py`
  - [ ] Adapt to use SQLAlchemy models instead of Pydantic/JSON

- [ ] **Day 5: Create Background Tasks**
  - [ ] Create `worker/tasks/github_sync.py`
  - [ ] Test Celery task execution
  - [ ] Set up periodic task scheduling

- [ ] **Day 6-7: API Endpoints**
  - [ ] Create `api/v1/pull_requests/` endpoints
  - [ ] Create `api/v1/analytics/` endpoints
  - [ ] Add access control using existing ACL system
  - [ ] Write tests

### Week 2: Frontend Integration

- [ ] **Day 1-2: Setup & Configuration**
  - [ ] Copy frontend_copy → frontend/
  - [ ] Update API client for JWT auth
  - [ ] Update environment variables
  - [ ] Configure CORS in backend

- [ ] **Day 3-4: Team Member Page (V1 Core)**
  - [ ] Create `TeamMemberPage.tsx`
  - [ ] Create `SnapshotTab.tsx` component
  - [ ] Create `AnalyticsTab.tsx` component
  - [ ] Create `TimelineTab.tsx` component

- [ ] **Day 5-6: Additional Dashboards**
  - [ ] Adapt `PRRiskDashboard.tsx` for new API
  - [ ] Adapt `AIImpactDashboard.tsx` for new API
  - [ ] Create team hierarchy view

- [ ] **Day 7: Polish & Deploy**
  - [ ] End-to-end testing
  - [ ] Performance optimization
  - [ ] Documentation
  - [ ] Deploy to staging

---

## 🔧 Key Integration Points

### 1. **Authentication**
**Prototype:** Uses GitHub OAuth with session cookies  
**Production:** Uses JWT tokens  
**Solution:** Keep GitHub OAuth for linking accounts, but issue JWT after successful OAuth

```python
@app.get("/auth/callback")
async def auth_callback(code: str, state: str):
    # Exchange code for GitHub token
    github_token = await exchange_code_for_token(code)
    gh_user = await fetch_github_user(github_token)
    
    # Find or create user in database
    user = await user_controller.get_or_create_from_github(gh_user)
    
    # Issue JWT token
    jwt_token = create_jwt_token(user.id)
    
    # Return JWT to frontend
    return {"access_token": jwt_token, "user": user}
```

### 2. **Data Storage**
**Prototype:** JSON files in `storage/data/`  
**Production:** PostgreSQL database  
**Solution:** Store in database, optionally cache in Redis

### 3. **Access Control**
**Prototype:** Simple session-based checks  
**Production:** Row-level ACL with TeamPrincipal  
**Solution:** Use existing ACL system

```python
# PullRequest.__acl__() already handles this!
def __acl__(self):
    return [
        (Allow, UserPrincipal(self.author_id), self_permissions),
        (Allow, TeamPrincipal(self.team_id), team_read_permissions),
        (Allow, RolePrincipal("cto"), all_permissions),
    ]
```

---

## 💡 Benefits of This Integration

| Aspect | Prototype | Production (After Integration) |
|--------|-----------|-------------------------------|
| **Data Storage** | JSON files | PostgreSQL with ACID guarantees |
| **Authentication** | Session cookies | JWT tokens (stateless, scalable) |
| **Access Control** | Manual checks | Row-level ACL (automatic enforcement) |
| **Team Management** | Not implemented | Full hierarchy with roles |
| **Scalability** | Single instance | Multi-instance with Redis cache |
| **Background Jobs** | Synchronous | Celery distributed tasks |
| **API Design** | Flat endpoints | RESTful with versioning |
| **Type Safety** | Runtime Pydantic | Database schema + Pydantic |

---

## 📊 What You'll Have After Integration

✅ **Production-Grade Backend** with:
- GitHub OAuth + JWT authentication
- Team hierarchy (CTO → Eng Head → Eng Manager → Engineer)
- PR risk analysis (stuckness, blast radius, dynamics)
- AI impact analysis
- Background task processing
- Row-level access control
- Database persistence
- Caching layer

✅ **Modern Frontend** with:
- Team Member Page (Snapshot, Analytics, Timeline)
- PR Risk Dashboard
- AI Impact Dashboard
- Beautiful Tailwind UI
- Chart visualizations
- Responsive design

✅ **LogPose V1 Complete** - The Team Member Page with all planned features!

---

## 🎯 Next Steps

1. **Review this plan** and let me know if you have questions
2. **Start with Backend Integration** (Week 1)
3. **Then Frontend Integration** (Week 2)
4. **Test end-to-end**
5. **Deploy to production**

Would you like me to help you start with any specific part? I can generate the migration files, create the enhanced models, or help set up the integration services.

