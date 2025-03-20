from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from printerm.printer import ThermalPrinter
from printerm.template_manager import TemplateManager


@pytest.fixture
def mock_network_printer() -> Generator[MagicMock, None, None]:
    with patch("printerm.printer.Network") as mock_network:
        yield mock_network


@pytest.fixture
def template_manager(tmp_path: Path) -> TemplateManager:
    # Set up a temporary template manager
    templates_path = tmp_path / "print_templates"
    templates_path.mkdir()
    manager = TemplateManager(str(templates_path))
    return manager


def test_printer_context_management(mock_network_printer: MagicMock, template_manager: TemplateManager) -> None:
    with ThermalPrinter("192.168.1.100", template_manager) as printer:
        assert printer.printer is not None
    # Ensure the printer connection is closed
    assert mock_network_printer.return_value.close.called


def test_print_template(mock_network_printer: MagicMock, template_manager: TemplateManager) -> None:
    # Create a sample template
    template_content = """
name: Test Template
description: A test template
variables: []
segments:
  - text: "Hello, World!"
    markdown: false
    styles:
      bold: true
"""
    template_file = template_manager.template_dir + "/test_template.yaml"
    with open(template_file, "w", encoding="utf-8") as f:
        f.write(template_content)
    template_manager.templates = template_manager.load_templates()

    with ThermalPrinter("192.168.1.100", template_manager) as printer:
        printer.print_template("test_template", {})
        # Ensure print_segments is called with correct segments
        mock_printer_instance = mock_network_printer.return_value
        mock_printer_instance.set.assert_has_calls(
            [
                call(
                    align="left",
                    font="a",
                    bold=True,
                    underline=False,
                    invert=False,
                    double_width=False,
                    double_height=False,
                ),
                call(
                    align="left",
                    font="a",
                    bold=False,
                    underline=False,
                    invert=False,
                    double_width=False,
                    double_height=False,
                ),
            ]
        )
        mock_printer_instance.text.assert_called_with("Hello, World!")
        assert mock_printer_instance.cut.called


def test_printer_connection_error(template_manager: TemplateManager) -> None:
    # Simulate a connection error
    with (
        patch("printerm.printer.Network", side_effect=Exception("Connection error")),
        pytest.raises(Exception, match="Connection error"),
        ThermalPrinter("192.168.1.100", template_manager),
    ):
        pass
