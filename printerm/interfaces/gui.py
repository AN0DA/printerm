"""GUI interface for the printerm application with enhanced UX."""

import contextlib
import logging
import subprocess  # nosec B404 # Used only for safe system theme detection on macOS
import sys
from typing import Any

try:
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QDialog,
        QFormLayout,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from printerm.error_handling import ErrorHandler
from printerm.exceptions import ConfigurationError, PrintermError
from printerm.services import service_container
from printerm.services.interfaces import ConfigService, PrinterService, TemplateService
from printerm.services.template_service import compute_agenda_variables

# Configure logging for GUI interface
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)

# Get services from container (like other interfaces)
config_service = service_container.get(ConfigService)
template_service = service_container.get(TemplateService)


class GuiSettings:
    """Handle GUI-specific settings like recent templates and window preferences using ConfigService."""

    def __init__(self, config_service: ConfigService) -> None:
        self.config_service = config_service

    def add_recent_template(self, template_name: str) -> None:
        """Add template to recent list."""
        try:
            recent = self.get_recent_templates()
            if template_name in recent:
                recent.remove(template_name)
            recent.insert(0, template_name)
            # Keep only last 5 recent templates
            recent = recent[:5]
            self.config_service.set_gui_recent_templates(recent)
        except Exception as e:
            logger.warning(f"Failed to save recent template: {e}")

    def get_recent_templates(self) -> list[str]:
        """Get list of recent templates."""
        try:
            return self.config_service.get_gui_recent_templates()
        except Exception as e:
            logger.warning(f"Failed to load recent templates: {e}")
            return []


gui_settings = GuiSettings(config_service)


