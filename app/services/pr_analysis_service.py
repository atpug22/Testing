"""
Enhanced PR Analysis Service with LangChain structured output.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel

from app.integrations.ai_prompts import PromptManager
from app.integrations.ai_providers import AIProviderFactory
from app.models.ai_analysis import AIModel
from app.prompts.prompt_registry import PromptVersion
from app.schemas.requests.pr_analysis_requests import (
    AIROIRequest,
    CopilotInsightsRequest,
    NarrativeTimelineRequest,
    PRBlockerFlagsRequest,
    PRRiskFlagsRequest,
    PRSummaryRequest,
)
from app.schemas.responses.pr_analysis_responses import (
    AIROIResponse,
    CopilotInsightsResponse,
    NarrativeTimelineResponse,
    PRBlockerFlagsResponse,
    PRRiskFlagsResponse,
    PRSummaryResponse,
)
from core.config import config

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class PRAnalysisService:
    """Enhanced PR Analysis Service with structured output support."""

    def __init__(self):
        self.provider_factory = AIProviderFactory()
        self.prompt_manager = PromptManager()
        # Handle missing enum values gracefully
        try:
            self.default_model = AIModel(config.AI_DEFAULT_MODEL)
        except ValueError:
            # Fallback to the first available model if the configured one doesn't exist
            self.default_model = list(AIModel)[0]

    async def _get_structured_analysis(
        self,
        request_data: BaseModel,
        prompt_template_name: str,
        response_model: Type[T],
    ) -> T:
        """
        Generic method for structured AI analysis with LangChain.

        Args:
            request_data: Pydantic model with input data
            prompt_template_name: Name of the prompt template file
            response_model: Pydantic model for output validation

        Returns:
            Structured response as Pydantic model
        """
        try:
            # Get AI provider
            provider = self.provider_factory.get_provider(self.default_model)

            # Get prompt template
            template = self.prompt_manager.get_template(
                prompt_template_name, PromptVersion.V1
            )
            if not template:
                raise ValueError(
                    f"Prompt template '{prompt_template_name}' not found")

            # Create output parser for structured output
            parser = PydanticOutputParser(pydantic_object=response_model)

            # Create prompt template with structured output format
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", template.system_prompt),
                    ("human", template.user_prompt_template),
                ]
            )

            # Format few-shot examples
            few_shot_examples = "\n".join(
                [
                    f"Input: {json.dumps(example['input'], indent=2)}\nOutput: {json.dumps(example['output'], indent=2)}"
                    for example in template.few_shot_examples
                ]
            )

            # Create the chain with structured output
            chain = prompt | provider.model.with_structured_output(
                response_model)

            # Prepare input data
            input_data = {
                "input_data": request_data.model_dump_json(),
                "few_shot_examples": few_shot_examples,
            }

            # Get structured response
            response = await chain.ainvoke(input_data)

            logger.info(
                f"Successfully generated structured analysis for {prompt_template_name}"
            )
            return response

        except Exception as e:
            logger.error(
                f"Failed to generate structured analysis for {prompt_template_name}: {e}"
            )
            raise

    async def analyze_pr_risk_flags(
        self, request: PRRiskFlagsRequest
    ) -> PRRiskFlagsResponse:
        """Analyze PR for risk flags using structured output."""
        return await self._get_structured_analysis(
            request, "pr_risk_flags", PRRiskFlagsResponse
        )

    async def analyze_pr_blocker_flags(
        self, request: PRBlockerFlagsRequest
    ) -> PRBlockerFlagsResponse:
        """Analyze PR for blocker flags using structured output."""
        return await self._get_structured_analysis(
            request, "pr_blocker_flags", PRBlockerFlagsResponse
        )

    async def generate_copilot_insights(
        self, request: CopilotInsightsRequest
    ) -> CopilotInsightsResponse:
        """Generate copilot insights using structured output."""
        return await self._get_structured_analysis(
            request, "copilot_insights", CopilotInsightsResponse
        )

    async def generate_narrative_timeline(
        self, request: NarrativeTimelineRequest
    ) -> NarrativeTimelineResponse:
        """Generate narrative timeline using structured output."""
        return await self._get_structured_analysis(
            request, "narrative_timeline", NarrativeTimelineResponse
        )

    async def analyze_ai_roi(self, request: AIROIRequest) -> AIROIResponse:
        """Analyze AI ROI metrics using structured output."""
        return await self._get_structured_analysis(
            request, "ai_roi", AIROIResponse
        )

    async def generate_pr_summary(self, request: PRSummaryRequest) -> PRSummaryResponse:
        """Generate PR summary using structured output."""
        return await self._get_structured_analysis(
            request, "pr_summary", PRSummaryResponse
        )


# Global instance
pr_analysis_service = PRAnalysisService()
