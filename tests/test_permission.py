import pytest

from speakeasy import permission
from speakeasy.permission import PermissionRequest


def make_request(**overrides: object) -> PermissionRequest:
    values: dict[str, object] = {
        "session_id": "session-1",
        "cwd": "/Users/example/code/speakeasy",
        "hook_event_name": "PermissionRequest",
        "tool_name": "Bash",
        "tool_input": {"command": "echo hello"},
    }
    values.update(overrides)
    return PermissionRequest(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("cwd", "expected"),
    [
        ("/Users/example/code/speakeasy", "speakeasy"),
        ("/Users/example/code/speakeasy/", "speakeasy"),
        ("/", "unknown project"),
        ("", "unknown project"),
    ],
)
def test_project_name_uses_leaf_directory(cwd: str, expected: str) -> None:
    assert permission._project_name(cwd) == expected


def test_fallback_summary_uses_known_tool_label() -> None:
    req = make_request(tool_name="Read")

    assert permission._fallback_summary(req) == (
        "Claude Code working on speakeasy wants to read a file."
    )


def test_fallback_summary_handles_unknown_tools() -> None:
    req = make_request(tool_name="NotebookEdit")

    assert permission._fallback_summary(req) == (
        "Claude Code working on speakeasy wants to use NotebookEdit."
    )


def test_summarize_request_uses_fallback_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    assert permission._summarize_request(make_request()) == (
        "Claude Code working on speakeasy wants to run a command."
    )


def test_handle_permission_speaks_summary_and_returns_ask(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spoken: list[str] = []
    monkeypatch.setattr(permission, "_summarize_request", lambda req: "Allow this?")
    monkeypatch.setattr(permission, "speak", spoken.append)

    decision = permission.handle_permission(make_request())

    assert spoken == ["Allow this?"]
    assert decision == {"behavior": "ask"}


def test_handle_permission_still_returns_ask_when_speech_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(permission, "_summarize_request", lambda req: "Allow this?")

    def fail_to_speak(_: str) -> None:
        raise RuntimeError("audio failed")

    monkeypatch.setattr(permission, "speak", fail_to_speak)

    assert permission.handle_permission(make_request()) == {"behavior": "ask"}
