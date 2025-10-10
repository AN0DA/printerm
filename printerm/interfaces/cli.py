import logging
import os
import subprocess  # nosec: B404
import sys
from difflib import get_close_matches
from typing import Annotated

import click
import typer

from printerm import __version__
from printerm.error_handling import ErrorHandler
from printerm.exceptions import ConfigurationError, PrintermError
from printerm.services import service_container
from printerm.services.interfaces import ConfigService, PrinterService, TemplateService, UpdateService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)

# Restructured CLI with better UX
app = typer.Typer(
    help="🖨️  Printerm - Smart thermal printer manager",
    rich_markup_mode="rich",
    no_args_is_help=False,  # We'll handle this ourselves for better UX
    invoke_without_command=True,
)

# Setup subcommand for configuration
setup_app = typer.Typer(help="⚙️  Setup and configuration")
app.add_typer(setup_app, name="setup")

missing_ip_message = "Printer IP address not set. Please set it using 'printerm setup printer --ip <IP>'."

# Get services from container
config_service = service_container.get(ConfigService)
template_service = service_container.get(TemplateService)
update_service = service_container.get(UpdateService)


@app.callback()
def main(ctx: typer.Context) -> None:
    """🖨️  Printerm - Smart thermal printer manager"""
    if ctx.invoked_subcommand is None:
        # Check if this is a first-time user
        try:
            config_service.get_printer_ip()
            # User has configuration, show status
            ctx.invoke(show_status)
        except ConfigurationError:
            # First-time user, show welcome message
            typer.echo("🖨️  [bold green]Welcome to Printerm![/]")
            typer.echo()
            typer.echo("It looks like this is your first time using Printerm.")
            typer.echo("Let's get you set up quickly:")
            typer.echo()
            typer.echo("  [bold cyan]printerm setup init[/]     # Run setup wizard")
            typer.echo("  [bold cyan]printerm list[/]          # See available templates")
            typer.echo("  [bold cyan]printerm --help[/]        # Show all commands")
            typer.echo()
            typer.echo("💡 [dim]Start with the setup wizard to configure your printer.[/]")


def suggest_similar_templates(template_name: str, available_templates: list[str]) -> str | None:
    """Suggest similar template names using fuzzy matching."""
    matches = get_close_matches(template_name, available_templates, n=3, cutoff=0.6)
    return matches[0] if matches else None


def display_template_list() -> None:
    """Display available templates in a user-friendly format."""
    try:
        templates = template_service.list_templates()
        if not templates:
            typer.echo("No templates available.")
            return

        typer.echo("📋 Available Templates:")
        typer.echo()

        # Template descriptions - these could be moved to template metadata in the future
        descriptions = {
            "agenda": "📅 Weekly agenda (auto-generated)",
            "task": "✅ Task with title and description",
            "ticket": "🎫 Label/ticket printing",
            "small_note": "📝 Quick note printing",
        }

        for template in sorted(templates):
            desc = descriptions.get(template, "📄 Template")
            typer.echo(f"  {template:<12} {desc}")

    except Exception as e:
        typer.echo(f"Failed to list templates: {e}")
        ErrorHandler.handle_error(e, "Error listing templates")


# CORE COMMANDS


