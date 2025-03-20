# printerm Module

This directory contains the main source code for the Thermal Printer Application.

## Directory Structure

- `app.py`: The CLI entry point of the application.
- `config.py`: Handles configuration settings.
- `gui.py`: Contains the GUI implementation using PyQt6.
- `printer.py`: Manages the printer connection and printing logic.
- `template_manager.py`: Manages loading and accessing print templates.
- `utils.py`: Utility functions, including template rendering.
- `web_app.py`: The Flask web application.
- `print_templates/`: Directory containing template YAML files.
  - `README.md`: Information about creating and managing templates.
- `templates/`: Contains HTML templates for the web application.
- `static/`: Contains static files for the web application.

## Modules

### app.py

The main CLI application that provides various commands to interact with the printer, manage settings, and update the application.

### config.py

Handles reading and writing configuration settings from `printerm_config.ini`.

### gui.py

Provides a PyQt6-based GUI for users who prefer a graphical interface.

### printer.py

Contains the `ThermalPrinter` class, which manages the connection to the printer and handles the printing process.

### template_manager.py

Loads and manages print templates from the `print_templates/` directory.

### utils.py

Includes utility classes and functions such as `TemplateRenderer`, which handles rendering templates using Jinja2 and Mistune.

### web_app.py

A Flask web application that provides a web interface to the application.

## How to Add New Modules

1. Create a new `.py` file in the `printerm/` directory.
2. Ensure you follow the existing code style and structure.
3. Update `__init__.py` if necessary to expose new modules.
