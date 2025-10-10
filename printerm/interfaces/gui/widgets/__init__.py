"""GUI widgets module for the printerm application."""

from .base import PYQT_AVAILABLE
from .dialog import TemplateDialog
from .main_window import MainWindow

__all__ = ["TemplateDialog", "MainWindow", "PYQT_AVAILABLE"]