@app.command("print")
def print_template(
    template_name: Annotated[str | None, typer.Argument(help="Template name to print")] = None,
    quick: Annotated[bool, typer.Option("--quick", "-q", help="Skip confirmations")] = False,
) -> None:
    """🖨️ Print using a template (main command)"""
    try:
        available_templates = template_service.list_templates()

        if not template_name:
            display_template_list()
            typer.echo()
            template_name = typer.prompt("Enter template name")

        # Check if template exists, provide suggestions if not
        if template_name not in available_templates:
            suggestion = suggest_similar_templates(template_name, available_templates)
            if suggestion:
                typer.echo(f"❌ Template '{template_name}' not found.")
                typer.echo(f"💡 Did you mean: {suggestion}")
                if not quick and typer.confirm(f"Use '{suggestion}' instead?"):
                    template_name = suggestion
                else:
                    typer.echo("📋 See all templates: printerm list")
                    sys.exit(1)
            else:
                typer.echo(f"❌ Template '{template_name}' not found.")
                typer.echo("📋 See all templates: printerm list")
                sys.exit(1)

        template = template_service.get_template(template_name)

        context = {}

        # Check if template has a script
        if template_service.has_script(template_name):
            # Use script to generate context
            context = template_service.generate_template_context(template_name)
        else:
            # Manual input for variables
            for var in template.get("variables", []):
                if var.get("markdown", False):
                    value = click.edit("", require_save=True)
                else:
                    value = typer.prompt(var["description"])
                context[var["name"]] = value

        with service_container.get(PrinterService) as printer:
            printer.print_template(template_name, context)

        typer.echo(f"✅ Printed using template '{template_name}'.")
    except PrintermError as e:
        typer.echo(f"❌ Failed to print: {e.message}")
        ErrorHandler.handle_error(e, "Error printing template")
        sys.exit(1)
    except Exception as e:
        typer.echo(f"❌ Failed to print: {e}")
        ErrorHandler.handle_error(e, f"Error printing template '{template_name}'")
        sys.exit(1)


@app.command("list")
def list_templates() -> None:
    """📋 List all available templates"""
    display_template_list()


@app.command("status")
def show_status() -> None:
    """📊 Show printer and system status"""
    try:
        typer.echo("🖨️  Printerm Status")
        typer.echo()

        # Printer status
        try:
            printer_ip = config_service.get_printer_ip()
            typer.echo(f"Printer:     ✅ Configured ({printer_ip})")
        except ConfigurationError:
            typer.echo("Printer:     ❌ Not configured")

        # Templates
        templates = template_service.list_templates()
        typer.echo(f"Templates:   {len(templates)} available")

        # Configuration status
        try:
            config_service.get_printer_ip()
            config_service.get_chars_per_line()
            typer.echo("Config:      ✅ All settings configured")
        except ConfigurationError:
            typer.echo("Config:      ⚠️  Incomplete configuration")

        typer.echo()
        typer.echo("Quick actions:")
        typer.echo("  printerm print [template]    Print a template")
        typer.echo("  printerm list               Show templates")
        typer.echo("  printerm setup printer      Configure printer")

    except Exception as e:
        typer.echo(f"❌ Failed to show status: {e}")
        ErrorHandler.handle_error(e, "Error showing status")
        sys.exit(1)


@app.command("version")
def show_version() -> None:
    """ℹ️  Show version information"""
    typer.echo(f"Printerm {__version__}")


# SETUP COMMANDS


@setup_app.command("init")
def setup_wizard() -> None:
    """🚀 Run initial setup wizard"""
    typer.echo("🚀 Printerm Setup Wizard")
    typer.echo()

    try:
        # Check current configuration
        try:
            current_ip = config_service.get_printer_ip()
            typer.echo(f"Current printer IP: {current_ip}")
            if not typer.confirm("Do you want to change the printer IP?"):
                typer.echo("✅ Setup complete!")
                return
        except ConfigurationError:
            typer.echo("No printer configured yet.")

        # Get printer IP
        printer_ip = typer.prompt("Enter printer IP address")
        config_service.set_printer_ip(printer_ip)
        typer.echo(f"✅ Printer IP set to {printer_ip}")

        # Optional settings
        if typer.confirm("Configure advanced settings?", default=False):
            chars = typer.prompt("Characters per line", default=config_service.get_chars_per_line())
            config_service.set_chars_per_line(chars)

            special_letters = typer.confirm(
                "Enable special letters?", default=config_service.get_enable_special_letters()
            )
            config_service.set_enable_special_letters(special_letters)

            updates = typer.confirm("Check for updates automatically?", default=config_service.get_check_for_updates())
            config_service.set_check_for_updates(updates)

        typer.echo()
        typer.echo("🎉 Setup complete! Try printing a template:")
        typer.echo("  printerm list      # See available templates")
        typer.echo("  printerm print     # Start printing")

    except Exception as e:
        typer.echo(f"❌ Setup failed: {e}")
        ErrorHandler.handle_error(e, "Error during setup")
        sys.exit(1)


