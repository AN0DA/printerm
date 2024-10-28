import configparser

CONFIG_FILE = "tp_config.ini"


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


def get_flask_port() -> int:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    try:
        return config.getint("Flask", "port")
    except (configparser.NoSectionError, configparser.NoOptionError):
        return 5555


def get_flask_debug() -> bool:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    try:
        return config.getboolean("Flask", "debug")
    except (configparser.NoSectionError, configparser.NoOptionError):
        return False


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


def set_flask_debug(debug: bool) -> None:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    if not config.has_section("Flask"):
        config.add_section("Flask")
    config.set("Flask", "debug", str(debug))
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
