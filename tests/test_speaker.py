from types import SimpleNamespace

import pytest

from speakeasy import speaker


@pytest.fixture(autouse=True)
def reset_speaker_state() -> None:
    speaker._cancel = None


def test_speak_strips_markdown_and_uses_loaded_voice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    synth_calls: list[dict[str, object]] = []
    played: list[bytes] = []
    monkeypatch.setattr(
        speaker,
        "get_personality",
        lambda: SimpleNamespace(speaker="bm_lewis", speed=1.2, language="british"),
    )

    def synthesize(**kwargs: object) -> bytes:
        synth_calls.append(kwargs)
        return b"x" * 200

    monkeypatch.setattr(speaker, "synthesize", synthesize)
    monkeypatch.setattr(speaker, "play_audio", lambda wav, cancel=None: played.append(wav))

    speaker.speak("Say **hello** to `Cursor`.")

    assert synth_calls == [
        {
            "text": "Say hello to Cursor.",
            "speaker": "bm_lewis",
            "speed": 1.2,
            "language": "british",
        }
    ]
    assert played == [b"x" * 200]
    assert not speaker.is_speaking()


def test_speak_skips_playback_if_interrupted_before_audio_starts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    played: list[bytes] = []
    monkeypatch.setattr(
        speaker,
        "get_personality",
        lambda: SimpleNamespace(speaker="af_heart", speed=1.0, language="american"),
    )

    def synthesize(**_: object) -> bytes:
        speaker.interrupt()
        return b"x" * 200

    monkeypatch.setattr(speaker, "synthesize", synthesize)
    monkeypatch.setattr(speaker, "play_audio", lambda wav, cancel=None: played.append(wav))

    speaker.speak("hello")

    assert played == []
    assert not speaker.is_speaking()


def test_interrupt_sets_current_cancel_event() -> None:
    cancel = speaker.threading.Event()
    speaker._cancel = cancel

    speaker.interrupt()

    assert cancel.is_set()
    assert speaker._cancel is None
    assert not speaker.is_speaking()


def test_speak_clears_state_when_synthesis_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        speaker,
        "get_personality",
        lambda: SimpleNamespace(speaker="af_heart", speed=1.0, language="american"),
    )

    def fail_to_synthesize(**_: object) -> bytes:
        raise RuntimeError("boom")

    monkeypatch.setattr(speaker, "synthesize", fail_to_synthesize)

    with pytest.raises(RuntimeError, match="boom"):
        speaker.speak("hello")

    assert not speaker.is_speaking()