@setup_app.command("printer")
def setup_printer(
    ip: Annotated[str | None, typer.Option("--ip", help="Printer IP address")] = None,
    test: Annotated[bool, typer.Option("--test", help="Test connection after setup")] = False,
) -> None:
    """🖨️ Configure printer settings"""
    try:
        if ip:
            config_service.set_printer_ip(ip)
            typer.echo(f"✅ Printer IP set to {ip}")
        else:
            try:
                current_ip = config_service.get_printer_ip()
                typer.echo(f"Current printer IP: {current_ip}")
            except ConfigurationError:
                typer.echo("No printer IP configured.")

            new_ip = typer.prompt("Enter new printer IP address")
            config_service.set_printer_ip(new_ip)
            typer.echo(f"✅ Printer IP set to {new_ip}")

        if test:
            typer.echo("🔍 Testing printer connection...")
            try:
                # Test printer connectivity
                with service_container.get(PrinterService) as printer_service:  # noqa: F841
                    # This will attempt to connect to the printer
                    typer.echo("✅ Connection test successful!")
            except Exception as e:
                typer.echo(f"❌ Connection test failed: {e}")
                typer.echo("💡 Check if the printer IP is correct and the printer is online.")

    except Exception as e:
        typer.echo(f"❌ Failed to configure printer: {e}")
        ErrorHandler.handle_error(e, "Error configuring printer")
        sys.exit(1)


@setup_app.command("show")
def show_config() -> None:
    """📋 Show current configuration"""
    try:
        try:
            ip_address = config_service.get_printer_ip()
        except ConfigurationError:
            ip_address = "Not set"

        chars_per_line = config_service.get_chars_per_line()
        enable_special_letters = config_service.get_enable_special_letters()
        check_for_updates = config_service.get_check_for_updates()

        typer.echo("⚙️  Current Configuration:")
        typer.echo()
        typer.echo(f"Printer IP Address:    {ip_address}")
        typer.echo(f"Characters Per Line:   {chars_per_line}")
        typer.echo(f"Enable Special Letters: {enable_special_letters}")
        typer.echo(f"Check for Updates:     {check_for_updates}")
    except Exception as e:
        typer.echo(f"❌ Failed to show configuration: {e}")
        ErrorHandler.handle_error(e, "Error showing configuration")
        sys.exit(1)


@setup_app.command("reset")
def reset_config() -> None:
    """🔄 Reset configuration to defaults"""
    if typer.confirm("⚠️  This will reset all configuration to defaults. Continue?"):
        try:
            typer.echo("🔄 Resetting configuration...")

            # Reset configuration by clearing the printer IP (main setting)
            # This will effectively reset the configuration to defaults
            import configparser

            from printerm.services.config_service import CONFIG_FILE

            config = configparser.ConfigParser()
            config.read(CONFIG_FILE)

            # Remove printer settings if they exist
            if config.has_section("printer"):
                config.remove_section("printer")

            # Reset to defaults - don't add printer section back (no IP = not configured)
            if not config.has_section("app"):
                config.add_section("app")
            config.set("app", "check_for_updates", "False")

            # Write the reset configuration
            with open(CONFIG_FILE, "w") as configfile:
                config.write(configfile)

            typer.echo("✅ Configuration reset to defaults.")
            typer.echo("Run 'printerm setup init' to reconfigure.")
        except Exception as e:
            typer.echo(f"❌ Failed to reset configuration: {e}")
            ErrorHandler.handle_error(e, "Error resetting configuration")
            sys.exit(1)
    else:
        typer.echo("Reset cancelled.")


@setup_app.command("edit")
def edit_config() -> None:
    """✏️  Open configuration file for editing"""
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
        typer.echo(f"❌ Failed to open configuration file: {e}")
        ErrorHandler.handle_error(e, "Error opening configuration file")
        sys.exit(1)


