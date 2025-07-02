"""Tests for markdown renderer."""

from unittest.mock import MagicMock

from mistune import BlockState

from printerm.services.markdown_renderer import PrinterRenderer


class TestPrinterRenderer:
    """Test cases for PrinterRenderer."""

    def test_init(self) -> None:
        """Test renderer initialization."""
        renderer = PrinterRenderer(chars_per_line=40)

        assert renderer.chars_per_line == 40
        assert renderer.segments == []
        assert renderer.list_depth == 0
        assert renderer.in_heading is False
        assert renderer.heading_level == 1

    def test_text_plain(self) -> None:
        """Test rendering plain text."""
        renderer = PrinterRenderer(chars_per_line=32)
        token = {"raw": "Hello world"}
        state = BlockState()

        result = renderer.text(token, state)

        assert result == "Hello world"
        assert len(renderer.segments) == 1
        assert renderer.segments[0]["text"] == "Hello world"
        assert renderer.segments[0]["styles"] == {}

    def test_text_in_heading_level_1(self) -> None:
        """Test text rendering in level 1 heading."""
        renderer = PrinterRenderer(chars_per_line=32)
        renderer.in_heading = True
        renderer.heading_level = 1

        token = {"raw": "Main Title"}
        state = BlockState()

        result = renderer.text(token, state)

        assert result == "Main Title"
        assert renderer.segments[0]["styles"] == {
            "bold": True,
            "double_width": True,
            "double_height": True,
            "align": "center",
        }

    def test_text_in_heading_level_2(self) -> None:
        """Test text rendering in level 2 heading."""
        renderer = PrinterRenderer(chars_per_line=32)
        renderer.in_heading = True
        renderer.heading_level = 2

        token = {"raw": "Subtitle"}
        state = BlockState()

        renderer.text(token, state)

        assert renderer.segments[0]["styles"] == {"bold": True, "double_width": True, "align": "center"}

    def test_text_in_heading_level_3(self) -> None:
        """Test text rendering in level 3 heading."""
        renderer = PrinterRenderer(chars_per_line=32)
        renderer.in_heading = True
        renderer.heading_level = 3

        token = {"raw": "Section"}
        state = BlockState()

        renderer.text(token, state)

        assert renderer.segments[0]["styles"] == {"bold": True, "underline": True}

    def test_text_in_heading_level_4_plus(self) -> None:
        """Test text rendering in level 4+ heading."""
        renderer = PrinterRenderer(chars_per_line=32)
        renderer.in_heading = True
        renderer.heading_level = 4

        token = {"raw": "Subsection"}
        state = BlockState()

        renderer.text(token, state)

        assert renderer.segments[0]["styles"] == {"bold": True}

    def test_strong(self) -> None:
        """Test rendering bold text."""
        renderer = PrinterRenderer(chars_per_line=32)
        token = {"children": [{"type": "text", "raw": "Bold text"}]}
        state = BlockState()

        result = renderer.strong(token, state)

        assert result == "Bold text"
        assert renderer.segments[0]["text"] == "Bold text"
        assert renderer.segments[0]["styles"] == {"bold": True}

    def test_strong_multiple_children(self) -> None:
        """Test rendering bold text with multiple children."""
        renderer = PrinterRenderer(chars_per_line=32)
        token = {"children": [{"type": "text", "raw": "Bold "}, {"type": "text", "raw": "text"}]}
        state = BlockState()

        result = renderer.strong(token, state)

        assert result == "Bold text"
        assert renderer.segments[0]["text"] == "Bold text"

    def test_emphasis(self) -> None:
        """Test rendering italic text."""
        renderer = PrinterRenderer(chars_per_line=32)
        token = {"children": [{"type": "text", "raw": "Italic text"}]}
        state = BlockState()

        result = renderer.emphasis(token, state)

        assert result == "Italic text"
        assert renderer.segments[0]["text"] == "Italic text"
        assert renderer.segments[0]["styles"] == {"italic": True}

    def test_codespan(self) -> None:
        """Test rendering inline code."""
        renderer = PrinterRenderer(chars_per_line=32)
        token = {"raw": "code_snippet"}
        state = BlockState()

        result = renderer.codespan(token, state)

        assert result == "code_snippet"
        assert renderer.segments[0]["text"] == "code_snippet"
        assert renderer.segments[0]["styles"] == {"font": "b"}

    def test_linebreak(self) -> None:
        """Test rendering line breaks."""
        renderer = PrinterRenderer(chars_per_line=32)
        token: dict[str, str] = {}
        state = BlockState()

        result = renderer.linebreak(token, state)

        assert result == "\n\n"
        assert renderer.segments[0]["text"] == "\n\n"
        assert renderer.segments[0]["styles"] == {}

    def test_softbreak(self) -> None:
        """Test rendering soft line breaks."""
        renderer = PrinterRenderer(chars_per_line=32)
        token: dict[str, str] = {}
        state = BlockState()

        result = renderer.softbreak(token, state)

        assert result == "\n"
        assert renderer.segments[0]["text"] == "\n"

    def test_heading(self) -> None:
        """Test rendering headings."""
        renderer = PrinterRenderer(chars_per_line=32)
        token = {"attrs": {"level": 2}, "children": [{"type": "text", "raw": "Heading Text"}]}
        state = BlockState()

        result = renderer.heading(token, state)

        assert result == ""
        # Should have spacing before, heading text, and spacing after
        assert len(renderer.segments) == 3
        assert renderer.segments[0]["text"] == "\n"  # Before spacing
        assert renderer.segments[1]["text"] == "Heading Text"  # Heading text
        assert renderer.segments[2]["text"] == "\n"  # After spacing

    def test_paragraph(self) -> None:
        """Test rendering paragraphs."""
        renderer = PrinterRenderer(chars_per_line=32)

        # Mock the text method to track calls
        renderer.text = MagicMock(return_value="text_result")  # type: ignore[method-assign]

        token = {"children": [{"type": "text", "raw": "Paragraph text"}]}
        state = BlockState()

        result = renderer.paragraph(token, state)

        assert result == ""
        # Should add paragraph break at the end
        assert renderer.segments[-1]["text"] == "\n\n"

    def test_thematic_break(self) -> None:
        """Test rendering horizontal rules."""
        renderer = PrinterRenderer(chars_per_line=40)
        token: dict[str, str] = {}
        state = BlockState()

        result = renderer.thematic_break(token, state)

        assert len(result) == 32  # Should be limited to 32 chars
        assert all(c == "-" for c in result)

        # Should have spacing before, separator, and spacing after
        assert len(renderer.segments) == 3
        assert renderer.segments[0]["text"] == "\n"
        assert renderer.segments[1]["text"] == result
        assert renderer.segments[1]["styles"]["align"] == "center"
        assert renderer.segments[2]["text"] == "\n\n"

    def test_thematic_break_short_line(self) -> None:
        """Test thematic break with short chars_per_line."""
        renderer = PrinterRenderer(chars_per_line=10)
        token: dict[str, str] = {}
        state = BlockState()

        result = renderer.thematic_break(token, state)

        assert len(result) == 10
        assert renderer.segments[1]["text"] == result

    def test_block_quote(self) -> None:
        """Test rendering blockquotes."""
        renderer = PrinterRenderer(chars_per_line=32)

        # Mock methods for children processing
        renderer.text = MagicMock()  # type: ignore[method-assign]

        token = {"children": [{"type": "text"}]}
        state = BlockState()

        result = renderer.block_quote(token, state)

        assert result == ""
        # Should have quote marker at start and spacing at end
        assert len(renderer.segments) >= 2
        assert renderer.segments[0]["text"] == "> "
        assert renderer.segments[0]["styles"]["italic"] is True
        assert renderer.segments[-1]["text"] == "\n\n"

    def test_block_code(self) -> None:
        """Test rendering code blocks."""
        renderer = PrinterRenderer(chars_per_line=32)
        token = {"raw": "def hello():\n    print('world')\n\n"}
        state = BlockState()

        result = renderer.block_code(token, state)

        assert result == "def hello():\n    print('world')"  # Trailing newlines removed

        # Should have spacing before, code, and spacing after
        assert len(renderer.segments) == 3
        assert renderer.segments[0]["text"] == "\n"
        assert renderer.segments[1]["text"] == "def hello():\n    print('world')"
        assert renderer.segments[1]["styles"]["font"] == "b"
        assert renderer.segments[2]["text"] == "\n\n"

    def test_list_item_depth_0(self) -> None:
        """Test rendering list items at depth 0."""
        renderer = PrinterRenderer(chars_per_line=32)
        renderer.list_depth = 0

        # Mock child processing
        renderer.text = MagicMock()  # type: ignore[method-assign]

        token = {"children": [{"type": "text"}]}
        state = BlockState()

        result = renderer.list_item(token, state)

        assert result == ""
        # Should have bullet at start and newline at end
        assert renderer.segments[0]["text"] == "• "
        assert renderer.segments[-1]["text"] == "\n"

    def test_list_item_nested(self) -> None:
        """Test rendering nested list items."""
        renderer = PrinterRenderer(chars_per_line=32)
        renderer.list_depth = 2

        renderer.text = MagicMock()  # type: ignore[method-assign]

        token = {"children": [{"type": "text"}]}
        state = BlockState()

        renderer.list_item(token, state)

        # Should have indentation and different bullet
        assert renderer.segments[0]["text"] == "    ▪ "

    def test_list_item_deep_nesting(self) -> None:
        """Test list items with deep nesting use fallback bullet."""
        renderer = PrinterRenderer(chars_per_line=32)
        renderer.list_depth = 5  # Beyond available bullets

        renderer.text = MagicMock()  # type: ignore[method-assign]

        token = {"children": [{"type": "text"}]}
        state = BlockState()

        renderer.list_item(token, state)

        # Should use last available bullet
        assert "- " in renderer.segments[0]["text"]

    def test_list_processing(self) -> None:
        """Test rendering lists."""
        renderer = PrinterRenderer(chars_per_line=32)
        renderer.list_depth = 0

        # Mock list_item method
        renderer.list_item = MagicMock()  # type: ignore[method-assign]

        token = {"children": [{"type": "list_item"}, {"type": "list_item"}]}
        state = BlockState()

        result = renderer.list(token, state)

        assert result == ""
        assert renderer.list_depth == 0  # Should be reset

        # Should add spacing before and after for top-level list
        assert renderer.segments[0]["text"] == "\n"  # Before spacing
        assert renderer.segments[-1]["text"] == "\n"  # After spacing

    def test_list_nested(self) -> None:
        """Test nested list processing."""
        renderer = PrinterRenderer(chars_per_line=32)
        renderer.list_depth = 1  # Start nested

        renderer.list_item = MagicMock()  # type: ignore[method-assign]

        token = {"children": [{"type": "list_item"}]}
        state = BlockState()

        renderer.list(token, state)

        assert renderer.list_depth == 1  # Should be back to original
        # Nested lists shouldn't add extra spacing
        assert len([s for s in renderer.segments if s["text"] == "\n"]) == 0

    def test_strikethrough(self) -> None:
        """Test rendering strikethrough text."""
        renderer = PrinterRenderer(chars_per_line=32)
        token = {"children": [{"type": "text", "raw": "deleted text"}]}
        state = BlockState()

        result = renderer.strikethrough(token, state)

        assert result == "deleted text"
        assert renderer.segments[0]["text"] == "[DELETED: deleted text]"
        assert renderer.segments[0]["styles"]["italic"] is True

    def test_link_text_equals_url(self) -> None:
        """Test rendering links where text equals URL."""
        renderer = PrinterRenderer(chars_per_line=32)
        token = {"children": [{"type": "text", "raw": "https://example.com"}], "attrs": {"url": "https://example.com"}}
        state = BlockState()

        result = renderer.link(token, state)

        assert result == "https://example.com"
        assert len(renderer.segments) == 1
        assert renderer.segments[0]["text"] == "https://example.com"
        assert renderer.segments[0]["styles"]["underline"] is True

    def test_link_text_different_from_url(self) -> None:
        """Test rendering links where text differs from URL."""
        renderer = PrinterRenderer(chars_per_line=32)
        token = {"children": [{"type": "text", "raw": "Example Site"}], "attrs": {"url": "https://example.com"}}
        state = BlockState()

        result = renderer.link(token, state)

        assert result == "Example Site"
        assert len(renderer.segments) == 2
        assert renderer.segments[0]["text"] == "Example Site"
        assert renderer.segments[1]["text"] == " (https://example.com)"
        assert renderer.segments[1]["styles"]["font"] == "b"

    def test_link_no_url(self) -> None:
        """Test rendering links without URL."""
        renderer = PrinterRenderer(chars_per_line=32)
        token = {"children": [{"type": "text", "raw": "Link text"}], "attrs": {}}
        state = BlockState()

        result = renderer.link(token, state)

        assert result == "Link text"
        assert renderer.segments[0]["text"] == "Link text"
        assert renderer.segments[1]["text"] == " ()"
