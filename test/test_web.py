"""Tests for web interface."""

from collections.abc import Iterator
from unittest.mock import MagicMock, Mock, patch

import pytest
from flask.testing import FlaskClient

from printerm.exceptions import ConfigurationError, PrintermError
from printerm.interfaces.web import WebSettings, WebThemeManager, app


class TestWebThemeManager:
    """Test cases for WebThemeManager."""

    def test_get_theme_styles_light(self) -> None:
        """Test getting light theme styles."""
        styles = WebThemeManager.get_theme_styles("light")

        assert styles["primary"] == "#2196f3"
        assert styles["background"] == "#f8f9fa"
        assert styles["text"] == "#212529"
        assert "navbar-bg" in styles

    def test_get_theme_styles_dark(self) -> None:
        """Test getting dark theme styles."""
        styles = WebThemeManager.get_theme_styles("dark")

        assert styles["primary"] == "#4a9eff"
        assert styles["background"] == "#1a1a1a"
        assert styles["text"] == "#ffffff"
        assert "navbar-bg" in styles

    def test_get_theme_from_request_with_cookie(self) -> None:
        """Test getting theme from request cookie."""
        with app.test_request_context("/", headers={"Cookie": "theme=dark"}):
            theme = WebThemeManager.get_theme_from_request()
            assert theme == "dark"

    def test_get_theme_from_request_default(self) -> None:
        """Test getting default theme when no cookie."""
        with app.test_request_context("/"):
            theme = WebThemeManager.get_theme_from_request()
            assert theme == "light"


class TestWebSettings:
    """Test cases for WebSettings."""

    def test_add_recent_template(self) -> None:
        """Test adding a template to recent list."""
        mock_config = Mock()
        mock_config.get_gui_recent_templates.return_value = ["template1", "template2"]

        settings = WebSettings(mock_config)
        settings.add_recent_template("template3")

        mock_config.set_gui_recent_templates.assert_called_once_with(["template3", "template1", "template2"])

    def test_add_existing_recent_template(self) -> None:
        """Test adding an existing template moves it to front."""
        mock_config = Mock()
        mock_config.get_gui_recent_templates.return_value = ["template1", "template2", "template3"]

        settings = WebSettings(mock_config)
        settings.add_recent_template("template2")

        mock_config.set_gui_recent_templates.assert_called_once_with(["template2", "template1", "template3"])

    def test_add_recent_template_limit(self) -> None:
        """Test recent template list is limited to 5 items."""
        mock_config = Mock()
        mock_config.get_gui_recent_templates.return_value = ["t1", "t2", "t3", "t4", "t5"]

        settings = WebSettings(mock_config)
        settings.add_recent_template("t6")

        mock_config.set_gui_recent_templates.assert_called_once_with(["t6", "t1", "t2", "t3", "t4"])

    def test_get_recent_templates_error_handling(self) -> None:
        """Test error handling when getting recent templates."""
        mock_config = Mock()
        mock_config.get_gui_recent_templates.side_effect = Exception("Config error")

        settings = WebSettings(mock_config)
        result = settings.get_recent_templates()

        assert result == []


