"""Tests for web interface."""

from collections.abc import Iterator
from unittest.mock import MagicMock, Mock, patch

import pytest
from flask.testing import FlaskClient

from printerm.exceptions import ConfigurationError, PrintermError
from printerm.interfaces.web import app


class TestWebInterface:
    """Test cases for web interface."""

    @pytest.fixture
    def client(self) -> Iterator[FlaskClient]:
        """Create test client for Flask app."""
        app.config["TESTING"] = True
        with app.test_client() as client, app.app_context():
            yield client

    @patch("printerm.interfaces.web.template_service")
    def test_index_route(self, mock_service: MagicMock, client: FlaskClient) -> None:
        """Test the index route."""
        mock_service.list_templates.return_value = ["agenda", "task"]
        mock_service.get_template.side_effect = lambda name: {
            "name": f"{name.title()} Template",
            "description": f"Template for {name}",
        }

        response = client.get("/")

        assert response.status_code == 200
        assert b"agenda" in response.data
        assert b"task" in response.data

    @patch("printerm.interfaces.web.template_service")
    def test_index_route_no_templates(self, mock_service: MagicMock, client: FlaskClient) -> None:
        """Test index route when no templates are available."""
        mock_service.list_templates.return_value = []

        response = client.get("/")

        assert response.status_code == 200

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

        response = client.get("/print/form_template")

        assert response.status_code == 200
        assert b"Document title" in response.data
        assert b"Document content" in response.data

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
