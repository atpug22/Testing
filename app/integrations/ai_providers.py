"""
AI Provider abstraction layer for multiple AI models.
Supports Azure OpenAI, OpenAI, Anthropic, and other providers via LangChain.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from langchain.chat_models import init_chat_model
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.models.ai_analysis import AIModel
from core.config import config

logger = logging.getLogger(__name__)


class AIProviderConfig(BaseModel):
    """Configuration for AI providers."""

    model_name: str = Field(..., description="Model name")
    temperature: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Temperature")
    max_tokens: int = Field(default=4000, ge=1, le=8000,
                            description="Maximum tokens")
    timeout: int = Field(
        default=60, ge=1, description="Request timeout in seconds")

    # Provider-specific settings
    api_key: Optional[str] = Field(None, description="API key")
    endpoint: Optional[str] = Field(None, description="API endpoint")
    api_version: Optional[str] = Field(None, description="API version")
    deployment_name: Optional[str] = Field(None, description="Deployment name")


class AIResponse(BaseModel):
    """Standardized AI response."""

    content: str = Field(..., description="Response content")
    model: str = Field(..., description="Model used")
    usage: Dict[str, int] = Field(
        default_factory=dict, description="Token usage")
    processing_time_ms: int = Field(...,
                                    description="Processing time in milliseconds")
    confidence_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence score"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class BaseAIProvider(ABC):
    """Base class for AI providers."""

    def __init__(self, config: AIProviderConfig):
        self.config = config
        self.model = None
        self._initialize_model()

    @abstractmethod
    def _initialize_model(self):
        """Initialize the AI model."""
        pass

    @abstractmethod
    async def generate_response(
        self, messages: List[BaseMessage], **kwargs
    ) -> AIResponse:
        """Generate a response from the AI model."""
        pass

    @abstractmethod
    async def generate_structured_response(
        self, messages: List[BaseMessage], output_schema: Dict[str, Any], **kwargs
    ) -> AIResponse:
        """Generate a structured response following a schema."""
        pass

    def _prepare_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: Optional[List[BaseMessage]] = None,
    ) -> List[BaseMessage]:
        """Prepare messages for the AI model."""
        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        if conversation_history:
            messages.extend(conversation_history)

        messages.append(HumanMessage(content=user_prompt))

        return messages


class AzureOpenAIProvider(BaseAIProvider):
    """Azure OpenAI provider."""

    def _initialize_model(self):
        """Initialize Azure OpenAI model."""
        try:
            # For Azure AI Foundry, we need to extract the base endpoint URL
            # from the full chat/completions URL
            endpoint = self.config.endpoint

            # If endpoint contains the full path, extract just the base URL
            if "/chat/completions" in endpoint:
                # Extract base URL (everything before /chat/completions)
                base_endpoint = endpoint.split("/chat/completions")[0]
                # Remove /deployments/{deployment_name} if present
                if "/deployments/" in base_endpoint:
                    base_endpoint = base_endpoint.split("/deployments/")[0]
            else:
                base_endpoint = endpoint

            # Ensure base endpoint ends with slash
            if not base_endpoint.endswith("/"):
                base_endpoint += "/"

            self.model = init_chat_model(
                "gpt-4o-mini",
                model_provider="azure_openai",
                azure_endpoint=base_endpoint,
                api_key=self.config.api_key,
                api_version=self.config.api_version,
                azure_deployment=self.config.deployment_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
            )
            logger.info(
                f"Initialized Azure OpenAI provider with deployment: {self.config.deployment_name}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI provider: {e}")
            raise

    async def generate_response(
        self, messages: List[BaseMessage], **kwargs
    ) -> AIResponse:
        """Generate a response from Azure OpenAI."""
        import time

        start_time = time.time()

        try:
            response = await self.model.ainvoke(messages)
            processing_time = int((time.time() - start_time) * 1000)

            # Extract usage information
            usage = {}
            if hasattr(response, "usage_metadata"):
                usage = {
                    "input_tokens": getattr(response.usage_metadata, "input_tokens", 0),
                    "output_tokens": getattr(
                        response.usage_metadata, "output_tokens", 0
                    ),
                    "total_tokens": getattr(response.usage_metadata, "total_tokens", 0),
                }

            return AIResponse(
                content=response.content,
                model=self.config.model_name,
                usage=usage,
                processing_time_ms=processing_time,
                metadata={"provider": "azure_openai"},
            )
        except Exception as e:
            logger.error(f"Azure OpenAI generation failed: {e}")
            raise

    async def generate_structured_response(
        self, messages: List[BaseMessage], output_schema: Dict[str, Any], **kwargs
    ) -> AIResponse:
        """Generate a structured response from Azure OpenAI."""
        # For now, use the regular generation and parse JSON
        # In the future, we can use function calling or structured output
        response = await self.generate_response(messages, **kwargs)

        # Try to parse as JSON if possible
        try:
            import json

            parsed_content = json.loads(response.content)
            response.metadata["structured_output"] = parsed_content
        except json.JSONDecodeError:
            logger.warning("Response is not valid JSON, returning as text")

        return response


class OpenAIProvider(BaseAIProvider):
    """OpenAI provider."""

    def _initialize_model(self):
        """Initialize OpenAI model."""
        try:
            self.model = init_chat_model(
                self.config.model_name,
                model_provider="openai",
                openai_api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
            )
            logger.info(
                f"Initialized OpenAI provider with model: {self.config.model_name}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            raise

    async def generate_response(
        self, messages: List[BaseMessage], **kwargs
    ) -> AIResponse:
        """Generate a response from OpenAI."""
        import time

        start_time = time.time()

        try:
            response = await self.model.ainvoke(messages)
            processing_time = int((time.time() - start_time) * 1000)

            # Extract usage information
            usage = {}
            if hasattr(response, "usage_metadata"):
                usage = {
                    "input_tokens": getattr(response.usage_metadata, "input_tokens", 0),
                    "output_tokens": getattr(
                        response.usage_metadata, "output_tokens", 0
                    ),
                    "total_tokens": getattr(response.usage_metadata, "total_tokens", 0),
                }

            return AIResponse(
                content=response.content,
                model=self.config.model_name,
                usage=usage,
                processing_time_ms=processing_time,
                metadata={"provider": "openai"},
            )
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise

    async def generate_structured_response(
        self, messages: List[BaseMessage], output_schema: Dict[str, Any], **kwargs
    ) -> AIResponse:
        """Generate a structured response from OpenAI."""
        response = await self.generate_response(messages, **kwargs)

        # Try to parse as JSON if possible
        try:
            import json

            parsed_content = json.loads(response.content)
            response.metadata["structured_output"] = parsed_content
        except json.JSONDecodeError:
            logger.warning("Response is not valid JSON, returning as text")

        return response


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider."""

    def _initialize_model(self):
        """Initialize Anthropic model."""
        try:
            self.model = init_chat_model(
                self.config.model_name,
                model_provider="anthropic",
                anthropic_api_key=self.config.api_key,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
            )
            logger.info(
                f"Initialized Anthropic provider with model: {self.config.model_name}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}")
            raise

    async def generate_response(
        self, messages: List[BaseMessage], **kwargs
    ) -> AIResponse:
        """Generate a response from Anthropic."""
        import time

        start_time = time.time()

        try:
            response = await self.model.ainvoke(messages)
            processing_time = int((time.time() - start_time) * 1000)

            # Extract usage information
            usage = {}
            if hasattr(response, "usage_metadata"):
                usage = {
                    "input_tokens": getattr(response.usage_metadata, "input_tokens", 0),
                    "output_tokens": getattr(
                        response.usage_metadata, "output_tokens", 0
                    ),
                    "total_tokens": getattr(response.usage_metadata, "total_tokens", 0),
                }

            return AIResponse(
                content=response.content,
                model=self.config.model_name,
                usage=usage,
                processing_time_ms=processing_time,
                metadata={"provider": "anthropic"},
            )
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise

    async def generate_structured_response(
        self, messages: List[BaseMessage], output_schema: Dict[str, Any], **kwargs
    ) -> AIResponse:
        """Generate a structured response from Anthropic."""
        response = await self.generate_response(messages, **kwargs)

        # Try to parse as JSON if possible
        try:
            import json

            parsed_content = json.loads(response.content)
            response.metadata["structured_output"] = parsed_content
        except json.JSONDecodeError:
            logger.warning("Response is not valid JSON, returning as text")

        return response


