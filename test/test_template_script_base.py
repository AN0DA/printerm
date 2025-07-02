"""Tests for template script base class."""

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from printerm.templates.scripts.base import TemplateScript


class ConcreteScript(TemplateScript):
    """Concrete implementation for testing."""

    @property
    def name(self) -> str:
        return "test_script"

    @property
    def description(self) -> str:
        return "A test script for unit testing"

    def generate_context(self, **kwargs: Any) -> dict[str, Any]:
        return {"test_key": "test_value", **kwargs}


class InvalidScript(TemplateScript):
    """Script that generates invalid context."""

    @property
    def name(self) -> str:
        return "invalid_script"

    @property
    def description(self) -> str:
        return "Script that generates invalid context"

    def generate_context(self, **kwargs: Any) -> dict[str, Any]:
        return {"test": "value"}

    def validate_context(self, context: dict[str, Any]) -> bool:
        return False  # Always invalid


class ParameterScript(TemplateScript):
    """Script with parameter requirements."""

    @property
    def name(self) -> str:
        return "param_script"

    @property
    def description(self) -> str:
        return "Script with parameter requirements"

    def generate_context(self, **kwargs: Any) -> dict[str, Any]:
        return kwargs

    def get_required_parameters(self) -> list[str]:
        return ["required_param"]

    def get_optional_parameters(self) -> list[str]:
        return ["optional_param"]


class TestTemplateScript:
    """Test cases for TemplateScript base class."""

    def test_init_without_config_service(self) -> None:
        """Test initialization without config service."""
        script = ConcreteScript()

        assert script.config_service is None
        assert script.logger is not None
        assert isinstance(script.logger, logging.Logger)

    def test_init_with_config_service(self) -> None:
        """Test initialization with config service."""
        mock_config = MagicMock()
        script = ConcreteScript(config_service=mock_config)

        assert script.config_service == mock_config

    def test_logger_name(self) -> None:
        """Test that logger has correct name."""
        script = ConcreteScript()

        expected_name = f"{ConcreteScript.__module__}.{ConcreteScript.__name__}"
        assert script.logger.name == expected_name

    def test_abstract_properties_implemented(self) -> None:
        """Test that concrete implementation provides required properties."""
        script = ConcreteScript()

        assert script.name == "test_script"
        assert script.description == "A test script for unit testing"

    def test_generate_context_basic(self) -> None:
        """Test basic context generation."""
        script = ConcreteScript()

        context = script.generate_context()

        assert context["test_key"] == "test_value"

    def test_generate_context_with_kwargs(self) -> None:
        """Test context generation with keyword arguments."""
        script = ConcreteScript()

        context = script.generate_context(custom_param="custom_value")

        assert context["test_key"] == "test_value"
        assert context["custom_param"] == "custom_value"

    def test_validate_context_default_valid(self) -> None:
        """Test default context validation with valid dict."""
        script = ConcreteScript()

        result = script.validate_context({"key": "value"})

        assert result is True

    def test_validate_context_default_invalid(self) -> None:
        """Test default context validation with invalid input."""
        script = ConcreteScript()

        # Type ignore since we're testing runtime behavior
        result = script.validate_context("not a dict")  # type: ignore

        assert result is False

    def test_validate_context_custom_implementation(self) -> None:
        """Test custom context validation implementation."""
        script = InvalidScript()

        result = script.validate_context({"test": "value"})

        assert result is False

    def test_get_required_parameters_default(self) -> None:
        """Test default required parameters (empty)."""
        script = ConcreteScript()

        params = script.get_required_parameters()

        assert params == []

    def test_get_optional_parameters_default(self) -> None:
        """Test default optional parameters (empty)."""
        script = ConcreteScript()

        params = script.get_optional_parameters()

        assert params == []

    def test_get_required_parameters_custom(self) -> None:
        """Test custom required parameters."""
        script = ParameterScript()

        params = script.get_required_parameters()

        assert params == ["required_param"]

    def test_get_optional_parameters_custom(self) -> None:
        """Test custom optional parameters."""
        script = ParameterScript()

        params = script.get_optional_parameters()

        assert params == ["optional_param"]

    def test_str_representation(self) -> None:
        """Test string representation of script."""
        script = ConcreteScript()

        str_repr = str(script)

        assert str_repr == "test_script: A test script for unit testing"

    def test_repr_representation(self) -> None:
        """Test developer representation of script."""
        script = ConcreteScript()

        repr_str = repr(script)

        expected = "TemplateScript(name='test_script', description='A test script for unit testing')"
        assert repr_str == expected

    def test_inheritance_structure(self) -> None:
        """Test that ConcreteScript is properly inheriting from TemplateScript."""
        script = ConcreteScript()

        assert isinstance(script, TemplateScript)
        assert hasattr(script, "name")
        assert hasattr(script, "description")
        assert hasattr(script, "generate_context")
        assert hasattr(script, "validate_context")

    def test_cannot_instantiate_abstract_base(self) -> None:
        """Test that abstract base class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TemplateScript()

    def test_config_service_passed_correctly(self) -> None:
        """Test that config service is stored correctly."""
        mock_config = MagicMock()
        mock_config.get_some_setting.return_value = "test_value"

        script = ConcreteScript(config_service=mock_config)

        assert script.config_service == mock_config
        # Script can use config service if needed
        if script.config_service:
            result = script.config_service.get_some_setting()
            assert result == "test_value"

    def test_logger_configuration(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that logger works correctly."""
        script = ConcreteScript()

        with caplog.at_level(logging.INFO):
            script.logger.info("Test log message")

        assert "Test log message" in caplog.text

    def test_parameter_script_functionality(self) -> None:
        """Test parameter script generates context from kwargs."""
        script = ParameterScript()

        context = script.generate_context(
            required_param="required_value", optional_param="optional_value", extra_param="extra_value"
        )

        assert context["required_param"] == "required_value"
        assert context["optional_param"] == "optional_value"
        assert context["extra_param"] == "extra_value"
