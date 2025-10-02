# LogPose Quick Reference Card

## 🚀 Getting Started (3 Steps)

```bash
# 1. Setup
poetry install
docker-compose up -d

# 2. Configure (create .env file with DB credentials)
echo 'POSTGRES_URL=postgresql+asyncpg://postgres:password123@localhost:5432/fastapi-db' > .env

# 3. Run
make migrate
make run
```

**Server**: http://localhost:8000  
**Docs**: http://localhost:8000/docs

---

## 📂 Where to Add Code

| Task | Location | Example |
|------|----------|---------|
| Add database table | `app/models/` | `app/models/team.py` |
| Add data queries | `app/repositories/` | `app/repositories/team.py` |
| Add business logic | `app/controllers/` | `app/controllers/team.py` |
| Add API endpoint | `api/v1/` | `api/v1/teams/` |
| Add request/response schemas | `app/schemas/` | `app/schemas/requests/team.py` |
| Register controller | `core/factory/factory.py` | `get_team_controller()` |

---

## 🗄️ Database

**Type**: PostgreSQL 14.2 (async with asyncpg)

```bash
# Migrations
make migrate              # Apply all migrations
make rollback             # Undo last migration
make reset-database       # Reset all
make generate-migration   # Create new migration

# Direct access
docker exec -it testing-postgresql-1 psql -U postgres -d fastapi-db
```

**Connection String**:  
`postgresql+asyncpg://postgres:password123@localhost:5432/fastapi-db`

---

## 🏗️ Architecture Pattern

```
Request → Route → Controller → Repository → Model → Database
                     ↓
                  Validation, Business Logic, ACL
```

**Example Flow**:
```python
# 1. Route (api/v1/teams/team.py)
@router.get("/{team_id}")
async def get_team(team_id: int, controller=Depends(Factory().get_team_controller)):
    return await controller.get_by_id(team_id)

# 2. Controller (app/controllers/team.py)
async def get_by_id(self, id: int) -> Team:
    return await self.repository.get_by_id(id)

# 3. Repository (app/repositories/team.py)
async def get_by_id(self, id: int) -> Team:
    query = select(Team).where(Team.id == id)
    return await self.session.execute(query)

# 4. Model (app/models/team.py)
class Team(Base):
    __tablename__ = "teams"
    id = Column(BigInteger, primary_key=True)
    # ...
```

---

## 🔐 Access Control (LogPose Hierarchy)

### Roles (from highest to lowest)
1. **CTO** - Access to ALL teams and PRs
2. **Engineering Head** - Access to assigned teams
3. **Engineering Manager** - Access to their team
4. **Engineer** - Access to own PRs only

### How It Works
```python
# In model's __acl__() method:
def __acl__(self):
    return [
        (Allow, UserPrincipal(self.author_id), [PRPermission.READ]),
        (Allow, TeamPrincipal(self.team_id), [PRPermission.READ]),
        (Allow, RolePrincipal("cto"), all_permissions),
    ]

# In route:
@router.get("/prs/{id}")
async def get_pr(id: int, assert_access=Depends(Permissions(PRPermission.READ))):
    pr = await controller.get_by_id(id)
    assert_access(pr)  # Raises 403 if no access
    return pr
```

---

## 📝 Common Code Patterns

### 1. Create a New Model
```python
# app/models/my_model.py
from sqlalchemy import Column, BigInteger, String
from core.database import Base

class MyModel(Base):
    __tablename__ = "my_models"
    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
```

### 2. Create Repository
```python
# app/repositories/my_model.py
from app.models import MyModel
from core.repository import BaseRepository

class MyModelRepository(BaseRepository[MyModel]):
    async def get_by_name(self, name: str):
        query = self._query()
        query = query.filter(MyModel.name == name)
        return await self._one_or_none(query)
```

### 3. Create Controller
```python
# app/controllers/my_model.py
from app.models import MyModel
from app.repositories import MyModelRepository
from core.controller import BaseController

class MyModelController(BaseController[MyModel]):
    def __init__(self, repository: MyModelRepository):
        super().__init__(model=MyModel, repository=repository)
        self.repository = repository
```

