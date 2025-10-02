from fastapi import APIRouter

from .github import router as github_router
from .email import router as email_router
from .me import router as me_router

router = APIRouter(prefix="/auth")
router.include_router(github_router, prefix="/github", tags=["GitHub Auth"])
router.include_router(email_router, prefix="/email", tags=["Email Auth"])
router.include_router(me_router, tags=["Auth"])
