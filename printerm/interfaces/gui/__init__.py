"""GUI module for the printerm application."""

from printerm.services import service_container

from .main import logger, main
from .settings import GuiSettings
from .theme import ThemeManager
from .widgets import PYQT_AVAILABLE, MainWindow, TemplateDialog
from .widgets.base import config_service, gui_settings, template_service

__all__ = [
    "main",
    "GuiSettings",
    "ThemeManager",
    "TemplateDialog",
    "MainWindow",
    "PYQT_AVAILABLE",
    "service_container",
    "logger",
    "config_service",
    "template_service",
    "gui_settings",
]

# Conditionally import PyQt6 classes if available
try:
    from PyQt6.QtWidgets import QApplication, QDialog  # noqa: F401

    __all__.extend(["QApplication", "QDialog"])
except ImportError:
    # PyQt6 not available, don't add to __all__
    pass
