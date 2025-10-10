from typing import Any

from mistune import BlockState
from mistune.renderers.markdown import MarkdownRenderer


class PrinterRenderer(MarkdownRenderer):
    """Enhanced markdown renderer for thermal printers."""

    def __init__(self, chars_per_line: int):
        super().__init__()
        self.chars_per_line = chars_per_line
        self.segments: list[dict[str, Any]] = []
        self.list_depth = 0
        self.in_heading = False
        self.heading_level = 1

    def text(self, token: dict, state: BlockState) -> str:
        """Render plain text."""
        text = token["raw"]

        # Apply heading styles if we're in a heading
        if self.in_heading:
            if self.heading_level == 1:
                styles = {"bold": True, "double_width": True, "double_height": True, "align": "center"}
            elif self.heading_level == 2:
                styles = {"bold": True, "double_width": True, "align": "center"}
            elif self.heading_level == 3:
                styles = {"bold": True, "underline": True}
            else:
                styles = {"bold": True}
        else:
            styles = {}

        self.segments.append({"text": text, "styles": styles})
        return text

    def strong(self, token: dict, state: BlockState) -> str:
        """Render bold text."""
        # Get text from children
        text = ""
        for child in token.get("children", []):
            if child.get("type") == "text":
                text += child.get("raw", "")

        self.segments.append({"text": text, "styles": {"bold": True}})
        return text

    def emphasis(self, token: dict, state: BlockState) -> str:
        """Render italic text."""
        # Get text from children
        text = ""
        for child in token.get("children", []):
            if child.get("type") == "text":
                text += child.get("raw", "")

        self.segments.append({"text": text, "styles": {"italic": True}})
        return text

    def codespan(self, token: dict, state: BlockState) -> str:
        """Render inline code."""
        # For codespan, the raw text is in the token itself
        text = token.get("raw", "")
        self.segments.append({"text": text, "styles": {"font": "b"}})
        return text

    def linebreak(self, token: dict, state: BlockState) -> str:
        """Render line breaks."""
        text = "\n\n"
        self.segments.append({"text": text, "styles": {}})
        return text

    def softbreak(self, token: dict, state: BlockState) -> str:
        """Render soft line breaks."""
        text = "\n"
        self.segments.append({"text": text, "styles": {}})
        return text

    def heading(self, token: dict, state: BlockState) -> str:
        """Render headings with different styles based on level."""
        self.heading_level = token.get("attrs", {}).get("level", 0)
        self.in_heading = True

        # Add some spacing before heading
        self.segments.append({"text": "\n", "styles": {}})

        # Process children manually since we need to apply heading styles
        for child in token.get("children", []):
            if child.get("type") == "text":
                self.text(child, state)

        # Add spacing after heading
        self.segments.append({"text": "\n", "styles": {}})

        self.in_heading = False
        return ""

    def paragraph(self, token: dict, state: BlockState) -> str:
        """Render paragraphs with proper spacing."""
        # Process children
        for child in token.get("children", []):
            if hasattr(self, child.get("type", "")):
                method = getattr(self, child["type"])
                method(child, state)

        # Add paragraph break
        self.segments.append({"text": "\n\n", "styles": {}})
        return ""

    def thematic_break(self, token: dict, state: BlockState) -> str:
        """Render horizontal rules (---) as dashed lines."""
        separator = "-" * min(self.chars_per_line, 32)
        self.segments.append({"text": "\n", "styles": {}})
        self.segments.append({"text": separator, "styles": {"align": "center", "bold": True}})
        self.segments.append({"text": "\n\n", "styles": {}})
        return separator

    def block_quote(self, token: dict, state: BlockState) -> str:
        """Render blockquotes with indentation and italic styling."""
        # This is a simplified implementation
        self.segments.append({"text": "> ", "styles": {"italic": True}})

        # Process children
        for child in token.get("children", []):
            if hasattr(self, child.get("type", "")):
                method = getattr(self, child["type"])
                method(child, state)

        self.segments.append({"text": "\n\n", "styles": {}})
        return ""

    def block_code(self, token: dict, state: BlockState) -> str:
        """Render code blocks with different font."""
        text = token.get("raw", "")
        # Remove trailing newlines and add consistent spacing
        text = text.rstrip("\n")

        self.segments.append({"text": "\n", "styles": {}})
        self.segments.append({"text": text, "styles": {"font": "b"}})
        self.segments.append({"text": "\n\n", "styles": {}})
        return text

    def list_item(self, token: dict, state: BlockState) -> str:
        """Render list items with proper indentation and bullets."""
        # Create indentation based on list depth
        indent = "  " * self.list_depth

        # Use different bullet styles based on depth
        bullets = ["• ", "◦ ", "▪ ", "- "]
        bullet = bullets[min(self.list_depth, len(bullets) - 1)]

        self.segments.append({"text": f"{indent}{bullet}", "styles": {}})

        # Process the list item content
        for child in token.get("children", []):
            child_type = child.get("type", "")
            if child_type == "list":
                # Handle nested lists
                self.list(child, state)
            elif hasattr(self, child_type):
                method = getattr(self, child_type)
                method(child, state)

        self.segments.append({"text": "\n", "styles": {}})
        return ""

    def list(self, token: dict, state: BlockState) -> str:
        """Render lists with proper nesting."""
        self.list_depth += 1

        # Only add spacing before top-level lists, and only if not already at the start
        if self.list_depth == 1 and self.segments and self.segments[-1].get("text", "").strip():
            self.segments.append({"text": "\n", "styles": {}})

        # Process list items
        for child in token.get("children", []):
            if hasattr(self, child.get("type", "")):
                method = getattr(self, child["type"])
                method(child, state)

        self.list_depth -= 1

        # Add spacing after top-level lists
        if self.list_depth == 0:
            self.segments.append({"text": "\n", "styles": {}})

        return ""

    def strikethrough(self, token: dict, state: BlockState) -> str:
        """Render strikethrough text."""
        # Get text from children
        text = ""
        for child in token.get("children", []):
            if child.get("type") == "text":
                text += child.get("raw", "")

        # Since thermal printers don't support strikethrough,
        # we'll use a text indicator
        self.segments.append({"text": f"[DELETED: {text}]", "styles": {"italic": True}})
        return text

    def link(self, token: dict, state: BlockState) -> str:
        """Render links showing both text and URL."""
        # Get text from children
        text = ""
        for child in token.get("children", []):
            if child.get("type") == "text":
                text += child.get("raw", "")

        url = token.get("attrs", {}).get("url", "")

        if text == url:
            # If text and URL are the same, just show the URL
            self.segments.append({"text": url, "styles": {"underline": True}})
        else:
            # Show text followed by URL in parentheses
            self.segments.append({"text": text, "styles": {}})
            self.segments.append({"text": f" ({url})", "styles": {"font": "b"}})
        return text
