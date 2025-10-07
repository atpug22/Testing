"""
Enhanced prompt management system using centralized registry.
"""

import logging
from typing import Any, Dict, List, Optional

from app.prompts.prompt_registry import PromptTemplate, PromptVersion, prompt_registry

logger = logging.getLogger(__name__)


class PromptManager:
    """Enhanced prompt manager using centralized registry."""

    def __init__(self):
        self.registry = prompt_registry

    def get_template(
        self, name: str, version: Optional[PromptVersion] = None
    ) -> Optional[PromptTemplate]:
        """
        Get a prompt template by name and version.

        Args:
            name: Name of the prompt template
            version: Version of the prompt (defaults to latest)

        Returns:
            PromptTemplate object or None if not found
        """
        return self.registry.get_prompt(name, version)

    def get_template_dict(
        self, name: str, version: Optional[PromptVersion] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a prompt template as dictionary for backward compatibility.

        Args:
            name: Name of the prompt template
            version: Version of the prompt (defaults to latest)

        Returns:
            Template dictionary or None if not found
        """
        template = self.get_template(name, version)
        if template:
            return template.model_dump()
        return None

    def list_templates(self) -> Dict[str, str]:
        """
        List all available prompt templates.

        Returns:
            Dictionary mapping template names to descriptions
        """
        all_prompts = self.registry.get_all_prompts()
        result = {}

        for name, versions in all_prompts.items():
            # Get the latest version
            latest_version = max(versions.keys())
            template = versions[latest_version]
            result[name] = template.description

        return result

    def get_prompts_by_tag(self, tag: str) -> List[PromptTemplate]:
        """
        Get all prompts with a specific tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of PromptTemplate objects
        """
        return self.registry.get_prompts_by_tag(tag)

    def get_available_versions(self, name: str) -> List[str]:
        """
        Get all available versions for a prompt template.

        Args:
            name: Name of the prompt template

        Returns:
            List of version strings
        """
        all_prompts = self.registry.get_all_prompts()
        if name in all_prompts:
            return list(all_prompts[name].keys())
        return []

    def reload_templates(self):
        """Reload all prompt templates (no-op for registry-based system)."""
        logger.info(
            "Prompt templates are managed by registry - no reload needed")


# Global prompt manager instance
prompt_manager = PromptManager()
