from pathlib import Path
from unittest.mock import MagicMock

import pytest

from printerm.template_manager import TemplateManager
from printerm.utils import TemplateRenderer, compute_agenda_variables, get_latest_version, is_new_version_available


@pytest.fixture
def template_manager(tmp_path: Path) -> TemplateManager:
    # Set up a temporary template directory and TemplateManager
    templates_path = tmp_path / "print_templates"
    templates_path.mkdir()

    # Create a sample template file
    template_content = """
name: Test Template
description: A test template
variables:
  - name: name
    description: Name
    required: true
    markdown: false
segments:
  - text: | 
      **Hello there**, {{ name }}!
      Nice to meet you.
    markdown: true
    styles: {}
"""
    template_file = templates_path / "test_template.yaml"
    with open(template_file, "w", encoding="utf-8") as f:
        f.write(template_content)

    manager = TemplateManager(str(templates_path))
    return manager


def test_template_renderer_markdown_parsing(template_manager: TemplateManager) -> None:
    renderer = TemplateRenderer(template_manager)
    context = {"name": "Alice"}
    segments = renderer.render_from_template("test_template", context)

    assert segments == [
        {"styles": {"bold": True}, "text": "Hello there"},
        {"styles": {}, "text": ", Alice!"},
        {"styles": {}, "text": "\n"},
        {"styles": {}, "text": "Nice to meet you."},
    ]


def test_template_renderer_special_letters_disabled(template_manager: TemplateManager) -> None:
    renderer = TemplateRenderer(template_manager)
    renderer.enable_special_letters = False
    context = {"name": "Zażółć gęślą jaźń"}
    segments = renderer.render_from_template("test_template", context)

    assert segments == [
        {"styles": {"bold": True}, "text": "Hello there"},
        {"styles": {}, "text": ", Zazolc gesla jazn!"},
        {"styles": {}, "text": "\n"},
        {"styles": {}, "text": "Nice to meet you."},
    ]


def test_compute_agenda_variables() -> None:
    variables = compute_agenda_variables()
    assert "week_number" in variables
    assert "week_start_date" in variables
    assert "week_end_date" in variables
    assert "days" in variables
    assert len(variables["days"]) == 7


def test_get_latest_version(mocker: MagicMock) -> None:
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"tag_name": "v1.2.3"}
    mocker.patch("printerm.utils.requests.get", return_value=mock_response)
    latest_version = get_latest_version()
    assert latest_version == "1.2.3"


def test_is_new_version_available(mocker: MagicMock) -> None:
    mocker.patch("printerm.utils.get_latest_version", return_value="1.2.3")
    assert is_new_version_available("1.0.0") is True
    assert is_new_version_available("1.2.3") is False
    assert is_new_version_available("1.3.0") is False


def test_template_renderer_missing_template(template_manager: TemplateManager) -> None:
    renderer = TemplateRenderer(template_manager)
    with pytest.raises(ValueError, match="Template 'nonexistent' not found."):
        renderer.render_from_template("nonexistent", {})
