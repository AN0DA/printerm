"""Tests for configuration service."""

import configparser
import os

import pytest

from printerm.exceptions import ConfigurationError
from printerm.services.config_service import ConfigServiceImpl


class TestConfigServiceImpl:
    """Test cases for ConfigServiceImpl."""

    def test_init_with_default_config_file(self) -> None:
        """Test initialization with default config file."""
        service = ConfigServiceImpl()
        assert service.config_file is not None
        assert "config.ini" in service.config_file

    def test_init_with_custom_config_file(self) -> None:
        """Test initialization with custom config file."""
        custom_file = "/custom/path/config.ini"
        service = ConfigServiceImpl(custom_file)
        assert service.config_file == custom_file

    def test_get_config_creates_config_parser(self, temp_config_dir: str) -> None:
        """Test that _get_config creates a ConfigParser instance."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)
        config = service._get_config()
        assert isinstance(config, configparser.ConfigParser)

    def test_save_config_writes_to_file(self, temp_config_dir: str) -> None:
        """Test that _save_config writes configuration to file."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        config = configparser.ConfigParser()
        config.add_section("Test")
        config.set("Test", "key", "value")

        service._save_config(config)

        # Verify file was created and content is correct
        assert os.path.exists(config_file)
        saved_config = configparser.ConfigParser()
        saved_config.read(config_file)
        assert saved_config.get("Test", "key") == "value"

    def test_save_config_handles_write_error(self, temp_config_dir: str) -> None:
        """Test that _save_config handles write errors."""
        # Use a directory path as file path to trigger error
        config_file = temp_config_dir  # This is a directory, not a file
        service = ConfigServiceImpl(config_file)

        config = configparser.ConfigParser()

        with pytest.raises(ConfigurationError, match="Failed to save configuration"):
            service._save_config(config)

    def test_get_printer_ip_success(self, temp_config_dir: str, sample_config_data: dict) -> None:
        """Test successful retrieval of printer IP address."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        self._create_config_file(config_file, sample_config_data)

        service = ConfigServiceImpl(config_file)
        ip = service.get_printer_ip()

        assert ip == "192.168.1.100"

    def test_get_printer_ip_missing_section(self, temp_config_dir: str) -> None:
        """Test error when Printer section is missing."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        with pytest.raises(ConfigurationError, match="Printer IP address not set"):
            service.get_printer_ip()

    def test_get_printer_ip_missing_option(self, temp_config_dir: str) -> None:
        """Test error when ip_address option is missing."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        config_data: dict[str, dict[str, str]] = {"Printer": {}}
        self._create_config_file(config_file, config_data)

        service = ConfigServiceImpl(config_file)

        with pytest.raises(ConfigurationError, match="Printer IP address not set"):
            service.get_printer_ip()

    def test_set_printer_ip_new_section(self, temp_config_dir: str) -> None:
        """Test setting printer IP creates new section if needed."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        service.set_printer_ip("192.168.1.200")

        config = configparser.ConfigParser()
        config.read(config_file)
        assert config.get("Printer", "ip_address") == "192.168.1.200"

    def test_set_printer_ip_existing_section(self, temp_config_dir: str, sample_config_data: dict) -> None:
        """Test setting printer IP in existing section."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        self._create_config_file(config_file, sample_config_data)

        service = ConfigServiceImpl(config_file)
        service.set_printer_ip("192.168.1.201")

        config = configparser.ConfigParser()
        config.read(config_file)
        assert config.get("Printer", "ip_address") == "192.168.1.201"

    def test_get_chars_per_line_success(self, temp_config_dir: str, sample_config_data: dict) -> None:
        """Test successful retrieval of chars per line."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        self._create_config_file(config_file, sample_config_data)

        service = ConfigServiceImpl(config_file)
        chars = service.get_chars_per_line()

        assert chars == 48

    def test_get_chars_per_line_default(self, temp_config_dir: str) -> None:
        """Test default value when chars per line is not set."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        chars = service.get_chars_per_line()

        assert chars == 32  # Default value

    def test_set_chars_per_line_valid(self, temp_config_dir: str) -> None:
        """Test setting valid chars per line."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        service.set_chars_per_line(40)

        config = configparser.ConfigParser()
        config.read(config_file)
        assert config.getint("Printer", "chars_per_line") == 40

    def test_set_chars_per_line_invalid(self, temp_config_dir: str) -> None:
        """Test error when setting invalid chars per line."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        with pytest.raises(ConfigurationError, match="Characters per line must be positive"):
            service.set_chars_per_line(0)

        with pytest.raises(ConfigurationError, match="Characters per line must be positive"):
            service.set_chars_per_line(-5)

    def test_get_enable_special_letters_success(self, temp_config_dir: str, sample_config_data: dict) -> None:
        """Test successful retrieval of enable special letters setting."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        self._create_config_file(config_file, sample_config_data)

        service = ConfigServiceImpl(config_file)
        enable = service.get_enable_special_letters()

        assert enable is True

    def test_get_enable_special_letters_default(self, temp_config_dir: str) -> None:
        """Test default value for enable special letters."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        enable = service.get_enable_special_letters()

        assert enable is False  # Default value

    def test_set_enable_special_letters(self, temp_config_dir: str) -> None:
        """Test setting enable special letters."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        service.set_enable_special_letters(True)

        config = configparser.ConfigParser()
        config.read(config_file)
        assert config.getboolean("Printer", "enable_special_letters") is True

    def test_get_check_for_updates_success(self, temp_config_dir: str, sample_config_data: dict) -> None:
        """Test successful retrieval of check for updates setting."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        self._create_config_file(config_file, sample_config_data)

        service = ConfigServiceImpl(config_file)
        check = service.get_check_for_updates()

        assert check is False

    def test_get_check_for_updates_default(self, temp_config_dir: str) -> None:
        """Test default value for check for updates."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        check = service.get_check_for_updates()

        assert check is True  # Default value

    def test_set_check_for_updates(self, temp_config_dir: str) -> None:
        """Test setting check for updates."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        service.set_check_for_updates(False)

        config = configparser.ConfigParser()
        config.read(config_file)
        assert config.getboolean("Updates", "check_for_updates") is False

    def test_get_flask_port_success(self, temp_config_dir: str, sample_config_data: dict) -> None:
        """Test successful retrieval of Flask port."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        self._create_config_file(config_file, sample_config_data)

        service = ConfigServiceImpl(config_file)
        port = service.get_flask_port()

        assert port == 8080

    def test_get_flask_port_default(self, temp_config_dir: str) -> None:
        """Test default value for Flask port."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        port = service.get_flask_port()

        assert port == 5555  # Default value

    def test_get_flask_secret_key_success(self, temp_config_dir: str, sample_config_data: dict) -> None:
        """Test successful retrieval of Flask secret key."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        self._create_config_file(config_file, sample_config_data)

        service = ConfigServiceImpl(config_file)
        key = service.get_flask_secret_key()

        assert key == "test_secret_key"

    def test_get_flask_secret_key_default(self, temp_config_dir: str) -> None:
        """Test default value for Flask secret key."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        key = service.get_flask_secret_key()

        assert key == "default_secret_key"  # Default value

    def test_set_flask_port_valid(self, temp_config_dir: str) -> None:
        """Test setting valid Flask port."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        service.set_flask_port(8080)

        config = configparser.ConfigParser()
        config.read(config_file)
        assert config.getint("Flask", "port") == 8080

    def test_set_flask_port_invalid(self, temp_config_dir: str) -> None:
        """Test error when setting invalid Flask port."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        with pytest.raises(ConfigurationError, match="Port must be between 1 and 65535"):
            service.set_flask_port(0)

        with pytest.raises(ConfigurationError, match="Port must be between 1 and 65535"):
            service.set_flask_port(70000)

    def test_set_flask_secret_key_valid(self, temp_config_dir: str) -> None:
        """Test setting valid Flask secret key."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        service.set_flask_secret_key("my_secret_key")

        config = configparser.ConfigParser()
        config.read(config_file)
        assert config.get("Flask", "secret_key") == "my_secret_key"

    def test_set_flask_secret_key_empty(self, temp_config_dir: str) -> None:
        """Test error when setting empty Flask secret key."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        with pytest.raises(ConfigurationError, match="Secret key cannot be empty"):
            service.set_flask_secret_key("")

    def test_get_gui_recent_templates_success(self, temp_config_dir: str, sample_config_data: dict) -> None:
        """Test successful retrieval of GUI recent templates."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        self._create_config_file(config_file, sample_config_data)

        service = ConfigServiceImpl(config_file)
        templates = service.get_gui_recent_templates()

        assert templates == ["template1", "template2", "template3"]

    def test_get_gui_recent_templates_empty(self, temp_config_dir: str) -> None:
        """Test empty recent templates list."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        config_data = {"GUI": {"recent_templates": ""}}
        self._create_config_file(config_file, config_data)

        service = ConfigServiceImpl(config_file)
        templates = service.get_gui_recent_templates()

        assert templates == []

    def test_get_gui_recent_templates_default(self, temp_config_dir: str) -> None:
        """Test default value for GUI recent templates."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        templates = service.get_gui_recent_templates()

        assert templates == []  # Default value

    def test_set_gui_recent_templates(self, temp_config_dir: str) -> None:
        """Test setting GUI recent templates."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        templates = ["template_a", "template_b", "template_c"]
        service.set_gui_recent_templates(templates)

        config = configparser.ConfigParser()
        config.read(config_file)
        stored_templates = config.get("GUI", "recent_templates")
        assert stored_templates == "template_a,template_b,template_c"

    def test_set_gui_recent_templates_limit_to_five(self, temp_config_dir: str) -> None:
        """Test that recent templates are limited to 5 items."""
        config_file = os.path.join(temp_config_dir, "test_config.ini")
        service = ConfigServiceImpl(config_file)

        templates = ["t1", "t2", "t3", "t4", "t5", "t6", "t7"]
        service.set_gui_recent_templates(templates)

        config = configparser.ConfigParser()
        config.read(config_file)
        stored_templates = config.get("GUI", "recent_templates")
        assert stored_templates == "t1,t2,t3,t4,t5"

    def _create_config_file(self, config_file: str, config_data: dict) -> None:
        """Helper method to create config file with test data."""
        config = configparser.ConfigParser()
        for section, options in config_data.items():
            config.add_section(section)
            for key, value in options.items():
                config.set(section, key, value)

        with open(config_file, "w") as f:
            config.write(f)
