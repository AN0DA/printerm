"""Custom exception classes for the printerm application."""


class PrintermError(Exception):
    """Base exception class for all printerm-related errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ConfigurationError(PrintermError):
    """Exception raised for configuration-related errors."""

    pass


class TemplateError(PrintermError):
    """Exception raised for template-related errors."""

    pass


class PrinterError(PrintermError):
    """Exception raised for printer-related errors."""

    pass


class NetworkError(PrintermError):
    """Exception raised for network-related errors."""

    pass


class ValidationError(PrintermError):
    """Exception raised for validation errors."""

    pass
