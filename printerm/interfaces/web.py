import logging
import os

from flask import Flask, flash, redirect, render_template, request, url_for
from waitress import serve
from werkzeug.wrappers import Response

from printerm.error_handling import ErrorHandler
from printerm.exceptions import ConfigurationError, PrintermError
from printerm.services import service_container
from printerm.services.interfaces import ConfigService, PrinterService, TemplateService
from printerm.services.template_service import compute_agenda_variables

logger = logging.getLogger(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))
template_dir = os.path.join(dir_path, "web_templates")

# Get services from container
config_service = service_container.get(ConfigService)
template_service = service_container.get(TemplateService)

app = Flask(__name__, template_folder=template_dir)
app.secret_key = config_service.get_flask_secret_key()


@app.route("/")
def index() -> str:
    templates = {name: template_service.get_template(name) for name in template_service.list_templates()}
    return render_template("index.html", templates=templates)


@app.route("/print/<template_name>", methods=["GET", "POST"])
def print_template(template_name: str) -> Response | str:
    try:
        templates = {name: template_service.get_template(name) for name in template_service.list_templates()}
        template = template_service.get_template(template_name)

        if request.method == "POST":
            context = {}
            try:
                match template_name:
                    case "agenda":
                        context = compute_agenda_variables()
                    case _:
                        context = {var["name"]: request.form.get(var["name"]) for var in template.get("variables", [])}

                        if not context:
                            confirm = request.form.get("confirm")
                            if confirm == "no":
                                flash(f"Cancelled printing {template_name}.", "info")
                                return redirect(url_for("index"))

                with service_container.get(PrinterService) as printer:
                    printer.print_template(template_name, context)
                flash(f"Printed using template '{template_name}'.", "success")
                return redirect(url_for("index"))

            except PrintermError as e:
                ErrorHandler.handle_error(e, f"Error printing template '{template_name}'")
                flash(f"Failed to print: {e.message}", "error")
            except Exception as e:
                ErrorHandler.handle_error(e, f"Error printing template '{template_name}'")
                flash(f"Failed to print: {e}", "error")

        return render_template(
            "print_template.html",
            templates=templates,
            template=template,
            markdown_vars=[var["name"] for var in template.get("variables", []) if var.get("markdown", False)],
        )
    except PrintermError as e:
        flash(f"Template error: {e.message}", "error")
        return redirect(url_for("index"))
    except Exception as e:
        ErrorHandler.handle_error(e, f"Error accessing template '{template_name}'")
        flash(f"Template '{template_name}' not found.", "error")
        return redirect(url_for("index"))


@app.route("/settings", methods=["GET", "POST"])
def settings() -> Response | str:
    try:
        templates = {name: template_service.get_template(name) for name in template_service.list_templates()}

        if request.method == "POST":
            ip_address = request.form.get("ip_address")
            chars_per_line_value = request.form.get("chars_per_line")
            enable_special_letters_value = request.form.get("enable_special_letters")
            check_for_updates_value = request.form.get("check_for_updates")

            try:
                if ip_address:
                    config_service.set_printer_ip(ip_address)

                if chars_per_line_value:
                    chars_per_line = int(chars_per_line_value)
                    config_service.set_chars_per_line(chars_per_line)

                enable_special_letters = (enable_special_letters_value or "").lower() in ("true", "yes", "1")
                config_service.set_enable_special_letters(enable_special_letters)

                check_for_updates = (check_for_updates_value or "").lower() in ("true", "yes", "1")
                config_service.set_check_for_updates(check_for_updates)

                flash("Settings updated successfully.", "success")
            except ValueError:
                flash("Invalid number for chars per line.", "error")
            except PrintermError as e:
                flash(f"Configuration error: {e.message}", "error")
            except Exception as e:
                ErrorHandler.handle_error(e, "Error updating settings")
                flash(f"Failed to update settings: {e}", "error")

            return redirect(url_for("settings"))

        # GET request - show current settings
        try:
            ip_address = config_service.get_printer_ip()
        except ConfigurationError:
            ip_address = ""

        chars_per_line = config_service.get_chars_per_line()
        enable_special_letters = config_service.get_enable_special_letters()
        check_for_updates = config_service.get_check_for_updates()

        return render_template(
            "settings.html",
            templates=templates,
            ip_address=ip_address,
            chars_per_line=chars_per_line,
            enable_special_letters=enable_special_letters,
            check_for_updates=check_for_updates,
        )
    except Exception as e:
        ErrorHandler.handle_error(e, "Error in settings")
        flash(f"Settings error: {e}", "error")
        return redirect(url_for("index"))


def main() -> None:
    port = config_service.get_flask_port()
    serve(app, host="0.0.0.0", port=port)  # nosec: B104
