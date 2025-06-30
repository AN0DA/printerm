"""Shopping list generator script for templates."""

from typing import Any

from .base import TemplateScript


class ShoppingListScript(TemplateScript):
    """Template script for generating shopping list variables."""

    @property
    def name(self) -> str:
        """Return the unique name of this script."""
        return "shopping_list"

    @property
    def description(self) -> str:
        """Return a human-readable description of what this script does."""
        return "Generates a formatted shopping list with categories and quantities"

    def generate_context(self, **kwargs: Any) -> dict[str, Any]:
        """Generate shopping list context variables.

        Args:
            **kwargs: Parameters:
                - items: List of items with optional quantities and categories
                - title: Optional title for the list
                - show_categories: Whether to group items by categories

        Returns:
            Dictionary containing shopping list variables
        """
        items = kwargs.get("items", [])
        title = kwargs.get("title", "Shopping List")
        show_categories = kwargs.get("show_categories", True)

        if not items:
            # Default empty list structure
            items = [{"name": "Add your items here", "quantity": "", "category": "misc"}]

        # Process and categorize items
        categorized_items: dict[str, list[dict[str, Any]]] = {}
        all_items = []

        for item in items:
            if isinstance(item, str):
                # Simple string item
                item_data = {"name": item, "quantity": "", "category": "misc"}
            else:
                # Item with details
                item_data = {
                    "name": item.get("name", "Unknown item"),
                    "quantity": item.get("quantity", ""),
                    "category": item.get("category", "misc"),
                    "checked": item.get("checked", False),
                }

            all_items.append(item_data)

            # Categorize
            category = item_data["category"]
            if category not in categorized_items:
                categorized_items[category] = []
            categorized_items[category].append(item_data)

        # Format items for display
        formatted_items = []
        if show_categories:
            for category, category_items in sorted(categorized_items.items()):
                formatted_items.append(f"\n--- {category.upper()} ---")
                for item in category_items:
                    quantity_str = f"({item['quantity']}) " if item["quantity"] else ""
                    check_mark = "☑ " if item.get("checked") else "☐ "
                    formatted_items.append(f"{check_mark}{quantity_str}{item['name']}")
        else:
            for item in all_items:
                quantity_str = f"({item['quantity']}) " if item["quantity"] else ""
                check_mark = "☑ " if item.get("checked") else "☐ "
                formatted_items.append(f"{check_mark}{quantity_str}{item['name']}")

        context = {
            "title": title,
            "items": all_items,
            "categorized_items": categorized_items,
            "formatted_items": formatted_items,
            "formatted_list": "\n".join(formatted_items),
            "total_items": len(all_items),
            "categories": list(categorized_items.keys()),
            "show_categories": show_categories,
        }

        self.logger.debug(f"Generated shopping list context with {len(all_items)} items")
        return context

    def get_required_parameters(self) -> list[str]:
        """Return list of required parameter names for this script."""
        return ["items"]

    def get_optional_parameters(self) -> list[str]:
        """Return list of optional parameter names for this script."""
        return ["title", "show_categories"]

    def validate_context(self, context: dict[str, Any]) -> bool:
        """Validate the generated context."""
        if not super().validate_context(context):
            return False

        # Check required fields
        required_fields = ["title", "items", "formatted_list"]
        if not all(field in context for field in required_fields):
            self.logger.error(f"Context missing required fields: {required_fields}")
            return False

        # Validate items structure
        items = context.get("items", [])
        if not isinstance(items, list):
            self.logger.error("Items must be a list")
            return False

        return True
