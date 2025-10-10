# Thermal Printer Application

Welcome to the Thermal Printer Application! This project provides a flexible and extensible way to interact with networked thermal printers. It supports printing tasks, tickets, small notes, and custom templates through a Command-Line Interface (CLI), Graphical User Interface (GUI), and a web application.

## Table of Contents

- [Thermal Printer Application](#thermal-printer-application)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Getting Started](#getting-started)
    - [Installation](#installation)
      - [Requirements](#requirements)
    - [Usage](#usage)
      - [Command-Line Interface](#command-line-interface)
        - [Printing a Template](#printing-a-template)
        - [Updating Settings](#updating-settings)
        - [Manual Update](#manual-update)
      - [Graphical User Interface](#graphical-user-interface)
      - [Web Application](#web-application)
    - [Configuration](#configuration)
      - [Configuration Options](#configuration-options)
      - [Editing Configuration](#editing-configuration)
        - [Through the CLI](#through-the-cli)
        - [Manually](#manually)
  - [Templates](#templates)
    - [Built-in Templates](#built-in-templates)
    - [Adding New Templates](#adding-new-templates)
  - [Development](#development)
    - [Setting Up the Development Environment](#setting-up-the-development-environment)
    - [Running Tests](#running-tests)
    - [Code Style and Formatting](#code-style-and-formatting)
  - [Contributing](#contributing)
    - [Guidelines](#guidelines)
  - [License](#license)
  - [Credits](#credits)

## Features

- **Multi-Interface Support**: Use the application via CLI, GUI, or web interface.
- **Template-Based Printing**: Define print templates using YAML files with Jinja2 and Markdown support.
- **Dynamic Templates**: Easily add new templates without changing the code.
- **Auto-Update Feature**: Automatically check for updates and prompt the user to update.
- **Customizable Settings**: Configure printer IP, characters per line, special character handling, and update preferences.
- **Support for Special Characters**: Handle special characters using transliteration.

## Getting Started

### Installation

You can install the Thermal Printer Application directly from GitHub:

```bash
pipx install printerm
```

#### Requirements

- Python 3.13 or higher
- Networked Thermal Printer compatible with the python-escpos library
-	Optional for GUI: PyQt6
-	Optional for Web App: Flask

### Usage

#### Command-Line Interface

After installation, you can use the printerm command:

```bash
printerm --help
```

##### Printing a Template

List available templates:

```bash
printerm print-template
```

Print using a template:

```bash
printerm print-template <template_name>
```

Example:

```bash
printerm print-template task
```

##### Updating Settings

Set the printer IP address:

```bash
printerm settings set-ip <printer_ip>
```

Show current settings:

```bash
printerm settings show
```

##### Manual Update

Manually update the application:

```bash
printerm update
```

#### Graphical User Interface

Launch the GUI:

```bash
printerm gui
```

Features:

-	Select templates and fill in required variables.
-	Access settings to configure the application.
-	Print directly from the interface.

#### Web Application

Launch the web server:

```bash
printerm web
```

By default, the web app runs on http://0.0.0.0:5555. Open this URL in your browser.

Features:

-	Select and print templates.
-	Access and update settings.
-	User-friendly interface accessible from any device on the network.

### Configuration

The application uses a configuration file config.ini, located in user config directory. You can edit this file directly or through the application interfaces.

#### Configuration Options

-	Printer IP Address: The IP address of your thermal printer.
-	Characters Per Line: Number of characters the printer can print per line (default is 32).
-	Enable Special Letters: Enable or disable special character handling (True/False).
-	Check for Updates: Enable or disable automatic update checks (True/False).

#### Editing Configuration

##### Through the CLI

```bash
printerm config edit
```

##### Manually

Open config.ini in your preferred text editor and modify the settings.

## Templates

Templates define what and how the content is printed. They are stored in the printerm/print_templates/ directory as YAML files.

### Built-in Templates

- Task: Print a task with a title and text.
-	Small Note: Print a blank note with space to write.
-	Ticket: Print a ticket with a title, ticket number, and text.
-	Weekly Agenda: Print a ready-to-fill agenda for the current week.

### Adding New Templates

1.	Create a YAML file in the printerm/print_templates/ directory.
2.	Define the template with metadata, variables, and segments.
3.	Use Jinja2 syntax for dynamic content and Mistune-supported Markdown for formatting.

Example template greeting.yaml:

```yaml
name: Greeting
description: Print a greeting message.
variables:
  - name: name
    description: Recipient's Name
    required: true
  - name: message
    description: Personal Message
    required: true
segments:
  - text: "**Hello**, {{ name }}!\n"
    styles:
      align: center
      bold: true
  - text: "{{ message }}\n"
    styles:
      align: left
```

## Development

### Setting Up the Development Environment

1.	Clone the repository:

```bash
git clone https://github.com/AN0DA/printerm.git
```


2.	Navigate to the project directory:

```bash
cd printerm
```


4.	Install the dependencies:

```bash
uv sync
```



### Running Tests

We use pytest for testing. To run the tests:

```bash
make test
```

### Code Style and Formatting

We follow PEP 8 style guidelines. Please ensure your code passes style checks using tools like flake8 or black.

```bash
make lint mypy
```

## Contributing

We welcome contributions! Here’s how you can help:

1.	Report Bugs: If you find a bug, please create an issue describing the problem.
2. Suggest Features: Have an idea? Open an issue to discuss it.
3. Submit Pull Requests: Fork the repository, make your changes, and submit a pull request.

### Guidelines

-	Follow the existing code style.
-	Write tests for your changes.
-	Update documentation if necessary.

## License

We recommend using the MIT License for this project.

```plaintext
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
...
```

This license is permissive, allowing others to use, modify, and distribute the software with minimal restrictions. It encourages collaboration and sharing while protecting your liability.

See the [LICENSE] file for details.

## Credits

[Label Printer](https://icons8.com/icon/80267/label-printer) icon by [Icons8](https://icons8.com)
