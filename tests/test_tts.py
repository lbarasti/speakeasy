import io
import wave

import numpy as np
import pytest

from speakeasy import tts


@pytest.fixture(autouse=True)
def reset_tts_model() -> None:
    tts._tts = None


class FakeFallback:
    def __init__(self) -> None:
        self.british = False


class FakeG2P:
    def __init__(self) -> None:
        self.fallback = FakeFallback()


class FakePhonemizer:
    def __init__(self) -> None:
        self._g2p = FakeG2P()


class FakeTTS:
    def __init__(self) -> None:
        self.phonemizer = FakePhonemizer()
        self.generate_calls: list[dict[str, object]] = []

    def list_voices(self) -> list[str]:
        return ["bm_lewis", "af_heart"]

    def _get_phonemizer(self, lang: str, voice: str) -> FakePhonemizer:
        assert lang == "a"
        assert voice == "bm_lewis"
        return self.phonemizer

    def generate(
        self, text: str, voice: str, speed: float, sample_rate: int
    ) -> object:
        self.generate_calls.append(
            {
                "text": text,
                "voice": voice,
                "speed": speed,
                "sample_rate": sample_rate,
            }
        )
        return type(
            "FakeResult",
            (),
            {
                "audio": np.array([-1.0, 0.0, 0.5, 1.0], dtype=np.float32),
                "sample_rate": sample_rate,
            },
        )()


def test_list_voices_requires_loaded_model() -> None:
    with pytest.raises(RuntimeError, match="TTS model not loaded"):
        tts.list_voices()


def test_list_voices_returns_sorted_voice_ids() -> None:
    tts._tts = FakeTTS()

    assert tts.list_voices() == ["af_heart", "bm_lewis"]


def test_synthesize_requires_loaded_model() -> None:
    with pytest.raises(RuntimeError, match="TTS model not loaded"):
        tts.synthesize("hello", speaker="af_heart", speed=1.0)


def test_synthesize_generates_wav_and_applies_language() -> None:
    fake = FakeTTS()
    tts._tts = fake

    wav_data = tts.synthesize(
        "hello",
        speaker="bm_lewis",
        speed=1.1,
        language="british",
        sample_rate=16000,
    )

    assert fake.generate_calls == [
        {
            "text": "hello",
            "voice": "bm_lewis",
            "speed": 1.1,
            "sample_rate": 16000,
        }
    ]
    assert fake.phonemizer._g2p.fallback.british is True

    with wave.open(io.BytesIO(wav_data), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16000
        assert wav_file.getnframes() == 4