class AIProviderFactory:
    """Factory for creating AI providers."""

    _providers: Dict[str, BaseAIProvider] = {}

    @classmethod
    def get_provider(
        cls, model: AIModel, custom_config: Optional[AIProviderConfig] = None
    ) -> BaseAIProvider:
        """Get or create an AI provider."""
        if model in cls._providers:
            return cls._providers[model]

        config = cls._get_default_config(model, custom_config)
        provider = cls._create_provider(model, config)
        cls._providers[model] = provider
        return provider

    @classmethod
    def _get_default_config(
        cls, model: AIModel, custom_config: Optional[AIProviderConfig]
    ) -> AIProviderConfig:
        """Get default configuration for a model."""
        if custom_config:
            return custom_config

        if model == AIModel.AZURE_OPENAI_GPT4O_MINI:
            return AIProviderConfig(
                model_name="gpt-4o-mini",
                api_key=config.AZURE_OPENAI_API_KEY,
                endpoint=config.AZURE_OPENAI_ENDPOINT,
                api_version=config.AZURE_OPENAI_API_VERSION,
                deployment_name=config.AZURE_OPENAI_DEPLOYMENT_NAME,
                temperature=config.AI_TEMPERATURE,
                max_tokens=config.AI_MAX_TOKENS,
            )
        elif model == AIModel.OPENAI_GPT4:
            return AIProviderConfig(
                model_name="gpt-4",
                api_key=config.OPENAI_API_KEY,
                temperature=config.AI_TEMPERATURE,
                max_tokens=config.AI_MAX_TOKENS,
            )
        elif model == AIModel.OPENAI_GPT35_TURBO:
            return AIProviderConfig(
                model_name="gpt-3.5-turbo",
                api_key=config.OPENAI_API_KEY,
                temperature=config.AI_TEMPERATURE,
                max_tokens=config.AI_MAX_TOKENS,
            )
        elif model == AIModel.ANTHROPIC_CLAUDE:
            return AIProviderConfig(
                model_name="claude-3-sonnet-20240229",
                api_key=config.ANTHROPIC_API_KEY,
                temperature=config.AI_TEMPERATURE,
                max_tokens=config.AI_MAX_TOKENS,
            )
        else:
            raise ValueError(f"Unsupported model: {model}")

    @classmethod
    def _create_provider(
        cls, model: AIModel, config: AIProviderConfig
    ) -> BaseAIProvider:
        """Create a provider instance."""
        if model == AIModel.AZURE_OPENAI_GPT4O_MINI:
            return AzureOpenAIProvider(config)
        elif model in [AIModel.OPENAI_GPT4, AIModel.OPENAI_GPT35_TURBO]:
            return OpenAIProvider(config)
        elif model == AIModel.ANTHROPIC_CLAUDE:
            return AnthropicProvider(config)
        else:
            raise ValueError(f"Unsupported model: {model}")

    @classmethod
    def clear_cache(cls):
        """Clear provider cache."""
        cls._providers.clear()

    @classmethod
    def get_available_models(cls) -> List[AIModel]:
        """Get list of available models based on configuration."""
        available = []

        if config.AZURE_OPENAI_API_KEY and config.AZURE_OPENAI_ENDPOINT:
            available.append(AIModel.AZURE_OPENAI_GPT4O_MINI)

        if config.OPENAI_API_KEY:
            available.extend([AIModel.OPENAI_GPT4, AIModel.OPENAI_GPT35_TURBO])

        if config.ANTHROPIC_API_KEY:
            available.append(AIModel.ANTHROPIC_CLAUDE)

        return available
