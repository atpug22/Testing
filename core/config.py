from enum import Enum
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


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
        env="POSTGRES_URL",
    )
    TEST_POSTGRES_URL: str = Field(
        default="postgresql+asyncpg://user:password@127.0.0.1:5431/db-test",
        env="TEST_POSTGRES_URL",
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/7", env="REDIS_URL")
    RELEASE_VERSION: str = Field(default="0.1", env="RELEASE_VERSION")
    SHOW_SQL_ALCHEMY_QUERIES: int = Field(default=0, env="SHOW_SQL_ALCHEMY_QUERIES")
    SECRET_KEY: str = Field(default="super-secret-key", env="SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_EXPIRE_MINUTES: int = Field(default=60 * 24, env="JWT_EXPIRE_MINUTES")
    CELERY_BROKER_URL: str = Field(
        default="amqp://rabbit:password@localhost:5672", env="CELERY_BROKER_URL"
    )
    CELERY_BACKEND_URL: str = Field(
        default="redis://localhost:6379/0", env="CELERY_BACKEND_URL"
    )

    # GitHub OAuth
    GITHUB_CLIENT_ID: str = Field(default="", env="GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: str = Field(default="", env="GITHUB_CLIENT_SECRET")
    APP_BASE_URL: str = Field(default="http://localhost:8000", env="APP_BASE_URL")
    FRONTEND_URL: str = Field(default="http://localhost:3000", env="FRONTEND_URL")

    # AI Configuration
    AZURE_OPENAI_API_KEY: str = Field(default="", env="AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: str = Field(default="", env="AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION: str = Field(
        default="2024-07-18-preview", env="AZURE_OPENAI_API_VERSION"
    )
    AZURE_OPENAI_DEPLOYMENT_NAME: str = Field(
        default="gpt-4o-mini", env="AZURE_OPENAI_DEPLOYMENT_NAME"
    )
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(default="", env="ANTHROPIC_API_KEY")
    AI_DEFAULT_MODEL: str = Field(
        default="AZURE_OPENAI_GPT4O_MINI", env="AI_DEFAULT_MODEL"
    )
    AI_MAX_TOKENS: int = Field(default=4000, env="AI_MAX_TOKENS")
    AI_TEMPERATURE: float = Field(default=0.7, env="AI_TEMPERATURE")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields from .env


config: Config = Config()
