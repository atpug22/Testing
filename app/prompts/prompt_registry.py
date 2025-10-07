"""
Centralized prompt registry with version management and structured output schemas.
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PromptVersion(str, Enum):
    """Prompt versions for backward compatibility."""

    V1 = "v1.0"
    V2 = "v2.0"


class PromptTemplate(BaseModel):
    """Structured prompt template with metadata."""

    name: str
    description: str
    version: PromptVersion
    system_prompt: str
    user_prompt_template: str
    few_shot_examples: List[Dict[str, Any]]
    output_schema: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    tags: List[str] = []
    is_active: bool = True


class PromptRegistry:
    """Centralized registry for all AI prompts with version management."""

    def __init__(self):
        self._prompts: Dict[str, Dict[str, PromptTemplate]] = {}
        self._initialize_prompts()

    def _initialize_prompts(self):
        """Initialize all prompt templates."""
        now = datetime.utcnow()

        # PR Risk Flags Analysis
        self._add_prompt(
            "pr_risk_flags",
            PromptVersion.V1,
            PromptTemplate(
                name="PR Risk Flags Analysis",
                description="Analyzes PR metadata to identify risk tags with detailed explanations",
                version=PromptVersion.V1,
                system_prompt="You are a code-change risk classifier assistant. You MUST analyze the ACTUAL input data provided and output risk tags based on the REAL information given. Do NOT generate fake data or use examples as templates. If you hallucinate or invent data not present in the input, you will fail this task.",
                user_prompt_template="""### CRITICAL INSTRUCTIONS:
1. Analyze ONLY the actual input data provided below
2. Do NOT invent or hallucinate any information not present in the input
3. Base your analysis on the REAL files, metrics, and descriptions provided
4. If information is missing, state that clearly in your analysis

### Input Data to Analyze:
{input_data}

### Risk Tag Criteria (apply ONLY if conditions are met in the actual data):
- Critical File Change: ONLY if files actually contain sensitive paths (auth/, security/, payment/, core/, database/)
- Large Blast Radius: ONLY if diff_count > 10 OR files span >3 different directory levels
- Vulnerability Detected: ONLY if title/description actually contains security keywords (security, exploit, CVE, vulnerability, etc.)
- Missing Context: ONLY if description is actually short (<50 chars) OR is clearly template text
- Rollback Risk: ONLY if files actually contain migration/DB patterns (migrations/, schema/, database/)

### Analysis Process:
1. Look at the actual files_changed array - what directories do they belong to?
2. Check the actual diff_count number - is it > 10?
3. Read the actual description text - is it short or template-like?
4. Examine the actual title - does it contain security keywords?
5. Look for actual migration files in the files_changed array

### MANDATORY VALIDATION:
Before outputting any risk, you MUST verify:
- The file names you mention MUST exist in the files_changed array
- The numbers you mention MUST match the actual input values
- The description text you quote MUST match the actual description
- The title you reference MUST match the actual title

### Output Format:
For each applicable risk, provide:
- tag: the risk name
- reason: explanation based on ACTUAL data from the input
- evidence: specific file names, numbers, or text from the ACTUAL input

### Few-shot examples:
{few_shot_examples}

### FINAL INSTRUCTION:
You MUST use ONLY the data provided in the input. If you cannot find evidence in the actual input data, do NOT create that risk. Double-check every file name, number, and text you reference against the actual input.

