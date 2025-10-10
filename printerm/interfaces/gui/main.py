"""GUI interface for the printerm application with enhanced UX."""

import logging
import os
import sys

from printerm import __version__
from printerm.error_handling import ErrorHandler
from printerm.interfaces import gui as gui_module
from printerm.services import service_container
from printerm.services.interfaces import ConfigService, TemplateService, UpdateService

from .theme import ThemeManager
from .widgets import MainWindow

# Configure logging for GUI interface
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger("printerm.interfaces.gui")

# Get services from container (like other interfaces)
config_service = service_container.get(ConfigService)
template_service = service_container.get(TemplateService)
update_service = service_container.get(UpdateService)


def check_for_updates_on_startup() -> None:
    """Check for updates on application startup."""
    try:
        if config_service.get_check_for_updates() and update_service.is_new_version_available(__version__):
            logger.info("A new version is available. User will be notified through the GUI.")
            # Store update available flag for GUI to show notification
            # This will be checked by the MainWindow
    except Exception as e:
        ErrorHandler.handle_error(e, "Error checking for updates")


def main() -> None:
    """Launch the GUI application."""
    if not gui_module.PYQT_AVAILABLE:
        logger.error("PyQt6 is not available")
        print("PyQt6 is not available. Please install it with: pip install PyQt6")  # noqa: T201
        sys.exit(1)

    # Check for updates on startup
    check_for_updates_on_startup()

    try:
        from PyQt6.QtGui import QIcon
        from PyQt6.QtWidgets import QApplication

        logger.info("Launching GUI application")
        app = QApplication(sys.argv)
        app.setApplicationName("printerm")
        app.setApplicationDisplayName("printerm")

        # Set application icon
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "assets",
            "icons",
            "printer_icon_32.png",
        )
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
            logger.info(f"Set application icon: {icon_path}")
        else:
            logger.warning(f"Icon not found: {icon_path}")

        theme = ThemeManager.get_current_theme()
        ThemeManager.apply_theme_to_app(app, theme)
        window = MainWindow()
        window.show()
        logger.info("GUI application started successfully")
        sys.exit(app.exec())
    except Exception as e:
        ErrorHandler.handle_error(e, "Error launching GUI")
        logger.error(f"Failed to launch GUI: {e}")
        print(f"Failed to launch GUI: {e}")  # noqa: T201
        sys.exit(1)


if __name__ == "__main__":
    check_for_updates_on_startup()
    main()
