import io
import os
import sys
import wave

import pytest

from speakeasy import tts


pytestmark = [
    pytest.mark.integration,
    pytest.mark.filterwarnings(
        r"ignore:`torch\.jit\.script` is deprecated.*:DeprecationWarning"
    ),
    pytest.mark.skipif(
        os.environ.get("SPEAKEASY_RUN_TTS_INTEGRATION") != "1",
        reason="set SPEAKEASY_RUN_TTS_INTEGRATION=1 to load the real TTS model",
    ),
    pytest.mark.skipif(
        sys.platform != "darwin",
        reason="real Kokoro MLX integration test requires macOS",
    ),
]


def test_real_tts_model_generates_valid_wav() -> None:
    tts.load_model()
    voices = tts.list_voices()
    assert "af_heart" in voices

    wav_data = tts.synthesize(
        text="Hello from the speakeasy integration test.",
        speaker="af_heart",
        speed=1.0,
        language="american",
    )

    assert len(wav_data) > 1_000

    with wave.open(io.BytesIO(wav_data), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 24_000
        frame_count = wav_file.getnframes()
        duration_seconds = frame_count / wav_file.getframerate()
        frames = wav_file.readframes(frame_count)

    assert frame_count > 0
    assert 1.0 < duration_seconds < 10.0
    assert any(byte != 0 for byte in frames)
