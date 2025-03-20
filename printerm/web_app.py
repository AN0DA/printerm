import logging
import os

from flask import Flask, flash, redirect, render_template, request, url_for
from waitress import serve
from werkzeug.wrappers import Response

from printerm.config import (
    PRINT_TEMPLATE_FOLDER,
    get_chars_per_line,
    get_check_for_updates,
    get_enable_special_letters,
    get_flask_secret_key,
    get_printer_ip,
    set_chars_per_line,
    set_check_for_updates,
    set_enable_special_letters,
    set_printer_ip,
)
from printerm.printer import ThermalPrinter
from printerm.template_manager import TemplateManager
from printerm.utils import compute_agenda_variables

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = get_flask_secret_key()

template_manager = TemplateManager(PRINT_TEMPLATE_FOLDER)


@app.route("/")
def index() -> str:
    templates = template_manager.templates
    return render_template("index.html", templates=templates)


@app.route("/print/<template_name>", methods=["GET", "POST"])
def print_template(template_name: str) -> Response | str:
    templates = template_manager.templates
    template = template_manager.get_template(template_name)
    if not template:
        flash(f"Template '{template_name}' not found.", "error")
        return redirect(url_for("index"))
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

            ip_address = get_printer_ip()
            with ThermalPrinter(ip_address, template_manager) as printer:
                printer.print_template(template_name, context)
            flash(f"Printed using template '{template_name}'.", "success")
            return redirect(url_for("index"))

        except Exception as e:
            logger.error(f"Error printing template '{template_name}': {e}", exc_info=True)
            flash(f"Failed to print: {e}", "error")
    return render_template(
        "print_template.html",
        templates=templates,
        template=template,
        markdown_vars=[var["name"] for var in template.get("variables", []) if var.get("markdown", False)],
    )


@app.route("/settings", methods=["GET", "POST"])
def settings() -> Response | str:
    templates = template_manager.templates

    if request.method == "POST":
        ip_address = request.form.get("ip_address")
        chars_per_line_value = request.form.get("chars_per_line")
        enable_special_letters_value = request.form.get("enable_special_letters")
        check_for_updates_value = request.form.get("check_for_updates")

        set_printer_ip(ip_address or "")

        try:
            chars_per_line = int(chars_per_line_value or 0)
            set_chars_per_line(chars_per_line)
        except ValueError:
            flash("Invalid number for chars per line.", "error")
            return redirect(url_for("settings"))

        if (enable_special_letters_value or "").lower() in ("true", "yes", "1"):
            enable_special_letters = True
        elif (enable_special_letters_value or "").lower() in ("false", "no", "0"):
            enable_special_letters = False
        else:
            flash("Invalid value for enable special letters. Use True or False.", "error")
            return redirect(url_for("settings"))
        set_enable_special_letters(enable_special_letters)

        if (check_for_updates_value or "").lower() in ("true", "yes", "1"):
            check_for_updates = True
        elif (check_for_updates_value or "").lower() in ("false", "no", "0"):
            check_for_updates = False
        else:
            flash("Invalid value for check for updates. Use True or False.", "error")
            return redirect(url_for("settings"))
        set_check_for_updates(check_for_updates)

        flash("Settings saved.", "success")
        return redirect(url_for("index"))
    else:
        try:
            ip_address = get_printer_ip()
        except ValueError:
            ip_address = ""
        chars_per_line = get_chars_per_line()
        enable_special_letters = get_enable_special_letters()
        check_for_updates = get_check_for_updates()
        return render_template(
            "settings.html",
            templates=templates,
            ip_address=ip_address,
            chars_per_line=chars_per_line,
            enable_special_letters=enable_special_letters,
            check_for_updates=check_for_updates,
        )


def main() -> None:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    template_dir = os.path.join(dir_path, "templates")
    static_dir = os.path.join(dir_path, "static")
    app.template_folder = template_dir
    app.static_folder = static_dir

    serve(app, host="0.0.0.0", port=5555)  # nosec: B104


if __name__ == "__main__":
    main()
