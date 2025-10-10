"""Theme management for GUI interface."""

import contextlib
import logging
import platform
import subprocess  # nosec B404 # Used only for safe system theme detection on macOS
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class ThemeManager:
    """Manage application themes and styling."""

    @staticmethod
    def get_current_theme() -> str:
        """Detect current system theme automatically."""
        # Always try to detect system theme
        try:
            system = platform.system()

            if system == "Darwin":  # macOS
                with contextlib.suppress(Exception):
                    # Use full path to defaults command for security  # nosec B607
                    result = subprocess.run(
                        ["/usr/bin/defaults", "read", "-g", "AppleInterfaceStyle"],
                        capture_output=True,
                        text=True,
                        timeout=2,
                        check=False,
                    )  # nosec B603
                    if result.returncode == 0 and "Dark" in result.stdout:
                        return "dark"
                    else:
                        return "light"

            elif system == "Windows":
                with contextlib.suppress(Exception):
                    import winreg

                    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)  # type: ignore[attr-defined]
                    key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")  # type: ignore[attr-defined]
                    value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")  # type: ignore[attr-defined]
                    winreg.CloseKey(key)  # type: ignore[attr-defined]
                    return "light" if value else "dark"

            # Try PyQt6 system detection as fallback
            with contextlib.suppress(Exception):
                try:
                    from PyQt6.QtWidgets import QApplication

                    app = QApplication.instance()
                    if app:
                        # Try to access the palette to determine theme
                        palette = app.palette()  # type: ignore[attr-defined]
                        bg_color = palette.color(palette.ColorRole.Window)
                        # Simple heuristic: if background is light, assume light theme
                        luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()) / 255
                        return "light" if luminance > 0.5 else "dark"
                except ImportError:
                    pass

        except Exception as e:
            logger.debug(f"Theme detection failed: {e}")

        return "light"  # Safe default fallback

    @staticmethod
    def get_theme_styles(theme: str) -> dict[str, str]:
        """Get CSS styles for the specified theme."""
        if theme == "dark":
            return {
                "background": "#2b2b2b",
                "surface": "#3c3c3c",
                "primary": "#4a9eff",
                "primary_dark": "#357abd",
                "text": "#ffffff",
                "text_secondary": "#b0b0b0",
                "border": "#555555",
                "success": "#4caf50",
                "success_dark": "#43a047",
                "warning": "#ff9800",
                "error": "#f44336",
                "card_background": "#404040",
                "card_hover": "#484848",
                "input_background": "#505050",
                "preview_background": "#2a2a2a",
            }
        else:  # light theme
            return {
                "background": "#f5f5f5",
                "surface": "#ffffff",
                "primary": "#2196f3",
                "primary_dark": "#1976d2",
                "text": "#212121",
                "text_secondary": "#757575",
                "border": "#e0e0e0",
                "success": "#4caf50",
                "success_dark": "#388e3c",
                "warning": "#ff9800",
                "error": "#f44336",
                "card_background": "#ffffff",
                "card_hover": "#f8f9fa",
                "input_background": "#ffffff",
                "preview_background": "#fafafa",
            }

    @staticmethod
    def get_app_stylesheet(theme: str) -> str:
        """Get the complete stylesheet for the application."""
        styles = ThemeManager.get_theme_styles(theme)

        return f"""
        QApplication {{
            background-color: {styles["background"]};
            color: {styles["text"]};
        }}

        QWidget {{
            background-color: {styles["background"]};
            color: {styles["text"]};
        }}

        QGroupBox {{
            font-weight: bold;
            border: 2px solid {styles["border"]};
            border-radius: 8px;
            margin-top: 8px;
            padding-top: 8px;
            background-color: {styles["surface"]};
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            background-color: {styles["surface"]};
        }}

        QPushButton {{
            background-color: {styles["primary"]};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: 500;
            min-width: 80px;
        }}

        QPushButton:hover {{
            background-color: {styles["primary_dark"]};
        }}

        QPushButton:pressed {{
            background-color: {styles["primary_dark"]};
            padding: 9px 15px 7px 17px;
        }}

        QLineEdit, QTextEdit {{
            background-color: {styles["input_background"]};
            border: 1px solid {styles["border"]};
            border-radius: 4px;
            padding: 6px;
            color: {styles["text"]};
        }}

        QLineEdit:focus, QTextEdit:focus {{
            border-color: {styles["primary"]};
        }}

        QTabWidget::pane {{
            border: 1px solid {styles["border"]};
            background-color: {styles["surface"]};
            border-radius: 4px;
        }}

        QTabBar::tab {{
            background-color: {styles["background"]};
            color: {styles["text"]};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}

        QTabBar::tab:selected {{
            background-color: {styles["surface"]};
            border-bottom: 2px solid {styles["primary"]};
        }}

        QTabBar::tab:hover {{
            background-color: {styles["card_hover"]};
        }}
        """

    @staticmethod
    def apply_theme_to_app(app: "QApplication", theme: str) -> None:
        """Apply theme styles to the entire application."""
        app.setStyleSheet(ThemeManager.get_app_stylesheet(theme))
