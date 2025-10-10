"""GUI settings management for the printerm application."""

import logging

from printerm.services.interfaces import ConfigService

logger = logging.getLogger(__name__)


class GuiSettings:
    """Handle GUI-specific settings like recent templates and window preferences using ConfigService."""

    def __init__(self, config_service: ConfigService) -> None:
        self.config_service = config_service

    def add_recent_template(self, template_name: str) -> None:
        """Add template to recent list."""
        try:
            recent = self.get_recent_templates()
            if template_name in recent:
                recent.remove(template_name)
            recent.insert(0, template_name)
            # Keep only last 5 recent templates
            recent = recent[:5]
            self.config_service.set_gui_recent_templates(recent)
        except Exception as e:
            logger.warning(f"Failed to save recent template: {e}")

    def get_recent_templates(self) -> list[str]:
        """Get list of recent templates."""
        try:
            return self.config_service.get_gui_recent_templates()
        except Exception as e:
            logger.warning(f"Failed to load recent templates: {e}")
            return []
