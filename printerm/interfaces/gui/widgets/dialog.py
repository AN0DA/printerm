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
    from PyQt6.QtGui import QFont, QKeyEvent
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
            self.should_reopen = False  # Flag to indicate if dialog should be reopened after printing

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

            # Status label for feedback
            self.status_label = QLabel("")
            self.status_label.setStyleSheet("color: #666; font-style: italic;")
            self.status_label.hide()  # Hidden by default

            # Button references for state management
            self.validate_button: QPushButton | None = None
            self.cancel_button: QPushButton | None = None
            self.print_button: QPushButton | None = None

            self.init_ui()

        def init_ui(self) -> None:
            try:
                template = self.template_service.get_template(self.template_name)

                # Main layout - vertical layout since no preview
                main_layout = QVBoxLayout()
                main_layout.setContentsMargins(20, 20, 20, 20)
                main_layout.setSpacing(15)

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
                title_layout.setContentsMargins(12, 12, 12, 12)
                title_layout.setSpacing(4)

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
                    # slightly tighter vertical spacing to remove odd gaps between rows
                    form_layout.setVerticalSpacing(6)
                    form_layout.setHorizontalSpacing(16)
                    form_layout.setContentsMargins(10, 6, 10, 10)

                    from PyQt6.QtCore import Qt

                    for var in variables:
                        # Create a proper label widget so we can control width and alignment
                        label_text = var.get("description", var["name"]) or var["name"]
                        short_label = label_text[:25] + "..." if len(label_text) > 28 else label_text

                        label_widget = QLabel(f"{short_label}:")
                        # Fixed width keeps the input column aligned (slightly narrower)
                        label_widget.setFixedWidth(110)
                        label_widget.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                        label_widget.setStyleSheet("padding-right: 6px; color: #ddd")

                        input_field = QTextEdit() if var.get("markdown", False) else QLineEdit()
                        if isinstance(input_field, QTextEdit):
                            input_field.setMaximumHeight(120)
                        # Give inputs more horizontal space so labels don't wrap
                        input_field.setMinimumWidth(360)
                        input_field.setMaximumWidth(640)

                        # Compact placeholder text
                        placeholder = var.get("description", var["name"])
                        if var.get("required", False):
                            placeholder += " *"
                        input_field.setPlaceholderText(placeholder)

                        # Create error label for this field and align it under the input
                        error_label = QLabel("")
                        error_label.setStyleSheet("color: #ff6666; font-size: 11px;")
                        # smaller top margin keeps error labels close to inputs
                        error_label.setContentsMargins(0, 2, 0, 0)
                        error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
                        error_label.hide()  # Hidden by default

                        # Add label + input as a single row, then add the error label beneath (spanning)
                        form_layout.addRow(label_widget, input_field)
                        # Use an empty QWidget for the first column (prevents styled QLabel boxes showing)
                        form_layout.addRow(QWidget(), error_label)

                        self.inputs[var["name"]] = input_field
                        # Store error label reference
                        if not hasattr(self, "error_labels"):
                            self.error_labels = {}
                        self.error_labels[var["name"]] = error_label

                    # Slightly tighten group box appearance for better balance
                    form_group.setStyleSheet("QGroupBox { margin-top: 6px; padding: 8px; border-radius: 6px; }")
                    form_group.setLayout(form_layout)
                    main_layout.addWidget(form_group)
                else:
                    no_vars_label = QLabel("✨ No variables needed")
                    no_vars_label.setStyleSheet("color: #666; font-style: italic; text-align: center;")
                    main_layout.addWidget(no_vars_label)

                # Button layout
                button_layout = QHBoxLayout()
                button_layout.setSpacing(8)

                # Status label above buttons
                main_layout.addWidget(self.status_label)

                # Validate button
                validate_button = QPushButton("✓ Validate")
                validate_button.setToolTip("Check if the template can be rendered with current inputs")
                validate_button.clicked.connect(self.validate_template)
                validate_button.setMaximumWidth(100)
                self.validate_button = validate_button
                button_layout.addWidget(validate_button)

                button_layout.addStretch()

                # Cancel button
                cancel_button = QPushButton("Cancel")
                cancel_button.setToolTip("Close dialog without printing")
                cancel_button.setMaximumWidth(80)
                cancel_button.clicked.connect(self.reject)
                self.cancel_button = cancel_button
                button_layout.addWidget(cancel_button)

                # Print button
                print_button = QPushButton("🖨️ Print")
                print_button.setToolTip("Print the template with current inputs")
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
                    QPushButton:disabled {{
                        background-color: #cccccc;
                        color: #666666;
                    }}
                """)
                print_button.clicked.connect(self.print_template)
                self.print_button = print_button
                button_layout.addWidget(print_button)

                main_layout.addLayout(button_layout)

                self.setLayout(main_layout)

                # Lock dialog size to the computed layout to avoid awkward resize behavior
                self.adjustSize()
                self.setFixedSize(self.width(), self.height())

                # Initial validation if no variables needed
                if not variables:
                    self.validate_template()

                # Set initial focus
                if variables:
                    # Focus first input field
                    first_var = variables[0]
                    first_input = self.inputs[first_var["name"]]
                    first_input.setFocus()
                else:
                    # Focus print button if no variables
                    print_button.setFocus()

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
                # Disable buttons during validation
                if self.validate_button:
                    self.validate_button.setEnabled(False)
                    self.validate_button.setText("🔍 Validating...")
                if self.print_button:
                    self.print_button.setEnabled(False)
                if self.cancel_button:
                    self.cancel_button.setEnabled(False)

                # Clear previous error messages
                if hasattr(self, "error_labels"):
                    for error_label in self.error_labels.values():
                        error_label.hide()
                        error_label.setText("")

                # Show validation status
                self.status_label.setText("🔍 Validating template...")
                self.status_label.setStyleSheet("color: #666; font-style: italic;")
                self.status_label.show()
                # Force UI update
                from PyQt6.QtWidgets import QApplication

                QApplication.processEvents()

                context = self.get_context()
                template = self.template_service.get_template(self.template_name)

                # Check required fields and show inline errors
                has_errors = False
                for var in template.get("variables", []):
                    if var.get("required", False):
                        value = context.get(var["name"], "")
                        if not value.strip():
                            if hasattr(self, "error_labels") and var["name"] in self.error_labels:
                                self.error_labels[var["name"]].setText("❌ This field is required")
                                self.error_labels[var["name"]].show()
                            has_errors = True

                if has_errors:
                    self.status_label.setText("❌ Validation failed - check required fields")
                    self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
                else:
                    # Try to render
                    template_service.render_template(self.template_name, context)
                    self.status_label.setText("✅ Template is valid")
                    self.status_label.setStyleSheet("color: #388e3c; font-weight: bold;")
                    QMessageBox.information(self, "✓ Validation Success", "Template is valid and ready to print!")

            except Exception as e:
                self.status_label.setText("❌ Validation failed")
                self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
                QMessageBox.critical(self, "Validation Error", f"Template validation failed: {e}")
            finally:
                # Re-enable buttons
                if self.validate_button:
                    self.validate_button.setEnabled(True)
                    self.validate_button.setText("✓ Validate")
                if self.print_button:
                    self.print_button.setEnabled(True)
                if self.cancel_button:
                    self.cancel_button.setEnabled(True)

                # Hide status after a short delay
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(3000, self.status_label.hide)

        def print_template(self) -> None:
            try:
                logger.info(f"Printing template: {self.template_name}")

                # Disable buttons during printing
                if self.validate_button:
                    self.validate_button.setEnabled(False)
                if self.print_button:
                    self.print_button.setEnabled(False)
                    self.print_button.setText("🖨️ Printing...")
                if self.cancel_button:
                    self.cancel_button.setEnabled(False)

                # Show printing status
                self.status_label.setText("🖨️ Printing template...")
                self.status_label.setStyleSheet("color: #1976d2; font-weight: bold;")
                self.status_label.show()
                # Force UI update
                from PyQt6.QtWidgets import QApplication

                QApplication.processEvents()

                context = self.get_context()

                # Use context manager like in CLI interface
                with service_container.get(PrinterService) as printer:
                    printer.print_template(self.template_name, context)

                # Add to recent templates
                gui_settings.add_recent_template(self.template_name)

                logger.info(f"Successfully printed template: {self.template_name}")

                # Update status
                self.status_label.setText("✅ Successfully printed!")
                self.status_label.setStyleSheet("color: #388e3c; font-weight: bold;")

                # Get display name for success message
                try:
                    template = self.template_service.get_template(self.template_name)
                    display_name = template.get("name", self.template_name)
                except Exception:
                    display_name = self.template_name

                # Success message with option to print again
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("✓ Success")
                msg_box.setText(f"Successfully printed '{display_name}' template!")
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                print_again_button = msg_box.addButton("Print Again", QMessageBox.ButtonRole.ActionRole)
                msg_box.exec()

                if msg_box.clickedButton() == print_again_button:
                    # Set flag to reopen dialog
                    self.should_reopen = True
                else:
                    # Close dialog normally
                    self.should_reopen = False

                self.accept()
            except PrintermError as e:
                self.status_label.setText("❌ Print failed")
                self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
                ErrorHandler.handle_error(e, f"Error printing template '{self.template_name}'")
                QMessageBox.critical(self, "Print Error", f"Failed to print: {e.message}")
            except Exception as e:
                self.status_label.setText("❌ Print failed")
                self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
                ErrorHandler.handle_error(e, f"Error printing template '{self.template_name}'")
                QMessageBox.critical(self, "Error", f"Failed to print: {e}")
            finally:
                # Re-enable buttons (only if dialog is still open)
                if not self.should_reopen:
                    if self.validate_button:
                        self.validate_button.setEnabled(True)
                    if self.print_button:
                        self.print_button.setEnabled(True)
                        self.print_button.setText("🖨️ Print")
                    if self.cancel_button:
                        self.cancel_button.setEnabled(True)

                # Hide status after a delay if dialog is still open
                if not self.should_reopen:
                    from PyQt6.QtCore import QTimer

                    QTimer.singleShot(3000, self.status_label.hide)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[no-untyped-def]
        """Handle keyboard shortcuts."""
        from PyQt6.QtCore import Qt

        if event.key() == Qt.Key.Key_Return:
            self.print_template()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)  # type: ignore[misc]
