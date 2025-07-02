"""Base template script interface."""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class TemplateScript(ABC):
    """Abstract base class for template scripts.

    Template scripts are responsible for generating context variables
    that can be used in template rendering.
    """

    def __init__(self, config_service: Any = None) -> None:
        """Initialize the template script.

        Args:
            config_service: Optional configuration service for accessing settings
        """
        self.config_service = config_service
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of this script."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a human-readable description of what this script does."""
        pass

    @abstractmethod
    def generate_context(self, **kwargs: Any) -> dict[str, Any]:
        """Generate context variables for template rendering.

        Args:
            **kwargs: Optional parameters that can be passed to the script

        Returns:
            Dictionary of context variables to be used in template rendering

        Raises:
            TemplateScriptError: If context generation fails
        """
        pass

    def validate_context(self, context: dict[str, Any]) -> bool:
        """Validate the generated context.

        Override this method to add custom validation logic.

        Args:
            context: The context dictionary to validate

        Returns:
            True if context is valid, False otherwise
        """
        return isinstance(context, dict)

    def get_required_parameters(self) -> list[str]:
        """Return list of required parameter names for this script.

        Override this method if your script requires specific parameters.

        Returns:
            List of required parameter names
        """
        return []

    def get_optional_parameters(self) -> list[str]:
        """Return list of optional parameter names for this script.

        Override this method to document optional parameters.

        Returns:
            List of optional parameter names
        """
        return []

    def __str__(self) -> str:
        """String representation of the script."""
        return f"{self.name}: {self.description}"

    def __repr__(self) -> str:
        """Developer representation of the script."""
        return f"TemplateScript(name='{self.name}', description='{self.description}')"