Now analyze the ACTUAL input data above and output JSON with applicable risks based on REAL information.""",
                few_shot_examples=[
                    {
                        "input": {
                            "title": "Fix authentication bug",
                            "files_changed": ["auth/login.js", "auth/logout.js", "core/security.py"],
                            "diff_count": 3,
                            "description": "Add login SSO",
                            "vulnerability_signals": ["none"]
                        },
                        "output": {
                            "risks": [
                                {
                                    "tag": "Critical File Change",
                                    "reason": "Files contain sensitive authentication and security paths",
                                    "evidence": "auth/login.js, auth/logout.js, core/security.py"
                                },
                                {
                                    "tag": "Missing Context",
                                    "reason": "Description is very brief at only 12 characters",
                                    "evidence": "Description: 'Add login SSO' (12 characters)"
                                }
                            ]
                        },
                    },
                    {
                        "input": {
                            "title": "Update UI components",
                            "files_changed": [
                                "ui/dashboard.js",
                                "backend/api/serviceA.js",
                                "backend/api/serviceB.js",
                                "backend/data/modelX.py",
                                "frontend/components/Button.js",
                                "tests/serviceA_test.js"
                            ],
                            "diff_count": 6,
                            "description": "Refactor UI components for better performance",
                            "vulnerability_signals": ["none"]
                        },
                        "output": {
                            "risks": [
                                {
                                    "tag": "Large Blast Radius",
                                    "reason": "Changes span multiple directory levels across different modules",
                                    "evidence": "6 files across ui/, backend/api/, backend/data/, frontend/components/, tests/ directories"
                                }
                            ]
                        },
                    },
                    {
                        "input": {
                            "title": "Black formatter staging",
                            "files_changed": ["core/controllers/admin.py", "core/controllers/base.py", "requirements_dev.in"],
                            "diff_count": 3,
                            "description": "## Overview\r\n\r\n<!--\r\nREAD ME FIRST:\r\nPlease answer *all* questions below and check off every point from the Essential Checklist!\r\nIf there is no corresponding issue number, fill in N/A where it says [fill_in_number_here] below in 1.\r\n-->\r\n\r\n1. This PR fixes or fixes part of #[fill_in_number_here].",
                            "vulnerability_signals": ["none"]
                        },
                        "output": {
                            "risks": [
                                {
                                    "tag": "Missing Context",
                                    "reason": "Description is template text with placeholder values instead of actual description",
                                    "evidence": "Description contains template placeholders: '[fill_in_number_here]' and checklist template"
                                }
                            ]
                        },
                    },
                ],
                output_schema={
                    "type": "object",
                    "properties": {
                        "risks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "tag": {
                                        "type": "string",
                                        "enum": [
                                            "Critical File Change",
                                            "Large Blast Radius",
                                            "Vulnerability Detected",
                                            "Missing Context",
                                            "Rollback Risk",
                                        ],
                                    },
                                    "reason": {"type": "string"},
                                    "evidence": {"type": "string"},
                                },
                                "required": ["tag", "reason"],
                            },
                        }
                    },
                    "required": ["risks"],
                },
                created_at=now,
                updated_at=now,
                tags=["pr", "risk", "analysis"],
            ),
        )

        # PR Blocker Flags Analysis
        self._add_prompt(
            "pr_blocker_flags",
            PromptVersion.V1,
            PromptTemplate(
                name="PR Blocker Flags Analysis",
                description="Detects PR blockers with detailed explanations based on metadata and thresholds",
                version=PromptVersion.V1,
                system_prompt="You are an assistant that detects PR blockers. You MUST analyze the ACTUAL input data provided and output blocker tags based on the REAL metrics and information given. Do NOT generate fake data or use examples as templates.",
                user_prompt_template="""### CRITICAL INSTRUCTIONS:
1. Analyze ONLY the actual input data provided below
2. Do NOT invent or hallucinate any information not present in the input
3. Base your analysis on the REAL metrics, counts, and status values provided
4. If information is missing, state that clearly in your analysis

### Input Data to Analyze:
{input_data}

### Blocker Tag Criteria (apply ONLY if conditions are met in the actual data):
- Awaiting Review: ONLY if review_requests > 0 AND comments_unresolved = 0 AND days_open > 1
- Review Stalemate: ONLY if comments_unresolved >= 2 AND no recent activity
- Broken Build: ONLY if ci_status actually equals "failing"
- Scope Creep: ONLY if lines_changed is significantly large compared to typical PRs
- Idle PR: ONLY if last_update_days > 3 OR days_open > 7 with no activity
- Missing Tests: ONLY if tests_modified = false AND files contain core modules

### Analysis Process:
1. Check the actual days_open number - is it > 1?
2. Check the actual review_requests number - is it > 0?
3. Check the actual comments_unresolved number - is it >= 2?
4. Check the actual ci_status value - is it "failing"?
5. Check the actual lines_changed number - is it unusually large?
6. Check the actual tests_modified value - is it false?

### Output Format:
For each applicable blocker, provide:
- tag: the blocker name
- reason: explanation based on ACTUAL data from the input
- evidence: specific numbers, names, or values from the ACTUAL input

### Few-shot examples:
{few_shot_examples}

