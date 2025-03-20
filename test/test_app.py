from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from printerm.app import app

runner = CliRunner()


@pytest.fixture
def mock_printer() -> Generator[MagicMock, None, None]:
    with patch("printerm.app.ThermalPrinter") as mock_printer_class:
        yield mock_printer_class


@pytest.fixture
def mock_get_printer_ip() -> Generator[None, None, None]:
    with patch("printerm.app.get_printer_ip", return_value="192.168.1.100"):
        yield


def test_print_template_command(mock_printer: MagicMock, mock_get_printer_ip: None) -> None:
    with patch("printerm.app.TemplateManager") as mock_template_manager:
        mock_template_manager.return_value.get_template.return_value = {
            "name": "Sample",
            "variables": [{"name": "title", "description": "Title"}],
            "segments": [{"text": "{{ title }}", "styles": {}}],
        }
        result = runner.invoke(app, ["print-template", "sample"], input="Test Title")
        assert result.exit_code == 0
        assert "Printed using template 'sample'." in result.output
        assert mock_printer.return_value.__enter__.return_value.print_template.called


def test_update_command(mocker: MagicMock) -> None:
    mock_subprocess = mocker.patch("printerm.app.subprocess.check_call")
    result = runner.invoke(app, ["update"])
    assert result.exit_code == 0
    mock_subprocess.assert_called_with(
        [mocker.ANY, "-m", "pip", "install", "--upgrade", "git+https://github.com/AN0DA/printerm.git"]
    )
    assert "Application updated successfully." in result.output


def test_set_check_for_updates_command() -> None:
    result = runner.invoke(app, ["settings", "set-check-for-updates", "False"])
    assert result.exit_code == 0
    assert "Check for updates set to False" in result.output
