"""Template dialog widget for the printerm GUI."""

import logging
from typing import Any

from printerm.error_handling import ErrorHandler
from printerm.exceptions import PrintermError
from printerm.interfaces.gui.theme import ThemeManager
from printerm.interfaces.gui.widgets.base import PYQT_AVAILABLE, gui_settings, template_service
from printerm.services import service_container
from printerm.services.interfaces import PrinterService, TemplateService

logger = logging.getLogger(__name__)

if PYQT_AVAILABLE:
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QDialog,
        QFormLayout,
        QFrame,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )


if PYQT_AVAILABLE:

    class TemplateDialog(QDialog):
        """Enhanced template dialog with preview and better UX."""

        def __init__(self, template_name: str, parent: QWidget | None = None):
            super().__init__(parent)
            self.template_name = template_name
            self.template_service = template_service
            self.inputs: dict[str, Any] = {}
            self.current_theme = ThemeManager.get_current_theme()

            # Get template to set proper title
            try:
                template = self.template_service.get_template(self.template_name)
                display_name = template.get("name", template_name.capitalize())
            except Exception:
                display_name = template_name.capitalize()

            self.setWindowTitle(f"Print {display_name}")
            self.setMinimumSize(700, 450)  # Reduced from 800x600
            self.setMaximumSize(900, 600)  # Add max size to prevent excessive space
            logger.debug(f"Initializing enhanced template dialog for: {template_name}")
            self.init_ui()

        def init_ui(self) -> None:
            try:
                template = self.template_service.get_template(self.template_name)

                # Main layout - vertical layout since no preview
                main_layout = QVBoxLayout()
                main_layout.setContentsMargins(10, 10, 10, 10)
                main_layout.setSpacing(12)

                # Title section
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

                title_label = QLabel(f"📄 {template.get('name', self.template_name.capitalize())}")
                title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
                title_layout.addWidget(title_label)

                # Description if available
                if template.get("description"):
                    desc_label = QLabel(template["description"])
                    desc_label.setFont(QFont("Arial", 11))
                    desc_label.setStyleSheet("color: #666; margin-top: 2px;")
                    desc_label.setWordWrap(True)
                    title_layout.addWidget(desc_label)

                title_frame.setLayout(title_layout)
                main_layout.addWidget(title_frame)

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
                            input_field.setMaximumHeight(80)
                        else:
                            pass

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
                    main_layout.addWidget(form_group)
                else:
                    no_vars_label = QLabel("✨ No variables needed")
                    no_vars_label.setStyleSheet("color: #666; font-style: italic; text-align: center;")
                    main_layout.addWidget(no_vars_label)

                # Button layout
                button_layout = QHBoxLayout()
                button_layout.setSpacing(8)

                # Validate button
                validate_button = QPushButton("✓ Validate")
                validate_button.clicked.connect(self.validate_template)
                validate_button.setMaximumWidth(100)
                button_layout.addWidget(validate_button)

                button_layout.addStretch()

                # Cancel button
                cancel_button = QPushButton("Cancel")
                cancel_button.setMaximumWidth(80)
                cancel_button.clicked.connect(self.reject)
                button_layout.addWidget(cancel_button)

                # Print button
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

                main_layout.addLayout(button_layout)

                self.setLayout(main_layout)

                # Initial validation if no variables needed
                if not variables:
                    self.validate_template()

            except Exception as e:
                ErrorHandler.handle_error(e, f"Error initializing template dialog for '{self.template_name}'")
                QMessageBox.critical(self, "Error", f"Failed to initialize template dialog: {e}")

        def get_context(self) -> dict[str, Any]:
            """Get current context from input fields."""
            context = {}

            # Check if template has a script
            template_service = service_container.get(TemplateService)
            if template_service.has_script(self.template_name):
                context = template_service.generate_template_context(self.template_name)
            else:
                for var_name, input_field in self.inputs.items():
                    if isinstance(input_field, QTextEdit):
                        context[var_name] = input_field.toPlainText()
                    else:
                        context[var_name] = input_field.text()

            return context

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
                # Get display name for success message
                try:
                    template = self.template_service.get_template(self.template_name)
                    display_name = template.get("name", self.template_name)
                except Exception:
                    display_name = self.template_name
                QMessageBox.information(self, "✓ Success", f"Successfully printed '{display_name}' template!")
                self.accept()
            except PrintermError as e:
                ErrorHandler.handle_error(e, f"Error printing template '{self.template_name}'")
                QMessageBox.critical(self, "Print Error", f"Failed to print: {e.message}")
            except Exception as e:
                ErrorHandler.handle_error(e, f"Error printing template '{self.template_name}'")
                QMessageBox.critical(self, "Error", f"Failed to print: {e}")