### 4. Register in Factory
```python
# core/factory/factory.py
from app.controllers import MyModelController
from app.models import MyModel
from app.repositories import MyModelRepository

class Factory:
    my_model_repository = partial(MyModelRepository, MyModel)
    
    def get_my_model_controller(self, db_session=Depends(get_session)):
        return MyModelController(
            repository=self.my_model_repository(db_session=db_session)
        )
```

### 5. Create API Route
```python
# api/v1/my_models/my_model.py
from fastapi import APIRouter, Depends
from core.factory import Factory

router = APIRouter(prefix="/my-models", tags=["My Models"])

@router.get("/{id}")
async def get_my_model(
    id: int,
    controller=Depends(Factory().get_my_model_controller)
):
    return await controller.get_by_id(id)
```

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test file
poetry run pytest tests/api/test_user.py -vv

# Run with coverage
poetry run pytest --cov=app --cov=core
```

---

## 📦 Key Dependencies

| Package | Purpose |
|---------|---------|
| FastAPI | Web framework |
| SQLAlchemy 2.0 | ORM |
| Alembic | Migrations |
| Pydantic | Validation |
| asyncpg | PostgreSQL driver |
| Redis | Caching |
| Celery | Background tasks |
| PyJWT | Authentication |
| Uvicorn | ASGI server |

---

## 🔍 Debugging

### View SQL Queries
Set in `.env`:
```
SHOW_SQL_ALCHEMY_QUERIES=1
```

### Check Docker Logs
```bash
docker-compose logs -f postgresql
docker-compose logs -f redis
```

### Interactive Python Shell
```bash
poetry shell
python

# In Python:
from app.models import User, Team
from core.database import get_session
# ... test queries
```

---

## 🎯 LogPose-Specific Enums

```python
# Already implemented in app/models/

# User Roles
Role.CTO
Role.ENGINEERING_HEAD
Role.ENGINEERING_MANAGER
Role.ENGINEER

# PR Status (domain concepts from master context)
PrimaryStatus.BALANCED
PrimaryStatus.OVERLOADED
PrimaryStatus.BLOCKED
PrimaryStatus.ONBOARDING
PrimaryStatus.FIREFIGHTING
PrimaryStatus.MENTORING

# Flow Blockers
FlowBlocker.AWAITING_REVIEW
FlowBlocker.REVIEW_STALEMATE
FlowBlocker.BROKEN_BUILD
FlowBlocker.IDLE_PR
FlowBlocker.MISSING_TESTS

# Risk Flags
RiskFlag.CRITICAL_FILE_CHANGE
RiskFlag.LARGE_BLAST_RADIUS
RiskFlag.SCOPE_CREEP_DETECTED
RiskFlag.MISSING_CONTEXT
RiskFlag.VULNERABILITY_DETECTED
RiskFlag.ROLLBACK_RISK
```

---

## 🚨 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| Port 5432 in use | `docker-compose down` then `docker-compose up -d` |
| Migration fails | `make reset-database` then `make migrate` |
| Module not found | `poetry install` |
| Permission denied | Ensure Docker is running |
| 401 on API calls | Include JWT token in headers |

---

## 📞 Need Help?

1. Check `SETUP_GUIDE.md` - Full setup instructions
2. Check `TEAM_ACCESS_CONTROL.md` - Access control details
3. Check `IMPLEMENTATION_SUMMARY.md` - What's been implemented
4. Check API docs at `/docs` - Interactive API testing

---

## 💡 Pro Tips

- Use `make` commands - they handle environment variables
- Enable SQL logging during development for debugging
- Use `join_={"relation_name"}` in repositories to eager load relationships
- All relationships use `lazy="raise"` to prevent N+1 queries
- Check existing tests in `tests/` for examples
- API is auto-documented at `/docs` - always up to date!

