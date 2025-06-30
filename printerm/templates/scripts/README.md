# Template Scripts System

The template scripts system provides a powerful and extensible way to generate dynamic content for your thermal printer templates. Instead of hardcoding logic in interface files, templates can now reference scripts that generate context variables automatically.

## Overview

The template scripts system consists of several key components:

- **Template Scripts**: Python classes that generate context variables
- **Script Registry**: Central registry for discovering and managing scripts
- **Script Loader**: Dynamically loads script modules
- **Enhanced Template Service**: Integrates scripts with template rendering

## How It Works

### 1. Template Configuration

Templates can now specify a script to generate their context variables:

```yaml
name: Weekly Agenda
description: Print a ready-to-fill agenda for the current week.
script: agenda_generator  # Reference to script
variables: []  # Can be empty if script generates context
segments:
  - text: "Week {{ week_number }}\n"
    # ... rest of template
```

### 2. Script Implementation

Scripts are Python classes that inherit from `TemplateScript`:

```python
from .base import TemplateScript

class AgendaGeneratorScript(TemplateScript):
    @property
    def name(self) -> str:
        return "agenda_generator"
    
    @property 
    def description(self) -> str:
        return "Generates variables for weekly agenda templates"
    
    def generate_context(self, **kwargs) -> Dict[str, Any]:
        # Generate and return context variables
        return {
            "week_number": 27,
            "days": [...],
            # ... more variables
        }
```

### 3. Automatic Integration

The template service automatically:
- Discovers available scripts
- Checks if templates have associated scripts
- Executes scripts to generate context
- Falls back to manual input if no script is available

## Available Scripts

### agenda_generator
Generates variables for weekly agenda templates including dates and day names.

**Generated Variables:**
- `week_number`: ISO week number
- `week_start_date`: Start date of the week (Monday)
- `week_end_date`: End date of the week (Sunday)
- `days`: List of day objects with day_name, date, etc.
- `year`, `month`, `current_date`: Additional date info

**Optional Parameters:**
- `date`: Specific date to generate agenda for (defaults to today)
- `week_offset`: Number of weeks to offset from the base date

### date_utils
Provides various date and time utilities for templates.

**Generated Variables:**
- Basic date/time: `current_date`, `current_time`, `current_datetime`
- Date components: `year`, `month`, `day`, `weekday`
- Formatted dates: `date_short`, `date_medium`, `date_long`, `date_full`
- Month/day names: `month_name`, `day_name`, etc.
- Time components: `hour`, `minute`, `ampm`
- Relative dates: `yesterday`, `tomorrow`

**Optional Parameters:**
- `date`: Specific date to use (defaults to today)
- `timezone`: Timezone to use
- `format_style`: Date format style

### shopping_list
Generates a formatted shopping list with categories and quantities.

**Generated Variables:**
- `title`: List title
- `items`: List of all items with details
- `categorized_items`: Items grouped by category
- `formatted_list`: Ready-to-print formatted list
- `total_items`: Number of items

**Required Parameters:**
- `items`: List of items to include

**Optional Parameters:**
- `title`: Title for the list
- `show_categories`: Whether to group by categories

## Creating Custom Scripts

### Step 1: Create Script Class

Create a new Python file in `printerm/templates/scripts/`:

```python
# my_custom_script.py
from typing import Any, Dict
from .base import TemplateScript

class MyCustomScript(TemplateScript):
    @property
    def name(self) -> str:
        return "my_custom_script"
    
    @property
    def description(self) -> str:
        return "Description of what this script does"
    
    def generate_context(self, **kwargs) -> Dict[str, Any]:
        # Your custom logic here
        return {
            "custom_variable": "custom_value",
            # ... more variables
        }
    
    def get_required_parameters(self) -> list[str]:
        return ["required_param"]  # Optional
    
    def get_optional_parameters(self) -> list[str]:
        return ["optional_param"]  # Optional
```

### Step 2: Create Template

Create a template that uses your script:

```yaml
name: My Custom Template
description: Uses my custom script
script: my_custom_script
variables: []
segments:
  - text: "{{ custom_variable }}\n"
    # ... rest of template
```

### Step 3: Test

The script will be automatically discovered and available for use.

## Best Practices

### Script Design
- Keep scripts focused on a single responsibility
- Use descriptive names and documentation
- Handle errors gracefully
- Validate input parameters
- Log important events for debugging

### Parameter Handling
- Define required vs optional parameters clearly
- Provide sensible defaults
- Validate parameter types and values
- Document parameter formats

### Context Generation
- Generate comprehensive but relevant context
- Use consistent naming conventions
- Include metadata (counts, totals, etc.)
- Consider template rendering requirements

### Error Handling
- Validate all inputs
- Provide meaningful error messages
- Use logging for debugging
- Fail gracefully with fallbacks

## Debugging

### Enable Debug Logging
```python
import logging
logging.getLogger('printerm.templates.scripts').setLevel(logging.DEBUG)
```

### Test Scripts Individually
```python
from printerm.templates.scripts import ScriptRegistry

registry = ScriptRegistry()
context = registry.execute_script('script_name', param1='value1')
print(context)
```

### Validate Script Discovery
```python
from printerm.templates.scripts import ScriptLoader

loader = ScriptLoader()
scripts = loader.discover_scripts()
print("Discovered scripts:", list(scripts.keys()))
```

## Migration Guide

### From Hardcoded Logic

If you have hardcoded template logic like the old `compute_agenda_variables()`:

1. **Create a script class** that encapsulates the logic
2. **Update the template YAML** to reference the script
3. **Remove hardcoded calls** from interface files
4. **Test** the new script-based approach

### From Manual Input

If you have templates that require manual input:

1. **Analyze the input requirements** 
2. **Determine if a script would be beneficial**
3. **Create a script** that generates sensible defaults
4. **Optionally support both** script and manual modes

## Architecture

```
Template System
├── Templates (YAML files)
│   ├── Reference scripts by name
│   └── Define rendering segments
├── Scripts (Python modules)
│   ├── Generate context variables
│   └── Handle business logic
├── Script Registry
│   ├── Discovers available scripts
│   └── Manages script lifecycle
└── Template Service
    ├── Integrates scripts with templates
    └── Provides unified API
```

## Benefits

- **Decoupled**: Template logic is separate from interface code
- **Extensible**: Easy to add new templates with custom behavior
- **Maintainable**: Single responsibility for each component
- **Testable**: Scripts can be unit tested independently
- **Consistent**: Same API across all interfaces (CLI, GUI, Web)
- **Flexible**: Support for both scripted and manual input modes
