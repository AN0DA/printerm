from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from flask.testing import FlaskClient

from printerm.interfaces.web import app


@pytest.fixture
def client() -> Generator[FlaskClient]:
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_printer() -> Generator[MagicMock]:
    with patch("printerm.interfaces.web.ThermalPrinter") as mock_printer_class:
        yield mock_printer_class


@pytest.fixture
def mock_get_printer_ip() -> Generator[None]:
    with patch("printerm.interfaces.web.get_printer_ip", return_value="192.168.1.100"):
        yield


def test_index_route(client: FlaskClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome to the Thermal Printer Application" in response.data
    assert b"Settings" in response.data


def test_print_template_route_get(client: FlaskClient) -> None:
    with patch("printerm.interfaces.web.template_manager") as mock_template_manager:
        mock_template_manager.get_template.return_value = {"name": "Sample", "variables": [], "segments": []}
        response = client.get("/print/sample")
        assert response.status_code == 200
        assert b"Print" in response.data


def test_print_template_route_post(client: FlaskClient, mock_printer: MagicMock, mock_get_printer_ip: None) -> None:
    with patch("printerm.interfaces.web.template_manager") as mock_template_manager:
        mock_template_manager.get_template.return_value = {
            "name": "Sample",
            "variables": [{"name": "title", "description": "Title"}],
            "segments": [{"text": "{{ title }}", "styles": {}}],
        }
        data = {"title": "Test Title"}
        response = client.post("/print/sample", data=data, follow_redirects=True)
        assert response.status_code == 200
        assert mock_printer.return_value.__enter__.return_value.print_template.called


def test_settings_route_get(client: FlaskClient) -> None:
    with (
        patch("printerm.interfaces.web.get_printer_ip", return_value="192.168.1.100"),
        patch("printerm.interfaces.web.get_chars_per_line", return_value=32),
        patch("printerm.interfaces.web.get_enable_special_letters", return_value=True),
        patch("printerm.interfaces.web.get_check_for_updates", return_value=True),
    ):
        response = client.get("/settings")
        assert response.status_code == 200
        assert b"192.168.1.100" in response.data
        assert b"32" in response.data
        assert b"True" in response.data


def test_settings_route_post(client: FlaskClient) -> None:
    data = {
        "ip_address": "192.168.1.101",
        "chars_per_line": "48",
        "enable_special_letters": "False",
        "check_for_updates": "True",
    }
    with (
        patch("printerm.interfaces.web.set_printer_ip") as mock_set_ip,
        patch("printerm.interfaces.web.set_chars_per_line") as mock_set_chars,
        patch("printerm.interfaces.web.set_enable_special_letters") as mock_set_enable,
        patch("printerm.interfaces.web.set_check_for_updates") as mock_set_check,
    ):
        response = client.post("/settings", data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b"Settings saved." in response.data
        mock_set_ip.assert_called_with("192.168.1.101")
        mock_set_chars.assert_called_with(48)
        mock_set_enable.assert_called_with(False)
        mock_set_check.assert_called_with(True)
