from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from speakeasy import server


@pytest.fixture
def client() -> TestClient:
    return TestClient(server.create_app())


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_notify_rejects_blank_messages(client: TestClient) -> None:
    response = client.post("/notify", json={"message": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Empty message"


def test_notify_speaks_trimmed_message(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    spoken: list[str] = []
    monkeypatch.setattr(server, "speak", spoken.append)

    response = client.post("/notify", json={"message": "  hello there  "})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert spoken == ["hello there"]


def test_tts_rejects_blank_messages(client: TestClient) -> None:
    response = client.post("/tts", json={"message": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Empty message"


def test_tts_returns_wav_response(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    synth_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        server,
        "get_personality",
        lambda: SimpleNamespace(speaker="bf_emma", speed=1.2, language="british"),
    )

    def synthesize(**kwargs: object) -> bytes:
        synth_calls.append(kwargs)
        return b"RIFFfake-wav"

    monkeypatch.setattr(server, "synthesize", synthesize)

    response = client.post("/tts", json={"message": "  Say **hello**  "})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.headers["content-disposition"] == 'attachment; filename="speakeasy.wav"'
    assert response.content == b"RIFFfake-wav"
    assert synth_calls == [
        {
            "text": "Say hello",
            "speaker": "bf_emma",
            "speed": 1.2,
            "language": "british",
        }
    ]


def test_permission_rejects_empty_tool_input(client: TestClient) -> None:
    response = client.post(
        "/permission",
        json={
            "session_id": "session-1",
            "cwd": "/tmp/project",
            "hook_event_name": "PermissionRequest",
            "tool_name": "Bash",
            "tool_input": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Missing required fields: tool_name, tool_input"


def test_permission_returns_hook_decision(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(server, "handle_permission", lambda req: {"behavior": "ask"})

    response = client.post(
        "/permission",
        json={
            "session_id": "session-1",
            "cwd": "/tmp/project",
            "hook_event_name": "PermissionRequest",
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {"behavior": "ask"},
        }
    }