Now analyze the ACTUAL input data above and output JSON with applicable blockers based on REAL information.""",
                few_shot_examples=[
                    {
                        "input": {
                            "days_open": 4,
                            "review_requests": 1,
                            "comments_unresolved": 0,
                            "ci_status": "passing",
                            "last_update_days": 0,
                            "lines_changed": 50,
                            "tests_modified": False,
                            "reviewers": ["alice", "bob"],
                            "pr_number": 123,
                            "pr_state": "open"
                        },
                        "output": {
                            "blockers": [
                                {
                                    "tag": "Awaiting Review",
                                    "reason": "PR has been open for 4 days with 1 review request but no resolved comments",
                                    "evidence": "days_open: 4, review_requests: 1, comments_unresolved: 0"
                                },
                                {
                                    "tag": "Missing Tests",
                                    "reason": "No test files were modified despite changes to core modules",
                                    "evidence": "tests_modified: false"
                                }
                            ]
                        },
                    },
                    {
                        "input": {
                            "days_open": 7,
                            "review_requests": 2,
                            "comments_unresolved": 3,
                            "ci_status": "passing",
                            "last_update_days": 0,
                            "lines_changed": 20,
                            "tests_modified": True,
                            "reviewers": ["charlie", "david"],
                            "pr_number": 124,
                            "pr_state": "open"
                        },
                        "output": {
                            "blockers": [
                                {
                                    "tag": "Review Stalemate",
                                    "reason": "Multiple unresolved comments indicate review discussion is stuck",
                                    "evidence": "comments_unresolved: 3, reviewers: charlie, david"
                                }
                            ]
                        },
                    },
                    {
                        "input": {
                            "days_open": 2,
                            "review_requests": 0,
                            "comments_unresolved": 0,
                            "ci_status": "failing",
                            "last_update_days": 0,
                            "lines_changed": 15,
                            "tests_modified": True,
                            "reviewers": [],
                            "pr_number": 125,
                            "pr_state": "open"
                        },
                        "output": {
                            "blockers": [
                                {
                                    "tag": "Broken Build",
                                    "reason": "Continuous integration status is failing",
                                    "evidence": "ci_status: failing"
                                }
                            ]
                        },
                    },
                ],
                output_schema={
                    "type": "object",
                    "properties": {
                        "blockers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "tag": {
                                        "type": "string",
                                        "enum": [
                                            "Awaiting Review",
                                            "Review Stalemate",
                                            "Broken Build",
                                            "Scope Creep Detected",
                                            "Idle PR",
                                            "Missing Tests",
                                        ],
                                    },
                                    "reason": {"type": "string"},
                                    "evidence": {"type": "string"},
                                },
                                "required": ["tag", "reason"],
                            },
                        }
                    },
                    "required": ["blockers"],
                },
                created_at=now,
                updated_at=now,
                tags=["pr", "blocker", "analysis"],
            ),
        )

        # Copilot Insights Analysis
        self._add_prompt(
            "copilot_insights",
            PromptVersion.V1,
            PromptTemplate(
                name="Copilot Insights Analysis",
                description="Generates manager-facing recommendations from engineering signals",
                version=PromptVersion.V1,
                system_prompt="You are an assistant that generates manager-facing recommendations from signals.",
                user_prompt_template="""### Input JSON:
{{input_data}}

### Signal categories & desired output:
- cycle_time_increase → recommendation to surface blocker or review scope
- after_hours_spike → recommendation to check workload / rest
- review_load_high → recommendation to rebalance review assignments
- velocity_drop → recommendation to examine scope & remove burdens
- collab_silo → recommend cross-team pairing or knowledge sharing

### Few-shot examples:
{few_shot_examples}

Now produce the JSON for the given input.""",
                few_shot_examples=[
                    {
                        "input": {
                            "signal": "cycle_time_increase",
                            "context": {"old": 2.1, "new": 4.0, "team_avg": 2.2},
                        },
                        "output": {
                            "signal": "cycle_time_increase",
                            "recommendation": "Schedule a 1:1 to identify blockers causing slowdown",
                        },
                    },
                    {
                        "input": {
                            "signal": "review_load_high",
                            "context": {"reviewLoad": 9, "teamAvg": 3},
                        },
                        "output": {
                            "signal": "review_load_high",
                            "recommendation": "Redistribute reviews to balance load among teammates",
                        },
                    },
                ],
                output_schema={
                    "type": "object",
                    "properties": {
                        "signal": {"type": "string"},
                        "recommendation": {"type": "string"},
                    },
                    "required": ["signal", "recommendation"],
                },
                created_at=now,
                updated_at=now,
                tags=["insights", "recommendation", "management"],
            ),
        )

        # Narrative Timeline Analysis
        self._add_prompt(
            "narrative_timeline",
            PromptVersion.V1,
            PromptTemplate(
                name="Narrative Timeline Analysis",
                description="Converts daily events into concise narrative timeline",
                version=PromptVersion.V1,
                system_prompt="You are an assistant that converts daily events into a concise narrative timeline for engineering work.",
                user_prompt_template="""### Input JSON:
{{input_data}}

### Rules:
- Only one or two key events per day
- If a PR has a special tag, mention in parentheses
- Use plain English
- Output as JSON:
{{"timeline": ["string", ...]}}

### Few-shot examples:
{few_shot_examples}

