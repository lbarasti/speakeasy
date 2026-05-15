import io
import os
import sys
import wave

import pytest
from fastapi.testclient import TestClient

from speakeasy import personality, server, tts


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


def assert_valid_wav(wav_data: bytes) -> None:
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

    assert_valid_wav(wav_data)


def test_tts_endpoint_returns_real_wav_response(tmp_path) -> None:
    tts.load_model()
    personality_path = tmp_path / "integration.md"
    personality_path.write_text(
        "\n".join(
            [
                "# Voice",
                "",
                "## Name",
                "",
                "Integration",
                "",
                "## Speaker",
                "",
                "af_heart",
                "",
                "## Language",
                "",
                "american",
                "",
                "## Speed",
                "",
                "1.0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    personality.load_personality(str(personality_path))

    client = TestClient(server.create_app())
    response = client.post(
        "/tts",
        json={"message": "Hello from the speakeasy TTS endpoint integration test."},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.headers["content-disposition"] == 'attachment; filename="speakeasy.wav"'
    assert_valid_wav(response.content)
