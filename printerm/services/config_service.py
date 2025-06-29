"""Configuration service implementation."""

import configparser
import os

from platformdirs import user_config_dir

from printerm.exceptions import ConfigurationError

CONFIG_FILE = os.path.join(user_config_dir("printerm", ensure_exists=True), "config.ini")


class ConfigServiceImpl:
    """Configuration service implementation."""

    def __init__(self, config_file: str = CONFIG_FILE) -> None:
        self.config_file = config_file

    def _get_config(self) -> configparser.ConfigParser:
        """Get configuration parser instance."""
        config = configparser.ConfigParser()
        config.read(self.config_file)
        return config

    def _save_config(self, config: configparser.ConfigParser) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as configfile:
                config.write(configfile)
        except Exception as e:
            raise ConfigurationError("Failed to save configuration", str(e)) from e

    def get_printer_ip(self) -> str:
        """Get printer IP address from configuration."""
        config = self._get_config()
        try:
            return config.get("Printer", "ip_address")
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            raise ConfigurationError("Printer IP address not set") from e

    def set_printer_ip(self, ip_address: str) -> None:
        """Set printer IP address in configuration."""
        config = self._get_config()
        if not config.has_section("Printer"):
            config.add_section("Printer")
        config.set("Printer", "ip_address", ip_address)
        self._save_config(config)

    def get_chars_per_line(self) -> int:
        """Get characters per line from configuration."""
        config = self._get_config()
        try:
            return config.getint("Printer", "chars_per_line")
        except (configparser.NoSectionError, configparser.NoOptionError):
            return 32  # Default value

    def set_chars_per_line(self, chars_per_line: int) -> None:
        """Set characters per line in configuration."""
        if chars_per_line <= 0:
            raise ConfigurationError("Characters per line must be positive")
        config = self._get_config()
        if not config.has_section("Printer"):
            config.add_section("Printer")
        config.set("Printer", "chars_per_line", str(chars_per_line))
        self._save_config(config)

    def get_enable_special_letters(self) -> bool:
        """Get enable special letters setting from configuration."""
        config = self._get_config()
        try:
            return config.getboolean("Printer", "enable_special_letters")
        except (configparser.NoSectionError, configparser.NoOptionError):
            return False  # Default value

    def set_enable_special_letters(self, enable: bool) -> None:
        """Set enable special letters in configuration."""
        config = self._get_config()
        if not config.has_section("Printer"):
            config.add_section("Printer")
        config.set("Printer", "enable_special_letters", str(enable))
        self._save_config(config)

    def get_check_for_updates(self) -> bool:
        """Get check for updates setting from configuration."""
        config = self._get_config()
        try:
            return config.getboolean("Updates", "check_for_updates")
        except (configparser.NoSectionError, configparser.NoOptionError):
            return True  # Default value

    def set_check_for_updates(self, check: bool) -> None:
        """Set check for updates in configuration."""
        config = self._get_config()
        if not config.has_section("Updates"):
            config.add_section("Updates")
        config.set("Updates", "check_for_updates", str(check))
        self._save_config(config)

    def get_flask_port(self) -> int:
        """Get Flask port from configuration."""
        config = self._get_config()
        try:
            return config.getint("Flask", "port")
        except (configparser.NoSectionError, configparser.NoOptionError):
            return 5555  # Default value

    def get_flask_secret_key(self) -> str:
        """Get Flask secret key from configuration."""
        config = self._get_config()
        try:
            return config.get("Flask", "secret_key")
        except (configparser.NoSectionError, configparser.NoOptionError):
            return "default_secret_key"  # Default value

    def set_flask_port(self, port: int) -> None:
        """Set Flask port in configuration."""
        if port <= 0 or port > 65535:
            raise ConfigurationError("Port must be between 1 and 65535")
        config = self._get_config()
        if not config.has_section("Flask"):
            config.add_section("Flask")
        config.set("Flask", "port", str(port))
        self._save_config(config)

    def set_flask_secret_key(self, secret_key: str) -> None:
        """Set Flask secret key in configuration."""
        if not secret_key:
            raise ConfigurationError("Secret key cannot be empty")
        config = self._get_config()
        if not config.has_section("Flask"):
            config.add_section("Flask")
        config.set("Flask", "secret_key", secret_key)
        self._save_config(config)

    def get_gui_recent_templates(self) -> list[str]:
        """Get recent templates from configuration."""
        config = self._get_config()
        try:
            templates_str = config.get("GUI", "recent_templates")
            if templates_str.strip():
                return [t.strip() for t in templates_str.split(",") if t.strip()]
            return []
        except (configparser.NoSectionError, configparser.NoOptionError):
            return []  # Default value

    def set_gui_recent_templates(self, templates: list[str]) -> None:
        """Set recent templates in configuration."""
        config = self._get_config()
        if not config.has_section("GUI"):
            config.add_section("GUI")
        # Store as comma-separated string
        templates_str = ",".join(templates[:5])  # Limit to 5 templates
        config.set("GUI", "recent_templates", templates_str)
        self._save_config(config)