Now generate the narrative.""",
                few_shot_examples=[
                    {
                        "input": {
                            "daily_events": [
                                {
                                    "day": "Mon",
                                    "actions": ["opened PR #421", "reviewed PR #420"],
                                },
                                {
                                    "day": "Tue",
                                    "actions": [
                                        "merged PR #421",
                                        "commented on PR #423",
                                    ],
                                },
                            ],
                            "key_tags": {"PR421": "High Blast"},
                        },
                        "output": {
                            "timeline": [
                                "Mon: Opened PR #421 (High Blast Radius) and reviewed PR #420",
                                "Tue: Merged PR #421 and commented on PR #423",
                            ]
                        },
                    }
                ],
                output_schema={
                    "type": "object",
                    "properties": {
                        "timeline": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["timeline"],
                },
                created_at=now,
                updated_at=now,
                tags=["timeline", "narrative", "events"],
            ),
        )

        # AI ROI Analysis
        self._add_prompt(
            "ai_roi",
            PromptVersion.V1,
            PromptTemplate(
                name="AI ROI Analysis",
                description="Interprets AI tool usage metrics and provides insights",
                version=PromptVersion.V1,
                system_prompt="You are an assistant that interprets AI tool usage metrics and gives insights + recommendation.",
                user_prompt_template="""### Input JSON:
{{input_data}}

### Metric interpretations:
- adoption high, acceptance low → need trust / enablement
- velocity gain >10% → positive signal
- churn high → risk of dropoff

### Few-shot examples:
{few_shot_examples}

Generate JSON for the input data.""",
                few_shot_examples=[
                    {
                        "input": {
                            "adoption_rate": 0.7,
                            "suggestion_acceptance_rate": 0.4,
                            "velocity_gain_pct": 0.15,
                            "churn_rate": 0.02,
                        },
                        "output": {
                            "insights": [
                                "Strong adoption, moderate acceptance — trust may need boosting",
                                "Velocity improved by 15% post adoption",
                            ],
                            "recommendation": "Host enablement workshop to boost acceptance",
                        },
                    }
                ],
                output_schema={
                    "type": "object",
                    "properties": {
                        "insights": {"type": "array", "items": {"type": "string"}},
                        "recommendation": {"type": "string"},
                    },
                    "required": ["insights", "recommendation"],
                },
                created_at=now,
                updated_at=now,
                tags=["roi", "metrics", "insights"],
            ),
        )

        # PR Summary Analysis
        self._add_prompt(
            "pr_summary",
            PromptVersion.V1,
            PromptTemplate(
                name="PR Summary Analysis",
                description="Generates detailed 2-3 line summary of PR with confidence assessment",
                version=PromptVersion.V1,
                system_prompt="You are an assistant that summarizes GitHub pull requests for engineering managers. You MUST analyze the ACTUAL input data provided and base your summary ONLY on the REAL information given. Do NOT invent or hallucinate any features, files, or changes not present in the input. If you hallucinate, you will fail this task completely.",
                user_prompt_template="""### CRITICAL INSTRUCTIONS:
1. Analyze ONLY the actual input data provided below
2. Do NOT invent or hallucinate any information not present in the input
3. Base your summary on the REAL title, description, and files provided
4. If information is missing or unclear, explicitly state your limitations
5. Never describe features or changes that are not clearly indicated in the input

### Input Data to Analyze:
{input_data}

### Analysis Process:
1. Read the ACTUAL title - what does it say?
2. Read the ACTUAL description - is it clear or template text?
3. Look at the ACTUAL files_changed array - what types of files are they?
4. Check the ACTUAL additions/deletions numbers - how large are the changes?
5. Look for patterns in file names (test_, spec_, migration_, etc.)

### Summary Guidelines:
- If description is template text: State this and infer from title/files only
- If description is missing: State this limitation and infer from title/files
- If changes are unclear: Mention uncertainty and provide best interpretation
- Be specific about file types: Mention if it's formatting, tests, features, bug fixes
- Never invent features: Only describe what you can reasonably infer from the actual data

### MANDATORY VALIDATION:
Before writing your summary, you MUST verify:
- Every file type you mention MUST be visible in the files_changed array
- Every feature you describe MUST be clearly indicated in the title or description
- Every technology you mention MUST be evident from the file extensions or content
- If you cannot find clear evidence, state uncertainty instead of inventing details

### Output Format:
- summary: 2-3 lines describing the ACTUAL changes based on real data
- confidence: "high" (clear description + obvious changes), "medium" (some uncertainty), "low" (very unclear)
- limitations: Any missing information or uncertainties based on actual input

