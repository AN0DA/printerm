"""Dependency injection container for services."""

from collections.abc import Callable
from typing import Any

from printerm.services.config_service import ConfigServiceImpl
from printerm.services.interfaces import ConfigService, PrinterService, TemplateService, UpdateService
from printerm.services.printer_service import PrinterServiceImpl
from printerm.services.template_service import TemplateServiceImpl
from printerm.services.update_service import UpdateServiceImpl


class ServiceContainer:
    """Simple dependency injection container."""

    def __init__(self) -> None:
        self._services: dict[type, Any] = {}
        self._singletons: dict[type, Any] = {}
        self._setup_services()

    def _setup_services(self) -> None:
        """Setup service registrations."""
        # Register singleton services
        self.register_singleton(ConfigService, ConfigServiceImpl)
        self.register_singleton(UpdateService, UpdateServiceImpl)

        # Register transient services (new instance each time)
        self.register_transient(TemplateService, self._create_template_service)
        self.register_transient(PrinterService, self._create_printer_service)

    def register_singleton(self, interface: type, implementation: type | Any) -> None:
        """Register a singleton service."""
        self._singletons[interface] = implementation

    def register_transient(self, interface: type, factory: Callable[[], Any]) -> None:
        """Register a transient service with a factory function."""
        self._services[interface] = factory

    def get(self, service_type: type) -> Any:
        """Get a service instance."""
        # Check for singleton
        if service_type in self._singletons:
            singleton = self._singletons[service_type]
            if not isinstance(singleton, type):
                return singleton  # Already instantiated

            # Instantiate singleton
            instance = singleton()
            self._singletons[service_type] = instance
            return instance

        # Check for transient
        if service_type in self._services:
            factory = self._services[service_type]
            return factory()

        raise ValueError(f"Service {service_type} not registered")

    def _create_template_service(self) -> TemplateServiceImpl:
        """Factory method for template service."""
        config_service = self.get(ConfigService)
        return TemplateServiceImpl(config_service=config_service)

    def _create_printer_service(self) -> PrinterServiceImpl:
        """Factory method for printer service."""
        config_service = self.get(ConfigService)
        template_service = self.get(TemplateService)
        return PrinterServiceImpl(config_service, template_service)


# Global service container instance
service_container = ServiceContainer()
