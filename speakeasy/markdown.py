from __future__ import annotations

from markdown_it import MarkdownIt

_md = MarkdownIt().enable("strikethrough")


def strip_markdown(text: str) -> str:
    """Extract plain text from markdown, suitable for spoken output."""
    tokens = _md.parse(text)
    parts: list[str] = []

    def walk(children: list) -> None:  # type: ignore[type-arg]
        for t in children:
            if t.children:
                walk(t.children)
            elif t.type in ("text", "code_inline"):
                parts.append(t.content)
            elif t.type in ("softbreak", "hardbreak"):
                parts.append(" ")

    for t in tokens:
        if t.type == "inline" and t.children:
            walk(t.children)
            parts.append("\n")
        elif t.type == "fence":
            parts.append(t.content.strip())
            parts.append("\n")

    return "\n".join(line for line in "".join(parts).splitlines() if line.strip())
