import logging
import sys
from typing import Any

from PyQt6.QtWidgets import (
    QApplication,
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

from printerm.config import (
    PRINT_TEMPLATE_FOLDER,
    get_chars_per_line,
    get_check_for_updates,
    get_enable_special_letters,
    get_printer_ip,
    set_chars_per_line,
    set_check_for_updates,
    set_enable_special_letters,
    set_printer_ip,
)
from printerm.printer import ThermalPrinter
from printerm.template_manager import TemplateManager
from printerm.utils import compute_agenda_variables

logger = logging.getLogger(__name__)


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.template_manager = TemplateManager(PRINT_TEMPLATE_FOLDER)
        self.setWindowTitle("Thermal Printer Application")
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()

        label = QLabel("Select a Printing Command:")
        layout.addWidget(label)

        button_layout = QHBoxLayout()

        for template_name in self.template_manager.list_templates():
            button = QPushButton(template_name.capitalize())
            button.clicked.connect(lambda _, t=template_name: self.open_template_dialog(t))
            button_layout.addWidget(button)

        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.open_settings_dialog)
        button_layout.addWidget(settings_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def open_template_dialog(self, template_name: str) -> None:
        dialog = TemplateDialog(template_name, self.template_manager, self)
        dialog.exec()

    def open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self)
        dialog.exec()


class TemplateDialog(QDialog):
    def __init__(self, template_name: str, template_manager: TemplateManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.template_name = template_name
        self.template_manager = template_manager
        self.inputs: dict[str, Any] = {}
        self.setWindowTitle(f"Print {template_name.capitalize()}")
        self.init_ui()

    def init_ui(self) -> None:
        template = self.template_manager.get_template(self.template_name)
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        for var in template.get("variables", []):
            input_field = QTextEdit() if var.get("markdown", False) else QLineEdit()
            if isinstance(input_field, QTextEdit):
                input_field.setAcceptRichText(False)  # Ensure plain text only
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

    def print_template(self) -> None:
        template = self.template_manager.get_template(self.template_name)
        context = {}
        if self.template_name == "agenda":
            context = compute_agenda_variables()
        else:
            for var in template.get("variables", []):
                input_field = self.inputs[var["name"]]
                if isinstance(input_field, QTextEdit):
                    context[var["name"]] = input_field.toPlainText()
                else:
                    context[var["name"]] = input_field.text()
        try:
            ip_address = get_printer_ip()
            with ThermalPrinter(ip_address, self.template_manager) as printer:
                printer.print_template(self.template_name, context)
            QMessageBox.information(self, "Success", f"Printed using template '{self.template_name}'.")
            self.accept()
        except Exception as e:
            logger.error(f"Error printing template '{self.template_name}': {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to print: {e}")


class SettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.ip_input = QLineEdit()
        try:
            self.ip_input.setText(get_printer_ip())
        except ValueError:
            self.ip_input.setText("")
        form_layout.addRow("Printer IP Address:", self.ip_input)

        self.chars_per_line_input = QLineEdit()
        self.chars_per_line_input.setText(str(get_chars_per_line()))
        form_layout.addRow("Characters Per Line:", self.chars_per_line_input)

        self.enable_special_letters_input = QLineEdit()
        self.enable_special_letters_input.setText(str(get_enable_special_letters()))
        form_layout.addRow("Enable Special Letters (True/False):", self.enable_special_letters_input)

        self.check_for_updates_input = QLineEdit()
        self.check_for_updates_input.setText(str(get_check_for_updates()))
        form_layout.addRow("Check for Updates (True/False):", self.check_for_updates_input)

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

    def save_settings(self) -> None:
        ip_address = self.ip_input.text()
        set_printer_ip(ip_address)

        chars_per_line_value = self.chars_per_line_input.text()
        try:
            chars_per_line = int(chars_per_line_value)
            set_chars_per_line(chars_per_line)
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid number for chars per line.")
            return

        enable_special_letters_value = self.enable_special_letters_input.text()
        if enable_special_letters_value.lower() in ("true", "yes", "1"):
            enable_special_letters = True
        elif enable_special_letters_value.lower() in ("false", "no", "0"):
            enable_special_letters = False
        else:
            QMessageBox.critical(self, "Error", "Invalid value for enable special letters. Use True or False.")
            return
        set_enable_special_letters(enable_special_letters)

        check_for_updates_value = self.check_for_updates_input.text()
        if check_for_updates_value.lower() in ("true", "yes", "1"):
            check_for_updates = True
        elif check_for_updates_value.lower() in ("false", "no", "0"):
            check_for_updates = False
        else:
            QMessageBox.critical(self, "Error", "Invalid value for check for updates. Use True or False.")
            return
        set_check_for_updates(check_for_updates)

        QMessageBox.information(self, "Success", "Settings saved.")
        self.accept()


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
