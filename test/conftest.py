from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from flask.testing import FlaskClient
from typer.testing import CliRunner

from printerm.template_manager import TemplateManager
from printerm.web_app import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_network_printer() -> Generator[MagicMock, None, None]:
    with patch("printerm.printer.Network") as mock_network:
        yield mock_network


@pytest.fixture
def template_manager(tmp_path: Path) -> TemplateManager:
    templates_path = tmp_path / "print_templates"
    templates_path.mkdir()
    manager = TemplateManager(str(templates_path))
    return manager


@pytest.fixture
def mock_printer() -> Generator[MagicMock, None, None]:
    with patch("printerm.app.ThermalPrinter") as mock_printer_class:
        yield mock_printer_class


@pytest.fixture
def mock_get_printer_ip() -> Generator[None, None, None]:
    with patch("printerm.app.get_printer_ip", return_value="192.168.1.100"):
        yield


@pytest.fixture
def mock_template_manager(tmp_path: Path) -> TemplateManager:
    with patch("printerm.app.TemplateManager") as mock_manager_class:
        mock_manager = mock_manager_class.return_value
        mock_manager.template_dir = str(tmp_path)
        return mock_manager
