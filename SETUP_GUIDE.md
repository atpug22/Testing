# LogPose Setup Guide

## 📊 Database & Infrastructure

### Database: PostgreSQL
This project uses **PostgreSQL 14.2** (via Docker) with **asyncpg** driver for async operations.

### Additional Services
- **Redis 6.2.7** - For caching
- **RabbitMQ 3.9.7** - For Celery task queue

All services are containerized using Docker Compose.

---

## 🚀 Quick Start

### Prerequisites
1. **Python 3.11+** (check with `python --version`)
2. **Docker & Docker Compose** ([Install](https://docs.docker.com/compose/install/))
3. **Poetry** - Python dependency manager ([Install](https://python-poetry.org/docs/#installation))

### Step-by-Step Setup

#### 1. Create Virtual Environment
```bash
poetry shell
```

#### 2. Install Dependencies
```bash
poetry install
```
Or using Make:
```bash
make install
```

#### 3. Start Docker Services
```bash
docker-compose up -d
```

This starts:
- PostgreSQL (main) on port **5432**
- PostgreSQL (test) on port **5431**
- Redis on port **6379**
- RabbitMQ on port **5672**

#### 4. Create Environment File
Create a `.env` file in the project root:

```bash
# .env
DEBUG=1
ENVIRONMENT=development
POSTGRES_URL=postgresql+asyncpg://postgres:password123@localhost:5432/fastapi-db
REDIS_URL=redis://localhost:6379/7
SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
CELERY_BROKER_URL=amqp://rabbit:password@localhost:5672
CELERY_BACKEND_URL=redis://localhost:6379/0
SHOW_SQL_ALCHEMY_QUERIES=0
```

#### 5. Run Migrations
```bash
make migrate
```

Or manually:
```bash
poetry run alembic upgrade head
```

This will create all tables including:
- `users` (with role, manager_id)
- `teams`
- `team_members`
- `pull_requests`
- `tasks`

#### 6. Start the Server
```bash
make run
```

Or manually:
```bash
poetry run python main.py
```

The server will start at: **http://localhost:8000**

#### 7. Access API Documentation
Open your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📁 Codebase Structure

```
Testing/
├── core/                    # Core boilerplate (minimal changes needed)
│   ├── cache/              # Redis caching system
│   ├── config.py           # Configuration management
│   ├── controller/         # Base controller class
│   ├── database/           # Database session, mixins, transactions
│   ├── exceptions/         # Custom exception handling
│   ├── factory/            # Dependency injection factory
│   │   └── factory.py      # 🔥 Register new controllers here
│   ├── fastapi/
│   │   ├── dependencies/   # FastAPI dependencies
│   │   │   ├── permissions.py  # 🔥 Access control principals
│   │   │   ├── current_user.py # Get current user
│   │   │   └── authentication.py
│   │   └── middlewares/    # Auth, logging, DB session middlewares
│   ├── repository/         # Base repository class
│   ├── security/           # JWT, password hashing, ACL
│   │   └── access_control.py  # 🔥 Principal system (TeamPrincipal, etc.)
│   ├── server.py           # FastAPI app creation
│   └── utils/              # Utility functions
│
├── app/                     # Application code (your main workspace)
│   ├── models/             # 🔥 Database models (SQLAlchemy)
│   │   ├── user.py         # User model with role, teams
│   │   ├── team.py         # Team model
│   │   ├── pull_request.py # PullRequest model
│   │   ├── role.py         # Role enum
│   │   └── task.py         # Task model (example)
│   │
│   ├── repositories/       # 🔥 Data access layer
│   │   ├── user.py         # User CRUD + team queries
│   │   ├── team.py         # Team CRUD + member management
│   │   ├── pull_request.py # PR queries
│   │   └── task.py         # Task repository
│   │
│   ├── controllers/        # 🔥 Business logic layer
│   │   ├── user.py         # User controller
│   │   ├── team.py         # Team controller
│   │   ├── pull_request.py # PR controller
│   │   ├── auth.py         # Authentication controller
│   │   └── task.py         # Task controller
│   │
│   ├── schemas/            # Pydantic schemas for validation
│   │   ├── requests/       # Request DTOs
│   │   ├── responses/      # Response DTOs
│   │   └── extras/         # Shared schemas
│   │
│   └── integrations/       # External API integrations (GitHub, etc.)
│
├── api/                     # 🔥 API endpoints (routes)
│   └── v1/
│       ├── users/          # User endpoints
│       ├── tasks/          # Task endpoints
│       ├── monitoring/     # Health checks
│       ├── teams/          # 🆕 Team endpoints (to be created)
│       └── pull_requests/  # 🆕 PR endpoints (to be created)
│
├── migrations/              # Alembic database migrations
│   └── versions/
│       ├── 20230205...initial_models.py
│       └── 20241002...add_team_and_hierarchy.py  # 🆕 Your migration
│
├── tests/                   # Test suite
│   ├── api/                # API tests
│   ├── core/               # Core tests
│   └── conftest.py         # Pytest fixtures
│
├── worker/                  # Celery tasks
│   └── tasks/
│
├── main.py                  # 🚀 Entry point
├── docker-compose.yml       # Docker services
├── pyproject.toml          # Poetry dependencies
├── alembic.ini             # Alembic configuration
├── Makefile                # Development commands
└── .env                    # Environment variables (create this)
```

---

## 🏗️ Architecture Overview

### Layered Architecture (Bottom to Top)

```
┌─────────────────────────────────────────────┐
│          API Layer (api/v1/*)               │  ← FastAPI routes
├─────────────────────────────────────────────┤
│      Controller Layer (app/controllers/)    │  ← Business logic
├─────────────────────────────────────────────┤
│    Repository Layer (app/repositories/)     │  ← Data access
├─────────────────────────────────────────────┤
│        Model Layer (app/models/)            │  ← SQLAlchemy models
└─────────────────────────────────────────────┘
```

### Request Flow Example

```
1. Client → GET /api/v1/teams/123
2. API Route → calls TeamController.get_by_id()
3. TeamController → calls TeamRepository.get_by_id()
4. TeamRepository → queries database using Team model
5. Database → returns Team object
6. TeamRepository → returns to Controller
7. TeamController → business logic, validation
8. API Route → serializes to response schema
9. Client ← JSON response
```

### Key Patterns

#### 1. **Factory Pattern** (`core/factory/factory.py`)
Centralized dependency injection:
```python
class Factory:
    def get_user_controller(self, db_session=Depends(get_session)):
        return UserController(
            user_repository=self.user_repository(db_session=db_session)
        )
```

#### 2. **Repository Pattern** (`app/repositories/*.py`)
Abstraction over database operations:
```python
class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str) -> User | None:
        # Database query logic
```

#### 3. **Access Control Lists (ACL)** (`app/models/*.py`)
Row-level permissions via `__acl__()` method:
```python
def __acl__(self):
    return [
        (Allow, UserPrincipal(self.author_id), [PRPermission.READ]),
        (Allow, TeamPrincipal(self.team_id), [PRPermission.READ]),
        (Allow, RolePrincipal("cto"), all_permissions),
    ]
```

---

## 🔧 Common Commands

### Database

```bash
# Run all migrations
make migrate

# Rollback last migration
make rollback

# Reset database (rollback all)
make reset-database

# Generate new migration (auto-detect model changes)
make generate-migration
```

### Development

```bash
# Start server (with hot reload)
make run
# or
make start

# Run tests
make test
# or
poetry run pytest -vv

# Format code
make format

# Lint code
make lint

# Check formatting (dry-run)
make check-format

# Start Celery worker
make celery-worker
```

### Docker

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f postgresql

# Access PostgreSQL CLI
docker exec -it testing-postgresql-1 psql -U postgres -d fastapi-db
```

---

## 🗃️ Database Connection Details

### Main Database (Development)
- **Host**: localhost
- **Port**: 5432
- **User**: postgres
- **Password**: password123
- **Database**: fastapi-db
- **URL**: `postgresql+asyncpg://postgres:password123@localhost:5432/fastapi-db`

### Test Database
- **Port**: 5431
- **Database**: db-test
- **URL**: `postgresql+asyncpg://postgres:password123@localhost:5431/db-test`

### Redis
- **Host**: localhost
- **Port**: 6379
- **URL**: `redis://localhost:6379/7`

---

## 📊 Current Database Schema

After running migrations, you'll have:

### Tables
1. **users**
   - id, uuid, email, username, password, is_admin
   - **role** (cto, engineering_head, engineering_manager, engineer)
   - **manager_id** (self-referential FK)
   - created_at, updated_at

2. **teams**
   - id, uuid, name, description
   - manager_id (FK to users)
   - created_at, updated_at

3. **team_members** (association table)
   - user_id (FK to users)
   - team_id (FK to teams)

4. **pull_requests**
   - id, uuid, github_pr_id, title, description, github_url, status
   - author_id (FK to users)
   - team_id (FK to teams)
   - created_at, updated_at

5. **tasks** (example)
   - id, uuid, title, description, is_completed
   - task_author_id (FK to users)
   - created_at, updated_at

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 5432
lsof -i :5432

# Stop existing PostgreSQL
docker-compose down
```

### Migration Errors
```bash
# Reset and re-run
make reset-database
make migrate
```

### Poetry Issues
```bash
# Update lock file
poetry lock

# Reinstall dependencies
poetry install --no-cache
```

### Database Connection Refused
```bash
# Ensure Docker containers are running
docker-compose ps

# Restart services
docker-compose restart postgresql
```

---

## 🎯 Next Steps for LogPose

1. **Create API endpoints** in `api/v1/teams/` and `api/v1/pull_requests/`
2. **Build Pydantic schemas** in `app/schemas/requests/` and `app/schemas/responses/`
3. **Integrate GitHub API** in `app/integrations/github.py`
4. **Add analytics logic** to controllers for Team Member Page
5. **Implement frontend** that calls these APIs

---

## 📚 Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Alembic**: https://alembic.sqlalchemy.org/
- **Poetry**: https://python-poetry.org/docs/

For LogPose-specific implementation details, see:
- `TEAM_ACCESS_CONTROL.md` - Access control system
- `IMPLEMENTATION_SUMMARY.md` - What was implemented

