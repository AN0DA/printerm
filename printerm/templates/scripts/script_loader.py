"""Template script loading and management."""

import importlib
import logging
import os
import sys
from pathlib import Path
from typing import Any

from printerm.exceptions import TemplateError

from .base import TemplateScript

logger = logging.getLogger(__name__)


class TemplateScriptError(TemplateError):
    """Exception raised when template script operations fail."""

    pass


class ScriptLoader:
    """Loads and manages template scripts dynamically."""

    def __init__(self, scripts_dir: str | None = None):
        """Initialize the script loader.

        Args:
            scripts_dir: Directory containing script modules.
                        Defaults to the scripts directory relative to this file.
        """
        if scripts_dir is None:
            scripts_dir = os.path.dirname(os.path.abspath(__file__))

        self.scripts_dir = Path(scripts_dir)
        self._loaded_scripts: dict[str, type[TemplateScript]] = {}
        self._script_instances: dict[str, TemplateScript] = {}

    def discover_scripts(self) -> dict[str, type[TemplateScript]]:
        """Discover all available script classes in the scripts directory.

        Returns:
            Dictionary mapping script names to script classes

        Raises:
            TemplateScriptError: If script discovery fails
        """
        discovered: dict[str, type[TemplateScript]] = {}

        if not self.scripts_dir.exists():
            logger.warning(f"Scripts directory does not exist: {self.scripts_dir}")
            return discovered

        try:
            for file_path in self.scripts_dir.glob("*.py"):
                if file_path.name.startswith("_") or file_path.name in [
                    "base.py",
                    "script_loader.py",
                    "script_registry.py",
                ]:
                    continue

                module_name = file_path.stem
                script_classes = self._load_script_module(module_name)
                discovered.update(script_classes)

        except Exception as e:
            raise TemplateScriptError(f"Failed to discover scripts: {e}") from e

        self._loaded_scripts.update(discovered)
        logger.info(f"Discovered {len(discovered)} template scripts")
        return discovered

    def _load_script_module(self, module_name: str) -> dict[str, type[TemplateScript]]:
        """Load a single script module and extract TemplateScript classes.

        Args:
            module_name: Name of the module to load

        Returns:
            Dictionary of script classes found in the module
        """
        script_classes = {}

        try:
            # Construct the full module path
            full_module_name = f"printerm.templates.scripts.{module_name}"

            # Import the module
            module = importlib.import_module(full_module_name)

            # Find all TemplateScript subclasses in the module
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                if isinstance(attr, type) and issubclass(attr, TemplateScript) and attr is not TemplateScript:
                    # Create an instance to get the script name
                    try:
                        instance = attr()
                        script_name = instance.name
                        script_classes[script_name] = attr
                        logger.debug(f"Loaded script: {script_name} from {module_name}")
                    except Exception as e:
                        logger.warning(f"Failed to instantiate script {attr_name}: {e}")

        except ImportError as e:
            logger.warning(f"Failed to import script module {module_name}: {e}")
        except Exception as e:
            logger.error(f"Error loading script module {module_name}: {e}")

        return script_classes

    def get_script(self, script_name: str, config_service: Any = None) -> TemplateScript:
        """Get a script instance by name.

        Args:
            script_name: Name of the script to get
            config_service: Optional configuration service to pass to script

        Returns:
            Instance of the requested script

        Raises:
            TemplateScriptError: If script is not found or cannot be instantiated
        """
        # Check if we already have an instance
        cache_key = f"{script_name}_{id(config_service) if config_service else 'none'}"
        if cache_key in self._script_instances:
            return self._script_instances[cache_key]

        # Ensure scripts are discovered
        if not self._loaded_scripts:
            self.discover_scripts()

        # Find the script class
        script_class = self._loaded_scripts.get(script_name)
        if not script_class:
            available = list(self._loaded_scripts.keys())
            raise TemplateScriptError(f"Script '{script_name}' not found. Available scripts: {available}")

        try:
            # Create and cache the instance
            instance = script_class(config_service=config_service)
            self._script_instances[cache_key] = instance
            return instance

        except Exception as e:
            raise TemplateScriptError(f"Failed to create script instance '{script_name}': {e}") from e

    def list_available_scripts(self) -> dict[str, str]:
        """List all available scripts with their descriptions.

        Returns:
            Dictionary mapping script names to descriptions
        """
        if not self._loaded_scripts:
            self.discover_scripts()

        scripts_info = {}
        for script_name, script_class in self._loaded_scripts.items():
            try:
                instance = script_class()
                scripts_info[script_name] = instance.description
            except Exception as e:
                scripts_info[script_name] = f"Error loading description: {e}"

        return scripts_info

    def reload_scripts(self) -> None:
        """Reload all scripts from disk.

        This is useful during development or when scripts are updated at runtime.
        """
        # Clear caches
        self._loaded_scripts.clear()
        self._script_instances.clear()

        # Reload modules that were previously imported
        modules_to_reload = [
            name
            for name in sys.modules
            if name.startswith("printerm.templates.scripts.")
            and not name.endswith(("base", "script_loader", "script_registry"))
        ]

        for module_name in modules_to_reload:
            try:
                importlib.reload(sys.modules[module_name])
            except Exception as e:
                logger.warning(f"Failed to reload module {module_name}: {e}")

        # Rediscover scripts
        self.discover_scripts()
        logger.info("Scripts reloaded successfully")
