"""Tests for template service."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from printerm.exceptions import TemplateError
from printerm.services.template_service import TemplateServiceImpl


class TestTemplateServiceImpl:
    """Test cases for TemplateServiceImpl."""

    def test_init_with_default_template_dir(self) -> None:
        """Test initialization with default template directory."""
        with patch.object(TemplateServiceImpl, "load_templates"):
            service = TemplateServiceImpl()
            assert service.template_dir is not None
            assert "print_templates" in service.template_dir

    def test_init_with_custom_template_dir(self, temp_template_dir: str) -> None:
        """Test initialization with custom template directory."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)
        assert service.template_dir == temp_template_dir
        assert len(service.templates) > 0  # Should load templates

    def test_init_with_config_service(self, temp_template_dir: str, mock_config_service: MagicMock) -> None:
        """Test initialization with config service."""
        service = TemplateServiceImpl(template_dir=temp_template_dir, config_service=mock_config_service)
        assert service.config_service == mock_config_service

    def test_load_templates_success(self, temp_template_dir: str) -> None:
        """Test successful loading of templates."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        # Should load the test templates created in fixture
        assert "test_template" in service.templates
        assert "script_template" in service.templates
        assert "markdown_template" in service.templates

        # Check template content
        test_template = service.templates["test_template"]
        assert test_template["name"] == "Test Template"
        assert len(test_template["segments"]) == 1

    def test_load_templates_missing_directory(self) -> None:
        """Test error when template directory doesn't exist."""
        with pytest.raises(TemplateError, match="Failed to load templates"):
            TemplateServiceImpl(template_dir="/nonexistent/path")

    def test_load_templates_invalid_yaml(self, temp_template_dir: str) -> None:
        """Test handling of invalid YAML files."""
        # Create an invalid YAML file
        invalid_file = Path(temp_template_dir) / "invalid.yaml"
        with open(invalid_file, "w") as f:
            f.write("invalid: yaml: content: [")

        # Should not raise exception but log warning
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        # Should still load valid templates, but not the invalid one
        assert "test_template" in service.templates
        assert "invalid" not in service.templates

    def test_get_template_success(self, temp_template_dir: str) -> None:
        """Test successful template retrieval."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        template = service.get_template("test_template")

        assert template["name"] == "Test Template"
        assert template["description"] == "A test template"

    def test_get_template_not_found(self, temp_template_dir: str) -> None:
        """Test error when template is not found."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        with pytest.raises(TemplateError, match="Template 'nonexistent' not found"):
            service.get_template("nonexistent")

    def test_list_templates(self, temp_template_dir: str) -> None:
        """Test listing available templates."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        templates = service.list_templates()

        assert "test_template" in templates
        assert "script_template" in templates
        assert "markdown_template" in templates
        assert len(templates) >= 3

    def test_render_template_with_context(self, temp_template_dir: str, sample_context: dict) -> None:
        """Test rendering template with provided context."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        context = {"title": "My Title", "content": "My Content"}
        segments = service.render_template("test_template", context)

        assert len(segments) == 1
        assert "My Title" in segments[0]["text"]
        assert "My Content" in segments[0]["text"]
        assert segments[0]["styles"]["bold"] is True

    def test_render_template_with_config_service(self, temp_template_dir: str, mock_config_service: MagicMock) -> None:
        """Test rendering template with config service settings."""
        mock_config_service.get_chars_per_line.return_value = 20
        mock_config_service.get_enable_special_letters.return_value = True

        service = TemplateServiceImpl(template_dir=temp_template_dir, config_service=mock_config_service)

        context = {"title": "Test", "content": "Content"}
        service.render_template("test_template", context)

        # Verify config service methods were called
        mock_config_service.get_chars_per_line.assert_called_once()
        mock_config_service.get_enable_special_letters.assert_called_once()

    def test_render_template_markdown(self, temp_template_dir: str) -> None:
        """Test rendering template with markdown content."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        context = {"title": "Header", "content": "Bold text"}
        segments = service.render_template("markdown_template", context)

        # Markdown should be processed into multiple segments
        assert len(segments) >= 1
        # Text should be wrapped according to chars_per_line

    def test_render_template_without_special_letters(
        self, temp_template_dir: str, mock_config_service: MagicMock
    ) -> None:
        """Test rendering template with special letters disabled."""
        mock_config_service.get_chars_per_line.return_value = 32
        mock_config_service.get_enable_special_letters.return_value = False

        service = TemplateServiceImpl(template_dir=temp_template_dir, config_service=mock_config_service)

        # Use context with special characters
        context = {"title": "Tëst Títlé", "content": "Cöntënt"}
        segments = service.render_template("test_template", context)

        # Special characters should be transliterated
        assert "Test Title" in segments[0]["text"]
        assert "Content" in segments[0]["text"]

    def test_render_template_jinja_error(self, temp_template_dir: str) -> None:
        """Test error handling for Jinja template errors."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        # Context missing required variable
        context = {"title": "Test"}  # Missing 'content'

        # Should handle gracefully - Jinja will render empty string for missing variables
        segments = service.render_template("test_template", context)
        assert len(segments) == 1

    def test_render_template_auto_context_with_script(self, temp_template_dir: str) -> None:
        """Test rendering template with auto-generated context from script."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        # Mock the script registry to return generated content
        mock_registry = MagicMock()
        mock_registry.execute_script.return_value = {"generated_content": "Auto-generated text"}
        service.script_registry = mock_registry

        segments = service.render_template("script_template")

        assert len(segments) == 1
        assert "Auto-generated text" in segments[0]["text"]
        mock_registry.execute_script.assert_called_once_with("test_script")

    def test_generate_template_context_with_script(self, temp_template_dir: str) -> None:
        """Test context generation using template script."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        # Mock the script registry
        mock_registry = MagicMock()
        mock_registry.execute_script.return_value = {"script_var": "script_value"}
        service.script_registry = mock_registry

        context = service.generate_template_context("script_template")

        assert context["script_var"] == "script_value"
        mock_registry.execute_script.assert_called_once_with("test_script")

    def test_generate_template_context_with_manual_override(self, temp_template_dir: str) -> None:
        """Test context generation with manual context override."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        # Mock the script registry
        mock_registry = MagicMock()
        mock_registry.execute_script.return_value = {"script_var": "script_value"}
        service.script_registry = mock_registry

        manual_context = {"script_var": "manual_value", "extra_var": "extra_value"}
        context = service.generate_template_context("script_template", manual_context)

        # Manual context should override script context
        assert context["script_var"] == "manual_value"
        assert context["extra_var"] == "extra_value"

    def test_generate_template_context_script_error(self, temp_template_dir: str) -> None:
        """Test context generation when script fails."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        # Mock the script registry to raise error
        mock_registry = MagicMock()
        mock_registry.execute_script.side_effect = Exception("Script failed")
        service.script_registry = mock_registry

        context = service.generate_template_context("script_template")

        # Should fall back to empty context
        assert context == {}

    def test_generate_template_context_no_script(self, temp_template_dir: str) -> None:
        """Test context generation for template without script."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        context = service.generate_template_context("test_template")

        assert context == {}

    def test_get_template_variables(self, temp_template_dir: str) -> None:
        """Test getting template variables."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        variables = service.get_template_variables("test_template")

        assert len(variables) == 2
        assert any(var["name"] == "title" for var in variables)
        assert any(var["name"] == "content" for var in variables)

    def test_get_template_variables_no_variables(self, temp_template_dir: str) -> None:
        """Test getting variables for template without variables defined."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        variables = service.get_template_variables("script_template")

        assert variables == []

    def test_has_script_true(self, temp_template_dir: str) -> None:
        """Test checking if template has script when it does."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        # Mock script registry
        mock_registry = MagicMock()
        mock_registry.has_script.return_value = True
        service.script_registry = mock_registry

        has_script = service.has_script("script_template")

        assert has_script is True
        mock_registry.has_script.assert_called_once_with("test_script")

    def test_has_script_false(self, temp_template_dir: str) -> None:
        """Test checking if template has script when it doesn't."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        has_script = service.has_script("test_template")

        assert has_script is False

    def test_get_script_info_with_script(self, temp_template_dir: str) -> None:
        """Test getting script info for template with script."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        # Mock script registry
        mock_registry = MagicMock()
        mock_registry.has_script.return_value = True
        mock_registry.get_script_info.return_value = {"name": "test_script", "description": "Test script"}
        service.script_registry = mock_registry

        script_info = service.get_script_info("script_template")

        assert script_info is not None
        assert script_info["name"] == "test_script"
        mock_registry.get_script_info.assert_called_once_with("test_script")

    def test_get_script_info_without_script(self, temp_template_dir: str) -> None:
        """Test getting script info for template without script."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        script_info = service.get_script_info("test_template")

        assert script_info is None

    def test_list_available_scripts(self, temp_template_dir: str) -> None:
        """Test listing available scripts."""
        service = TemplateServiceImpl(template_dir=temp_template_dir)

        # Mock script registry
        mock_registry = MagicMock()
        mock_registry.list_scripts.return_value = {"script1": "Description 1", "script2": "Description 2"}
        service.script_registry = mock_registry

        scripts = service.list_available_scripts()

        assert len(scripts) == 2
        assert scripts["script1"] == "Description 1"
        mock_registry.list_scripts.assert_called_once()
