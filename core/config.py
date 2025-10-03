from enum import Enum
from typing import Optional

from pydantic import BaseSettings, Field


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


class Config(BaseSettings):
    DEBUG: int = Field(default=0, env="DEBUG")
    DEFAULT_LOCALE: str = Field(default="en_US", env="DEFAULT_LOCALE")
    ENVIRONMENT: str = Field(default=EnvironmentType.DEVELOPMENT, env="ENVIRONMENT")
    POSTGRES_URL: str = Field(
        default="postgresql+asyncpg://user:password@127.0.0.1:5432/db-name",
        env="POSTGRES_URL"
    )
    TEST_POSTGRES_URL: str = Field(
        default="postgresql+asyncpg://user:password@127.0.0.1:5431/db-test",
        env="TEST_POSTGRES_URL"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/7", env="REDIS_URL")
    RELEASE_VERSION: str = Field(default="0.1", env="RELEASE_VERSION")
    SHOW_SQL_ALCHEMY_QUERIES: int = Field(default=0, env="SHOW_SQL_ALCHEMY_QUERIES")
    SECRET_KEY: str = Field(default="super-secret-key", env="SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES: int = Field(default=60 * 24, env="JWT_EXPIRE_MINUTES")
    CELERY_BROKER_URL: str = Field(default="amqp://rabbit:password@localhost:5672", env="CELERY_BROKER_URL")
    CELERY_BACKEND_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BACKEND_URL")
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: str = Field(default="", env="GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: str = Field(default="", env="GITHUB_CLIENT_SECRET")
    APP_BASE_URL: str = Field(default="http://localhost:8000", env="APP_BASE_URL")
    FRONTEND_URL: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields from .env


config: Config = Config()
