"""Tests for service interfaces and protocol compliance."""

from unittest.mock import MagicMock

import pytest

from printerm.services.config_service import ConfigServiceImpl
from printerm.services.interfaces import (
    ConfigService,
    PrinterService,
    TemplateService,
    UpdateService,
)
from printerm.services.printer_service import PrinterServiceImpl
from printerm.services.template_service import TemplateServiceImpl
from printerm.services.update_service import UpdateServiceImpl


class TestServiceProtocolCompliance:
    """Test that service implementations comply with their protocols."""

    def test_config_service_protocol_compliance(self) -> None:
        """Test that ConfigServiceImpl implements ConfigService protocol."""
        # Get all methods from the protocol
        protocol_methods = {
            name
            for name in dir(ConfigService)
            if not name.startswith("_") and callable(getattr(ConfigService, name, None))
        }

        # Get all methods from the implementation
        impl_methods = {
            name
            for name in dir(ConfigServiceImpl)
            if not name.startswith("_") and callable(getattr(ConfigServiceImpl, name, None))
        }

        # Check that all protocol methods are implemented
        missing_methods = protocol_methods - impl_methods
        assert not missing_methods, f"ConfigServiceImpl missing methods: {missing_methods}"

    def test_template_service_protocol_compliance(self) -> None:
        """Test that TemplateServiceImpl implements TemplateService protocol."""
        # Get all methods from the protocol
        protocol_methods = {
            name
            for name in dir(TemplateService)
            if not name.startswith("_") and callable(getattr(TemplateService, name, None))
        }

        # Get all methods from the implementation
        impl_methods = {
            name
            for name in dir(TemplateServiceImpl)
            if not name.startswith("_") and callable(getattr(TemplateServiceImpl, name, None))
        }

        # Check that all protocol methods are implemented
        missing_methods = protocol_methods - impl_methods
        assert not missing_methods, f"TemplateServiceImpl missing methods: {missing_methods}"

    def test_printer_service_protocol_compliance(self) -> None:
        """Test that PrinterServiceImpl implements PrinterService protocol."""
        # Get all methods from the protocol
        protocol_methods = {
            name
            for name in dir(PrinterService)
            if not name.startswith("_") and callable(getattr(PrinterService, name, None))
        }

        # Get all methods from the implementation
        impl_methods = {
            name
            for name in dir(PrinterServiceImpl)
            if not name.startswith("_") and callable(getattr(PrinterServiceImpl, name, None))
        }

        # Check that all protocol methods are implemented
        missing_methods = protocol_methods - impl_methods
        assert not missing_methods, f"PrinterServiceImpl missing methods: {missing_methods}"

    def test_update_service_protocol_compliance(self) -> None:
        """Test that UpdateServiceImpl implements UpdateService protocol."""
        # Get all methods from the protocol
        protocol_methods = {
            name
            for name in dir(UpdateService)
            if not name.startswith("_") and callable(getattr(UpdateService, name, None))
        }

        # Get all methods from the implementation
        impl_methods = {
            name
            for name in dir(UpdateServiceImpl)
            if not name.startswith("_") and callable(getattr(UpdateServiceImpl, name, None))
        }

        # Check that all protocol methods are implemented
        missing_methods = protocol_methods - impl_methods
        assert not missing_methods, f"UpdateServiceImpl missing methods: {missing_methods}"


class TestServiceInstantiation:
    """Test that services can be instantiated correctly."""

    def test_config_service_instantiation(self, temp_config_dir: str) -> None:
        """Test ConfigServiceImpl can be instantiated."""
        config_file = f"{temp_config_dir}/test_config.ini"
        service = ConfigServiceImpl(config_file)
        assert isinstance(service, ConfigServiceImpl)
        assert service.config_file == config_file

    def test_template_service_instantiation(self, temp_template_dir: str, mock_config_service: MagicMock) -> None:
        """Test TemplateServiceImpl can be instantiated."""
        service = TemplateServiceImpl(template_dir=temp_template_dir, config_service=mock_config_service)
        assert isinstance(service, TemplateServiceImpl)
        assert service.template_dir == temp_template_dir
        assert service.config_service == mock_config_service

    def test_printer_service_instantiation(
        self, mock_config_service: ConfigService, mock_template_service: MagicMock
    ) -> None:
        """Test PrinterServiceImpl can be instantiated."""
        service = PrinterServiceImpl(mock_config_service, mock_template_service)
        assert isinstance(service, PrinterServiceImpl)
        assert service.config_service == mock_config_service
        assert service.template_service == mock_template_service

    def test_update_service_instantiation(self) -> None:
        """Test UpdateServiceImpl can be instantiated."""
        service = UpdateServiceImpl()
        assert isinstance(service, UpdateServiceImpl)
        assert service.pypi_url is not None


class TestServiceIntegration:
    """Test integration between services."""

    def test_printer_service_uses_config_and_template_services(
        self, temp_config_dir: str, temp_template_dir: str
    ) -> None:
        """Test that printer service properly integrates with other services."""
        # Create real services
        config_service = ConfigServiceImpl(f"{temp_config_dir}/test_config.ini")
        template_service = TemplateServiceImpl(template_dir=temp_template_dir, config_service=config_service)
        printer_service = PrinterServiceImpl(config_service, template_service)

        # Test that services are connected
        assert printer_service.config_service == config_service
        assert printer_service.template_service == template_service
        assert template_service.config_service == config_service

    def test_template_service_without_config_service(self, temp_template_dir: str) -> None:
        """Test that template service works without config service."""
        template_service = TemplateServiceImpl(template_dir=temp_template_dir, config_service=None)

        # Should still be able to load templates
        templates = template_service.list_templates()
        assert len(templates) > 0

        # Should use default configuration values
        context = {"title": "Test", "content": "Content"}
        segments = template_service.render_template("test_template", context)
        assert len(segments) > 0

    def test_error_propagation_between_services(
        self, mock_config_service: ConfigService, mock_template_service: MagicMock, sample_context: dict
    ) -> None:
        """Test that errors propagate correctly between services."""
        # Setup printer service with mocked dependencies
        printer_service = PrinterServiceImpl(mock_config_service, mock_template_service)

        # Mock template service to raise an error
        from printerm.exceptions import TemplateError

        mock_template_service.render_template.side_effect = TemplateError("Template not found")

        # Setup mock printer
        from unittest.mock import MagicMock

        mock_printer = MagicMock()
        printer_service._printer = mock_printer

        # Test that TemplateError is wrapped in PrinterError
        from printerm.exceptions import PrinterError

        with pytest.raises(PrinterError, match="Failed to print template"):
            printer_service.print_template("test_template", sample_context)
