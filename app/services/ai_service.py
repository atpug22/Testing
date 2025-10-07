"""
AI Service layer for handling AI analysis business logic.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.ai_prompts import prompt_manager
from app.integrations.ai_providers import AIProviderFactory, BaseAIProvider
from app.models.ai_analysis import (
    AIAnalysis,
    AIModel,
    AIPromptTemplate,
    AIUsageMetrics,
    AnalysisStatus,
    AnalysisType,
)
from app.schemas.requests.ai_requests import (
    BaseAIAnalysisRequest,
    BatchAnalysisRequest,
    CodeReviewRequest,
    CustomAnalysisRequest,
    PRSummaryRequest,
    RiskAssessmentRequest,
    TechnicalDebtRequest,
)
from app.schemas.responses.ai_responses import (
    BaseAIAnalysisResponse,
    BatchAnalysisResponse,
    CodeReviewResponse,
    CustomAnalysisResponse,
    PRSummaryResponse,
    RiskAssessmentResponse,
    TechnicalDebtResponse,
)
from core.database.session import get_session

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI analysis operations."""

    def __init__(self):
        # Initialize default prompt templates
        # Templates are now managed by the centralized registry
        pass

    async def analyze_pr_summary(
        self,
        request: PRSummaryRequest,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        pull_request_id: Optional[int] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> PRSummaryResponse:
        """Perform PR summary analysis."""
        try:
            # Get AI model
            ai_model = (
                AIModel(request.ai_model)
                if request.ai_model
                else AIModel.AZURE_OPENAI_GPT4O_MINI
            )
            provider = AIProviderFactory.get_provider(ai_model)

            # Get prompt template
            template = prompt_manager.get_template(
                "pr_summary_analysis",
                analysis_type=AnalysisType.PR_SUMMARY,
                ai_model=ai_model,
            )

            if not template:
                raise ValueError("PR summary prompt template not found")

            # Format prompt
            system_prompt, user_prompt = prompt_manager.format_prompt(
                template,
                pr_title=request.pr_title,
                pr_description=request.pr_description,
                repository_name=request.repository_name,
                author=request.author,
                reviewers=", ".join(request.reviewers),
                changed_files="\n".join(
                    f"- {file}" for file in request.changed_files),
                commit_messages="\n".join(
                    f"- {msg}" for msg in request.commit_messages
                ),
                diff_content=request.diff_content or "No diff content provided",
            )

            # Create analysis record
            analysis = await self._create_analysis_record(
                analysis_type=AnalysisType.PR_SUMMARY,
                ai_model=ai_model,
                input_data=request.dict(),
                input_text=user_prompt,
                prompt_template=template.name,
                user_id=user_id,
                team_id=team_id,
                pull_request_id=pull_request_id,
                db_session=db_session,
            )

            # Generate AI response
            from langchain.schema import HumanMessage, SystemMessage

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await provider.generate_structured_response(
                messages=messages, output_schema=template.output_schema
            )

            # Parse response
            try:
                output_data = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback to text parsing
                output_data = {"raw_output": response.content}

            # Update analysis record
            analysis.status = AnalysisStatus.COMPLETED
            analysis.output_data = output_data
            analysis.output_text = response.content
            analysis.confidence_score = int(
                output_data.get("confidence_score", 0.8) * 100
            )
            analysis.processing_time_ms = response.processing_time_ms
            analysis.token_usage = response.usage
            analysis.completed_at = datetime.utcnow()

            if db_session:
                await db_session.commit()

            # Record usage metrics
            await self._record_usage_metrics(
                ai_model=ai_model,
                analysis_type=AnalysisType.PR_SUMMARY,
                usage=response.usage,
                processing_time_ms=response.processing_time_ms,
                success=True,
                user_id=user_id,
                team_id=team_id,
                db_session=db_session,
            )

            # Create response
            return PRSummaryResponse(
                id=analysis.id,
                analysis_type=analysis.analysis_type.value,
                status=analysis.status.value,
                ai_model=analysis.ai_model.value,
                output_data=analysis.output_data,
                output_text=analysis.output_text,
                confidence_score=analysis.confidence_score,
                processing_time_ms=analysis.processing_time_ms,
                token_usage=analysis.token_usage,
                created_at=analysis.created_at,
                updated_at=analysis.updated_at,
                completed_at=analysis.completed_at,
                summary=output_data.get("summary"),
                key_changes=output_data.get("key_changes", []),
                risk_level=output_data.get("risk_level"),
                code_quality_score=output_data.get("code_quality_score"),
                performance_impact=output_data.get("performance_impact"),
                recommendations=output_data.get("recommendations", []),
                suggested_reviewers=output_data.get("suggested_reviewers", []),
                files_analyzed=len(request.changed_files),
                lines_changed=(
                    len(request.diff_content.split("\n")
                        ) if request.diff_content else 0
                ),
            )

        except Exception as e:
            logger.error(f"PR summary analysis failed: {e}")

            # Update analysis record with error
            if "analysis" in locals():
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                analysis.completed_at = datetime.utcnow()
                if db_session:
                    await db_session.commit()

            raise

    async def analyze_code_review(
        self,
        request: CodeReviewRequest,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> CodeReviewResponse:
        """Perform code review analysis."""
        try:
            # Get AI model
            ai_model = (
                AIModel(request.ai_model)
                if request.ai_model
                else AIModel.AZURE_OPENAI_GPT4O_MINI
            )
            provider = AIProviderFactory.get_provider(ai_model)

            # Get prompt template
            template = prompt_manager.get_template(
                "code_review_analysis",
                analysis_type=AnalysisType.CODE_REVIEW,
                ai_model=ai_model,
            )

            if not template:
                raise ValueError("Code review prompt template not found")

            # Format prompt
            system_prompt, user_prompt = prompt_manager.format_prompt(
                template,
                file_path=request.file_path,
                language=request.language,
                code_content=request.code_content,
                pr_context=request.pr_context or "No PR context provided",
                coding_standards=request.coding_standards
                or "Standard coding practices",
                check_security=request.check_security,
                check_performance=request.check_performance,
                check_best_practices=request.check_best_practices,
                check_readability=request.check_readability,
            )

            # Create analysis record
            analysis = await self._create_analysis_record(
                analysis_type=AnalysisType.CODE_REVIEW,
                ai_model=ai_model,
                input_data=request.dict(),
                input_text=user_prompt,
                prompt_template=template.name,
                user_id=user_id,
                team_id=team_id,
                db_session=db_session,
            )

            # Generate AI response
            from langchain.schema import HumanMessage, SystemMessage

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await provider.generate_structured_response(
                messages=messages, output_schema=template.output_schema
            )

            # Parse response
            try:
                output_data = json.loads(response.content)
            except json.JSONDecodeError:
                output_data = {"raw_output": response.content}

            # Update analysis record
            analysis.status = AnalysisStatus.COMPLETED
            analysis.output_data = output_data
            analysis.output_text = response.content
            analysis.confidence_score = int(
                output_data.get("confidence_score", 0.8) * 100
            )
            analysis.processing_time_ms = response.processing_time_ms
            analysis.token_usage = response.usage
            analysis.completed_at = datetime.utcnow()

            if db_session:
                await db_session.commit()

            # Record usage metrics
            await self._record_usage_metrics(
                ai_model=ai_model,
                analysis_type=AnalysisType.CODE_REVIEW,
                usage=response.usage,
                processing_time_ms=response.processing_time_ms,
                success=True,
                user_id=user_id,
                team_id=team_id,
                db_session=db_session,
            )

            # Create response
            return CodeReviewResponse(
                id=analysis.id,
                analysis_type=analysis.analysis_type.value,
                status=analysis.status.value,
                ai_model=analysis.ai_model.value,
                output_data=analysis.output_data,
                output_text=analysis.output_text,
                confidence_score=analysis.confidence_score,
                processing_time_ms=analysis.processing_time_ms,
                token_usage=analysis.token_usage,
                created_at=analysis.created_at,
                updated_at=analysis.updated_at,
                completed_at=analysis.completed_at,
                security_issues=output_data.get("security_issues", []),
                performance_issues=output_data.get("performance_issues", []),
                best_practice_violations=output_data.get(
                    "best_practice_violations", []
                ),
                readability_issues=output_data.get("readability_issues", []),
                overall_score=output_data.get("overall_score"),
                severity_level=output_data.get("severity_level"),
                improvement_suggestions=output_data.get(
                    "improvement_suggestions", []),
                refactoring_opportunities=output_data.get(
                    "refactoring_opportunities", []
                ),
            )

        except Exception as e:
            logger.error(f"Code review analysis failed: {e}")

            if "analysis" in locals():
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                analysis.completed_at = datetime.utcnow()
                if db_session:
                    await db_session.commit()

            raise

    async def analyze_risk_assessment(
        self,
        request: RiskAssessmentRequest,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        pull_request_id: Optional[int] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> RiskAssessmentResponse:
        """Perform risk assessment analysis."""
        try:
            # Get AI model
            ai_model = (
                AIModel(request.ai_model)
                if request.ai_model
                else AIModel.AZURE_OPENAI_GPT4O_MINI
            )
            provider = AIProviderFactory.get_provider(ai_model)

            # Get prompt template
            template = prompt_manager.get_template(
                "risk_assessment_analysis",
                analysis_type=AnalysisType.RISK_ASSESSMENT,
                ai_model=ai_model,
            )

            if not template:
                raise ValueError("Risk assessment prompt template not found")

            # Format prompt
            system_prompt, user_prompt = prompt_manager.format_prompt(
                template,
                pr_data=json.dumps(request.pr_data, indent=2),
                consider_blast_radius=request.consider_blast_radius,
                consider_author_experience=request.consider_author_experience,
                consider_reviewer_load=request.consider_reviewer_load,
                consider_ci_status=request.consider_ci_status,
                high_risk_threshold=request.high_risk_threshold,
                medium_risk_threshold=request.medium_risk_threshold,
            )

            # Create analysis record
            analysis = await self._create_analysis_record(
                analysis_type=AnalysisType.RISK_ASSESSMENT,
                ai_model=ai_model,
                input_data=request.dict(),
                input_text=user_prompt,
                prompt_template=template.name,
                user_id=user_id,
                team_id=team_id,
                pull_request_id=pull_request_id,
                db_session=db_session,
            )

            # Generate AI response
            from langchain.schema import HumanMessage, SystemMessage

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await provider.generate_structured_response(
                messages=messages, output_schema=template.output_schema
            )

            # Parse response
            try:
                output_data = json.loads(response.content)
            except json.JSONDecodeError:
                output_data = {"raw_output": response.content}

            # Update analysis record
            analysis.status = AnalysisStatus.COMPLETED
            analysis.output_data = output_data
            analysis.output_text = response.content
            analysis.confidence_score = int(
                output_data.get("confidence_score", 0.8) * 100
            )
            analysis.processing_time_ms = response.processing_time_ms
            analysis.token_usage = response.usage
            analysis.completed_at = datetime.utcnow()

            if db_session:
                await db_session.commit()

            # Record usage metrics
            await self._record_usage_metrics(
                ai_model=ai_model,
                analysis_type=AnalysisType.RISK_ASSESSMENT,
                usage=response.usage,
                processing_time_ms=response.processing_time_ms,
                success=True,
                user_id=user_id,
                team_id=team_id,
                db_session=db_session,
            )

            # Create response
            return RiskAssessmentResponse(
                id=analysis.id,
                analysis_type=analysis.analysis_type.value,
                status=analysis.status.value,
                ai_model=analysis.ai_model.value,
                output_data=analysis.output_data,
                output_text=analysis.output_text,
                confidence_score=analysis.confidence_score,
                processing_time_ms=analysis.processing_time_ms,
                token_usage=analysis.token_usage,
                created_at=analysis.created_at,
                updated_at=analysis.updated_at,
                completed_at=analysis.completed_at,
                overall_risk_score=output_data.get("overall_risk_score"),
                blast_radius_score=output_data.get("blast_radius_score"),
                author_experience_score=output_data.get(
                    "author_experience_score"),
                reviewer_load_score=output_data.get("reviewer_load_score"),
                ci_status_score=output_data.get("ci_status_score"),
                risk_level=output_data.get("risk_level"),
                risk_factors=output_data.get("risk_factors", []),
                mitigation_strategies=output_data.get(
                    "mitigation_strategies", []),
                recommended_actions=output_data.get("recommended_actions", []),
            )

        except Exception as e:
            logger.error(f"Risk assessment analysis failed: {e}")

            if "analysis" in locals():
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                analysis.completed_at = datetime.utcnow()
                if db_session:
                    await db_session.commit()

            raise

    async def analyze_custom(
        self,
        request: CustomAnalysisRequest,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> CustomAnalysisResponse:
        """Perform custom analysis."""
        try:
            # Get AI model
            ai_model = (
                AIModel(request.ai_model)
                if request.ai_model
                else AIModel.AZURE_OPENAI_GPT4O_MINI
            )
            provider = AIProviderFactory.get_provider(ai_model)

            # Create analysis record
            analysis = await self._create_analysis_record(
                analysis_type=AnalysisType.CUSTOM,
                ai_model=ai_model,
                input_data=request.dict(),
                input_text=request.custom_prompt,
                prompt_template="custom",
                user_id=user_id,
                team_id=team_id,
                db_session=db_session,
            )

            # Generate AI response
            from langchain.schema import HumanMessage

            messages = [HumanMessage(content=request.custom_prompt)]

            response = await provider.generate_response(messages=messages)

            # Parse response if JSON format requested
            output_data = None
            if request.output_format == "json":
                try:
                    output_data = json.loads(response.content)
                except json.JSONDecodeError:
                    output_data = {"raw_output": response.content}

            # Update analysis record
            analysis.status = AnalysisStatus.COMPLETED
            analysis.output_data = output_data
            analysis.output_text = response.content
            analysis.confidence_score = 75  # Default confidence for custom analysis
            analysis.processing_time_ms = response.processing_time_ms
            analysis.token_usage = response.usage
            analysis.completed_at = datetime.utcnow()

            if db_session:
                await db_session.commit()

            # Record usage metrics
            await self._record_usage_metrics(
                ai_model=ai_model,
                analysis_type=AnalysisType.CUSTOM,
                usage=response.usage,
                processing_time_ms=response.processing_time_ms,
                success=True,
                user_id=user_id,
                team_id=team_id,
                db_session=db_session,
            )

            # Create response
            return CustomAnalysisResponse(
                id=analysis.id,
                analysis_type=analysis.analysis_type.value,
                status=analysis.status.value,
                ai_model=analysis.ai_model.value,
                output_data=analysis.output_data,
                output_text=analysis.output_text,
                confidence_score=analysis.confidence_score,
                processing_time_ms=analysis.processing_time_ms,
                token_usage=analysis.token_usage,
                created_at=analysis.created_at,
                updated_at=analysis.updated_at,
                completed_at=analysis.completed_at,
                custom_output=output_data,
                formatted_output=response.content,
                output_format=request.output_format,
                processing_notes=["Custom analysis completed"],
            )

        except Exception as e:
            logger.error(f"Custom analysis failed: {e}")

            if "analysis" in locals():
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = str(e)
                analysis.completed_at = datetime.utcnow()
                if db_session:
                    await db_session.commit()

            raise

    async def analyze_batch(
        self,
        request: BatchAnalysisRequest,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> BatchAnalysisResponse:
        """Perform batch analysis."""
        import uuid

        batch_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        try:
            results = []
            errors = []

            if request.parallel:
                # Run analyses in parallel
                tasks = []
                for analysis_request in request.analyses:
                    task = self._process_single_analysis(
                        analysis_request, user_id, team_id, db_session
                    )
                    tasks.append(task)

                # Wait for all tasks to complete
                analysis_results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, result in enumerate(analysis_results):
                    if isinstance(result, Exception):
                        errors.append(
                            {
                                "index": i,
                                "error": str(result),
                                "analysis_type": request.analyses[i].analysis_type,
                            }
                        )
                    else:
                        results.append(result)
            else:
                # Run analyses sequentially
                for i, analysis_request in enumerate(request.analyses):
                    try:
                        result = await self._process_single_analysis(
                            analysis_request, user_id, team_id, db_session
                        )
                        results.append(result)
                    except Exception as e:
                        errors.append(
                            {
                                "index": i,
                                "error": str(e),
                                "analysis_type": analysis_request.analysis_type,
                            }
                        )

            completed_at = datetime.utcnow()
            total_processing_time = int(
                (completed_at - start_time).total_seconds() * 1000
            )

            return BatchAnalysisResponse(
                batch_id=batch_id,
                total_analyses=len(request.analyses),
                completed_analyses=len(results),
                failed_analyses=len(errors),
                results=results,
                errors=errors if errors else None,
                total_processing_time_ms=total_processing_time,
                parallel_execution=request.parallel,
                started_at=start_time,
                completed_at=completed_at,
            )

        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            raise

    async def _process_single_analysis(
        self,
        request: BaseAIAnalysisRequest,
        user_id: Optional[int],
        team_id: Optional[int],
        db_session: Optional[AsyncSession],
    ) -> BaseAIAnalysisResponse:
        """Process a single analysis request."""
        if isinstance(request, PRSummaryRequest):
            return await self.analyze_pr_summary(
                request, user_id, team_id, None, db_session
            )
        elif isinstance(request, CodeReviewRequest):
            return await self.analyze_code_review(request, user_id, team_id, db_session)
        elif isinstance(request, RiskAssessmentRequest):
            return await self.analyze_risk_assessment(
                request, user_id, team_id, None, db_session
            )
        elif isinstance(request, CustomAnalysisRequest):
            return await self.analyze_custom(request, user_id, team_id, db_session)
        else:
            raise ValueError(
                f"Unsupported analysis request type: {type(request)}")

    async def _create_analysis_record(
        self,
        analysis_type: AnalysisType,
        ai_model: AIModel,
        input_data: Dict[str, Any],
        input_text: str,
        prompt_template: str,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        pull_request_id: Optional[int] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> AIAnalysis:
        """Create an analysis record in the database."""
        analysis = AIAnalysis(
            analysis_type=analysis_type,
            status=AnalysisStatus.PENDING,
            ai_model=ai_model,
            input_data=input_data,
            input_text=input_text,
            prompt_template=prompt_template,
            user_id=user_id,
            team_id=team_id,
            pull_request_id=pull_request_id,
        )

        if db_session:
            db_session.add(analysis)
            await db_session.flush()
            await db_session.refresh(analysis)

        return analysis

    async def _record_usage_metrics(
        self,
        ai_model: AIModel,
        analysis_type: AnalysisType,
        usage: Dict[str, int],
        processing_time_ms: int,
        success: bool,
        user_id: Optional[int] = None,
        team_id: Optional[int] = None,
        db_session: Optional[AsyncSession] = None,
    ):
        """Record usage metrics for AI analysis."""
        if not db_session:
            return

        metrics = AIUsageMetrics(
            ai_model=ai_model,
            analysis_type=analysis_type,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            processing_time_ms=processing_time_ms,
            success=1 if success else 0,
            user_id=user_id,
            team_id=team_id,
        )

        db_session.add(metrics)
        await db_session.flush()


# Global AI service instance
ai_service = AIService()