# INTERFACE LAUNCHERS


@app.command("gui")
def launch_gui() -> None:
    """🖥️  Launch graphical interface"""
    try:
        from printerm.interfaces import gui

        gui.main()
    except ImportError as e:
        typer.echo("❌ Failed to launch GUI. PyQt6 might not be installed.")
        typer.echo("Install it using 'pip install PyQt6'")
        logger.error(f"Error launching GUI: {e}", exc_info=True)
        sys.exit(1)


@app.command("web")
def launch_web(
    port: Annotated[int, typer.Option("--port", "-p", help="Port number")] = 5000,
    host: Annotated[str, typer.Option("--host", help="Host address")] = "localhost",
) -> None:
    """🌐 Launch web interface"""
    try:
        from waitress import serve

        from printerm.interfaces import web

        typer.echo(f"🚀 Starting web interface on {host}:{port}")
        typer.echo(f"📱 Open http://{host}:{port} in your browser")
        typer.echo("Press Ctrl+C to stop")

        # Use the provided host and port instead of config defaults
        serve(web.app, host=host, port=port)
    except ImportError as e:
        typer.echo("❌ Failed to launch web interface. Flask might not be installed.")
        typer.echo("Install it using 'pip install Flask'")
        logger.error(f"Error launching web interface: {e}", exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        typer.echo("\n👋 Web interface stopped.")
    except Exception as e:
        typer.echo(f"❌ Failed to start web interface: {e}")
        logger.error(f"Error launching web interface: {e}", exc_info=True)
        sys.exit(1)


# UTILITY COMMANDS


def check_for_updates_on_startup() -> None:
    """Check for updates on application startup."""
    try:
        if config_service.get_check_for_updates() and update_service.check_for_updates_with_retry(__version__):
            update = typer.confirm("A new version is available. Do you want to update?")
            if update:
                perform_update()
            else:
                typer.echo("You can update later by running 'printerm update' command.")
    except Exception as e:
        ErrorHandler.handle_error(e, "Error checking for updates")


def perform_update() -> None:
    """Update the application to the latest version from PyPI."""
    import os
    import subprocess  # nosec
    import sys

    try:
        typer.echo("⬆️  Updating the application...")

        # Check if we're in a virtual environment
        in_venv = sys.prefix != sys.base_prefix
        if in_venv:
            typer.echo("📦 Detected virtual environment - updating via pip")
        else:
            typer.echo("⚠️  Not in a virtual environment - update may require admin privileges")

        # Check for user permissions on pip executable
        pip_path = sys.executable
        if not os.access(pip_path, os.X_OK):
            typer.echo("❌ Cannot execute Python interpreter")
            sys.exit(1)

        # Use pip with --user flag if not in venv to avoid permission issues
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "--quiet", "printerm"]
        if not in_venv:
            cmd.insert(3, "--user")

        typer.echo(f"Running: {' '.join(cmd)}")

        # Run with timeout and capture output
        result = subprocess.run(  # nosec
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            check=False,  # Don't raise exception immediately
        )

        if result.returncode == 0:
            typer.echo("✅ Application updated successfully.")
            typer.echo("💡 Please restart the application to use the new version.")
            sys.exit(0)
        else:
            typer.echo(f"❌ Failed to update application (exit code: {result.returncode})")
            if result.stdout:
                typer.echo(f"Output: {result.stdout}")
            if result.stderr:
                typer.echo(f"Error: {result.stderr}")
            sys.exit(1)

    except subprocess.TimeoutExpired:
        typer.echo("❌ Update timed out after 5 minutes")
        sys.exit(1)
    except FileNotFoundError:
        typer.echo("❌ Python or pip not found")
        sys.exit(1)
    except Exception as e:
        typer.echo(f"❌ Unexpected error during update: {e}")
        sys.exit(1)


@app.command("update")
def update_app() -> None:
    """⬆️  Update to latest version"""
    perform_update()


if __name__ == "__main__":
    check_for_updates_on_startup()
    app()
