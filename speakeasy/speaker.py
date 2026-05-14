from __future__ import annotations

import threading

from .markdown import strip_markdown
from .personality import get_personality
from .playback import play_audio
from .tts import synthesize

_cancel: threading.Event | None = None
_lock = threading.Lock()


def interrupt() -> None:
    global _cancel
    with _lock:
        if _cancel is not None:
            _cancel.set()
            _cancel = None
            from .console import dim
            dim("[interrupted]")


def speak(text: str) -> None:
    global _cancel
    interrupt()

    cancel = threading.Event()
    with _lock:
        _cancel = cancel

    try:
        personality = get_personality()
        clean_text = strip_markdown(text)
        wav_data = synthesize(
            text=clean_text,
            speaker=personality.speaker,
            speed=personality.speed,
            language=personality.language,
        )
        if cancel.is_set():
            return
        play_audio(wav_data, cancel=cancel)
    finally:
        with _lock:
            if _cancel is cancel:
                _cancel = None


def is_speaking() -> bool:
    with _lock:
        return _cancel is not None
