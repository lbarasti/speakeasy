import io
import sys
from types import SimpleNamespace

import pytest
from rich.console import Console

from speakeasy import __main__ as cli
from speakeasy import console, personality, speaker, tts


WAV_BYTES = b"RIFF\x00\xfffake-wav"


@pytest.fixture
def cli_dependencies(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    synth_calls: list[dict[str, object]] = []

    monkeypatch.setattr(cli, "_personalities_dir", lambda: "/tmp/personalities")
    monkeypatch.setattr(
        personality,
        "resolve_personality",
        lambda name, personalities_dir: f"{personalities_dir}/{name or 'default'}.md",
    )
    monkeypatch.setattr(
        personality,
        "load_personality",
        lambda path: SimpleNamespace(
            name="Default",
            speaker="am_adam",
            language="american",
            speed=1.0,
        ),
    )
    monkeypatch.setattr(tts, "load_model", lambda: None)

    def synthesize(**kwargs: object) -> bytes:
        synth_calls.append(kwargs)
        return WAV_BYTES

    monkeypatch.setattr(tts, "synthesize", synthesize)
    return synth_calls


def test_stdout_writes_synthesized_wav_to_stdout(
    cli_dependencies: list[dict[str, object]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = SimpleNamespace(buffer=io.BytesIO())
    monkeypatch.setattr(sys, "argv", ["speakeasy", "--stdout", "Say", "**hello**"])
    monkeypatch.setattr(sys, "stdout", stdout)

    cli.main()

    assert stdout.buffer.getvalue() == WAV_BYTES
    assert cli_dependencies == [
        {
            "text": "Say hello",
            "speaker": "am_adam",
            "speed": 1.0,
            "language": "american",
        }
    ]


def test_stdout_keeps_status_output_off_stdout(
    cli_dependencies: list[dict[str, object]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stdout = SimpleNamespace(buffer=io.BytesIO())
    stderr = io.StringIO()
    monkeypatch.setattr(sys, "argv", ["speakeasy", "--stdout", "Hello"])
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(console, "console", Console(file=stderr, force_terminal=False))

    cli.main()

    assert stdout.buffer.getvalue() == WAV_BYTES
    assert "Personality: Default" in stderr.getvalue()


def test_stdout_ignores_broken_pipe(
    cli_dependencies: list[dict[str, object]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ClosedPipe:
        def write(self, data: bytes) -> None:
            raise BrokenPipeError

    stdout = SimpleNamespace(buffer=ClosedPipe())
    monkeypatch.setattr(sys, "argv", ["speakeasy", "--stdout", "Hello"])
    monkeypatch.setattr(sys, "stdout", stdout)

    cli.main()


def test_stdout_requires_text(
    cli_dependencies: list[dict[str, object]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["speakeasy", "--stdout"])

    with pytest.raises(SystemExit):
        cli.main()


def test_text_without_output_plays_audio(
    cli_dependencies: list[dict[str, object]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spoken: list[str] = []
    monkeypatch.setattr(sys, "argv", ["speakeasy", "Hello"])
    monkeypatch.setattr(speaker, "speak", spoken.append)

    cli.main()

    assert spoken == ["Hello"]
    assert cli_dependencies == []


def test_text_with_personality_plays_audio(
    cli_dependencies: list[dict[str, object]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spoken: list[str] = []
    monkeypatch.setattr(sys, "argv", ["speakeasy", "--personality", "adam", "Hello"])
    monkeypatch.setattr(speaker, "speak", spoken.append)

    cli.main()

    assert spoken == ["Hello"]
    assert cli_dependencies == []
