from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Personality:
    name: str
    speaker: str
    language: str
    speed: float


_active: Personality | None = None


def load_personality(path: str) -> Personality:
    global _active

    with open(path, encoding="utf-8") as f:
        text = f.read()

    sections: dict[str, str] = {}
    current_section: str | None = None
    current_lines: list[str] = []

    for line in text.split("\n"):
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_lines).strip()
                current_lines.clear()
            current_section = line[3:].strip().lower()
        elif current_section is not None:
            current_lines.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_lines).strip()

    _active = Personality(
        name=sections.get("name", "Assistant"),
        speaker=sections.get("speaker", "af_heart"),
        language=sections.get("language", "american"),
        speed=float(sections.get("speed", "1.0")),
    )
    return _active


def get_personality() -> Personality:
    if _active is None:
        raise RuntimeError("Personality not loaded. Call load_personality() first.")
    return _active


def list_personalities(personalities_dir: str) -> list[str]:
    return sorted(
        f.removesuffix(".md")
        for f in os.listdir(personalities_dir)
        if f.endswith(".md")
    )


def resolve_personality(name: str | None, personalities_dir: str) -> str:
    if name is None:
        name = os.environ.get("PERSONALITY", "default")

    # Absolute or relative path
    if "/" in name or name.endswith(".md"):
        return os.path.abspath(name)

    path = os.path.join(personalities_dir, f"{name}.md")
    if os.path.isfile(path):
        return path

    available = list_personalities(personalities_dir)
    raise SystemExit(
        f'Personality "{name}" not found in {personalities_dir}\n'
        f"Available: {', '.join(available)}"
    )
