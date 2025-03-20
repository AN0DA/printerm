# Print Templates

This directory contains print templates used by the Thermal Printer Application. Templates are defined in YAML files and allow you to customize what and how content is printed.

## Template Structure

A template YAML file consists of:

- **name**: The display name of the template.
- **description**: A brief description of what the template does.
- **variables**: A list of variables required by the template.
- **segments**: The content to print, along with styling options.

### Example Template

```yaml
name: Greeting
description: Print a personalized greeting.
variables:
  - name: name
    description: Recipient's Name
    required: true
segments:
  - text: "**Hello**, {{ name }}!\n"
    styles:
      align: center
      bold: true
```

## Variables

Variables are placeholders that will be replaced with user-provided values when printing. Each variable has:

-	`name`: The variable name used in the template.
-	`description`: A user-friendly description displayed in interfaces.
-	`required`: Whether the variable must be provided.

## Segments

Segments define the content and styling of the printed output.

-	`text`: The content to print. Supports Jinja2 templating and Markdown syntax.
-	`styles`: Styling options for the segment.

### Supported Styles

-	`align`: Text alignment (`left`, `center`, `right`).
-	`font`: Font type (`a`, `b`).
-	`bold`: Bold text (`true`, `false`).
-	`italic`: Italic text (`true`, `false`).
-	`underline`: Underline text (`true`, `false`).
-	`double_width`: Double the text width (`true`, `false`).
-	`double_height`: Double the text height (`true`, `false`).

## Adding a New Template

1.	Create a YAML file in this directory, e.g., my_template.yaml.
2.	Define the template using the structure described above.
3.	Save the file. The application will automatically detect new templates.

### Examples

#### Task Template

```yaml
name: Task
description: Print a task with title and description.
variables:
  - name: title
    description: Task Title
    required: true
  - name: description
    description: Task Description
    required: true
segments:
  - text: "# {{ title }}\n"
    styles:
      bold: true
      double_height: true
  - text: "{{ description }}\n"
    styles: {}
```

#### Ticket Template

```yaml
name: Ticket
description: Print a ticket with number and details.
variables:
  - name: ticket_number
    description: Ticket Number
    required: true
  - name: details
    description: Ticket Details
    required: false
segments:
  - text: "## Ticket {{ ticket_number }}\n"
    styles:
      bold: true
  - text: "{{ details }}\n"
    styles: {}
```