class ThemeManager:
    """Manage application themes and styling."""

    @staticmethod
    def get_current_theme() -> str:
        """Detect current system theme automatically."""
        # Always try to detect system theme
        try:
            # Try to detect system theme using environment variables (fallback)
            import platform

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
                if PYQT_AVAILABLE:
                    app = QApplication.instance()
                    if app:
                        # Try to access the palette to determine theme
                        palette = app.palette()  # type: ignore[attr-defined]
                        bg_color = palette.color(palette.ColorRole.Window)
                        # Simple heuristic: if background is light, assume light theme
                        luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()) / 255
                        return "light" if luminance > 0.5 else "dark"

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
    def apply_theme_to_app(app: QApplication, theme: str) -> None:
        """Apply theme styles to the entire application."""
        styles = ThemeManager.get_theme_styles(theme)

        app_style = f"""
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

        app.setStyleSheet(app_style)


# ...existing code...


if PYQT_AVAILABLE:

    class TemplatePreview(QWidget):
        """Widget to show a preview of how the template will look when printed."""

        def __init__(self, parent: QWidget | None = None) -> None:
            super().__init__(parent)
            self.current_theme = ThemeManager.get_current_theme()
            self.init_ui()

        def init_ui(self) -> None:
            layout = QVBoxLayout()
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(5)

            # Preview label with bigger font
            preview_label = QLabel("Preview:")
            preview_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # Increased from 10
            layout.addWidget(preview_label)

            # Preview area with scroll - full height
            self.preview_area = QScrollArea()
            self.preview_area.setWidgetResizable(True)
            self.preview_area.setMinimumHeight(200)  # Increased minimum height
            # Remove maximum height to allow full expansion

            # Preview content widget with bigger font
            self.preview_content = QLabel()
            self.preview_content.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            self.preview_content.setWordWrap(True)
            self.preview_content.setFont(QFont("Courier New", 10))  # Increased from 9

            # Apply theme-aware styling
            self.apply_preview_theme()

            self.preview_area.setWidget(self.preview_content)
            layout.addWidget(self.preview_area)

            self.setLayout(layout)

        def apply_preview_theme(self) -> None:
            """Apply theme-specific styling to preview area."""
            styles = ThemeManager.get_theme_styles(self.current_theme)
            self.preview_content.setStyleSheet(f"""
                QLabel {{
                    background-color: {styles["preview_background"]};
                    border: 1px solid {styles["border"]};
                    padding: 8px;
                    color: {styles["text"]};
                    border-radius: 4px;
                }}
            """)

        def update_preview(self, template_name: str, context: dict[str, Any]) -> None:
            """Update the preview with rendered template."""
            try:
                rendered_segments = template_service.render_template(template_name, context)
                preview_text = ""

                for segment in rendered_segments:
                    text = segment["text"]
                    styles = segment.get("styles", {})

                    # Add some basic formatting indicators
                    if styles.get("bold"):
                        text = f"**{text}**"
                    if styles.get("align") == "center":
                        lines = text.split("\n")
                        centered_lines = []
                        for line in lines:
                            if line.strip():
                                centered_lines.append(line.center(42))  # Reduced width
                            else:
                                centered_lines.append(line)
                        text = "\n".join(centered_lines)

                    preview_text += text

                self.preview_content.setText(preview_text or "Preview will appear here...")
            except Exception as e:
                self.preview_content.setText(f"Preview error: {str(e)}")

        def update_theme(self, theme: str) -> None:
            """Update the theme of the preview widget."""
            self.current_theme = theme
            self.apply_preview_theme()

    class TemplateDialog(QDialog):
        """Enhanced template dialog with preview and better UX."""

        def __init__(self, template_name: str, parent: QWidget | None = None):
            super().__init__(parent)
            self.template_name = template_name
            self.template_service = template_service
            self.inputs: dict[str, Any] = {}
            self.preview_timer = QTimer()
            self.preview_timer.setSingleShot(True)
            self.preview_timer.timeout.connect(self.update_preview)
            self.current_theme = ThemeManager.get_current_theme()

            self.setWindowTitle(f"Print {template_name.capitalize()}")
            self.setMinimumSize(700, 450)  # Reduced from 800x600
            self.setMaximumSize(900, 600)  # Add max size to prevent excessive space
            logger.debug(f"Initializing enhanced template dialog for: {template_name}")
            self.init_ui()

        def init_ui(self) -> None:
            try:
                template = self.template_service.get_template(self.template_name)

                # Main layout with reduced margins
                main_layout = QHBoxLayout()  # Changed to horizontal for side-by-side layout
                main_layout.setContentsMargins(10, 10, 10, 10)
                main_layout.setSpacing(12)

                # Left side - Input form with title
                input_widget = QWidget()
                input_layout = QVBoxLayout()
                input_layout.setContentsMargins(5, 5, 5, 5)
                input_layout.setSpacing(8)

                # Title in the input column (more visual appeal)
                title_frame = QFrame()
                title_frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {"#f5f5f5" if self.current_theme == "light" else "#3d3d3d"};
                        border-radius: 8px;
                        padding: 8px;
                        margin-bottom: 4px;
                    }}
                """)
                title_layout = QVBoxLayout()
                title_layout.setContentsMargins(8, 8, 8, 8)
                title_layout.setSpacing(2)

                title_label = QLabel(f"📄 {self.template_name.capitalize()}")
                title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))  # Increased from 14
                title_layout.addWidget(title_label)

                # Description if available (more compact)
                if template.get("description"):
                    desc_label = QLabel(template["description"])
                    desc_label.setFont(QFont("Arial", 11))  # Increased from 9
                    desc_label.setStyleSheet("color: #666; margin-top: 2px;")
                    desc_label.setWordWrap(True)
                    title_layout.addWidget(desc_label)

                title_frame.setLayout(title_layout)
                input_layout.addWidget(title_frame)

                # Input form
                variables = template.get("variables", [])
                if variables:
                    form_group = QGroupBox("Variables")
                    form_layout = QFormLayout()
                    form_layout.setVerticalSpacing(6)
                    form_layout.setHorizontalSpacing(8)

                    for var in variables:
                        input_field = QTextEdit() if var.get("markdown", False) else QLineEdit()

                        if isinstance(input_field, QTextEdit):
                            input_field.setMaximumHeight(80)  # Reduced from 100
                            input_field.textChanged.connect(self.on_input_changed)
                        else:
                            input_field.textChanged.connect(self.on_input_changed)

                        # Compact placeholder text
                        placeholder = var.get("description", var["name"])
                        if var.get("required", False):
                            placeholder += " *"

                        input_field.setPlaceholderText(placeholder)

                        # Shorter labels
                        label_text = var["description"]
                        if len(label_text) > 20:
                            label_text = label_text[:17] + "..."
                        form_layout.addRow(f"{label_text}:", input_field)
                        self.inputs[var["name"]] = input_field

                    form_group.setLayout(form_layout)
                    input_layout.addWidget(form_group)
                else:
                    no_vars_label = QLabel("✨ No variables needed")
                    no_vars_label.setStyleSheet("color: #666; font-style: italic; text-align: center;")
                    input_layout.addWidget(no_vars_label)

                # Compact button layout at the bottom of input column
                button_layout = QHBoxLayout()
                button_layout.setSpacing(8)

                # Validate button (smaller)
                validate_button = QPushButton("✓ Validate")
                validate_button.clicked.connect(self.validate_template)
                validate_button.setMaximumWidth(100)
                button_layout.addWidget(validate_button)

                button_layout.addStretch()

                # Print button (styled)
                cancel_button = QPushButton("Cancel")
                cancel_button.setMaximumWidth(80)
                cancel_button.clicked.connect(self.reject)
                button_layout.addWidget(cancel_button)

                print_button = QPushButton("🖨️ Print")
                print_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {"#4caf50" if self.current_theme == "light" else "#43a047"};
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        font-size: 13px;
                        font-weight: bold;
                        border-radius: 6px;
                        min-width: 100px;
                    }}
                    QPushButton:hover {{
                        background-color: {"#45a049" if self.current_theme == "light" else "#388e3c"};
                    }}
                    QPushButton:pressed {{
                        background-color: {"#3d8b40" if self.current_theme == "light" else "#2e7d32"};
                    }}
                """)
                print_button.clicked.connect(self.print_template)
                button_layout.addWidget(print_button)

                input_layout.addLayout(button_layout)
                input_widget.setLayout(input_layout)

                # Right side - Full-height preview
                self.preview_widget = TemplatePreview()
                self.preview_widget.setMinimumWidth(350)  # Ensure preview gets adequate space

                # Add widgets to main layout
                main_layout.addWidget(input_widget, 1)  # Input gets 1 part
                main_layout.addWidget(self.preview_widget, 1)  # Preview gets 1 part (50/50 split)

                self.setLayout(main_layout)

                # Initial preview update
                self.update_preview()

            except Exception as e:
                ErrorHandler.handle_error(e, f"Error initializing template dialog for '{self.template_name}'")
                QMessageBox.critical(self, "Error", f"Failed to initialize template dialog: {e}")

        def on_input_changed(self) -> None:
            """Handle input field changes with debounced preview update."""
            self.preview_timer.stop()
            self.preview_timer.start(300)  # Reduced delay from 500ms

        def get_context(self) -> dict[str, Any]:
            """Get current context from input fields."""
            context = {}

            # Handle agenda template specially
            if self.template_name == "agenda":
                context = compute_agenda_variables()
            else:
                for var_name, input_field in self.inputs.items():
                    if isinstance(input_field, QTextEdit):
                        context[var_name] = input_field.toPlainText()
                    else:
                        context[var_name] = input_field.text()

            return context

        def update_preview(self) -> None:
            """Update the preview with current input values."""
            try:
                context = self.get_context()
                self.preview_widget.update_preview(self.template_name, context)
            except Exception as e:
                logger.debug(f"Preview update failed: {e}")

        def validate_template(self) -> None:
            """Validate the current template configuration."""
            try:
                context = self.get_context()
                template = self.template_service.get_template(self.template_name)

                # Check required fields
                errors = []
                for var in template.get("variables", []):
                    if var.get("required", False):
                        value = context.get(var["name"], "")
                        if not value.strip():
                            errors.append(f"'{var['description']}' is required")

                if errors:
                    QMessageBox.warning(self, "Validation Error", "\n".join(errors))
                else:
                    # Try to render
                    template_service.render_template(self.template_name, context)
                    QMessageBox.information(self, "✓ Validation Success", "Template is valid and ready to print!")

            except Exception as e:
                QMessageBox.critical(self, "Validation Error", f"Template validation failed: {e}")

        def print_template(self) -> None:
            try:
                logger.info(f"Printing template: {self.template_name}")
                context = self.get_context()

                # Use context manager like in CLI interface
                with service_container.get(PrinterService) as printer:
                    printer.print_template(self.template_name, context)

                # Add to recent templates
                gui_settings.add_recent_template(self.template_name)

                logger.info(f"Successfully printed template: {self.template_name}")
                QMessageBox.information(self, "✓ Success", f"Successfully printed '{self.template_name}' template!")
                self.accept()
            except PrintermError as e:
                ErrorHandler.handle_error(e, f"Error printing template '{self.template_name}'")
                QMessageBox.critical(self, "Print Error", f"Failed to print: {e.message}")
            except Exception as e:
                ErrorHandler.handle_error(e, f"Error printing template '{self.template_name}'")
                QMessageBox.critical(self, "Error", f"Failed to print: {e}")

    class MainWindow(QWidget):
        """Enhanced main window with better UX and compact design."""

        def __init__(self) -> None:
            super().__init__()
            self.config_service = config_service
            self.template_service = template_service
            self.current_theme = ThemeManager.get_current_theme()
            self.last_recent_templates = gui_settings.get_recent_templates()  # Track changes

            self.setWindowTitle("🖨️ Thermal Printer")
            self.setFixedSize(650, 500)  # Fixed size to block resizing

            logger.info("Starting enhanced GUI application")
            self.init_ui()
            # Theme is automatically applied in the main() function

        def init_ui(self) -> None:
            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(12, 12, 12, 12)  # Reduced margins
            main_layout.setSpacing(8)  # Reduced spacing

            # Compact header
            header_widget = self.create_header()
            main_layout.addWidget(header_widget)

            # Main content with tabs
            self.tab_widget = QTabWidget()

            # Templates tab with improved layout
            templates_tab = self.create_templates_tab()
            self.tab_widget.addTab(templates_tab, "📄 Templates")

            # Settings tab
            settings_tab = self.create_settings_tab()
            self.tab_widget.addTab(settings_tab, "⚙️ Settings")

            main_layout.addWidget(self.tab_widget)
            self.setLayout(main_layout)

        def create_header(self) -> QWidget:
            """Create a compact header widget."""
            header_widget = QWidget()
            header_layout = QVBoxLayout()
            header_layout.setContentsMargins(0, 0, 0, 0)
            header_layout.setSpacing(4)

            # Title
            title_label = QLabel("🖨️ Thermal Printer")
            title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))  # Increased from 16
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_layout.addWidget(title_label)

            # Subtitle
            subtitle_label = QLabel("Create and print thermal receipts")
            subtitle_label.setFont(QFont("Arial", 11))  # Increased from 9
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle_label.setStyleSheet("color: #666; margin-bottom: 8px;")
            header_layout.addWidget(subtitle_label)

            header_widget.setLayout(header_layout)
            return header_widget

        def create_templates_tab(self) -> QWidget:
            """Create an improved templates tab with better grid layout."""
            templates_widget = QWidget()
            templates_layout = QVBoxLayout()
            templates_layout.setContentsMargins(8, 8, 8, 8)
            templates_layout.setSpacing(10)

            # Recent templates section (horizontal list)
            recent_templates = gui_settings.get_recent_templates()
            if recent_templates:
                recent_group = QGroupBox("🕒 Recent Templates")
                recent_layout = QHBoxLayout()
                recent_layout.setSpacing(6)

                for template_name in recent_templates[:4]:  # Show max 4 recent
                    recent_btn = QPushButton(f"📄 {template_name.title()}")
                    recent_btn.setMaximumWidth(150)
                    recent_btn.setMinimumHeight(35)
                    recent_btn.clicked.connect(lambda checked, name=template_name: self.open_template_dialog(name))
                    recent_layout.addWidget(recent_btn)

                recent_layout.addStretch()
                recent_group.setLayout(recent_layout)
                templates_layout.addWidget(recent_group)

            # All templates section with improved list view
            all_templates_group = QGroupBox("📋 All Templates")
            all_layout = QVBoxLayout()
            all_layout.setSpacing(4)

            try:
                available_templates = self.template_service.list_templates()
                logger.debug(f"Available templates: {available_templates}")

                # Create a scrollable list instead of grid
                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                scroll_area.setMaximumHeight(250)  # Limit height to prevent excessive space

                scroll_widget = QWidget()
                scroll_layout = QVBoxLayout()
                scroll_layout.setSpacing(3)

                for template_name in sorted(available_templates):
                    # Get template info
                    try:
                        template = self.template_service.get_template(template_name)
                        description = template.get("description", "No description")
                    except Exception:
                        description = "Template information unavailable"

                    # Create compact template row
                    template_row = QWidget()
                    template_row.setFixedHeight(50)  # Fixed height for consistency
                    row_layout = QHBoxLayout()
                    row_layout.setContentsMargins(8, 4, 8, 4)
                    row_layout.setSpacing(8)

                    # Template info
                    info_layout = QVBoxLayout()
                    info_layout.setSpacing(2)

                    name_label = QLabel(f"📄 {template_name.title()}")
                    name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # Increased from 11
                    info_layout.addWidget(name_label)

                    desc_label = QLabel(description[:60] + "..." if len(description) > 60 else description)
                    desc_label.setFont(QFont("Arial", 10))  # Increased from 8
                    desc_label.setStyleSheet("color: #666;")
                    info_layout.addWidget(desc_label)

                    row_layout.addLayout(info_layout, 1)  # Take most space

                    # Action button with border
                    action_button = QPushButton("Open")
                    action_button.setMaximumWidth(80)
                    action_button.setMinimumHeight(35)
                    action_button.setStyleSheet("""
                        QPushButton {
                            border: 1px solid #ccc;
                            border-radius: 4px;
                            padding: 6px 12px;
                            font-size: 12px;
                            font-weight: 500;
                        }
                        QPushButton:hover {
                            border-color: #999;
                        }
                    """)
                    action_button.clicked.connect(lambda checked, name=template_name: self.open_template_dialog(name))
                    row_layout.addWidget(action_button)

                    template_row.setLayout(row_layout)

                    # Remove hover effect to prevent highlighting
                    template_row.setStyleSheet("""
                        QWidget {
                            border: 1px solid transparent;
                            border-radius: 4px;
                            background-color: transparent;
                        }
                    """)

                    scroll_layout.addWidget(template_row)

                scroll_layout.addStretch()
                scroll_widget.setLayout(scroll_layout)
                scroll_area.setWidget(scroll_widget)
                all_layout.addWidget(scroll_area)

            except Exception as e:
                ErrorHandler.handle_error(e, "Error loading templates")
                error_label = QLabel(f"❌ Failed to load templates: {e}")
                error_label.setStyleSheet("color: red; padding: 20px;")
                all_layout.addWidget(error_label)

            all_templates_group.setLayout(all_layout)
            templates_layout.addWidget(all_templates_group)

            templates_widget.setLayout(templates_layout)
            return templates_widget

        def create_settings_tab(self) -> QWidget:
            """Create a compact settings tab widget."""
            settings_widget = QWidget()
            settings_layout = QVBoxLayout()
            settings_layout.setContentsMargins(12, 12, 12, 12)
            settings_layout.setSpacing(12)

            # Improved group box styling for better dark mode appearance
            styles = ThemeManager.get_theme_styles(self.current_theme)
            group_style = f"""
                QGroupBox {{
                    font-weight: bold;
                    font-size: 13px;
                    border: 1px solid {styles["border"]};
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 12px;
                    background-color: {styles["surface"]};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 6px;
                    background-color: {styles["background"]};
                    border-radius: 4px;
                    color: {styles["text"]};
                }}
                QLabel {{
                    background-color: transparent;
                    color: {styles["text"]};
                    font-size: 12px;
                }}
            """

            # Printer settings
            printer_group = QGroupBox("🖨️ Printer Configuration")
            printer_group.setStyleSheet(group_style)
            printer_layout = QFormLayout()
            printer_layout.setVerticalSpacing(10)
            printer_layout.setHorizontalSpacing(12)

            # Printer IP
            self.ip_input = QLineEdit()
            with contextlib.suppress(ConfigurationError):
                self.ip_input.setText(self.config_service.get_printer_ip())
            self.ip_input.setPlaceholderText("e.g., 192.168.1.100")
            printer_layout.addRow("IP Address:", self.ip_input)

            # Characters per line
            self.chars_input = QLineEdit()
            self.chars_input.setText(str(self.config_service.get_chars_per_line()))
            self.chars_input.setPlaceholderText("e.g., 48")
            printer_layout.addRow("Characters per Line:", self.chars_input)

            printer_group.setLayout(printer_layout)
            settings_layout.addWidget(printer_group)

            # Advanced settings
            advanced_group = QGroupBox("⚙️ Advanced Options")
            advanced_group.setStyleSheet(group_style)
            advanced_layout = QFormLayout()
            advanced_layout.setVerticalSpacing(10)
            advanced_layout.setHorizontalSpacing(12)

            # Special letters
            self.special_letters_checkbox = QCheckBox()
            self.special_letters_checkbox.setChecked(self.config_service.get_enable_special_letters())
            advanced_layout.addRow("Enable Special Letters:", self.special_letters_checkbox)

            # Check for updates
            self.check_updates_checkbox = QCheckBox()
            self.check_updates_checkbox.setChecked(self.config_service.get_check_for_updates())
            advanced_layout.addRow("Check for Updates:", self.check_updates_checkbox)

            advanced_group.setLayout(advanced_layout)
            settings_layout.addWidget(advanced_group)

            # Save button with better styling
            save_layout = QHBoxLayout()
            save_layout.addStretch()

            save_button = QPushButton("💾 Save Settings")
            save_button.setMinimumHeight(40)  # Slightly taller
            save_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {styles["success"]};
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 13px;
                    font-weight: bold;
                    border-radius: 6px;
                    min-width: 140px;
                }}
                QPushButton:hover {{
                    background-color: {styles["success_dark"]};
                }}
                QPushButton:pressed {{
                    background-color: {styles["success_dark"]};
                    padding: 11px 19px 9px 21px;
                }}
            """)
            save_button.clicked.connect(self.save_settings)
            save_layout.addWidget(save_button)

            settings_layout.addLayout(save_layout)
            settings_layout.addStretch()

            settings_widget.setLayout(settings_layout)
            return settings_widget

        def save_settings(self) -> None:
            """Save settings from the settings tab."""
            try:
                logger.info("Saving settings from main window")

                # Save IP address
                ip_address = self.ip_input.text().strip()
                if ip_address:
                    self.config_service.set_printer_ip(ip_address)

                # Save characters per line
                chars_text = self.chars_input.text().strip()
                if chars_text:
                    chars_per_line = int(chars_text)
                    self.config_service.set_chars_per_line(chars_per_line)

                # Save special letters setting
                enable_special_letters = self.special_letters_checkbox.isChecked()
                self.config_service.set_enable_special_letters(enable_special_letters)

                # Save check for updates setting
                check_for_updates = self.check_updates_checkbox.isChecked()
                self.config_service.set_check_for_updates(check_for_updates)

                QMessageBox.information(self, "✓ Success", "Settings saved successfully!")

            except ValueError:
                QMessageBox.critical(self, "❌ Error", "Invalid number for characters per line.")
            except Exception as e:
                ErrorHandler.handle_error(e, "Error saving settings")
                QMessageBox.critical(self, "❌ Error", f"Failed to save settings: {e}")

        def open_template_dialog(self, template_name: str) -> None:
            try:
                logger.debug(f"Opening template dialog for: {template_name}")
                dialog = TemplateDialog(template_name, self)
                dialog.exec()

                # Refresh recent templates after printing
                recent_templates = gui_settings.get_recent_templates()
                if recent_templates != self.last_recent_templates:
                    self.refresh_templates_tab()

            except Exception as e:
                ErrorHandler.handle_error(e, f"Error opening template dialog for '{template_name}'")
                QMessageBox.critical(self, "❌ Error", f"Failed to open template dialog: {e}")

        def refresh_templates_tab(self) -> None:
            """Refresh the templates tab to show updated recent templates."""
            try:
                # Store current tab index
                current_index = self.tab_widget.currentIndex()

                # Recreate templates tab
                new_templates_tab = self.create_templates_tab()
                self.tab_widget.removeTab(0)  # Remove old templates tab
                self.tab_widget.insertTab(0, new_templates_tab, "📄 Templates")

                # Restore tab selection
                self.tab_widget.setCurrentIndex(current_index)

                self.last_recent_templates = gui_settings.get_recent_templates()
            except Exception as e:
                logger.warning(f"Failed to refresh templates tab: {e}")

else:
    # Dummy classes for when PyQt6 is not available
    class MainWindow:  # type: ignore[no-redef]
        def __init__(self) -> None:
            raise ImportError("PyQt6 is not available")

    class TemplateDialog:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError("PyQt6 is not available")

    class SettingsDialog:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise ImportError("PyQt6 is not available")


def main() -> None:
    """Launch the GUI application."""
    if not PYQT_AVAILABLE:
        logger.error("PyQt6 is not available")
        print("PyQt6 is not available. Please install it with: pip install PyQt6")  # noqa: T201
        sys.exit(1)

    try:
        logger.info("Launching GUI application")
        app = QApplication(sys.argv)
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
    main()
