from __future__ import annotations

import io
import wave

import numpy as np

from .console import dim, info, warn

_tts: object | None = None


def load_model() -> None:
    global _tts

    dim("Loading Kokoro TTS model...")

    try:
        from huggingface_hub import snapshot_download
        local_dir = snapshot_download(
            repo_id="mlx-community/Kokoro-82M-bf16", local_files_only=True
        )
        dim(f"  Using cached model at: {local_dir}")
    except Exception:
        from huggingface_hub import snapshot_download
        dim("  Model not cached, downloading from HuggingFace (first run)...")
        local_dir = snapshot_download(repo_id="mlx-community/Kokoro-82M-bf16")
        dim(f"  Downloaded model to: {local_dir}")

    from kokoro_mlx import KokoroTTS
    _tts = KokoroTTS.from_pretrained(local_dir)

    try:
        voices = _tts.list_voices()  # type: ignore[union-attr]
        _phonemizer = _tts._get_phonemizer("a", voices[0])  # type: ignore[union-attr]
        if hasattr(_phonemizer, "_g2p"):
            from misaki.espeak import EspeakFallback
            _phonemizer._g2p.fallback = EspeakFallback(british=False)
            dim("  Patched phonemizer with espeak-ng fallback")
    except Exception as e:
        warn(f"Could not patch espeak fallback: {e}")

    voice_count = len(_tts.list_voices())  # type: ignore[union-attr]
    info(f"Kokoro TTS loaded ({voice_count} voices)")


def list_voices() -> list[str]:
    if _tts is None:
        raise RuntimeError("TTS model not loaded. Call load_model() first.")
    return sorted(_tts.list_voices())  # type: ignore[union-attr]


def synthesize(
    text: str,
    speaker: str,
    speed: float,
    language: str = "american",
    sample_rate: int = 24000,
) -> bytes:
    if _tts is None:
        raise RuntimeError("TTS model not loaded. Call load_model() first.")

    try:
        voices = _tts.list_voices()  # type: ignore[union-attr]
        phonemizer = _tts._get_phonemizer("a", voices[0])  # type: ignore[union-attr]
        if hasattr(phonemizer, "_g2p") and hasattr(phonemizer._g2p, "fallback"):
            phonemizer._g2p.fallback.british = language == "british"
    except Exception:
        pass

    result = _tts.generate(  # type: ignore[union-attr]
        text=text,
        voice=speaker,
        speed=speed,
        sample_rate=sample_rate,
    )

    audio_int16 = (result.audio * 32767).clip(-32768, 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(result.sample_rate)
        wav_file.writeframes(audio_int16.tobytes())

    return buf.getvalue()
