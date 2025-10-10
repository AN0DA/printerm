import logging
import os

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from waitress import serve
from werkzeug.wrappers import Response

from printerm import __version__
from printerm.error_handling import ErrorHandler
from printerm.exceptions import ConfigurationError, PrintermError
from printerm.services import service_container
from printerm.services.interfaces import ConfigService, PrinterService, TemplateService, UpdateService

logger = logging.getLogger(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))
template_dir = os.path.join(dir_path, "web_templates")
# Get services from container
config_service = service_container.get(ConfigService)
template_service = service_container.get(TemplateService)
update_service = service_container.get(UpdateService)
app = Flask(__name__, template_folder=template_dir)
app.secret_key = config_service.get_flask_secret_key()


class WebThemeManager:
    """Manage web interface themes and styling."""

    @staticmethod
    def get_theme_from_request() -> str:
        """Get theme preference from request or default to light."""
        return request.cookies.get("theme", "light")

    @staticmethod
    def get_theme_styles(theme: str) -> dict[str, str]:
        """Get CSS custom properties for the specified theme."""
        if theme == "dark":
            return {
                "primary": "#4a9eff",
                "primary-dark": "#357abd",
                "background": "#1a1a1a",
                "surface": "#2d2d2d",
                "surface-variant": "#3a3a3a",
                "text": "#ffffff",
                "text-secondary": "#b0b0b0",
                "border": "#555555",
                "success": "#4caf50",
                "warning": "#ff9800",
                "error": "#f44336",
                "card-background": "#2d2d2d",
                "card-hover": "#3a3a3a",
                "input-background": "#3a3a3a",
                "navbar-bg": "#1a1a1a",
                "navbar-brand": "#ffffff",
            }
        else:  # light theme
            return {
                "primary": "#2196f3",
                "primary-dark": "#1976d2",
                "background": "#f8f9fa",
                "surface": "#ffffff",
                "surface-variant": "#f5f5f5",
                "text": "#212529",
                "text-secondary": "#6c757d",
                "border": "#dee2e6",
                "success": "#198754",
                "warning": "#fd7e14",
                "error": "#dc3545",
                "card-background": "#ffffff",
                "card-hover": "#f8f9fa",
                "input-background": "#ffffff",
                "navbar-bg": "#212529",
                "navbar-brand": "#ffffff",
            }


class WebSettings:
    """Handle web interface specific settings using ConfigService."""

    def __init__(self, config_service: ConfigService) -> None:
        self.config_service = config_service

    def add_recent_template(self, template_name: str) -> None:
        """Add template to recent list."""
        try:
            recent = self.get_recent_templates()
            if template_name in recent:
                recent.remove(template_name)
            recent.insert(0, template_name)
            # Keep only last 5 recent templates
            recent = recent[:5]
            self.config_service.set_gui_recent_templates(recent)
        except Exception as e:
            logger.warning(f"Failed to save recent template: {e}")

    def get_recent_templates(self) -> list[str]:
        """Get list of recent templates."""
        try:
            return self.config_service.get_gui_recent_templates()
        except Exception as e:
            logger.warning(f"Failed to load recent templates: {e}")
            return []


web_settings = WebSettings(config_service)


@app.route("/")
def index() -> str:
    templates = {name: template_service.get_template(name) for name in template_service.list_templates()}
    recent_templates = web_settings.get_recent_templates()
    theme = WebThemeManager.get_theme_from_request()
    theme_styles = WebThemeManager.get_theme_styles(theme)

    # Check for updates
    update_available = False
    if config_service.get_check_for_updates():
        try:
            update_available = update_service.check_for_updates_with_retry(__version__)
        except Exception as e:
            logger.warning(f"Failed to check for updates: {e}")

    return render_template(
        "index.html",
        templates=templates,
        recent_templates=recent_templates,
        theme=theme,
        theme_styles=theme_styles,
        update_available=update_available,
    )


