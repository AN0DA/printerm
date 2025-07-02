"""Tests for error handling module."""

import logging

import pytest

from printerm.error_handling import ErrorHandler
from printerm.exceptions import ConfigurationError


class TestErrorHandler:
    """Test cases for ErrorHandler."""

    def test_handle_error_with_printerm_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test handling of PrintermError instances."""
        error = ConfigurationError("Config error", "Details about the error")

        with caplog.at_level(logging.ERROR):
            ErrorHandler.handle_error(error, "Test context")

        assert "Test context: Config error" in caplog.text

    def test_handle_error_with_printerm_error_no_details(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test handling of PrintermError without details."""
        error = ConfigurationError("Config error")

        with caplog.at_level(logging.ERROR):
            ErrorHandler.handle_error(error, "Test context")

        assert "Test context: Config error" in caplog.text

    def test_handle_error_with_printerm_error_and_details(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test handling of PrintermError with details."""
        error = ConfigurationError("Config error", "Detailed error information")

        with caplog.at_level(logging.DEBUG):
            ErrorHandler.handle_error(error, "Test context")

        assert "Test context: Config error" in caplog.text
        assert "Error details: Detailed error information" in caplog.text

    def test_handle_error_with_generic_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test handling of generic exceptions."""
        error = ValueError("Generic error")

        with caplog.at_level(logging.ERROR):
            ErrorHandler.handle_error(error, "Test context")

        assert "Test context: Generic error" in caplog.text

    def test_handle_error_without_context(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test handling error without context."""
        error = ValueError("Generic error")

        with caplog.at_level(logging.ERROR):
            ErrorHandler.handle_error(error)

        assert ": Generic error" in caplog.text

    def test_wrap_error_successful_execution(self) -> None:
        """Test wrap_error with successful function execution."""

        def test_func(x: int, y: int) -> int:
            return x + y

        wrapped_func = ErrorHandler.wrap_error(test_func, ConfigurationError, "Addition failed", "Math operation")

        result = wrapped_func(2, 3)
        assert result == 5

    def test_wrap_error_with_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test wrap_error when function raises exception."""

        def test_func() -> None:
            raise ValueError("Original error")

        wrapped_func = ErrorHandler.wrap_error(test_func, ConfigurationError, "Wrapped error message", "Test operation")

        with pytest.raises(ConfigurationError, match="Wrapped error message"):
            wrapped_func()

        # Check that error was logged
        assert "Test operation: Original error" in caplog.text

    def test_wrap_error_preserves_function_signature(self) -> None:
        """Test that wrap_error preserves function arguments."""

        def test_func(a: int, b: str, c: bool = False) -> str:
            return f"{a}-{b}-{c}"

        wrapped_func = ErrorHandler.wrap_error(test_func, ConfigurationError, "Function failed")

        result = wrapped_func(42, "test", c=True)
        assert result == "42-test-True"

    def test_wrap_error_with_kwargs(self) -> None:
        """Test wrap_error with keyword arguments."""

        def test_func(**kwargs: int) -> int:
            return sum(kwargs.values())

        wrapped_func = ErrorHandler.wrap_error(test_func, ConfigurationError, "Sum failed")

        result = wrapped_func(a=1, b=2, c=3)
        assert result == 6

    def test_wrap_error_exception_chaining(self) -> None:
        """Test that wrap_error properly chains exceptions."""

        def test_func() -> None:
            raise ValueError("Original error")

        wrapped_func = ErrorHandler.wrap_error(test_func, ConfigurationError, "Wrapped error")

        with pytest.raises(ConfigurationError) as exc_info:
            wrapped_func()

        assert exc_info.value.message == "Wrapped error"
        assert exc_info.value.details == "Original error"
        assert isinstance(exc_info.value.__cause__, ValueError)

    def test_wrap_error_no_context(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test wrap_error without context."""

        def test_func() -> None:
            raise ValueError("Original error")

        wrapped_func = ErrorHandler.wrap_error(test_func, ConfigurationError, "Wrapped error")

        with pytest.raises(ConfigurationError):
            wrapped_func()

        # Should still log the error even without explicit context
        assert ": Original error" in caplog.text
