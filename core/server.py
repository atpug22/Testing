import logging
from typing import List

from fastapi import Depends, FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import router
from core.cache import Cache, CustomKeyMaker, RedisBackend
from core.config import config
from core.exceptions import CustomException
from core.fastapi.dependencies import Logging
from core.fastapi.middlewares import (
    AuthBackend,
    AuthenticationMiddleware,
    ResponseLoggerMiddleware,
    SQLAlchemyMiddleware,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def on_auth_error(request: Request, exc: Exception):
    status_code, error_code, message = 401, None, str(exc)
    if isinstance(exc, CustomException):
        status_code = int(exc.code)
        error_code = exc.error_code
        message = exc.message

    return JSONResponse(
        status_code=status_code,
        content={"error_code": error_code, "message": message},
    )


def init_routers(app_: FastAPI) -> None:
    logger.info("Initializing routers...")
    try:
        app_.include_router(router)
        logger.info("✅ Router included successfully")
        logger.info(
            f"Registered routes: {[route.path for route in app_.routes if hasattr(route, 'path')]}"
        )
    except Exception as e:
        logger.error(f"❌ Failed to include router: {e}")
        raise


def init_listeners(app_: FastAPI) -> None:
    @app_.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        return JSONResponse(
            status_code=exc.code,
            content={"error_code": exc.error_code, "message": exc.message},
        )


def make_middleware() -> List[Middleware]:
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(
            AuthenticationMiddleware,
            backend=AuthBackend(),
            on_error=on_auth_error,
        ),
        Middleware(SQLAlchemyMiddleware),
        Middleware(ResponseLoggerMiddleware),
    ]
    return middleware


def init_cache() -> None:
    Cache.init(backend=RedisBackend(), key_maker=CustomKeyMaker())


def create_app() -> FastAPI:
    logger.info("🚀 Creating FastAPI application...")
    try:
        app_ = FastAPI(
            title="FastAPI Boilerplate",
            description="FastAPI Boilerplate by @iam-abbas",
            version="1.0.0",
            docs_url=None if config.ENVIRONMENT == "production" else "/docs",
            redoc_url=None if config.ENVIRONMENT == "production" else "/redoc",
            dependencies=[Depends(Logging)],
            middleware=make_middleware(),
        )
        logger.info("✅ FastAPI app created")

        init_routers(app_=app_)
        init_listeners(app_=app_)
        init_cache()

        logger.info("🎉 Application initialization complete!")
        return app_
    except Exception as e:
        logger.error(f"❌ Failed to create app: {e}")
        raise


app = create_app()
