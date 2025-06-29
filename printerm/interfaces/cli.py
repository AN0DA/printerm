import logging
import os
import subprocess  # nosec: B404
import sys

import click
import typer

from printerm import __version__
from printerm.error_handling import ErrorHandler
from printerm.exceptions import ConfigurationError, PrintermError
from printerm.services import service_container
from printerm.services.interfaces import ConfigService, PrinterService, TemplateService, UpdateService
from printerm.services.template_service import compute_agenda_variables

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)

app = typer.Typer(help="Thermal Printer Application")
settings_app = typer.Typer(help="Settings commands")
config_app = typer.Typer(help="Configuration commands")

app.add_typer(settings_app, name="settings")
app.add_typer(config_app, name="config")

missing_ip_message = "Printer IP address not set. Please set it using 'settings set-ip'."

# Get services from container
config_service = service_container.get(ConfigService)
template_service = service_container.get(TemplateService)
update_service = service_container.get(UpdateService)


def check_for_updates_on_startup() -> None:
    try:
        if config_service.get_check_for_updates() and update_service.is_new_version_available(__version__):
            update = typer.confirm("A new version is available. Do you want to update?")
            if update:
                perform_update()
            else:
                typer.echo("You can update later by running 'printerm update' command.")
    except Exception as e:
        ErrorHandler.handle_error(e, "Error checking for updates")


def perform_update() -> None:
    """Update the application to the latest version from PyPI."""
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "printerm"]
        typer.echo("Updating the application...")

        # Check for user permissions
        if not os.access(sys.executable, os.W_OK):
            typer.echo("You might not have permission to update the application.")
            typer.echo("Please run the update command with administrative privileges.")
            sys.exit(1)

        subprocess.check_call(cmd)  # nosec: B603
        typer.echo("Application updated successfully.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Failed to update application: {e}")
        sys.exit(1)


@app.command()
def print_template(template_name: str = typer.Argument(None)) -> None:
    """
    Print using a specified template.
    """
    try:
        if not template_name:
            typer.echo("Available templates:")
            for name in template_service.list_templates():
                typer.echo(f"- {name}")
            template_name = typer.prompt("Enter the template name")

        template = template_service.get_template(template_name)

        context = {}
        if template_name == "agenda":
            context = compute_agenda_variables()
        else:
            for var in template.get("variables", []):
                if var.get("markdown", False):
                    value = click.edit(var["description"], require_save=True)
                else:
                    value = typer.prompt(var["description"])
                context[var["name"]] = value

        with service_container.get(PrinterService) as printer:
            printer.print_template(template_name, context)
        typer.echo(f"Printed using template '{template_name}'.")
    except PrintermError as e:
        typer.echo(f"Failed to print: {e.message}")
        ErrorHandler.handle_error(e, "Error printing template")
        sys.exit(1)
    except Exception as e:
        typer.echo(f"Failed to print: {e}")
        ErrorHandler.handle_error(e, f"Error printing template '{template_name}'")
        sys.exit(1)


@settings_app.command("set-ip")
def set_ip(ip_address: str = typer.Argument(..., help="Printer IP Address")) -> None:
    """
    Set the printer IP address.
    """
    try:
        config_service.set_printer_ip(ip_address)
        typer.echo(f"Printer IP address set to {ip_address}")
    except PrintermError as e:
        typer.echo(f"Failed to set IP address: {e.message}")
        ErrorHandler.handle_error(e, "Error setting IP address")
        sys.exit(1)


@settings_app.command("set-chars-per-line")
def set_chars_per_line_command(chars_per_line: int = typer.Argument(..., help="Characters Per Line")) -> None:
    """
    Set the number of characters per line.
    """
    try:
        config_service.set_chars_per_line(chars_per_line)
        typer.echo(f"Characters per line set to {chars_per_line}")
    except PrintermError as e:
        typer.echo(f"Failed to set characters per line: {e.message}")
        ErrorHandler.handle_error(e, "Error setting characters per line")
        sys.exit(1)


@settings_app.command("set-enable-special-letters")
def set_enable_special_letters_command(
    enable: bool = typer.Argument(..., help="Enable special letters (True/False)"),
) -> None:
    """
    Enable or disable special letters.
    """
    try:
        config_service.set_enable_special_letters(enable)
        typer.echo(f"Enable special letters set to {enable}")
    except PrintermError as e:
        typer.echo(f"Failed to set special letters setting: {e.message}")
        ErrorHandler.handle_error(e, "Error setting special letters")
        sys.exit(1)


@settings_app.command("set-check-for-updates")
def set_check_for_updates_command(
    check: bool = typer.Argument(..., help="Enable or disable automatic updates (True/False)"),
) -> None:
    """
    Enable or disable automatic update checking.
    """
    try:
        config_service.set_check_for_updates(check)
        typer.echo(f"Check for updates set to {check}")
    except PrintermError as e:
        typer.echo(f"Failed to set update checking: {e.message}")
        ErrorHandler.handle_error(e, "Error setting update checking")
        sys.exit(1)


@settings_app.command()
def show() -> None:
    """
    Show current settings.
    """
    try:
        try:
            ip_address = config_service.get_printer_ip()
        except ConfigurationError:
            ip_address = "Not set"

        chars_per_line = config_service.get_chars_per_line()
        enable_special_letters = config_service.get_enable_special_letters()
        check_for_updates = config_service.get_check_for_updates()

        typer.echo(f"Printer IP Address: {ip_address}")
        typer.echo(f"Characters Per Line: {chars_per_line}")
        typer.echo(f"Enable Special Letters: {enable_special_letters}")
        typer.echo(f"Check for Updates: {check_for_updates}")
    except Exception as e:
        typer.echo(f"Failed to show settings: {e}")
        ErrorHandler.handle_error(e, "Error showing settings")
        sys.exit(1)


@app.command()
def update() -> None:
    """
    Manually update the application to the latest version.
    """
    perform_update()


@app.command()
def gui() -> None:
    """
    Launch the GUI version of the application.
    """
    try:
        from printerm.interfaces import gui

        gui.main()
    except ImportError as e:
        typer.echo("Failed to launch GUI. PyQt6 might not be installed.")
        typer.echo("Install it using 'pip install PyQt6'")
        logger.error(f"Error launching GUI: {e}", exc_info=True)
        sys.exit(1)


@app.command()
def web() -> None:
    """
    Launch the web server with the web interface.
    """
    try:
        from printerm.interfaces import web

        web.main()
    except ImportError as e:
        typer.echo("Failed to launch web interface. Flask might not be installed.")
        typer.echo("Install it using 'pip install Flask'")
        logger.error(f"Error launching web interface: {e}", exc_info=True)
        sys.exit(1)


@config_app.command("edit")
def config_edit() -> None:
    """
    Open the configuration file for editing.
    """
    from printerm.services.config_service import CONFIG_FILE

    config_file_path = os.path.abspath(CONFIG_FILE)
    typer.echo(f"Opening configuration file: {config_file_path}")
    try:
        if sys.platform == "win32":
            os.startfile(config_file_path)  # nosec: B606
        elif sys.platform == "darwin":
            subprocess.call(["open", config_file_path])  # nosec: B603, B607
        else:
            # For Linux and other platforms
            editor = os.environ.get("EDITOR", "nano")
            subprocess.call([editor, config_file_path])  # nosec: B603
    except Exception as e:
        typer.echo(f"Failed to open configuration file: {e}")
        ErrorHandler.handle_error(e, "Error opening configuration file")
        sys.exit(1)


if __name__ == "__main__":
    check_for_updates_on_startup()
    app()
