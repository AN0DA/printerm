import os
from typing import Any

import yaml


class TemplateManager:
    def __init__(self, template_dir: str):
        self.template_dir = template_dir
        self.templates = self.load_templates()

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
