from typing import Any

from mistune import BlockState
from mistune.renderers.markdown import MarkdownRenderer


class PrinterRenderer(MarkdownRenderer):
    def __init__(self, chars_per_line: int):
        super().__init__()
        self.chars_per_line = chars_per_line
        self.segments: list[dict[str, Any]] = []

    def _join_children(self, token: dict) -> str:
        return "".join(child["raw"] for child in token["children"])

    def text(self, token: dict, state: BlockState) -> str:
        text = token["raw"]

        self.segments.append({"text": text, "styles": {}})
        return text

    def strong(self, token: dict, state: BlockState) -> str:
        text = self._join_children(token)

        self.segments.append({"text": text, "styles": {"bold": True}})
        return text

    def emphasis(self, token: dict, state: BlockState) -> str:
        text = self._join_children(token)

        self.segments.append({"text": text, "styles": {"italic": True}})
        return text

    def codespan(self, token: dict, state: BlockState) -> str:
        text = self._join_children(token)

        self.segments.append({"text": text, "styles": {"font": "b"}})
        return text

    def linebreak(self, token: dict, state: BlockState) -> str:
        text = "\n\n"

        self.segments.append({"text": text, "styles": {}})
        return text

    def softbreak(self, token: dict, state: BlockState) -> str:
        text = "\n"

        self.segments.append({"text": text, "styles": {}})
        return text
