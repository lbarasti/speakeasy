from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import threading
import time

from .console import error


def play_audio(
    wav_data: bytes,
    cancel: threading.Event | None = None,
) -> None:
    if len(wav_data) < 100:
        return
    if cancel is not None and cancel.is_set():
        return

    fd, tmp_path = tempfile.mkstemp(suffix=".wav", prefix="speakeasy-")
    try:
        os.write(fd, wav_data)
        os.close(fd)

        proc = subprocess.Popen(["afplay", tmp_path])

        while proc.poll() is None:
            if cancel is not None and cancel.is_set():
                proc.send_signal(signal.SIGKILL)
                proc.wait()
                return
            time.sleep(0.05)

        if proc.returncode != 0:
            error(f"Playback failed with exit code {proc.returncode}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
