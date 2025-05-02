"""
Common utilities for interfaces (CLI, GUI, and web).
Centralizes shared functionality to reduce code duplication.
"""

import logging
from typing import Any

from printerm.core.config import get_printer_ip
from printerm.printing.printer import ThermalPrinter
from printerm.templates.template_manager import TemplateManager

logger = logging.getLogger(__name__)


def get_template_variables(
    template_manager: TemplateManager, template_name: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Get the variable definitions and script variables for a template.

    Args:
        template_manager: The template manager instance
        template_name: Name of the template

    Returns:
        Tuple of (template variable definitions, script-generated variables)
    """
    template = template_manager.get_template(template_name)
    if not template:
        raise ValueError(f"Template '{template_name}' not found.")

    # Get variable definitions from template
    variable_defs = template.get("variables", [])

    # Get script variables if available
    script_variables = {}
    script_func = template_manager.get_template_script(template_name)
    if script_func:
        try:
            script_variables = script_func()
            logger.debug(f"Applied script variables for template '{template_name}'")
        except Exception as e:
            logger.error(f"Error executing script for template '{template_name}': {e}", exc_info=True)

    return variable_defs, script_variables


def print_rendered_template(
    template_manager: TemplateManager, template_name: str, context: dict[str, Any], ip_address: str | None = None
) -> None:
    """
    Print a template with the given context.

    Args:
        template_manager: The template manager instance
        template_name: Name of the template to print
        context: The template context (variables)
        ip_address: Optional printer IP address (if None, will be retrieved from config)

    Raises:
        ValueError: If the template is not found
        RuntimeError: If the printer connection fails
    """
    if not ip_address:
        ip_address = get_printer_ip()

    template = template_manager.get_template(template_name)
    if not template:
        raise ValueError(f"Template '{template_name}' not found.")

    # Create complete context with script variables if necessary
    with ThermalPrinter(ip_address, template_manager) as printer:
        printer.print_template(template_name, context)
