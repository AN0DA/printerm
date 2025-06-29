"""GUI interface for the printerm application."""

import logging
import sys
from typing import Any

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QDialog,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
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


if PYQT_AVAILABLE:

    class MainWindow(QWidget):
        def __init__(self) -> None:
            super().__init__()
            # Use services from container like other interfaces
            self.config_service = config_service
            self.template_service = template_service
            self.setWindowTitle("Thermal Printer Application")
            logger.info("Starting GUI application")
            self.init_ui()

        def init_ui(self) -> None:
            layout = QVBoxLayout()

            label = QLabel("Select a Printing Command:")
            layout.addWidget(label)

            button_layout = QHBoxLayout()

            try:
                available_templates = self.template_service.list_templates()
                logger.debug(f"Available templates: {available_templates}")
                
                for template_name in available_templates:
                    button = QPushButton(template_name.capitalize())
                    button.clicked.connect(lambda checked, name=template_name: self.open_template_dialog(name))
                    button_layout.addWidget(button)
            except Exception as e:
                ErrorHandler.handle_error(e, "Error loading templates")
                QMessageBox.critical(self, "Error", f"Failed to load templates: {e}")

            settings_button = QPushButton("Settings")
            settings_button.clicked.connect(self.open_settings_dialog)
            button_layout.addWidget(settings_button)

            layout.addLayout(button_layout)
            self.setLayout(layout)

        def open_template_dialog(self, template_name: str) -> None:
            try:
                logger.debug(f"Opening template dialog for: {template_name}")
                dialog = TemplateDialog(template_name, self)
                dialog.exec()
            except Exception as e:
                ErrorHandler.handle_error(e, f"Error opening template dialog for '{template_name}'")
                QMessageBox.critical(self, "Error", f"Failed to open template dialog: {e}")

        def open_settings_dialog(self) -> None:
            try:
                logger.debug("Opening settings dialog")
                dialog = SettingsDialog(self)
                dialog.exec()
            except Exception as e:
                ErrorHandler.handle_error(e, "Error opening settings dialog")
                QMessageBox.critical(self, "Error", f"Failed to open settings dialog: {e}")


    class TemplateDialog(QDialog):
        def __init__(self, template_name: str, parent: QWidget | None = None):
            super().__init__(parent)
            self.template_name = template_name
            # Use services from container like other interfaces
            self.template_service = template_service
            self.inputs: dict[str, Any] = {}
            self.setWindowTitle(f"Print {template_name.capitalize()}")
            logger.debug(f"Initializing template dialog for: {template_name}")
            self.init_ui()

        def init_ui(self) -> None:
            try:
                template = self.template_service.get_template(self.template_name)
                layout = QVBoxLayout()

                form_layout = QFormLayout()
                for var in template.get("variables", []):
                    input_field = QTextEdit() if var.get("markdown", False) else QLineEdit()
                    if isinstance(input_field, QTextEdit):
                        input_field.setAcceptRichText(False)  # Ensure plain text only
                        input_field.setMaximumHeight(100)
                    form_layout.addRow(var["description"], input_field)
                    self.inputs[var["name"]] = input_field
                layout.addLayout(form_layout)

                button_layout = QHBoxLayout()
                print_button = QPushButton("Print")
                print_button.clicked.connect(self.print_template)
                button_layout.addWidget(print_button)

                cancel_button = QPushButton("Cancel")
                cancel_button.clicked.connect(self.reject)
                button_layout.addWidget(cancel_button)

                layout.addLayout(button_layout)
                self.setLayout(layout)
            except Exception as e:
                ErrorHandler.handle_error(e, f"Error initializing template dialog for '{self.template_name}'")
                QMessageBox.critical(self, "Error", f"Failed to initialize template dialog: {e}")

        def print_template(self) -> None:
            try:
                logger.info(f"Printing template: {self.template_name}")
                context = {}
                
                # Handle agenda template specially like other interfaces
                if self.template_name == "agenda":
                    context = compute_agenda_variables()
                    logger.debug("Using computed agenda variables")
                else:
                    for var_name, input_field in self.inputs.items():
                        if isinstance(input_field, QTextEdit):
                            context[var_name] = input_field.toPlainText()
                        else:
                            context[var_name] = input_field.text()
                    logger.debug(f"Collected input context: {list(context.keys())}")

                # Use context manager like in CLI interface
                with service_container.get(PrinterService) as printer:
                    printer.print_template(self.template_name, context)
                
                logger.info(f"Successfully printed template: {self.template_name}")
                QMessageBox.information(self, "Success", f"Printed using template '{self.template_name}'.")
                self.accept()
            except PrintermError as e:
                ErrorHandler.handle_error(e, f"Error printing template '{self.template_name}'")
                QMessageBox.critical(self, "Print Error", f"Failed to print: {e.message}")
            except Exception as e:
                ErrorHandler.handle_error(e, f"Error printing template '{self.template_name}'")
                QMessageBox.critical(self, "Error", f"Failed to print: {e}")


    class SettingsDialog(QDialog):
        def __init__(self, parent: QWidget | None = None):
            super().__init__(parent)
            # Use services from container like other interfaces
            self.config_service = config_service
            self.setWindowTitle("Settings")
            logger.debug("Initializing settings dialog")
            self.init_ui()

        def init_ui(self) -> None:
            try:
                layout = QVBoxLayout()

                form_layout = QFormLayout()

                # IP Address
                self.ip_input = QLineEdit()
                try:
                    self.ip_input.setText(self.config_service.get_printer_ip())
                except ConfigurationError:
                    logger.debug("No printer IP configured")
                    pass  # Leave empty if not configured
                form_layout.addRow("Printer IP Address:", self.ip_input)

                # Characters per line
                self.chars_input = QLineEdit()
                self.chars_input.setText(str(self.config_service.get_chars_per_line()))
                form_layout.addRow("Characters per Line:", self.chars_input)

                # Enable special letters (like web interface)
                self.special_letters_checkbox = QCheckBox()
                self.special_letters_checkbox.setChecked(self.config_service.get_enable_special_letters())
                form_layout.addRow("Enable Special Letters:", self.special_letters_checkbox)

                # Check for updates (like web interface)
                self.check_updates_checkbox = QCheckBox()
                self.check_updates_checkbox.setChecked(self.config_service.get_check_for_updates())
                form_layout.addRow("Check for Updates:", self.check_updates_checkbox)

                layout.addLayout(form_layout)

                button_layout = QHBoxLayout()
                save_button = QPushButton("Save")
                save_button.clicked.connect(self.save_settings)
                button_layout.addWidget(save_button)

                cancel_button = QPushButton("Cancel")
                cancel_button.clicked.connect(self.reject)
                button_layout.addWidget(cancel_button)

                layout.addLayout(button_layout)
                self.setLayout(layout)
            except Exception as e:
                ErrorHandler.handle_error(e, "Error initializing settings dialog")
                QMessageBox.critical(self, "Error", f"Failed to initialize settings dialog: {e}")

        def save_settings(self) -> None:
            try:
                logger.info("Saving settings")
                
                # Save IP address
                ip_address = self.ip_input.text().strip()
                if ip_address:
                    self.config_service.set_printer_ip(ip_address)
                    logger.debug(f"Updated printer IP: {ip_address}")

                # Save characters per line
                chars_text = self.chars_input.text().strip()
                if chars_text:
                    chars_per_line = int(chars_text)
                    self.config_service.set_chars_per_line(chars_per_line)
                    logger.debug(f"Updated chars per line: {chars_per_line}")

                # Save special letters setting (like web interface)
                enable_special_letters = self.special_letters_checkbox.isChecked()
                self.config_service.set_enable_special_letters(enable_special_letters)
                logger.debug(f"Updated enable special letters: {enable_special_letters}")

                # Save check for updates setting (like web interface)
                check_for_updates = self.check_updates_checkbox.isChecked()
                self.config_service.set_check_for_updates(check_for_updates)
                logger.debug(f"Updated check for updates: {check_for_updates}")

                logger.info("Settings saved successfully")
                QMessageBox.information(self, "Success", "Settings saved successfully.")
                self.accept()
            except ValueError:
                ErrorHandler.handle_error(ValueError("Invalid number for characters per line"), "Settings validation error")
                QMessageBox.critical(self, "Error", "Invalid number for characters per line.")
            except PrintermError as e:
                ErrorHandler.handle_error(e, "Error saving settings")
                QMessageBox.critical(self, "Configuration Error", f"Failed to save settings: {e.message}")
            except Exception as e:
                ErrorHandler.handle_error(e, "Error saving settings")
                QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

else:
    # Dummy classes for when PyQt6 is not available
    class MainWindow:
        def __init__(self) -> None:
            raise ImportError("PyQt6 is not available")
    
    class TemplateDialog:
        def __init__(self, *args, **kwargs) -> None:
            raise ImportError("PyQt6 is not available")
    
    class SettingsDialog:
        def __init__(self, *args, **kwargs) -> None:
            raise ImportError("PyQt6 is not available")


def main() -> None:
    """Launch the GUI application."""
    if not PYQT_AVAILABLE:
        logger.error("PyQt6 is not available")
        print("PyQt6 is not available. Please install it with: pip install PyQt6")
        sys.exit(1)
    
    try:
        logger.info("Launching GUI application")
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        logger.info("GUI application started successfully")
        sys.exit(app.exec())
    except Exception as e:
        ErrorHandler.handle_error(e, "Error launching GUI")
        logger.error(f"Failed to launch GUI: {e}")
        print(f"Failed to launch GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
