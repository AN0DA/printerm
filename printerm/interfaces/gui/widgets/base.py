"""Base GUI components and imports for the printerm application."""

import logging
from typing import Any

from printerm.interfaces.gui.settings import GuiSettings
from printerm.services import service_container
from printerm.services.interfaces import ConfigService, PrinterService, TemplateService, UpdateService

logger = logging.getLogger(__name__)

# Get services from container (like other interfaces)
config_service = service_container.get(ConfigService)
template_service = service_container.get(TemplateService)
printer_service = service_container.get(PrinterService)
update_service = service_container.get(UpdateService)
gui_settings = GuiSettings(config_service)

try:
    import PyQt6  # noqa: F401

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


if not PYQT_AVAILABLE:
    # Dummy classes for when PyQt6 is not available
    class MainWindow:
        def __init__(self) -> None:
            raise ImportError("PyQt6 is not available")

    class TemplateDialog:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError("PyQt6 is not available")
