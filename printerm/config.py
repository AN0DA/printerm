import configparser
import os

from platformdirs import user_config_dir

CONFIG_FILE = os.path.join(user_config_dir("printerm", ensure_exists=True), "config.ini")

PRINT_TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), "print_templates")


def get_printer_ip() -> str:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    try:
        return config.get("Printer", "ip_address")
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        raise ValueError("Printer IP address not set") from e


def set_printer_ip(ip_address: str) -> None:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if not config.has_section("Printer"):
        config.add_section("Printer")
    config.set("Printer", "ip_address", ip_address)
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)


def get_chars_per_line() -> int:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    try:
        return config.getint("Printer", "chars_per_line")
    except (configparser.NoSectionError, configparser.NoOptionError):
        return 32


def set_chars_per_line(chars_per_line: int) -> None:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if not config.has_section("Printer"):
        config.add_section("Printer")
    config.set("Printer", "chars_per_line", str(chars_per_line))
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)


def get_enable_special_letters() -> bool:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    try:
        return config.getboolean("Printer", "enable_special_letters")
    except (configparser.NoSectionError, configparser.NoOptionError):
        return False


def set_enable_special_letters(enable: bool) -> None:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if not config.has_section("Printer"):
        config.add_section("Printer")
    config.set("Printer", "enable_special_letters", str(enable))
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)


def get_check_for_updates() -> bool:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    try:
        return config.getboolean("Updates", "check_for_updates")
    except (configparser.NoSectionError, configparser.NoOptionError):
        return True  # Default to True


def set_check_for_updates(check: bool) -> None:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if not config.has_section("Updates"):
        config.add_section("Updates")
    config.set("Updates", "check_for_updates", str(check))
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)


def get_flask_port() -> int:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    try:
        return config.getint("Flask", "port")
    except (configparser.NoSectionError, configparser.NoOptionError):
        return 5555


def get_flask_secret_key() -> str:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    try:
        return config.get("Flask", "secret_key")
    except (configparser.NoSectionError, configparser.NoOptionError):
        return "default_secret_key"


def set_flask_port(port: int) -> None:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if not config.has_section("Flask"):
        config.add_section("Flask")
    config.set("Flask", "port", str(port))
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)


def set_flask_secret_key(secret_key: str) -> None:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if not config.has_section("Flask"):
        config.add_section("Flask")
    config.set("Flask", "secret_key", secret_key)
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)
