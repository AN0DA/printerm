"""Centralized error handling for the printerm application."""

import logging
from typing import Any

from printerm.exceptions import PrintermError

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling class."""

    @staticmethod
    def handle_error(error: Exception, context: str = "") -> None:
        """Handle and log errors appropriately."""
        if isinstance(error, PrintermError):
            logger.error(f"{context}: {error.message}")
            if error.details:
                logger.debug(f"Error details: {error.details}")
        else:
            logger.error(f"{context}: {error}", exc_info=True)

    @staticmethod
    def wrap_error(func: Any, error_type: type[PrintermError], message: str, context: str = "") -> Any:
        """Wrap a function call and convert exceptions to PrintermError types."""

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ErrorHandler.handle_error(e, context)
                raise error_type(message, str(e)) from e

        return wrapper
