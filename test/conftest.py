"""Test configuration and fixtures."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import yaml


@pytest.fixture
def temp_config_dir() -> Generator[str]:
    """Create a temporary directory for config files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_template_dir() -> Generator[str]:
    """Create a temporary directory for template files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a sample template file
        template_data = {
            "name": "Test Template",
            "description": "A test template",
            "variables": [
                {"name": "title", "description": "Title text", "required": True, "type": "string"},
                {"name": "content", "description": "Content text", "required": False, "type": "string"},
            ],
            "segments": [{"text": "{{ title }}\n{{ content }}", "styles": {"bold": True, "align": "center"}}],
        }

        template_path = Path(temp_dir) / "test_template.yaml"
        with open(template_path, "w") as f:
            yaml.dump(template_data, f)

        # Create a template with script
        script_template_data = {
            "name": "Script Template",
            "description": "Template with script",
            "script": "test_script",
            "segments": [{"text": "Generated: {{ generated_content }}", "styles": {"bold": False}}],
        }

        script_template_path = Path(temp_dir) / "script_template.yaml"
        with open(script_template_path, "w") as f:
            yaml.dump(script_template_data, f)

        # Create a markdown template
        markdown_template_data = {
            "name": "Markdown Template",
            "description": "Template with markdown",
            "segments": [{"text": "# {{ title }}\n\n**{{ content }}**", "markdown": True, "styles": {}}],
        }

        markdown_template_path = Path(temp_dir) / "markdown_template.yaml"
        with open(markdown_template_path, "w") as f:
            yaml.dump(markdown_template_data, f)

        yield temp_dir


@pytest.fixture
def sample_config_data() -> dict[str, Any]:
    """Sample configuration data for testing."""
    return {
        "Printer": {"ip_address": "192.168.1.100", "chars_per_line": "48", "enable_special_letters": "True"},
        "Updates": {"check_for_updates": "False"},
        "Flask": {"port": "8080", "secret_key": "test_secret_key"},
        "GUI": {"recent_templates": "template1,template2,template3"},
    }


@pytest.fixture
def mock_config_service() -> MagicMock:
    """Mock configuration service for testing."""
    mock = MagicMock()
    mock.get_printer_ip.return_value = "192.168.1.100"
    mock.get_chars_per_line.return_value = 32
    mock.get_enable_special_letters.return_value = False
    mock.get_check_for_updates.return_value = True
    mock.get_flask_port.return_value = 5555
    mock.get_flask_secret_key.return_value = "test_secret"
    mock.get_gui_recent_templates.return_value = ["template1", "template2"]
    return mock


@pytest.fixture
def mock_template_service() -> MagicMock:
    """Mock template service for testing."""
    mock = MagicMock()
    mock.get_template.return_value = {"name": "Test Template", "segments": [{"text": "Test content", "styles": {}}]}
    mock.list_templates.return_value = ["test_template", "another_template"]
    mock.render_template.return_value = [{"text": "Rendered content", "styles": {"bold": True}}]
    return mock


@pytest.fixture
def mock_printer() -> MagicMock:
    """Mock printer for testing."""
    mock = MagicMock()
    return mock


@pytest.fixture
def sample_context() -> dict[str, Any]:
    """Sample template context for testing."""
    return {
        "title": "Test Title",
        "content": "Test content here",
        "date": "2025-06-30",
        "items": ["Item 1", "Item 2", "Item 3"],
    }


@pytest.fixture
def sample_segments() -> list[dict[str, Any]]:
    """Sample print segments for testing."""
    return [
        {"text": "Header Text", "styles": {"bold": True, "align": "center"}},
        {"text": "Body content with multiple lines\nSecond line here", "styles": {"bold": False, "align": "left"}},
        {"text": "Footer", "styles": {"underline": True, "align": "center"}},
    ]


@pytest.fixture
def mock_requests_response() -> MagicMock:
    """Mock requests response for testing."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"info": {"version": "2.0.0"}}
    return mock


def pytest_configure(config: Any) -> None:
    import logging

    logging.basicConfig(level=logging.DEBUG)
    os.environ.setdefault("PYTEST_DISABLE_NETWORK", "1")
