"""Main window widget for the printerm GUI."""

import contextlib
import logging
from typing import Any

from printerm import __version__
from printerm.error_handling import ErrorHandler
from printerm.exceptions import ConfigurationError
from printerm.interfaces.gui.theme import ThemeManager
from printerm.interfaces.gui.widgets.base import (
    PYQT_AVAILABLE,
    config_service,
    gui_settings,
    printer_service,
    template_service,
    update_service,
)
from printerm.utils import is_running_via_pipx

logger = logging.getLogger(__name__)

if PYQT_AVAILABLE:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QCheckBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    from .dialog import TemplateDialog


if PYQT_AVAILABLE:

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
            # Check for updates after UI is initialized
            self.check_for_updates()
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
                    # Get template display name and variables
                    try:
                        template = self.template_service.get_template(template_name)
                        display_name = template.get("name", template_name.title())
                        variables = template.get("variables", [])
                    except Exception:
                        display_name = template_name.title()
                        variables = ["dummy"]  # Assume has variables if can't load
                    button_text = "Open" if variables else "Print"
                    recent_btn = QPushButton(f"📄 {display_name}")
                    recent_btn.setMaximumWidth(150)
                    recent_btn.setMinimumHeight(35)
                    if variables:
                        recent_btn.clicked.connect(lambda checked, name=template_name: self.open_template_dialog(name))
                    else:
                        recent_btn.clicked.connect(
                            lambda checked, name=template_name: self.print_template_directly(name)
                        )
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
                        variables = template.get("variables", [])
                    except Exception:
                        description = "Template information unavailable"
                        variables = ["dummy"]  # Assume has variables if can't load

                    # Create compact template row
                    template_row = QWidget()
                    template_row.setFixedHeight(50)  # Fixed height for consistency
                    row_layout = QHBoxLayout()
                    row_layout.setContentsMargins(8, 4, 8, 4)
                    row_layout.setSpacing(8)

                    # Template info
                    info_layout = QVBoxLayout()
                    info_layout.setSpacing(2)

                    name_label = QLabel(
                        f"📄 {template.get('name', template_name.title()) if 'template' in locals() else template_name.title()}"
                    )
                    name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))  # Increased from 11
                    info_layout.addWidget(name_label)

                    desc_label = QLabel(description[:60] + "..." if len(description) > 60 else description)
                    desc_label.setFont(QFont("Arial", 10))  # Increased from 8
                    desc_label.setStyleSheet("color: #666;")
                    info_layout.addWidget(desc_label)

                    row_layout.addLayout(info_layout, 1)  # Take most space

                    # Action button with border
                    button_text = "Open" if variables else "Print"
                    action_button = QPushButton(button_text)
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
                    if variables:
                        action_button.clicked.connect(
                            lambda checked, name=template_name: self.open_template_dialog(name)
                        )
                    else:
                        action_button.clicked.connect(
                            lambda checked, name=template_name: self.print_template_directly(name)
                        )
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
                while True:
                    logger.debug(f"Opening template dialog for: {template_name}")
                    dialog = TemplateDialog(template_name, self)
                    dialog.exec()

                    if not dialog.should_reopen:
                        break
                    # If should reopen, continue the loop to open dialog again

                # Refresh recent templates after printing
                recent_templates = gui_settings.get_recent_templates()
                if recent_templates != self.last_recent_templates:
                    self.refresh_templates_tab()

            except Exception as e:
                ErrorHandler.handle_error(e, f"Error opening template dialog for '{template_name}'")
                QMessageBox.critical(self, "❌ Error", f"Failed to open template dialog: {e}")

        def print_template_directly(self, template_name: str) -> None:
            """Print template directly with confirmation popup."""
            try:
                logger.info(f"Direct printing template: {template_name}")

                # Get display name
                template = self.template_service.get_template(template_name)
                display_name = template.get("name", template_name)

                # Confirmation popup
                reply = QMessageBox.question(
                    self,
                    "Confirmation",
                    f"Do you want to print '{display_name}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

                # Print template
                context: dict[str, Any] = {}  # No variables needed
                with printer_service as printer:
                    printer.print_template(template_name, context)

                # Add to recent templates
                gui_settings.add_recent_template(template_name)

                logger.info(f"Successfully printed template: {template_name}")

                # Success message with option to print again
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("✓ Success")
                msg_box.setText(f"Successfully printed '{display_name}' template!")
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                print_again_button = msg_box.addButton("Print Again", QMessageBox.ButtonRole.ActionRole)
                msg_box.exec()

                if msg_box.clickedButton() == print_again_button:
                    # Print the same template again
                    self.print_template_directly(template_name)
                    return  # Don't refresh UI again since print_template_directly will handle it

                # Refresh recent templates
                self.refresh_templates_tab()

            except Exception as e:
                ErrorHandler.handle_error(e, f"Error printing template '{template_name}'")
                QMessageBox.critical(self, "❌ Error", f"Failed to print: {e}")

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

        def check_for_updates(self) -> None:
            """Check for updates and show notification if available."""
            try:
                if self.config_service.get_check_for_updates() and update_service.check_for_updates_with_retry(
                    __version__
                ):
                    self.show_update_dialog()
            except Exception as e:
                logger.error(f"Error checking for updates: {e}")

        def show_update_dialog(self) -> None:
            """Show update available dialog."""
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Update Available")
            msg_box.setText("A new version of Printerm is available!")
            msg_box.setInformativeText("Would you like to update now?")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            msg_box.setIcon(QMessageBox.Icon.Information)

            reply = msg_box.exec()
            if reply == QMessageBox.StandardButton.Yes:
                self.perform_update()

        def perform_update(self) -> None:
            """Perform the update by running the update command."""
            import subprocess  # nosec
            import sys

            try:
                # Show progress message
                QMessageBox.information(
                    self, "Updating", "Updating Printerm to the latest version...\n\nThis may take a few moments."
                )

                # Check if we're running via pipx
                if is_running_via_pipx():
                    cmd = ["pipx", "update", "printerm"]
                else:
                    # Check if we're in a virtual environment
                    in_venv = sys.prefix != sys.base_prefix

                    # Use pip with --user flag if not in venv
                    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "--quiet", "printerm"]
                    if not in_venv:
                        cmd.insert(3, "--user")

                # Run with timeout
                result = subprocess.run(  # nosec
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                    check=False,
                )

                if result.returncode == 0:
                    QMessageBox.information(
                        self,
                        "Update Complete",
                        "Printerm has been successfully updated!\n\nPlease restart the application to use the new version.",
                    )
                else:
                    error_msg = f"Failed to update Printerm (exit code: {result.returncode})"
                    if result.stderr:
                        error_msg += f"\n\nError: {result.stderr[:200]}..."  # Truncate long errors
                    QMessageBox.critical(self, "Update Failed", error_msg)

            except subprocess.TimeoutExpired:
                QMessageBox.critical(self, "Update Failed", "Update timed out after 5 minutes")
            except Exception as e:
                QMessageBox.critical(self, "Update Error", f"An error occurred during update:\n\n{str(e)}")
