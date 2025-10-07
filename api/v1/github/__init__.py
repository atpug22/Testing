from fastapi import APIRouter

from .public_repos import router as public_repos_router
from .repositories import router as repositories_router

router = APIRouter(prefix="/github")
router.include_router(
    repositories_router, prefix="/repos", tags=["GitHub Repositories"]
)
router.include_router(
    public_repos_router, prefix="/public", tags=["Public Repositories"]
)
