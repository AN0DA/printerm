"""Test utilities and helpers."""

import configparser
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import yaml


def create_test_config_file(config_data: dict[str, dict[str, str]], temp_dir: str) -> str:
    """Create a test configuration file with the given data.

    Args:
        config_data: Dictionary of section -> {key: value} mappings
        temp_dir: Temporary directory to create the file in

    Returns:
        Path to the created config file
    """
    config_file = Path(temp_dir) / "test_config.ini"
    config = configparser.ConfigParser()

    for section, options in config_data.items():
        config.add_section(section)
        for key, value in options.items():
            config.set(section, key, value)

    with open(config_file, "w") as f:
        config.write(f)

    return str(config_file)


def create_test_template_file(template_data: dict[str, Any], temp_dir: str, filename: str) -> str:
    """Create a test template file with the given data.

    Args:
        template_data: Template data dictionary
        temp_dir: Temporary directory to create the file in
        filename: Name of the template file (without extension)

    Returns:
        Path to the created template file
    """
    template_file = Path(temp_dir) / f"{filename}.yaml"

    with open(template_file, "w") as f:
        yaml.dump(template_data, f)

    return str(template_file)


def create_mock_printer() -> MagicMock:
    """Create a mock printer with common methods.

    Returns:
        Mock printer object
    """
    mock_printer = MagicMock()
    mock_printer.set_with_default = MagicMock()
    mock_printer.text = MagicMock()
    mock_printer.set = MagicMock()
    mock_printer.cut = MagicMock()
    mock_printer.close = MagicMock()
    return mock_printer


def create_mock_config_service(overrides: dict[str, Any] | None = None) -> MagicMock:
    """Create a mock config service with default values.

    Args:
        overrides: Dictionary of method_name -> return_value overrides

    Returns:
        Mock config service
    """
    mock = MagicMock()

    # Set default return values
    mock.get_printer_ip.return_value = "192.168.1.100"
    mock.get_chars_per_line.return_value = 32
    mock.get_enable_special_letters.return_value = False
    mock.get_check_for_updates.return_value = True
    mock.get_flask_port.return_value = 5555
    mock.get_flask_secret_key.return_value = "test_secret"
    mock.get_gui_recent_templates.return_value = []

    # Apply overrides
    if overrides:
        for method_name, return_value in overrides.items():
            getattr(mock, method_name).return_value = return_value

    return mock


def create_mock_template_service(overrides: dict[str, Any] | None = None) -> MagicMock:
    """Create a mock template service with default values.

    Args:
        overrides: Dictionary of method_name -> return_value overrides

    Returns:
        Mock template service
    """
    mock = MagicMock()

    # Set default return values
    mock.get_template.return_value = {"name": "Test Template", "segments": [{"text": "Test content", "styles": {}}]}
    mock.list_templates.return_value = ["test_template"]
    mock.render_template.return_value = [{"text": "Rendered content", "styles": {"bold": True}}]
    mock.get_template_variables.return_value = []
    mock.has_script.return_value = False
    mock.get_script_info.return_value = None
    mock.list_available_scripts.return_value = {}

    # Apply overrides
    if overrides:
        for method_name, return_value in overrides.items():
            getattr(mock, method_name).return_value = return_value

    return mock


def assert_mock_called_with_any_of(mock_method: MagicMock, expected_calls: list) -> None:
    """Assert that a mock method was called with any of the expected call arguments.

    Args:
        mock_method: The mock method to check
        expected_calls: List of expected call arguments

    Raises:
        AssertionError: If the method was not called with any of the expected arguments
    """
    actual_calls = mock_method.call_args_list

    for expected_call in expected_calls:
        if expected_call in actual_calls:
            return

    raise AssertionError(
        f"Expected method to be called with any of {expected_calls}, but actual calls were: {actual_calls}"
    )


def assert_config_file_contains(config_file: str, section: str, key: str, expected_value: str) -> None:
    """Assert that a config file contains the expected value.

    Args:
        config_file: Path to the config file
        section: Config section name
        key: Config key name
        expected_value: Expected value

    Raises:
        AssertionError: If the config file doesn't contain the expected value
    """
    config = configparser.ConfigParser()
    config.read(config_file)

    if not config.has_section(section):
        raise AssertionError(f"Config file {config_file} does not have section '{section}'")

    if not config.has_option(section, key):
        raise AssertionError(f"Config file {config_file} section '{section}' does not have option '{key}'")

    actual_value = config.get(section, key)
    if actual_value != expected_value:
        raise AssertionError(
            f"Config file {config_file} section '{section}' key '{key}' "
            f"has value '{actual_value}', expected '{expected_value}'"
        )


def get_sample_template_data() -> dict[str, Any]:
    """Get sample template data for testing.

    Returns:
        Dictionary containing sample template data
    """
    return {
        "name": "Sample Template",
        "description": "A sample template for testing",
        "variables": [
            {"name": "title", "description": "Title text", "required": True, "type": "string"},
            {"name": "content", "description": "Content text", "required": False, "type": "string"},
        ],
        "segments": [{"text": "{{ title }}\n---\n{{ content }}", "styles": {"bold": True, "align": "center"}}],
    }


def get_sample_context_data() -> dict[str, Any]:
    """Get sample context data for testing.

    Returns:
        Dictionary containing sample context data
    """
    return {
        "title": "Test Title",
        "content": "This is test content",
        "date": "2025-06-30",
        "items": ["Item 1", "Item 2", "Item 3"],
        "user": "Test User",
    }
