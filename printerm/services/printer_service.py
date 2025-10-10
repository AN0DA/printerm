"""Printer service implementation."""

import logging
from typing import Any

from escpos.printer import Network

from printerm.exceptions import PrinterError
from printerm.services.interfaces import ConfigService, TemplateService

logger = logging.getLogger(__name__)


class PrinterServiceImpl:
    """Printer service implementation."""

    def __init__(self, config_service: ConfigService, template_service: TemplateService) -> None:
        self.config_service = config_service
        self.template_service = template_service
        self._printer: Network | None = None

    def __enter__(self) -> "PrinterServiceImpl":
        """Context manager entry."""
        try:
            ip_address = self.config_service.get_printer_ip()
            self._printer = Network(ip_address, timeout=10)
            logger.debug(f"Opened printer connection to {ip_address}")
            return self
        except Exception as e:
            raise PrinterError("Failed to connect to printer", str(e)) from e

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        if self._printer:
            try:
                self._printer.close()
                logger.debug("Closed printer connection")
            except Exception as e:
                logger.error(f"Error closing printer connection: {e}")

    def print_segments(self, segments: list[dict[str, Any]]) -> None:
        """Print a list of text segments with styles."""
        if not self._printer:
            raise PrinterError("Printer connection is not open")

        try:
            for segment in segments:
                text = segment["text"]
                styles = segment.get("styles", {}).copy()

                # Map italic to invert for printer compatibility
                if styles.get("italic", False):
                    styles["invert"] = True
                    del styles["italic"]

                # Set default values for missing style keys
                default_styles = {
                    "align": "left",
                    "font": "a",
                    "bold": False,
                    "underline": False,
                    "invert": False,
                    "double_width": False,
                    "double_height": False,
                }
                for key, default_value in default_styles.items():
                    if key not in styles:
                        styles[key] = default_value

                self._printer.set_with_default(**styles)
                self._printer.text(text)
                self._printer.ln()

            # Reset styles
            self._printer.set(
                align="left",
                font="a",
                bold=False,
                underline=False,
                invert=False,
                double_width=False,
                double_height=False,
            )
            logger.info("Printed segments successfully")
        except Exception as e:
            raise PrinterError("Failed to print segments", str(e)) from e

    def print_template(self, template_name: str, context: dict[str, Any]) -> None:
        """Render and print a template."""
        if not self._printer:
            raise PrinterError("Printer connection is not open")
        try:
            segments = self.template_service.render_template(template_name, context)
            self.print_segments(segments)
            self._printer.cut()
            logger.info(f"Successfully printed template '{template_name}'")
        except Exception as e:
            if isinstance(e, PrinterError):
                raise
            raise PrinterError(f"Failed to print template '{template_name}'", str(e)) from e
