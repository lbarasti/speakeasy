from __future__ import annotations

import json
import os

from pydantic import BaseModel

from .console import error, log
from .speaker import speak

TOOL_LABELS: dict[str, str] = {
    "Bash": "run a command",
    "Read": "read a file",
    "Write": "write a file",
    "Edit": "edit a file",
    "Agent": "spawn an agent",
}


class PermissionRequest(BaseModel):
    session_id: str
    cwd: str
    hook_event_name: str
    tool_name: str
    tool_input: dict[str, object]


def _project_name(cwd: str) -> str:
    return cwd.rstrip("/").rsplit("/", 1)[-1] or "unknown project"


def _fallback_summary(req: PermissionRequest) -> str:
    project = _project_name(req.cwd)
    action = TOOL_LABELS.get(req.tool_name, f"use {req.tool_name}")
    return f"Claude Code working on {project} wants to {action}."


def _summarize_request(req: PermissionRequest) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_summary(req)

    try:
        import anthropic

        tool_input_str = json.dumps(req.tool_input, indent=2)
        if len(tool_input_str) > 300:
            tool_input_str = tool_input_str[:300] + "\n... (truncated)"

        project = _project_name(req.cwd)

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=os.environ.get("LLM_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=60,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Write a short permission question (1 sentence) for a voice assistant to speak aloud.\n\n"
                        f'Format: "Claude Code working on {project} wants to [brief action]. Allow?"\n\n'
                        "Rules:\n"
                        f'- Use ONLY the project name "{project}", never the full path\n'
                        '- Describe the ACTION briefly (e.g., "search for config files", "edit the settings file")\n'
                        "- Do NOT read out file paths, commands, or code verbatim\n"
                        "- Keep it under 25 words total\n\n"
                        f"Tool: {req.tool_name}\n"
                        f"Input: {tool_input_str}"
                    ),
                }
            ],
        )
        text = message.content[0].text  # type: ignore[union-attr]
        return text.strip()

    except Exception as e:
        error(f"LLM summarisation failed: {e}")
        return _fallback_summary(req)


def handle_permission(req: PermissionRequest) -> dict[str, object]:
    input_preview = json.dumps(req.tool_input)[:120]
    log("permission", f"{req.tool_name}: {input_preview}", style="yellow")

    try:
        summary = _summarize_request(req)
        log("permission", f"Speaking: {summary}", style="yellow")
        speak(summary)
    except Exception as e:
        error(f"Permission error: {e}")

    return {"behavior": "ask"}
