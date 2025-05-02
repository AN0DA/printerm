import importlib.util
import os
import sys
from collections.abc import Callable
from typing import Any

import yaml


class TemplateManager:
    def __init__(self, template_dir: str):
        self.template_dir = template_dir
        self.templates = self.load_templates()
        self.scripts_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "scripts")

    def load_templates(self) -> dict[str, dict[str, Any]]:
        templates = {}
        for filename in os.listdir(self.template_dir):
            if filename.endswith(".yaml"):
                path = os.path.join(self.template_dir, filename)
                with open(path, encoding="utf-8") as file:
                    template = yaml.safe_load(file)
                    key = os.path.splitext(filename)[0]
                    templates[key] = template
        return templates

    def get_template(self, name: str) -> dict[str, Any]:
        template = self.templates.get(name)

        if not template:
            raise ValueError(f"Template '{name}' not found.")
        return template

    def list_templates(self) -> list[str]:
        return list(self.templates.keys())

    def get_template_script(self, template_name: str) -> Callable[[], dict[str, Any]] | None:
        """
        Get the compute_variables function for a template script if it exists.

        Args:
            template_name: The name of the template

        Returns:
            A callable that computes variables for the template, or None if no script exists
        """
        script_path = os.path.join(self.scripts_dir, f"{template_name}.py")
        if not os.path.exists(script_path):
            return None

        # Import the script module
        try:
            spec = importlib.util.spec_from_file_location(f"printerm.templates.scripts.{template_name}", script_path)
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Check if the module has a compute_variables function
            if hasattr(module, "compute_variables") and callable(module.compute_variables):
                return module.compute_variables
            return None
        except (ImportError, AttributeError):
            return None