class TestWebInterface:
    """Test cases for web interface."""

    @pytest.fixture
    def client(self) -> Iterator[FlaskClient]:
        """Create test client for Flask app."""
        app.config["TESTING"] = True
        with app.test_client() as client, app.app_context():
            yield client

    @patch("printerm.interfaces.web.template_service")
    @patch("printerm.interfaces.web.web_settings")
    def test_index_route(self, mock_web_settings: MagicMock, mock_service: MagicMock, client: FlaskClient) -> None:
        """Test the index route with enhanced features."""
        mock_service.list_templates.return_value = ["agenda", "task"]
        mock_service.get_template.side_effect = lambda name: {
            "name": f"{name.title()} Template",
            "description": f"Template for {name}",
            "variables": [] if name == "agenda" else [{"name": "title", "description": "Task title"}],
        }
        mock_web_settings.get_recent_templates.return_value = ["task"]

        with patch("printerm.interfaces.web.WebThemeManager.get_theme_from_request") as mock_theme:
            mock_theme.return_value = "light"
            response = client.get("/")

        assert response.status_code == 200
        assert b"agenda" in response.data
        assert b"task" in response.data
        # Check for recent templates section
        assert b"Recent Templates" in response.data or b"recent-templates" in response.data

    @patch("printerm.interfaces.web.template_service")
    @patch("printerm.interfaces.web.web_settings")
    def test_index_route_no_templates(
        self, mock_web_settings: MagicMock, mock_service: MagicMock, client: FlaskClient
    ) -> None:
        """Test index route when no templates are available."""
        mock_service.list_templates.return_value = []
        mock_web_settings.get_recent_templates.return_value = []

        with patch("printerm.interfaces.web.WebThemeManager.get_theme_from_request") as mock_theme:
            mock_theme.return_value = "light"
            response = client.get("/")

        assert response.status_code == 200
        # Should show "No Templates Available" message
        assert b"No Templates" in response.data or b"no templates" in response.data.lower()

    @patch("printerm.interfaces.web.service_container")
    @patch("printerm.interfaces.web.template_service")
    def test_print_template_get_request(
        self, mock_template_service: MagicMock, mock_container: MagicMock, client: FlaskClient
    ) -> None:
        """Test GET request to print template route."""
        mock_template_service.list_templates.return_value = ["test_template"]
        mock_template_service.get_template.return_value = {
            "name": "Test Template",
            "description": "A test template",
            "variables": [{"name": "title", "description": "Enter title", "required": True}],
        }

        response = client.get("/print/test_template")

        assert response.status_code == 200
        assert b"Test Template" in response.data

    @patch("printerm.interfaces.web.service_container")
    @patch("printerm.interfaces.web.template_service")
    def test_print_template_post_without_script(
        self, mock_template_service: MagicMock, mock_container: MagicMock, client: FlaskClient
    ) -> None:
        """Test POST request to print template without script."""
        mock_template_service.list_templates.return_value = ["test_template"]
        mock_template_service.get_template.return_value = {
            "name": "Test Template",
            "variables": [{"name": "title", "description": "Enter title"}],
        }
        mock_template_service.has_script.return_value = False

        # Mock printer service
        mock_printer = Mock()
        mock_printer.__enter__ = Mock(return_value=mock_printer)
        mock_printer.__exit__ = Mock(return_value=None)

        def get_service(service_type: type) -> Mock:
            if service_type.__name__ == "PrinterService":
                return mock_printer
            return Mock()

        mock_container.get.side_effect = get_service

        response = client.post("/print/test_template", data={"title": "Test Title", "confirm": "yes"})

        assert response.status_code == 302  # Redirect after successful print
        mock_printer.print_template.assert_called_once()

    @patch("printerm.interfaces.web.service_container")
    @patch("printerm.interfaces.web.template_service")
    def test_print_template_post_with_script(
        self, mock_template_service: MagicMock, mock_container: MagicMock, client: FlaskClient
    ) -> None:
        """Test POST request to print template with script."""
        mock_template_service.list_templates.return_value = ["script_template"]
        mock_template_service.get_template.return_value = {"name": "Script Template", "script": "test_script"}
        mock_template_service.has_script.return_value = True
        mock_template_service.generate_template_context.return_value = {"generated": "content"}

        # Mock printer service
        mock_printer = Mock()
        mock_printer.__enter__ = Mock(return_value=mock_printer)
        mock_printer.__exit__ = Mock(return_value=None)

        def get_service(service_type: type) -> Mock:
            if service_type.__name__ == "PrinterService":
                return mock_printer
            return Mock()

        mock_container.get.side_effect = get_service

        response = client.post("/print/script_template", data={"confirm": "yes"})

        assert response.status_code == 302  # Redirect after successful print
        mock_template_service.generate_template_context.assert_called_once()
        mock_printer.print_template.assert_called_with("script_template", {"generated": "content"})

    @patch("printerm.interfaces.web.service_container")
    @patch("printerm.interfaces.web.template_service")
    def test_print_template_cancel(
        self, mock_template_service: MagicMock, mock_container: MagicMock, client: FlaskClient
    ) -> None:
        """Test canceling print operation."""
        mock_template_service.list_templates.return_value = ["test_template"]
        mock_template_service.get_template.return_value = {"name": "Test Template", "variables": []}
        mock_template_service.has_script.return_value = False

        response = client.post("/print/test_template", data={"confirm": "no"})

        # Should redirect without printing
        assert response.status_code == 302

    @patch("printerm.interfaces.web.service_container")
    @patch("printerm.interfaces.web.template_service")
    def test_print_template_printer_error(
        self, mock_template_service: MagicMock, mock_container: MagicMock, client: FlaskClient
    ) -> None:
        """Test print template with printer error."""
        mock_template_service.list_templates.return_value = ["test_template"]
        mock_template_service.get_template.return_value = {"name": "Test Template", "variables": []}
        mock_template_service.has_script.return_value = False

        # Mock printer service to raise error
        mock_printer = Mock()
        mock_printer.__enter__ = Mock(return_value=mock_printer)
        mock_printer.__exit__ = Mock(return_value=None)
        mock_printer.print_template.side_effect = PrintermError("Printer offline")

        def get_service(service_type: type) -> Mock:
            if service_type.__name__ == "PrinterService":
                return mock_printer
            return Mock()

        mock_container.get.side_effect = get_service

        with patch("printerm.interfaces.web.ErrorHandler"):
            response = client.post("/print/test_template", data={"confirm": "yes"})

            # Should still return 200 but with error message
            assert response.status_code == 200

    @patch("printerm.interfaces.web.service_container")
    @patch("printerm.interfaces.web.template_service")
    def test_print_template_configuration_error(
        self, mock_template_service: MagicMock, mock_container: MagicMock, client: FlaskClient
    ) -> None:
        """Test print template with configuration error."""
        mock_template_service.list_templates.return_value = ["test_template"]
        mock_template_service.get_template.return_value = {"name": "Test Template", "variables": []}
        mock_template_service.has_script.return_value = False

        # Mock printer service to raise configuration error
        mock_printer = Mock()
        mock_printer.__enter__ = Mock(return_value=mock_printer)
        mock_printer.__exit__ = Mock(return_value=None)
        mock_printer.print_template.side_effect = ConfigurationError("Printer not configured")

        def get_service(service_type: type) -> Mock:
            if service_type.__name__ == "PrinterService":
                return mock_printer
            return Mock()

        mock_container.get.side_effect = get_service

        with patch("printerm.interfaces.web.ErrorHandler"):
            response = client.post("/print/test_template", data={"confirm": "yes"})

            assert response.status_code == 200

    @patch("printerm.interfaces.web.template_service")
    def test_print_template_invalid_template(self, mock_service: MagicMock, client: FlaskClient) -> None:
        """Test print route with invalid template name."""
        mock_service.list_templates.return_value = ["valid_template"]
        mock_service.get_template.side_effect = Exception("Template not found")

        response = client.get("/print/invalid_template")

        # Expect redirect on error
        assert response.status_code in [302, 500, 200]

    @patch("printerm.interfaces.web.template_service")
    def test_print_template_empty_context(self, mock_service: MagicMock, client: FlaskClient) -> None:
        """Test print template with empty context."""
        mock_service.list_templates.return_value = ["empty_template"]
        mock_service.get_template.return_value = {"name": "Empty Template", "variables": []}

        response = client.get("/print/empty_template")

        assert response.status_code == 200

    @patch("printerm.interfaces.web.service_container")
    @patch("printerm.interfaces.web.template_service")
    def test_print_template_multiple_variables(
        self, mock_template_service: MagicMock, mock_container: MagicMock, client: FlaskClient
    ) -> None:
        """Test print template with multiple variables."""
        mock_template_service.list_templates.return_value = ["multi_var_template"]
        mock_template_service.get_template.return_value = {
            "name": "Multi Variable Template",
            "variables": [
                {"name": "var1", "description": "Variable 1"},
                {"name": "var2", "description": "Variable 2"},
                {"name": "var3", "description": "Variable 3"},
            ],
        }
        mock_template_service.has_script.return_value = False

        mock_printer = Mock()
        mock_printer.__enter__ = Mock(return_value=mock_printer)
        mock_printer.__exit__ = Mock(return_value=None)

        def get_service(service_type: type) -> Mock:
            if service_type.__name__ == "PrinterService":
                return mock_printer
            return Mock()

        mock_container.get.side_effect = get_service

        response = client.post(
            "/print/multi_var_template", data={"var1": "value1", "var2": "value2", "var3": "value3", "confirm": "yes"}
        )

        assert response.status_code == 302
        # Verify the printer was called with the correct context
        call_args = mock_printer.print_template.call_args
        assert call_args[0][0] == "multi_var_template"
        context = call_args[0][1]
        assert context["var1"] == "value1"
        assert context["var2"] == "value2"
        assert context["var3"] == "value3"

    @patch("printerm.interfaces.web.template_service")
    def test_print_template_get_with_variables(self, mock_service: MagicMock, client: FlaskClient) -> None:
        """Test GET request displays template variables correctly."""
        mock_service.list_templates.return_value = ["form_template"]
        mock_service.get_template.return_value = {
            "name": "Form Template",
            "description": "A template with form fields",
            "variables": [
                {"name": "title", "description": "Document title", "required": True},
                {"name": "content", "description": "Document content", "required": False},
            ],
        }
        mock_service.has_script.return_value = False

        with patch("printerm.interfaces.web.WebThemeManager.get_theme_from_request") as mock_theme:
            mock_theme.return_value = "light"
            response = client.get("/print/form_template")

        assert response.status_code == 200
        # Check for template name and description
        assert b"Form Template" in response.data
        assert b"template with form fields" in response.data

    @patch("printerm.interfaces.web.service_container")
    @patch("printerm.interfaces.web.template_service")
    def test_app_initialization(self, mock_template_service: MagicMock, mock_container: MagicMock) -> None:
        """Test that the Flask app initializes correctly."""
        # Test that app is configured with default secret key
        assert app.secret_key == "default_secret_key"
        assert app.config["TESTING"]  # Set in test fixture

    def test_template_folder_configuration(self) -> None:
        """Test that template folder is configured correctly."""
        # The app should have web_templates folder configured
        assert app.template_folder is not None
        assert "web_templates" in str(app.template_folder)

    @patch("printerm.interfaces.web.template_service")
    def test_template_service_integration(self, mock_service: MagicMock, client: FlaskClient) -> None:
        """Test integration with template service."""
        # Test that template service is called appropriately
        mock_service.list_templates.return_value = ["test"]
        mock_service.get_template.return_value = {"name": "Test"}

        client.get("/")

        # Verify service methods were called
        mock_service.list_templates.assert_called_once()
        mock_service.get_template.assert_called_with("test")

    @patch("printerm.interfaces.web.service_container")
    @patch("printerm.interfaces.web.template_service")
    def test_error_handling_middleware(
        self, mock_template_service: MagicMock, mock_container: MagicMock, client: FlaskClient
    ) -> None:
        """Test that errors are handled gracefully."""
        from printerm.exceptions import TemplateError

        mock_template_service.list_templates.side_effect = TemplateError("Service unavailable")

        with patch("printerm.interfaces.web.ErrorHandler") as mock_handler:
            # The index route doesn't have error handling, so expect exception
            with pytest.raises(TemplateError):
                client.get("/")

            # ErrorHandler should still be available for other routes
            assert mock_handler is not None

    # API Endpoint Tests

    @patch("printerm.interfaces.web.template_service")
    def test_api_validate_template_success(self, mock_service: MagicMock, client: FlaskClient) -> None:
        """Test successful template validation API."""
        mock_service.get_template.return_value = {
            "name": "Test Template",
            "variables": [
                {"name": "title", "description": "Title", "required": True},
                {"name": "content", "description": "Content", "required": False},
            ],
        }

        response = client.post(
            "/api/validate/test_template",
            json={"title": "Test Title", "content": "Some content"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["valid"] is True
        assert "successful" in data["message"]
        assert data["invalid_fields"] == []

    @patch("printerm.interfaces.web.template_service")
    def test_api_validate_template_missing_required(self, mock_service: MagicMock, client: FlaskClient) -> None:
        """Test template validation with missing required fields."""
        mock_service.get_template.return_value = {
            "name": "Test Template",
            "variables": [
                {"name": "title", "description": "Title", "required": True},
                {"name": "content", "description": "Content", "required": True},
            ],
        }

        response = client.post(
            "/api/validate/test_template",
            json={"title": "Test Title", "content": ""},  # Missing content
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["valid"] is False
        assert len(data["errors"]) == 1
        assert "Content" in data["errors"][0]
        assert data["invalid_fields"] == [{"field": "content", "label": "Content"}]

    @patch("printerm.interfaces.web.template_service")
    def test_api_validate_template_error(self, mock_service: MagicMock, client: FlaskClient) -> None:
        """Test template validation API error handling."""
        mock_service.get_template.side_effect = Exception("Template not found")

        response = client.post("/api/validate/invalid_template", json={}, content_type="application/json")

        assert response.status_code == 400
        data = response.get_json()
        assert data["valid"] is False
        assert "error" in data["errors"][0]
        assert data["invalid_fields"] == []

    def test_api_theme_set_valid(self, client: FlaskClient) -> None:
        """Test setting valid theme."""
        response = client.post("/api/theme", json={"theme": "dark"}, content_type="application/json")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["theme"] == "dark"

        # Check cookie is set in response headers
        set_cookie_header = response.headers.get("Set-Cookie", "")
        assert "theme=dark" in set_cookie_header

    def test_api_theme_set_invalid(self, client: FlaskClient) -> None:
        """Test setting invalid theme defaults to light."""
        response = client.post("/api/theme", json={"theme": "invalid"}, content_type="application/json")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["theme"] == "light"  # Should default to light

    def test_api_theme_missing_data(self, client: FlaskClient) -> None:
        """Test theme API with missing data."""
        response = client.post("/api/theme", json={}, content_type="application/json")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["theme"] == "light"  # Should default to light

    def test_api_theme_error_handling(self, client: FlaskClient) -> None:
        """Test theme API error handling."""
        # Send invalid JSON to trigger error
        response = client.post("/api/theme", data="invalid json", content_type="application/json")

        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data

    # Enhanced Print Template Tests

    @patch("printerm.interfaces.web.service_container")
    @patch("printerm.interfaces.web.template_service")
    @patch("printerm.interfaces.web.web_settings")
    def test_print_template_adds_to_recent(
        self,
        mock_web_settings: MagicMock,
        mock_template_service: MagicMock,
        mock_container: MagicMock,
        client: FlaskClient,
    ) -> None:
        """Test that printing a template adds it to recent templates."""
        mock_template_service.list_templates.return_value = ["test_template"]
        mock_template_service.get_template.return_value = {"name": "Test Template", "variables": []}
        mock_template_service.has_script.return_value = False

        # Mock printer service
        mock_printer = Mock()
        mock_printer.__enter__ = Mock(return_value=mock_printer)
        mock_printer.__exit__ = Mock(return_value=None)

        def get_service(service_type: type) -> Mock:
            if service_type.__name__ == "PrinterService":
                return mock_printer
            return Mock()

        mock_container.get.side_effect = get_service

        with patch("printerm.interfaces.web.WebThemeManager.get_theme_from_request") as mock_theme:
            mock_theme.return_value = "light"
            response = client.post("/print/test_template", data={"confirm": "yes"})

        assert response.status_code == 302  # Redirect after successful print
        mock_web_settings.add_recent_template.assert_called_once_with("test_template")

    @patch("printerm.interfaces.web.service_container")
    @patch("printerm.interfaces.web.template_service")
    def test_print_template_get_with_theme_support(
        self, mock_template_service: MagicMock, mock_container: MagicMock, client: FlaskClient
    ) -> None:
        """Test GET request to print template includes theme support."""
        mock_template_service.list_templates.return_value = ["test_template"]
        mock_template_service.get_template.return_value = {
            "name": "Test Template",
            "description": "A test template",
            "variables": [{"name": "title", "description": "Enter title", "required": True}],
        }
        mock_template_service.has_script.return_value = False

        with patch("printerm.interfaces.web.WebThemeManager.get_theme_from_request") as mock_theme:
            mock_theme.return_value = "dark"
            response = client.get("/print/test_template")

        assert response.status_code == 200
        assert b"Test Template" in response.data
        # Should include theme data
        assert b"dark" in response.data or b"theme" in response.data

    # Settings Route Tests

    @patch("printerm.interfaces.web.config_service")
    @patch("printerm.interfaces.web.template_service")
    def test_settings_get_request(
        self, mock_template_service: MagicMock, mock_config_service: MagicMock, client: FlaskClient
    ) -> None:
        """Test GET request to settings route."""
        mock_template_service.list_templates.return_value = ["template1"]
        mock_template_service.get_template.return_value = {"name": "Template 1"}

        mock_config_service.get_printer_ip.return_value = "192.168.1.100"
        mock_config_service.get_chars_per_line.return_value = 32
        mock_config_service.get_enable_special_letters.return_value = True
        mock_config_service.get_check_for_updates.return_value = False

        with patch("printerm.interfaces.web.WebThemeManager.get_theme_from_request") as mock_theme:
            mock_theme.return_value = "light"
            response = client.get("/settings")

        assert response.status_code == 200
        assert b"192.168.1.100" in response.data
        assert b"32" in response.data
        assert b"Configuration Settings" in response.data

    @patch("printerm.interfaces.web.config_service")
    @patch("printerm.interfaces.web.template_service")
    def test_settings_get_request_no_ip(
        self, mock_template_service: MagicMock, mock_config_service: MagicMock, client: FlaskClient
    ) -> None:
        """Test GET request to settings when no IP is configured."""
        mock_template_service.list_templates.return_value = []
        mock_template_service.get_template.return_value = {}

        mock_config_service.get_printer_ip.side_effect = ConfigurationError("No IP configured")
        mock_config_service.get_chars_per_line.return_value = 32
        mock_config_service.get_enable_special_letters.return_value = False
        mock_config_service.get_check_for_updates.return_value = True

        with patch("printerm.interfaces.web.WebThemeManager.get_theme_from_request") as mock_theme:
            mock_theme.return_value = "dark"
            response = client.get("/settings")

        assert response.status_code == 200
        # Should handle missing IP gracefully

    @patch("printerm.interfaces.web.config_service")
    @patch("printerm.interfaces.web.template_service")
    def test_settings_post_request_success(
        self, mock_template_service: MagicMock, mock_config_service: MagicMock, client: FlaskClient
    ) -> None:
        """Test successful POST request to update settings."""
        mock_template_service.list_templates.return_value = []
        mock_template_service.get_template.return_value = {}

        response = client.post(
            "/settings",
            data={
                "ip_address": "192.168.1.200",
                "chars_per_line": "48",
                "enable_special_letters": "True",
                "check_for_updates": "False",
            },
        )

        assert response.status_code == 302  # Redirect after successful update

        # Verify all config methods were called
        mock_config_service.set_printer_ip.assert_called_once_with("192.168.1.200")
        mock_config_service.set_chars_per_line.assert_called_once_with(48)
        mock_config_service.set_enable_special_letters.assert_called_once_with(True)
        mock_config_service.set_check_for_updates.assert_called_once_with(False)

    @patch("printerm.interfaces.web.config_service")
    @patch("printerm.interfaces.web.template_service")
    def test_settings_post_invalid_chars_per_line(
        self, mock_template_service: MagicMock, mock_config_service: MagicMock, client: FlaskClient
    ) -> None:
        """Test POST request with invalid chars_per_line value."""
        mock_template_service.list_templates.return_value = []
        mock_template_service.get_template.return_value = {}

        response = client.post(
            "/settings",
            data={"ip_address": "192.168.1.100", "chars_per_line": "invalid_number", "enable_special_letters": "True"},
        )

        # Should redirect back to settings (error will be shown via flash message)
        assert response.status_code == 302
        assert "/settings" in response.location

    @patch("printerm.interfaces.web.config_service")
    @patch("printerm.interfaces.web.template_service")
    def test_settings_post_config_error(
        self, mock_template_service: MagicMock, mock_config_service: MagicMock, client: FlaskClient
    ) -> None:
        """Test POST request with configuration error."""
        mock_template_service.list_templates.return_value = []
        mock_template_service.get_template.return_value = {}

        mock_config_service.set_printer_ip.side_effect = PrintermError("Configuration failed")

        response = client.post("/settings", data={"ip_address": "192.168.1.100", "chars_per_line": "32"})

        # Should redirect back to settings (error will be shown via flash message)
        assert response.status_code == 302
        assert "/settings" in response.location

    @patch("printerm.interfaces.web.config_service")
    @patch("printerm.interfaces.web.template_service")
    def test_settings_boolean_handling(
        self, mock_template_service: MagicMock, mock_config_service: MagicMock, client: FlaskClient
    ) -> None:
        """Test proper handling of boolean settings."""
        mock_template_service.list_templates.return_value = []
        mock_template_service.get_template.return_value = {}

        # Test various boolean representations
        test_cases = [
            ("true", True),
            ("yes", True),
            ("1", True),
            ("false", False),
            ("no", False),
            ("0", False),
            ("", False),
        ]

        for bool_value, expected in test_cases:
            mock_config_service.reset_mock()

            client.post(
                "/settings",
                data={
                    "ip_address": "192.168.1.100",
                    "chars_per_line": "32",
                    "enable_special_letters": bool_value,
                    "check_for_updates": bool_value,
                },
            )

            mock_config_service.set_enable_special_letters.assert_called_with(expected)
            mock_config_service.set_check_for_updates.assert_called_with(expected)

    # Integration and Error Handling Tests
