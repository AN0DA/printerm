"""Tests for GUI interface.

All test classes in this file are marked with @pytest.mark.gui to exclude them
from CI/CD pipelines where GUI dependencies are not available.
Use 'pytest -m gui' to run only GUI tests or 'pytest -m "not gui"' to exclude them.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock PyQt6 since it might not be available in test environment
with patch.dict(
    "sys.modules",
    {
        "PyQt6": MagicMock(),
        "PyQt6.QtCore": MagicMock(),
        "PyQt6.QtGui": MagicMock(),
        "PyQt6.QtWidgets": MagicMock(),
    },
):
    from printerm.interfaces.gui import (
        GuiSettings,
        TemplateDialog,
        ThemeManager,
    )


@pytest.mark.gui
class TestGuiSettings:
    """Test cases for GuiSettings class."""

    def test_gui_settings_init(self) -> None:
        """Test GuiSettings initialization."""
        mock_config = Mock()
        settings = GuiSettings(mock_config)

        assert settings.config_service == mock_config

    def test_add_recent_template(self) -> None:
        """Test adding a recent template."""
        mock_config = Mock()
        mock_config.get_gui_recent_templates.return_value = ["template1", "template2"]

        settings = GuiSettings(mock_config)
        settings.add_recent_template("new_template")

        mock_config.set_gui_recent_templates.assert_called_once()
        # Should call with new template at the beginning
        args = mock_config.set_gui_recent_templates.call_args[0][0]
        assert args[0] == "new_template"

    def test_add_recent_template_existing(self) -> None:
        """Test adding an existing template moves it to front."""
        mock_config = Mock()
        mock_config.get_gui_recent_templates.return_value = ["template1", "template2", "template3"]

        settings = GuiSettings(mock_config)
        settings.add_recent_template("template2")

        # Should move template2 to front and remove from middle
        args = mock_config.set_gui_recent_templates.call_args[0][0]
        assert args[0] == "template2"
        assert args.count("template2") == 1  # Should only appear once

    def test_add_recent_template_limit(self) -> None:
        """Test that recent templates are limited to 5."""
        mock_config = Mock()
        mock_config.get_gui_recent_templates.return_value = ["t1", "t2", "t3", "t4", "t5"]

        settings = GuiSettings(mock_config)
        settings.add_recent_template("new_template")

        args = mock_config.set_gui_recent_templates.call_args[0][0]
        assert len(args) == 5
        assert args[0] == "new_template"
        assert "t5" not in args  # Should be removed

    def test_add_recent_template_error(self) -> None:
        """Test handling error when adding recent template."""
        mock_config = Mock()
        mock_config.get_gui_recent_templates.side_effect = Exception("Config error")

        settings = GuiSettings(mock_config)

        # Should not raise exception
        settings.add_recent_template("template")

    def test_get_recent_templates_success(self) -> None:
        """Test getting recent templates successfully."""
        mock_config = Mock()
        expected = ["template1", "template2"]
        mock_config.get_gui_recent_templates.return_value = expected

        settings = GuiSettings(mock_config)
        result = settings.get_recent_templates()

        assert result == expected

    def test_get_recent_templates_error(self) -> None:
        """Test handling error when getting recent templates."""
        mock_config = Mock()
        mock_config.get_gui_recent_templates.side_effect = Exception("Config error")

        settings = GuiSettings(mock_config)
        result = settings.get_recent_templates()

        assert result == []  # Should return empty list on error


@pytest.mark.gui
class TestThemeManager:
    """Test cases for ThemeManager class."""

    def test_get_current_theme_default(self) -> None:
        """Test getting current theme with default behavior."""
        theme = ThemeManager.get_current_theme()

        # Should return a valid theme string
        assert isinstance(theme, str)
        assert theme in ["light", "dark", "auto"] or theme  # Should be non-empty


@pytest.mark.gui
class TestGUIInterface:
    """Test cases for GUI interface."""

    def test_main_function_pyqt_available(self) -> None:
        """Test main function when PyQt6 is available."""
        pytest.skip("This test causes freezing due to QApplication mock issues")

    def test_main_function_pyqt_not_available(self) -> None:
        """Test main function when PyQt6 is not available."""
        pytest.skip("This test causes freezing due to QApplication mock issues")

    @patch("printerm.interfaces.gui.service_container")
    def test_template_dialog_init(self, mock_container: MagicMock) -> None:
        """Test TemplateDialog initialization."""
        mock_template_service = Mock()
        mock_template_service.get_template.return_value = {
            "name": "Test Template",
            "description": "A test template",
            "variables": [],
        }

        mock_container.get.return_value = mock_template_service

        with patch("printerm.interfaces.gui.QDialog.__init__", return_value=None):
            dialog = TemplateDialog("test_template")

            # Should have template_name attribute
            assert hasattr(dialog, "template_name")

    def test_main_window_creation(self) -> None:
        """Test MainWindow can be created."""
        # Skip this test since MainWindow requires complex PyQt setup
        pytest.skip("MainWindow creation test requires full PyQt environment")

    def test_gui_module_imports(self) -> None:
        """Test that GUI module handles imports correctly."""
        # Test that PYQT_AVAILABLE is defined
        from printerm.interfaces import gui

        assert hasattr(gui, "PYQT_AVAILABLE")

    @patch("printerm.interfaces.gui.service_container")
    def test_gui_services_initialization(self, mock_container: MagicMock) -> None:
        """Test that GUI services are initialized correctly."""
        from printerm.interfaces import gui

        # Should have service instances
        assert hasattr(gui, "config_service")
        assert hasattr(gui, "template_service")
        assert hasattr(gui, "gui_settings")

    def test_theme_manager_static_methods(self) -> None:
        """Test ThemeManager static methods."""
        # get_current_theme should be callable
        assert callable(ThemeManager.get_current_theme)

    @patch("printerm.interfaces.gui.service_container")
    def test_gui_settings_integration(self, mock_container: MagicMock) -> None:
        """Test GuiSettings integration with services."""
        mock_config = Mock()
        mock_container.get.return_value = mock_config

        from printerm.interfaces import gui
        from printerm.interfaces.gui import GuiSettings

        # gui_settings should be created with config_service
        assert hasattr(gui, "gui_settings")
        assert isinstance(gui.gui_settings, GuiSettings)

    def test_gui_error_handling(self) -> None:
        """Test that GUI handles errors gracefully."""
        # Test that the module can be imported even with mocked PyQt6
        from printerm.interfaces import gui

        # Should have fallback classes when PyQt6 is not available
        assert hasattr(gui, "MainWindow")
        assert hasattr(gui, "TemplateDialog")

    @patch("printerm.interfaces.gui.PYQT_AVAILABLE", False)
    def test_gui_fallback_classes(self) -> None:
        """Test fallback classes when PyQt6 is not available."""
        # When PyQt6 is not available, should still have basic classes
        from printerm.interfaces import gui

        # Should have dummy classes
        assert hasattr(gui, "MainWindow")
        assert hasattr(gui, "TemplateDialog")

    def test_gui_logging_setup(self) -> None:
        """Test that GUI logging is set up correctly."""
        from printerm.interfaces import gui

        # Should have logger
        assert hasattr(gui, "logger")
        assert gui.logger.name == "printerm.interfaces.gui"

    @patch("platform.system")
    def test_theme_manager_platform_detection(self, mock_platform: MagicMock) -> None:
        """Test ThemeManager platform detection."""
        mock_platform.return_value = "Darwin"  # macOS

        theme = ThemeManager.get_current_theme()

        # Should handle platform-specific detection
        assert isinstance(theme, str)
        mock_platform.assert_called_once()