@app.route("/print/<template_name>", methods=["GET", "POST"])
def print_template(template_name: str) -> Response | str:
    try:
        templates = {name: template_service.get_template(name) for name in template_service.list_templates()}
        template = template_service.get_template(template_name)
        theme = WebThemeManager.get_theme_from_request()
        theme_styles = WebThemeManager.get_theme_styles(theme)
        if request.method == "POST":
            context = {}
            try:
                # Check if template has a script
                if template_service.has_script(template_name):
                    context = template_service.generate_template_context(template_name)
                else:
                    context = {var["name"]: request.form.get(var["name"]) for var in template.get("variables", [])}
                    if not context:
                        confirm = request.form.get("confirm")
                        if confirm == "no":
                            display_name = template.get("name", template_name)
                            flash(f"Cancelled printing {display_name}.", "info")
                            return redirect(url_for("index"))
                # Add to recent templates
                web_settings.add_recent_template(template_name)
                with service_container.get(PrinterService) as printer:
                    printer.print_template(template_name, context)
                display_name = template.get("name", template_name)
                flash(f"Printed using template '{display_name}'.", "success")
                return redirect(url_for("index"))
            except PrintermError as e:
                display_name = template.get("name", template_name)
                ErrorHandler.handle_error(e, f"Error printing template '{display_name}'")
                flash(f"Failed to print: {e.message}", "error")
            except Exception as e:
                display_name = template.get("name", template_name)
                ErrorHandler.handle_error(e, f"Error printing template '{display_name}'")
                flash(f"Failed to print: {e}", "error")
        return render_template(
            "print_template.html",
            templates=templates,
            template=template,
            template_name=template_name,
            markdown_vars=[var["name"] for var in template.get("variables", []) if var.get("markdown", False)],
            has_script=template_service.has_script(template_name),
            theme=theme,
            theme_styles=theme_styles,
        )
    except PrintermError as e:
        ErrorHandler.handle_error(e, f"Error accessing template '{template_name}'")
        flash(f"Template error: {e.message}", "error")
        return redirect(url_for("index"))
    except Exception as e:
        ErrorHandler.handle_error(e, f"Error accessing template '{template_name}'")
        try:
            template = template_service.get_template(template_name)
            display_name = template.get("name", template_name)
        except Exception:
            display_name = template_name
        flash(f"Template '{display_name}' not found.", "error")
        return redirect(url_for("index"))


@app.route("/settings", methods=["GET", "POST"])
def settings() -> Response | str:
    try:
        templates = {name: template_service.get_template(name) for name in template_service.list_templates()}
        theme = WebThemeManager.get_theme_from_request()
        theme_styles = WebThemeManager.get_theme_styles(theme)
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
            theme=theme,
            theme_styles=theme_styles,
        )
    except Exception as e:
        ErrorHandler.handle_error(e, "Error in settings")
        flash(f"Settings error: {e}", "error")
        return redirect(url_for("index"))


@app.route("/api/validate/<template_name>", methods=["POST"])
def validate_template(template_name: str) -> Response:
    """Validate template with current context."""
    try:
        template = template_service.get_template(template_name)
        variables = template.get("variables", [])
        # Check for required variables
        missing_required = []
        context = request.get_json() or {}
        for var in variables:
            if var.get("required", False):
                value = context.get(var["name"], "").strip()
                if not value:
                    missing_required.append(
                        {
                            "field": var["name"],
                            "label": var.get("description") or var["name"],
                        }
                    )
        if missing_required:
            return jsonify(
                {
                    "valid": False,
                    "errors": [f"Required field missing: {field['label']}" for field in missing_required],
                    "invalid_fields": missing_required,
                }
            )
        return jsonify({"valid": True, "message": "Template validation successful", "invalid_fields": []})
    except Exception as e:
        response = jsonify({"valid": False, "errors": [f"Validation error: {str(e)}"], "invalid_fields": []})
        response.status_code = 400
        return response


@app.route("/api/theme", methods=["POST"])
def set_theme() -> Response:
    """Set the user's theme preference."""
    try:
        request_data = request.get_json() or {}
        theme = request_data.get("theme", "light")
        if theme not in ["light", "dark"]:
            theme = "light"
        response = jsonify({"success": True, "theme": theme})
        response.set_cookie("theme", theme, max_age=60 * 60 * 24 * 365)  # 1 year
        return response
    except Exception as e:
        response = jsonify({"success": False, "error": str(e)})
        response.status_code = 400
        return response


@app.route("/api/updates/check", methods=["GET"])
def check_updates() -> Response:
    """Check for available updates."""
    try:
        update_available = False
        latest_version = None
        current_version = __version__

        if config_service.get_check_for_updates():
            update_available = update_service.is_new_version_available(current_version)
            if update_available:
                latest_version = update_service.get_latest_version()

        return jsonify(
            {
                "update_available": update_available,
                "current_version": current_version,
                "latest_version": latest_version,
                "check_enabled": config_service.get_check_for_updates(),
            }
        )
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        response = jsonify(
            {
                "update_available": False,
                "error": "Failed to check for updates",
                "check_enabled": config_service.get_check_for_updates(),
            }
        )
        response.status_code = 500
        return response


def main() -> None:
    port = config_service.get_flask_port()
    serve(app, host="0.0.0.0", port=port)  # nosec: B104
