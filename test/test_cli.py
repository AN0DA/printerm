"""Tests for CLI interface."""

from unittest.mock import MagicMock, Mock, patch

import typer.testing

from printerm.exceptions import ConfigurationError, PrintermError
from printerm.interfaces.cli import app, display_template_list, suggest_similar_templates


class TestCLI:
    """Test cases for CLI interface."""

    def setup_method(self) -> None:
        """Set up test environment before each test."""
        self.runner = typer.testing.CliRunner()

    @patch("printerm.interfaces.cli.config_service")
    @patch("printerm.interfaces.cli.service_container")
    def test_main_callback_first_time_user(self, mock_container: MagicMock, mock_config_service: MagicMock) -> None:
        """Test main callback behavior for first-time users."""
        # Mock config service to raise ConfigurationError
        mock_config_service.get_printer_ip.side_effect = ConfigurationError("No printer configured")

        result = self.runner.invoke(app, [])

        assert result.exit_code == 0
        assert "Welcome to Printerm!" in result.stdout
        assert "printerm setup init" in result.stdout
        assert "first time" in result.stdout

    @patch("printerm.interfaces.cli.config_service")
    def test_main_callback_existing_user(self, mock_config: MagicMock) -> None:
        """Test main callback behavior for existing users."""
        # Mock config service to return valid IP
        mock_config.get_printer_ip.return_value = "192.168.1.100"

        # Run the main command without subcommand (should invoke status)
        result = self.runner.invoke(app, [])

        # Should show status information and not show first-time user message
        assert result.exit_code == 0
        assert "Printerm Status" in result.stdout
        assert "first time" not in result.stdout

    def test_suggest_similar_templates_found(self) -> None:
        """Test template suggestion with close matches."""
        available = ["agenda", "task", "ticket", "small_note"]

        suggestion = suggest_similar_templates("agend", available)
        assert suggestion == "agenda"

        suggestion = suggest_similar_templates("tak", available)
        assert suggestion == "task"

    def test_suggest_similar_templates_not_found(self) -> None:
        """Test template suggestion with no close matches."""
        available = ["agenda", "task", "ticket", "small_note"]

        suggestion = suggest_similar_templates("xyz", available)
        assert suggestion is None

    def test_suggest_similar_templates_empty_list(self) -> None:
        """Test template suggestion with empty available list."""
        suggestion = suggest_similar_templates("test", [])
        assert suggestion is None

    @patch("printerm.interfaces.cli.template_service")
    def test_display_template_list_with_templates(self, mock_service: MagicMock) -> None:
        """Test displaying template list when templates exist."""
        mock_service.list_templates.return_value = ["agenda", "task", "ticket"]

        # Capture output by running in test environment
        with patch("typer.echo") as mock_echo:
            display_template_list()

            # Should call echo multiple times for formatting
            mock_echo.assert_called()
            calls = [str(call.args[0]) if call.args else str(call) for call in mock_echo.call_args_list]
            output = " ".join(calls)
            assert "Available Templates" in output

    @patch("printerm.interfaces.cli.template_service")
    def test_display_template_list_no_templates(self, mock_service: MagicMock) -> None:
        """Test displaying template list when no templates exist."""
        mock_service.list_templates.return_value = []

        with patch("typer.echo") as mock_echo:
            display_template_list()

            mock_echo.assert_called_with("No templates available.")

    @patch("printerm.interfaces.cli.template_service")
    def test_display_template_list_error(self, mock_service: MagicMock) -> None:
        """Test displaying template list when service raises error."""
        mock_service.list_templates.side_effect = Exception("Service error")

        with patch("typer.echo") as mock_echo, patch("printerm.interfaces.cli.ErrorHandler") as mock_handler:
            display_template_list()

            # Should show error message
            mock_echo.assert_called()
            mock_handler.handle_error.assert_called_once()

    @patch("printerm.interfaces.cli.template_service")
    @patch("printerm.interfaces.cli.service_container")
    def test_print_template_command_success(self, mock_container: MagicMock, mock_template_service: MagicMock) -> None:
        """Test successful print template command."""
        # Mock services
        mock_template_service.list_templates.return_value = ["test_template"]
        mock_template_service.get_template.return_value = {"name": "Test Template", "variables": []}
        mock_template_service.has_script.return_value = False

        mock_printer = Mock()
        mock_printer.__enter__ = Mock(return_value=mock_printer)
        mock_printer.__exit__ = Mock(return_value=None)

        def get_service(service_type: type) -> Mock:
            if service_type.__name__ == "PrinterService":
                return mock_printer
            return Mock()

        mock_container.get.side_effect = get_service

        result = self.runner.invoke(app, ["print", "test_template", "--quick"])

        assert result.exit_code == 0
        assert "Printed using template 'test_template'" in result.stdout
        mock_printer.print_template.assert_called_once()

    @patch("printerm.interfaces.cli.service_container")
    def test_print_template_command_template_not_found(self, mock_container: MagicMock) -> None:
        """Test print template command with non-existent template."""
        mock_template_service = Mock()
        mock_template_service.list_templates.return_value = ["agenda", "task"]

        def get_service(service_type: type) -> Mock:
            if service_type.__name__ == "TemplateService":
                return mock_template_service
            return Mock()

        mock_container.get.side_effect = get_service

        result = self.runner.invoke(app, ["print", "nonexistent", "--quick"])

        assert result.exit_code == 1
        assert "Template 'nonexistent' not found" in result.stdout

    @patch("printerm.interfaces.cli.service_container")
    def test_print_template_command_with_suggestion(self, mock_container: MagicMock) -> None:
        """Test print template command with suggestion."""
        mock_template_service = Mock()
        mock_template_service.list_templates.return_value = ["agenda", "task"]

        def get_service(service_type: type) -> Mock:
            if service_type.__name__ == "TemplateService":
                return mock_template_service
            return Mock()

        mock_container.get.side_effect = get_service

        result = self.runner.invoke(app, ["print", "agend", "--quick"])

        assert result.exit_code == 1
        assert "Did you mean: agenda" in result.stdout

    @patch("printerm.interfaces.cli.template_service")
    @patch("printerm.interfaces.cli.service_container")
    def test_print_template_command_printer_error(
        self, mock_container: MagicMock, mock_template_service: MagicMock
    ) -> None:
        """Test print template command with printer error."""
        mock_template_service.list_templates.return_value = ["test_template"]
        mock_template_service.get_template.return_value = {"variables": []}
        mock_template_service.has_script.return_value = False

        mock_printer = Mock()
        mock_printer.__enter__ = Mock(return_value=mock_printer)
        mock_printer.__exit__ = Mock(return_value=None)
        mock_printer.print_template.side_effect = PrintermError("Printer offline")

        def get_service(service_type: type) -> Mock:
            if service_type.__name__ == "PrinterService":
                return mock_printer
            return Mock()

        mock_container.get.side_effect = get_service

        with patch("printerm.interfaces.cli.ErrorHandler"):
            result = self.runner.invoke(app, ["print", "test_template", "--quick"])

            assert result.exit_code == 1
            assert "Failed to print: Printer offline" in result.stdout

    @patch("printerm.interfaces.cli.template_service")
    def test_list_templates_command(self, mock_service: MagicMock) -> None:
        """Test list templates command."""
        mock_service.list_templates.return_value = ["agenda", "task"]

        with patch("printerm.interfaces.cli.display_template_list") as mock_display:
            result = self.runner.invoke(app, ["list"])

            assert result.exit_code == 0
            mock_display.assert_called_once()

    @patch("printerm.interfaces.cli.template_service")
    @patch("printerm.interfaces.cli.config_service")
    @patch("printerm.interfaces.cli.service_container")
    def test_status_command_success(
        self, mock_container: MagicMock, mock_config: MagicMock, mock_template_service: MagicMock
    ) -> None:
        """Test status command with configured printer."""
        mock_config.get_printer_ip.return_value = "192.168.1.100"
        mock_config.get_chars_per_line.return_value = 48

        mock_template_service.list_templates.return_value = ["agenda", "task", "ticket"]

        result = self.runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "Printerm Status" in result.stdout
        assert "✅ Configured (192.168.1.100)" in result.stdout
        assert "3 available" in result.stdout

    @patch("printerm.interfaces.cli.template_service")
    @patch("printerm.interfaces.cli.config_service")
    @patch("printerm.interfaces.cli.service_container")
    def test_status_command_unconfigured(
        self, mock_container: MagicMock, mock_config: MagicMock, mock_template_service: MagicMock
    ) -> None:
        """Test status command with unconfigured printer."""
        mock_config.get_printer_ip.side_effect = ConfigurationError("No printer")
        mock_template_service.list_templates.return_value = []

        result = self.runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "❌ Not configured" in result.stdout
        assert "0 available" in result.stdout

    def test_version_command(self) -> None:
        """Test version command."""
        with patch("printerm.interfaces.cli.__version__", "1.2.3"):
            result = self.runner.invoke(app, ["version"])

            assert result.exit_code == 0
            assert "Printerm 1.2.3" in result.stdout

    @patch("printerm.interfaces.cli.config_service")
    @patch("printerm.interfaces.cli.service_container")
    def test_setup_init_command_new_user(self, mock_container: MagicMock, mock_config: MagicMock) -> None:
        """Test setup init command for new user."""
        mock_config.get_printer_ip.side_effect = ConfigurationError("No printer")
        mock_config.get_chars_per_line.return_value = 48

        # Simulate user input
        result = self.runner.invoke(
            app,
            ["setup", "init"],
            input="192.168.1.100\nn\n",  # IP address, no advanced settings
        )

        assert result.exit_code == 0
        mock_config.set_printer_ip.assert_called_with("192.168.1.100")

    @patch("printerm.interfaces.cli.config_service")
    def test_setup_init_command_existing_user_no_change(self, mock_config: MagicMock) -> None:
        """Test setup init command for existing user who doesn't want to change."""
        mock_config.get_printer_ip.return_value = "192.168.1.100"

        # User chooses not to change IP (should return early)
        result = self.runner.invoke(
            app,
            ["setup", "init"],
            input="n\n",  # Don't change IP
        )

        assert result.exit_code == 0
        assert "Setup complete!" in result.stdout

    @patch("printerm.interfaces.cli.template_service")
    def test_print_template_with_variables(self, mock_service: MagicMock) -> None:
        """Test print template with user input variables."""
        mock_service.list_templates.return_value = ["test_template"]
        mock_service.get_template.return_value = {
            "variables": [
                {"name": "title", "description": "Enter title", "markdown": False},
                {"name": "content", "description": "Enter content", "markdown": False},
            ]
        }
        mock_service.has_script.return_value = False

        with patch("printerm.interfaces.cli.service_container") as mock_container:
            mock_printer = Mock()
            mock_printer.__enter__ = Mock(return_value=mock_printer)
            mock_printer.__exit__ = Mock(return_value=None)

            def get_service(service_type: type) -> Mock:
                if service_type.__name__ == "TemplateService":
                    return mock_service
                elif service_type.__name__ == "PrinterService":
                    return mock_printer
                return Mock()

            mock_container.get.side_effect = get_service

            with patch("typer.prompt") as mock_prompt:
                mock_prompt.side_effect = ["Test Title", "Test Content"]

                result = self.runner.invoke(app, ["print", "test_template", "--quick"])

                assert result.exit_code == 0
                mock_printer.print_template.assert_called_once()

    @patch("printerm.interfaces.cli.template_service")
    def test_print_template_with_script(self, mock_service: MagicMock) -> None:
        """Test print template with script generation."""
        mock_service.list_templates.return_value = ["script_template"]
        mock_service.get_template.return_value = {"script": "test_script"}
        mock_service.has_script.return_value = True
        mock_service.generate_template_context.return_value = {"generated": "data"}

        with patch("printerm.interfaces.cli.service_container") as mock_container:
            mock_printer = Mock()
            mock_printer.__enter__ = Mock(return_value=mock_printer)
            mock_printer.__exit__ = Mock(return_value=None)

            def get_service(service_type: type) -> Mock:
                if service_type.__name__ == "TemplateService":
                    return mock_service
                elif service_type.__name__ == "PrinterService":
                    return mock_printer
                return Mock()

            mock_container.get.side_effect = get_service

            result = self.runner.invoke(app, ["print", "script_template", "--quick"])

            assert result.exit_code == 0
            mock_service.generate_template_context.assert_called_once()
            mock_printer.print_template.assert_called_with("script_template", {"generated": "data"})

    @patch("printerm.interfaces.cli.template_service")
    def test_print_template_interactive_selection(self, mock_service: MagicMock) -> None:
        """Test print template with interactive template selection."""
        mock_service.list_templates.return_value = ["agenda", "task"]
        mock_service.get_template.return_value = {"variables": []}
        mock_service.has_script.return_value = False

        with (
            patch("printerm.interfaces.cli.service_container") as mock_container,
            patch("printerm.interfaces.cli.display_template_list") as mock_display,
            patch("typer.prompt") as mock_prompt,
        ):
            mock_prompt.return_value = "task"

            mock_printer = Mock()
            mock_printer.__enter__ = Mock(return_value=mock_printer)
            mock_printer.__exit__ = Mock(return_value=None)

            def get_service(service_type: type) -> Mock:
                if service_type.__name__ == "TemplateService":
                    return mock_service
                elif service_type.__name__ == "PrinterService":
                    return mock_printer
                return Mock()

            mock_container.get.side_effect = get_service

            # No template name provided, should prompt
            result = self.runner.invoke(app, ["print", "--quick"])

            assert result.exit_code == 0
            mock_display.assert_called_once()
            mock_prompt.assert_called_with("Enter template name")
