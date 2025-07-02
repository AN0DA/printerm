"""Tests for script registry."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from printerm.templates.scripts.base import TemplateScript
from printerm.templates.scripts.script_loader import TemplateScriptError
from printerm.templates.scripts.script_registry import ScriptRegistry


class MockScript(TemplateScript):
    """Mock script for testing."""

    @property
    def name(self) -> str:
        return "mock_script"

    @property
    def description(self) -> str:
        return "A mock script for testing"

    def generate_context(self, **kwargs: Any) -> dict[str, Any]:
        return {"mock": "data", **kwargs}

    def get_required_parameters(self) -> list[str]:
        return ["required_param"]

    def get_optional_parameters(self) -> list[str]:
        return ["optional_param"]


class ValidatingScript(TemplateScript):
    """Script with custom validation."""

    @property
    def name(self) -> str:
        return "validating_script"

    @property
    def description(self) -> str:
        return "Script with validation"

    def generate_context(self, **kwargs: Any) -> dict[str, Any]:
        return {"validated": True}

    def validate_context(self, context: dict[str, Any]) -> bool:
        return "validated" in context and context["validated"] is True


class InvalidatingScript(TemplateScript):
    """Script that always generates invalid context."""

    @property
    def name(self) -> str:
        return "invalidating_script"

    @property
    def description(self) -> str:
        return "Script that generates invalid context"

    def generate_context(self, **kwargs: Any) -> dict[str, Any]:
        return {"invalid": True}

    def validate_context(self, context: dict[str, Any]) -> bool:
        return False  # Always invalid


class TestScriptRegistry:
    """Test cases for ScriptRegistry."""

    def test_init_without_config_service(self) -> None:
        """Test initialization without config service."""
        registry = ScriptRegistry()

        assert registry.config_service is None
        assert registry.loader is not None
        assert registry._initialized is False

    def test_init_with_config_service(self) -> None:
        """Test initialization with config service."""
        mock_config = MagicMock()
        registry = ScriptRegistry(config_service=mock_config)

        assert registry.config_service == mock_config

    @patch.object(ScriptRegistry, "initialize")
    def test_lazy_initialization(self, mock_initialize: MagicMock) -> None:
        """Test that registry initializes lazily."""
        registry = ScriptRegistry()

        # Mock the loader to avoid real script discovery
        with patch.object(registry.loader, "get_script") as mock_get_script:
            mock_script = MagicMock()
            mock_get_script.return_value = mock_script

            # Should not be initialized yet
            assert not mock_initialize.called

            # These methods should trigger initialization
            registry.get_script("test")
            mock_initialize.assert_called()

    def test_initialize_success(self) -> None:
        """Test successful initialization."""
        registry = ScriptRegistry()

        with patch.object(registry.loader, "discover_scripts") as mock_discover:
            registry.initialize()

            assert registry._initialized is True
            mock_discover.assert_called_once()

    def test_initialize_error(self) -> None:
        """Test initialization with error."""
        registry = ScriptRegistry()

        with (
            patch.object(registry.loader, "discover_scripts", side_effect=Exception("Discovery failed")),
            pytest.raises(TemplateScriptError, match="Script registry initialization failed"),
        ):
            registry.initialize()

    def test_initialize_idempotent(self) -> None:
        """Test that initialize can be called multiple times safely."""
        registry = ScriptRegistry()

        with patch.object(registry.loader, "discover_scripts") as mock_discover:
            registry.initialize()
            registry.initialize()  # Second call should be ignored

            assert mock_discover.call_count == 1

    def test_get_script_success(self) -> None:
        """Test successful script retrieval."""
        registry = ScriptRegistry()

        with patch.object(registry.loader, "get_script", return_value=MockScript()) as mock_get:
            script = registry.get_script("mock_script")

            assert isinstance(script, MockScript)
            mock_get.assert_called_once_with("mock_script", config_service=None)

    def test_get_script_with_config_service(self) -> None:
        """Test script retrieval with config service."""
        mock_config = MagicMock()
        registry = ScriptRegistry(config_service=mock_config)

        with patch.object(registry.loader, "get_script", return_value=MockScript()) as mock_get:
            registry.get_script("mock_script")

            mock_get.assert_called_once_with("mock_script", config_service=mock_config)

    def test_has_script_true(self) -> None:
        """Test has_script returns True for existing script."""
        registry = ScriptRegistry()
        registry.loader._loaded_scripts = {"existing_script": MockScript}
        registry._initialized = True

        result = registry.has_script("existing_script")

        assert result is True

    def test_has_script_false(self) -> None:
        """Test has_script returns False for non-existing script."""
        registry = ScriptRegistry()
        registry.loader._loaded_scripts = {"other_script": MockScript}
        registry._initialized = True

        result = registry.has_script("missing_script")

        assert result is False

    def test_list_scripts(self) -> None:
        """Test listing available scripts."""
        registry = ScriptRegistry()

        expected_scripts = {"script1": "Description 1", "script2": "Description 2"}

        with patch.object(registry.loader, "list_available_scripts", return_value=expected_scripts):
            result = registry.list_scripts()

            assert result == expected_scripts

    def test_execute_script_success(self) -> None:
        """Test successful script execution."""
        registry = ScriptRegistry()
        mock_script = MockScript()

        with patch.object(registry, "get_script", return_value=mock_script):
            context = registry.execute_script("mock_script", required_param="value")

            assert context["mock"] == "data"
            assert context["required_param"] == "value"

    def test_execute_script_missing_required_params(self) -> None:
        """Test script execution with missing required parameters."""
        registry = ScriptRegistry()
        mock_script = MockScript()

        with (
            patch.object(registry, "get_script", return_value=mock_script),
            pytest.raises(TemplateScriptError, match="missing required parameters"),
        ):
            registry.execute_script("mock_script")  # Missing required_param

    def test_execute_script_validation_failure(self) -> None:
        """Test script execution with context validation failure."""
        registry = ScriptRegistry()
        mock_script = InvalidatingScript()

        with (
            patch.object(registry, "get_script", return_value=mock_script),
            pytest.raises(TemplateScriptError, match="generated invalid context"),
        ):
            registry.execute_script("invalidating_script")

    def test_execute_script_generation_error(self) -> None:
        """Test script execution with context generation error."""
        registry = ScriptRegistry()

        # Create a script that raises an error during context generation
        mock_script = MagicMock()
        mock_script.get_required_parameters.return_value = []
        mock_script.generate_context.side_effect = ValueError("Generation failed")

        with (
            patch.object(registry, "get_script", return_value=mock_script),
            pytest.raises(TemplateScriptError, match="Failed to execute script"),
        ):
            registry.execute_script("failing_script")

    def test_execute_script_propagates_template_script_error(self) -> None:
        """Test that TemplateScriptError is propagated without wrapping."""
        registry = ScriptRegistry()

        mock_script = MagicMock()
        mock_script.get_required_parameters.return_value = []
        mock_script.generate_context.side_effect = TemplateScriptError("Original error")

        with (
            patch.object(registry, "get_script", return_value=mock_script),
            pytest.raises(TemplateScriptError, match="Original error"),
        ):
            registry.execute_script("failing_script")

    def test_execute_script_with_validation_success(self) -> None:
        """Test script execution with successful validation."""
        registry = ScriptRegistry()
        mock_script = ValidatingScript()

        with patch.object(registry, "get_script", return_value=mock_script):
            context = registry.execute_script("validating_script")

            assert context["validated"] is True

    def test_reload_scripts(self) -> None:
        """Test script reloading."""
        registry = ScriptRegistry()

        with patch.object(registry.loader, "reload_scripts") as mock_reload:
            registry.reload_scripts()

            mock_reload.assert_called_once()

    def test_get_script_info(self) -> None:
        """Test getting script information."""
        registry = ScriptRegistry()
        mock_script = MockScript()

        with patch.object(registry, "get_script", return_value=mock_script):
            info = registry.get_script_info("mock_script")

            expected_info = {
                "name": "mock_script",
                "description": "A mock script for testing",
                "required_parameters": ["required_param"],
                "optional_parameters": ["optional_param"],
                "class_name": "MockScript",
                "module": mock_script.__class__.__module__,
            }

            assert info == expected_info

    def test_get_script_info_error(self) -> None:
        """Test get_script_info when script is not found."""
        registry = ScriptRegistry()

        with (
            patch.object(registry, "get_script", side_effect=TemplateScriptError("Script not found")),
            pytest.raises(TemplateScriptError, match="Script not found"),
        ):
            registry.get_script_info("missing_script")

    def test_execute_script_with_all_parameters(self) -> None:
        """Test script execution with both required and optional parameters."""
        registry = ScriptRegistry()
        mock_script = MockScript()

        with patch.object(registry, "get_script", return_value=mock_script):
            context = registry.execute_script(
                "mock_script",
                required_param="required_value",
                optional_param="optional_value",
                extra_param="extra_value",
            )

            assert context["required_param"] == "required_value"
            assert context["optional_param"] == "optional_value"
            assert context["extra_param"] == "extra_value"

    @patch.object(ScriptRegistry, "initialize")
    def test_methods_trigger_initialization(self, mock_initialize: MagicMock) -> None:
        """Test that various methods trigger initialization."""
        registry = ScriptRegistry()

        # Test has_script
        with patch.object(registry.loader, "_loaded_scripts", {}):
            registry.has_script("test")
            mock_initialize.assert_called()

        mock_initialize.reset_mock()

        # Test list_scripts
        with patch.object(registry.loader, "list_available_scripts", return_value={}):
            registry.list_scripts()
            mock_initialize.assert_called()

    def test_script_registry_integration(self) -> None:
        """Test full integration with script execution."""
        # This test uses real script classes to test the full flow
        registry = ScriptRegistry()

        # Mock the loader to return our test script
        registry.loader._loaded_scripts = {"mock_script": MockScript}
        registry._initialized = True

        # Execute script with proper parameters
        context = registry.execute_script("mock_script", required_param="test_value")

        assert context["mock"] == "data"
        assert context["required_param"] == "test_value"

        # Test script info retrieval
        info = registry.get_script_info("mock_script")
        assert info["name"] == "mock_script"
        assert "required_param" in info["required_parameters"]
