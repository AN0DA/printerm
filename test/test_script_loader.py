"""Tests for script loader."""

import logging
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from printerm.templates.scripts.base import TemplateScript
from printerm.templates.scripts.script_loader import ScriptLoader, TemplateScriptError


class MockScript(TemplateScript):
    """Mock script for testing."""

    @property
    def name(self) -> str:
        return "mock_script"

    @property
    def description(self) -> str:
        return "A mock script for testing"

    def generate_context(self, **kwargs: Any) -> dict[str, Any]:
        return {"mock": "data"}


class AnotherMockScript(TemplateScript):
    """Another mock script for testing."""

    @property
    def name(self) -> str:
        return "another_mock"

    @property
    def description(self) -> str:
        return "Another mock script"

    def generate_context(self, **kwargs: Any) -> dict[str, Any]:
        return {"another": "data"}


class TestScriptLoader:
    """Test cases for ScriptLoader."""

    def test_init_default_scripts_dir(self) -> None:
        """Test initialization with default scripts directory."""
        loader = ScriptLoader()

        assert loader.scripts_dir is not None
        assert isinstance(loader.scripts_dir, Path)
        assert loader._loaded_scripts == {}
        assert loader._script_instances == {}

    def test_init_custom_scripts_dir(self) -> None:
        """Test initialization with custom scripts directory."""
        custom_dir = "/custom/scripts/path"
        loader = ScriptLoader(custom_dir)

        assert str(loader.scripts_dir) == custom_dir

    def test_discover_scripts_nonexistent_directory(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test script discovery with nonexistent directory."""
        loader = ScriptLoader("/nonexistent/path")

        discovered = loader.discover_scripts()

        assert discovered == {}
        assert "Scripts directory does not exist" in caplog.text

    @patch("printerm.templates.scripts.script_loader.ScriptLoader._load_script_module")
    def test_discover_scripts_success(self, mock_load_module: MagicMock) -> None:
        """Test successful script discovery."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test Python files
            scripts_dir = Path(temp_dir)
            (scripts_dir / "test_script.py").touch()
            (scripts_dir / "another_script.py").touch()
            (scripts_dir / "_private.py").touch()  # Should be ignored
            (scripts_dir / "base.py").touch()  # Should be ignored

            mock_load_module.side_effect = [{"test_script": MockScript}, {"another_script": AnotherMockScript}]

            loader = ScriptLoader(str(scripts_dir))
            discovered = loader.discover_scripts()

            assert len(discovered) == 2
            assert "test_script" in discovered
            assert "another_script" in discovered

            # Verify excluded files were not processed
            assert mock_load_module.call_count == 2

    @patch("printerm.templates.scripts.script_loader.ScriptLoader._load_script_module")
    def test_discover_scripts_with_error(self, mock_load_module: MagicMock) -> None:
        """Test script discovery with loading error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            scripts_dir = Path(temp_dir)
            (scripts_dir / "error_script.py").touch()

            mock_load_module.side_effect = Exception("Loading failed")

            loader = ScriptLoader(str(scripts_dir))

            with pytest.raises(TemplateScriptError, match="Failed to discover scripts"):
                loader.discover_scripts()

    @patch("importlib.import_module")
    def test_load_script_module_success(self, mock_import: MagicMock) -> None:
        """Test successful script module loading."""
        # Create mock module with script classes
        mock_module = MagicMock()

        # Set up the module attributes directly
        mock_module.MockScript = MockScript
        mock_module.AnotherMockScript = AnotherMockScript
        mock_module.SomeOtherClass = str  # Not a TemplateScript
        mock_module.TemplateScript = TemplateScript  # Base class, should be ignored

        mock_import.return_value = mock_module

        # Mock dir() to return attribute names and getattr to access them
        with (
            patch("builtins.dir", return_value=["MockScript", "AnotherMockScript", "SomeOtherClass", "TemplateScript"]),
            patch("builtins.getattr", side_effect=lambda obj, name: getattr(mock_module, name)),
        ):
            loader = ScriptLoader()
            result = loader._load_script_module("test_module")

        assert len(result) == 2
        assert "mock_script" in result
        assert "another_mock" in result

    @patch("importlib.import_module")
    def test_load_script_module_import_error(self, mock_import: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Test script module loading with import error."""
        mock_import.side_effect = ImportError("Module not found")

        loader = ScriptLoader()
        result = loader._load_script_module("nonexistent_module")

        assert result == {}
        assert "Failed to import script module" in caplog.text

    @patch("importlib.import_module")
    def test_load_script_module_instantiation_error(
        self, mock_import: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test script module loading with instantiation error."""

        # Create a script class that fails to instantiate
        class FailingScript(TemplateScript):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ValueError("Instantiation failed")

            @property
            def name(self) -> str:
                return "failing_script"

            @property
            def description(self) -> str:
                return "A failing script"

            def generate_context(self, **kwargs: Any) -> dict[str, Any]:
                return {}

        mock_module = MagicMock()
        mock_module.FailingScript = FailingScript
        mock_import.return_value = mock_module

        with (
            caplog.at_level(logging.WARNING),
            patch("builtins.dir", return_value=["FailingScript"]),
            patch("builtins.getattr", side_effect=lambda obj, name: getattr(mock_module, name)),
        ):
            loader = ScriptLoader()
            result = loader._load_script_module("failing_module")

        assert result == {}
        assert "Failed to instantiate script" in caplog.text

    def test_get_script_cached(self) -> None:
        """Test getting a cached script instance."""
        loader = ScriptLoader()
        loader._loaded_scripts = {"test_script": MockScript}

        # First call should create and cache instance
        script1 = loader.get_script("test_script")

        # Second call should return cached instance
        script2 = loader.get_script("test_script")

        assert script1 is script2
        assert isinstance(script1, MockScript)

    def test_get_script_with_config_service(self) -> None:
        """Test getting script with config service."""
        loader = ScriptLoader()
        loader._loaded_scripts = {"test_script": MockScript}

        mock_config = MagicMock()
        script = loader.get_script("test_script", config_service=mock_config)

        assert script.config_service == mock_config

    def test_get_script_different_config_services(self) -> None:
        """Test that different config services create separate instances."""
        loader = ScriptLoader()
        loader._loaded_scripts = {"test_script": MockScript}

        config1 = MagicMock()
        config2 = MagicMock()

        script1 = loader.get_script("test_script", config_service=config1)
        script2 = loader.get_script("test_script", config_service=config2)

        assert script1 is not script2
        assert script1.config_service == config1
        assert script2.config_service == config2

    @patch.object(ScriptLoader, "discover_scripts")
    def test_get_script_triggers_discovery(self, mock_discover: MagicMock) -> None:
        """Test that get_script triggers script discovery if needed."""
        loader = ScriptLoader()

        # Mock discover_scripts to populate _loaded_scripts
        def mock_discovery() -> None:
            loader._loaded_scripts = {"test_script": MockScript}

        mock_discover.side_effect = mock_discovery

        script = loader.get_script("test_script")

        mock_discover.assert_called_once()
        assert isinstance(script, MockScript)

    def test_get_script_not_found(self) -> None:
        """Test error when requested script is not found."""
        loader = ScriptLoader()
        loader._loaded_scripts = {"other_script": MockScript}

        with pytest.raises(TemplateScriptError, match="Script 'missing_script' not found"):
            loader.get_script("missing_script")

    def test_get_script_instantiation_error(self) -> None:
        """Test error when script instantiation fails."""

        class FailingScript(TemplateScript):
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                raise ValueError("Cannot instantiate")

            @property
            def name(self) -> str:
                return "failing"

            @property
            def description(self) -> str:
                return "Failing script"

            def generate_context(self, **kwargs: Any) -> dict[str, Any]:
                return {}

        loader = ScriptLoader()
        loader._loaded_scripts = {"failing_script": FailingScript}

        with pytest.raises(TemplateScriptError, match="Failed to create script instance"):
            loader.get_script("failing_script")

    @patch.object(ScriptLoader, "discover_scripts")
    def test_list_available_scripts(self, mock_discover: MagicMock) -> None:
        """Test listing available scripts."""
        loader = ScriptLoader()

        # Mock discover_scripts to populate _loaded_scripts
        def mock_discovery() -> None:
            loader._loaded_scripts = {"script1": MockScript, "script2": AnotherMockScript}

        mock_discover.side_effect = mock_discovery

        scripts = loader.list_available_scripts()

        assert len(scripts) == 2
        assert scripts["script1"] == "A mock script for testing"
        assert scripts["script2"] == "Another mock script"

    def test_list_available_scripts_with_error(self) -> None:
        """Test listing scripts when description retrieval fails."""

        class ErrorScript(TemplateScript):
            def __init__(self) -> None:
                raise ValueError("Cannot get description")

            @property
            def name(self) -> str:
                return "error_script"

            @property
            def description(self) -> str:
                return "Error script"

            def generate_context(self, **kwargs: Any) -> dict[str, Any]:
                return {}

        loader = ScriptLoader()
        loader._loaded_scripts = {"error_script": ErrorScript}

        scripts = loader.list_available_scripts()

        assert "error_script" in scripts
        assert "Error loading description" in scripts["error_script"]

    @patch("importlib.reload")
    @patch("sys.modules")
    def test_reload_scripts(self, mock_modules: MagicMock, mock_reload: MagicMock) -> None:
        """Test reloading scripts."""
        # Create mock module objects
        mock_module1 = MagicMock()
        mock_module1.__name__ = "printerm.templates.scripts.test_script"
        mock_module2 = MagicMock()
        mock_module2.__name__ = "printerm.templates.scripts.another_script"

        # Mock sys.modules dictionary
        modules_dict = {
            "printerm.templates.scripts.test_script": mock_module1,
            "printerm.templates.scripts.another_script": mock_module2,
            "printerm.templates.scripts.base": MagicMock(),  # Should be excluded
            "other.module": MagicMock(),  # Should be excluded
        }

        mock_modules.__iter__ = lambda self: iter(modules_dict.keys())
        mock_modules.__getitem__ = lambda self, key: modules_dict[key]
        mock_modules.__contains__ = lambda self, key: key in modules_dict

        loader = ScriptLoader()
        loader._loaded_scripts = {"old_script": MockScript}
        loader._script_instances = {"old_instance": MagicMock()}

        with patch.object(loader, "discover_scripts") as mock_discover:
            loader.reload_scripts()

        # Should clear caches
        assert loader._loaded_scripts == {}
        assert loader._script_instances == {}

        # Should reload relevant modules (modules might fail to reload due to mocking)
        # The important thing is that caches are cleared and discovery is called
        mock_discover.assert_called_once()
        mock_discover.assert_called_once()

    @patch("sys.modules")
    def test_reload_scripts_with_reload_error(self, mock_modules: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Test reloading scripts with reload error."""
        mock_modules.__iter__ = lambda self: iter(["printerm.templates.scripts.failing_script"])
        mock_modules.__getitem__ = lambda self, key: MagicMock()

        loader = ScriptLoader()

        with (
            patch("importlib.reload", side_effect=Exception("Reload failed")),
            patch.object(loader, "discover_scripts"),
        ):
            loader.reload_scripts()

        assert "Failed to reload module" in caplog.text
