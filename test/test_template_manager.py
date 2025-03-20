import os
from collections.abc import Generator
from pathlib import Path

import pytest

from printerm.template_manager import TemplateManager


@pytest.fixture
def template_dir(tmp_path: Path) -> Generator[str, None, None]:
    # Set up a temporary template directory
    templates_path = tmp_path / "print_templates"
    templates_path.mkdir()
    yield str(templates_path)
    # Teardown happens automatically


def test_load_templates(template_dir: str) -> None:
    # Create a sample template file
    template_content = """
name: Test Template
description: A test template
variables:
  - name: title
    description: Title
    required: true
    markdown: false
segments:
  - text: "{{ title }}"
    markdown: false
    styles: {}
"""
    template_file = os.path.join(template_dir, "test_template.yaml")
    with open(template_file, "w", encoding="utf-8") as f:
        f.write(template_content)

    manager = TemplateManager(template_dir)
    templates = manager.templates

    assert "test_template" in templates
    assert templates["test_template"]["name"] == "Test Template"


def test_get_template(template_dir: str) -> None:
    # Create a sample template file
    template_content = """
name: Sample Template
description: A sample template
variables: []
segments: []
"""
    template_file = os.path.join(template_dir, "sample.yaml")
    with open(template_file, "w", encoding="utf-8") as f:
        f.write(template_content)

    manager = TemplateManager(template_dir)
    template = manager.get_template("sample")
    assert template is not None
    assert template["name"] == "Sample Template"


def test_list_templates(template_dir: str) -> None:
    # Create multiple sample template files
    template_names = ["template1.yaml", "template2.yaml"]
    for name in template_names:
        with open(os.path.join(template_dir, name), "w", encoding="utf-8") as f:
            f.write(f"name: {name}\n")

    manager = TemplateManager(template_dir)
    templates_list = manager.list_templates()
    assert len(templates_list) == 2
    assert "template1" in templates_list
    assert "template2" in templates_list
