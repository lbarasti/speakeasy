from __future__ import annotations

from rich.console import Console
from rich.text import Text

console = Console(force_terminal=True)


def info(msg: str) -> None:
    t = Text("✓ ", style="green")
    t.append(msg)
    console.print(t)


def warn(msg: str) -> None:
    t = Text("! ", style="yellow")
    t.append(msg)
    console.print(t)


def error(msg: str) -> None:
    t = Text("✗ ", style="red")
    t.append(msg)
    console.print(t)


def dim(msg: str) -> None:
    console.print(Text(msg, style="dim"))


def log(tag: str, msg: str, style: str = "blue") -> None:
    t = Text()
    t.append(f"[{tag}]", style=style)
    t.append(f" {msg}")
    console.print(t)
