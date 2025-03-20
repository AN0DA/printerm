# tests/test_config.py

import configparser
import os
from collections.abc import Generator

import pytest

from printerm import config

CONFIG_FILE = config.CONFIG_FILE


@pytest.fixture(autouse=True)
def setup_and_teardown() -> Generator[None, None, None]:
    # Setup: Ensure the config file is removed before each test
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    yield
    # Teardown: Remove the config file after each test
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)


def test_get_printer_ip_not_set() -> None:
    with pytest.raises(ValueError, match="Printer IP address not set"):
        config.get_printer_ip()


def test_set_and_get_printer_ip() -> None:
    config.set_printer_ip("192.168.1.100")
    assert config.get_printer_ip() == "192.168.1.100"


def test_get_chars_per_line_default() -> None:
    assert config.get_chars_per_line() == 32


def test_set_and_get_chars_per_line() -> None:
    config.set_chars_per_line(48)
    assert config.get_chars_per_line() == 48


def test_get_enable_special_letters_default() -> None:
    assert config.get_enable_special_letters() is False


def test_set_and_get_enable_special_letters() -> None:
    config.set_enable_special_letters(False)
    assert config.get_enable_special_letters() is False


# def test_get_flask_debug_default() -> None:
#     assert config.get_flask_debug() is False
#
#
# def test_set_and_get_flask_debug() -> None:
#     config.set_flask_debug(True)
#     assert config.get_flask_debug() is True
#
#
# def test_get_flask_secret_key_default() -> None:
#     assert config.get_flask_secret_key() == "default_secret_key"
#
#
# def test_set_and_get_flask_secret_key() -> None:
#     config.set_flask_secret_key("my_secret_key")
#     assert config.get_flask_secret_key() == "my_secret_key"


def test_corrupted_config_file() -> None:
    # Write invalid content to the config file
    with open(CONFIG_FILE, "w") as f:
        f.write("Invalid Content")
    # Test that exceptions are raised for all getters
    with pytest.raises(configparser.Error):
        config.get_printer_ip()
    with pytest.raises(configparser.Error):
        config.get_chars_per_line()
    with pytest.raises(configparser.Error):
        config.get_enable_special_letters()
