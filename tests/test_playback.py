import os
import signal
import threading

import pytest

from speakeasy import playback


def test_play_audio_ignores_tiny_audio(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    monkeypatch.setattr(playback.subprocess, "Popen", lambda cmd: calls.append(cmd))

    playback.play_audio(b"short")

    assert calls == []


def test_play_audio_ignores_pre_cancelled_audio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []
    cancel = threading.Event()
    cancel.set()
    monkeypatch.setattr(playback.subprocess, "Popen", lambda cmd: calls.append(cmd))

    playback.play_audio(b"x" * 200, cancel=cancel)

    assert calls == []


def test_play_audio_writes_and_deletes_temp_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    temp_paths: list[str] = []

    class CompletedProcess:
        returncode = 0

        def __init__(self, cmd: list[str]) -> None:
            temp_paths.append(cmd[1])

        def poll(self) -> int:
            return 0

    monkeypatch.setattr(playback.subprocess, "Popen", CompletedProcess)

    playback.play_audio(b"x" * 200)

    assert len(temp_paths) == 1
    assert not os.path.exists(temp_paths[0])


def test_play_audio_kills_process_when_cancelled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cancel = threading.Event()
    sent_signals: list[signal.Signals] = []

    class RunningProcess:
        returncode = None

        def __init__(self, cmd: list[str]) -> None:
            self.cmd = cmd

        def poll(self) -> None:
            return None

        def send_signal(self, sig: signal.Signals) -> None:
            sent_signals.append(sig)
            self.returncode = -9

        def wait(self) -> None:
            return None

    monkeypatch.setattr(playback.subprocess, "Popen", RunningProcess)
    monkeypatch.setattr(playback.time, "sleep", lambda _: cancel.set())

    playback.play_audio(b"x" * 200, cancel=cancel)

    assert sent_signals == [signal.SIGKILL]
