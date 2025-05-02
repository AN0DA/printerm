import configparser
import os
from collections.abc import Callable
from typing import Any, TypeVar

from platformdirs import user_config_dir

CONFIG_FILE = os.path.join(user_config_dir("printerm", ensure_exists=True), "config.ini")

PRINT_TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "templates", "print_templates")

T = TypeVar("T")


def _get_config_value(
    section: str,
    option: str,
    getter: Callable[[configparser.ConfigParser, str, str], T],
    default: T,
    error_msg: str = "",
) -> T:
    """Generic function to get a config value with a specific getter function."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    try:
        return getter(config, section, option)
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        if error_msg:
            raise ValueError(error_msg) from e
        return default


def _set_config_value(section: str, option: str, value: Any) -> None:
    """Generic function to set a config value."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, option, str(value))
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)


def get_printer_ip() -> str:
    return _get_config_value(
        "Printer", "ip_address", lambda config, s, o: config.get(s, o), "", "Printer IP address not set"
    )


def set_printer_ip(ip_address: str) -> None:
    _set_config_value("Printer", "ip_address", ip_address)


def get_chars_per_line() -> int:
    return _get_config_value("Printer", "chars_per_line", lambda config, s, o: config.getint(s, o), 32)


def set_chars_per_line(chars_per_line: int) -> None:
    _set_config_value("Printer", "chars_per_line", chars_per_line)


def get_enable_special_letters() -> bool:
    return _get_config_value("Printer", "enable_special_letters", lambda config, s, o: config.getboolean(s, o), False)


def set_enable_special_letters(enable: bool) -> None:
    _set_config_value("Printer", "enable_special_letters", enable)


def get_check_for_updates() -> bool:
    return _get_config_value("Updates", "check_for_updates", lambda config, s, o: config.getboolean(s, o), True)


def set_check_for_updates(check: bool) -> None:
    _set_config_value("Updates", "check_for_updates", check)


def get_flask_port() -> int:
    return _get_config_value("Flask", "port", lambda config, s, o: config.getint(s, o), 5555)


def get_flask_secret_key() -> str:
    return _get_config_value("Flask", "secret_key", lambda config, s, o: config.get(s, o), "default_secret_key")


def set_flask_port(port: int) -> None:
    _set_config_value("Flask", "port", port)


def set_flask_secret_key(secret_key: str) -> None:
    _set_config_value("Flask", "secret_key", secret_key)
