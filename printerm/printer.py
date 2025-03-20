import logging
from typing import Any

from escpos.printer import Network

from printerm.template_manager import TemplateManager
from printerm.utils import TemplateRenderer

logger = logging.getLogger(__name__)


class ThermalPrinter:
    """
    A class to interface with a thermal printer over the network.
    """

    def __init__(self, ip_address: str, template_manager: TemplateManager):
        """
        Initialize the ThermalPrinter with the given IP address and TemplateManager.
        """
        self.ip_address = ip_address
        self.template_manager = template_manager
        self.template_renderer = TemplateRenderer(template_manager)
        logging.debug(f"Initialized ThermalPrinter with IP {ip_address}")
        self.printer: Network = None

    def __enter__(self) -> "ThermalPrinter":
        self.printer = Network(self.ip_address, timeout=10)
        logging.debug("Opened printer connection.")
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object | None
    ) -> None:
        if self.printer:
            try:
                self.printer.close()
                logging.debug("Closed printer connection.")
            except Exception as e:
                logger.error(f"Error closing printer connection: {e}")

    def print_segments(self, segments: list[dict[str, Any]]) -> None:
        """
        Given a list of segments, each a dict with 'text' and 'styles', print them accordingly.
        """
        try:
            for segment in segments:
                text = segment["text"]
                styles = segment.get("styles", {})
                logger.debug("Printing segment: %s with styles: %s", text, styles)
                self.printer.set(
                    align=styles.get("align", "left"),
                    font=styles.get("font", "a"),
                    bold=styles.get("bold", False),
                    underline=styles.get("underline", False),
                    invert=styles.get("italic", False),
                    double_width=styles.get("double_width", False),
                    double_height=styles.get("double_height", False),
                )
                self.printer.text(text)
            # Reset styles
            self.printer.set(
                align="left",
                font="a",
                bold=False,
                underline=False,
                invert=False,
                double_width=False,
                double_height=False,
            )
            logger.info("Printed segments successfully.")
        except Exception as e:
            logger.error(f"Error printing segments: {e}", exc_info=True)
            raise

    def print_template(self, template_name: str, context: dict[str, Any]) -> None:
        """
        Render and print a template by name with the given context.
        """
        if not self.printer:
            raise RuntimeError("Printer connection is not open.")
        segments = self.template_renderer.render_from_template(template_name, context)
        self.print_segments(segments)
        self.printer.cut()