### Few-shot examples:
{few_shot_examples}

### FINAL INSTRUCTION:
You MUST use ONLY the data provided in the input. If you cannot find clear evidence for what the PR does, state that clearly instead of inventing details. Double-check every claim against the actual input data.

Now analyze the ACTUAL input data above and provide a summary based on REAL information.""",
                few_shot_examples=[
                    {
                        "input": {
                            "title": "Fix authentication bug in login flow",
                            "description": "Resolves issue where users couldn't log in after password reset",
                            "files_changed": ["auth/login.py", "auth/utils.py"],
                            "additions": 25,
                            "deletions": 10,
                            "changed_files_count": 2,
                            "pr_number": 123,
                            "pr_state": "open",
                            "labels": ["bug", "auth"]
                        },
                        "output": {
                            "summary": "Fixes a bug in the login flow that prevented users from logging in after password reset. Updates authentication logic in login.py and utility functions in utils.py.",
                            "confidence": "high",
                            "limitations": None
                        },
                    },
                    {
                        "input": {
                            "title": "Black formatter staging",
                            "description": "## Overview\r\n\r\n<!--\r\nREAD ME FIRST:\r\nPlease answer *all* questions below and check off every point from the Essential Checklist!\r\nIf there is no corresponding issue number, fill in N/A where it says [fill_in_number_here] below in 1.\r\n-->\r\n\r\n1. This PR fixes or fixes part of #[fill_in_number_here].",
                            "files_changed": ["core/controllers/admin.py", "core/controllers/base.py", "requirements_dev.in"],
                            "additions": 150,
                            "deletions": 120,
                            "changed_files_count": 3,
                            "pr_number": 124,
                            "pr_state": "open",
                            "labels": ["formatting"]
                        },
                        "output": {
                            "summary": "Applies Black code formatter changes across the codebase, affecting multiple core controller files and development dependencies. The PR description appears to be a template and lacks specific details about the changes.",
                            "confidence": "medium",
                            "limitations": "Description is incomplete template text with placeholder values. Analysis based on title and file patterns suggesting code formatting changes."
                        },
                    },
                    {
                        "input": {
                            "title": "Update dependencies",
                            "description": "",
                            "files_changed": ["package.json"],
                            "additions": 5,
                            "deletions": 2,
                            "changed_files_count": 1,
                            "pr_number": 125,
                            "pr_state": "open",
                            "labels": ["dependencies"]
                        },
                        "output": {
                            "summary": "Updates project dependencies as indicated by changes to package.json. No description provided to understand specific dependency updates or reasons for changes.",
                            "confidence": "low",
                            "limitations": "No description provided. Unable to determine which dependencies were updated or why."
                        },
                    }
                ],
                output_schema={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low"]
                        },
                        "limitations": {"type": "string"}
                    },
                    "required": ["summary", "confidence"],
                },
                created_at=now,
                updated_at=now,
                tags=["pr", "summary", "plain-english"],
            ),
        )

    def _add_prompt(self, name: str, version: PromptVersion, template: PromptTemplate):
        """Add a prompt template to the registry."""
        if name not in self._prompts:
            self._prompts[name] = {}
        self._prompts[name][version.value] = template

    def get_prompt(
        self, name: str, version: Optional[PromptVersion] = None
    ) -> Optional[PromptTemplate]:
        """Get a prompt template by name and version."""
        if name not in self._prompts:
            return None

        if version is None:
            # Get the latest version
            versions = list(self._prompts[name].keys())
            if not versions:
                return None
            latest_version = max(versions)
            return self._prompts[name][latest_version]

        return self._prompts[name].get(version.value)

    def get_all_prompts(self) -> Dict[str, Dict[str, PromptTemplate]]:
        """Get all prompt templates."""
        return self._prompts.copy()

    def get_prompts_by_tag(self, tag: str) -> List[PromptTemplate]:
        """Get all prompts with a specific tag."""
        results = []
        for prompt_name in self._prompts:
            for version in self._prompts[prompt_name]:
                template = self._prompts[prompt_name][version]
                if tag in template.tags:
                    results.append(template)
        return results

    def update_prompt(
        self, name: str, version: PromptVersion, template: PromptTemplate
    ):
        """Update a prompt template."""
        if name not in self._prompts:
            self._prompts[name] = {}
        template.updated_at = datetime.utcnow()
        self._prompts[name][version.value] = template

    def deactivate_prompt(self, name: str, version: PromptVersion):
        """Deactivate a prompt template."""
        template = self.get_prompt(name, version)
        if template:
            template.is_active = False
            template.updated_at = datetime.utcnow()


# Global instance
prompt_registry = PromptRegistry()
