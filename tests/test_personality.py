from pathlib import Path

import pytest

from speakeasy import personality


@pytest.fixture(autouse=True)
def reset_active_personality() -> None:
    personality._active = None


def test_load_personality_parses_voice_fields(tmp_path: Path) -> None:
    path = tmp_path / "british.md"
    path.write_text(
        """
# Voice

## Name
British narrator

## Speaker
bm_lewis

## Language
british

## Speed
1.2
""".strip(),
        encoding="utf-8",
    )

    loaded = personality.load_personality(str(path))

    assert loaded.name == "British narrator"
    assert loaded.speaker == "bm_lewis"
    assert loaded.language == "british"
    assert loaded.speed == 1.2
    assert personality.get_personality() == loaded


def test_load_personality_uses_defaults_for_missing_fields(tmp_path: Path) -> None:
    path = tmp_path / "minimal.md"
    path.write_text("# Voice\n", encoding="utf-8")

    loaded = personality.load_personality(str(path))

    assert loaded.name == "Assistant"
    assert loaded.speaker == "af_heart"
    assert loaded.language == "american"
    assert loaded.speed == 1.0


def test_get_personality_requires_loaded_config() -> None:
    with pytest.raises(RuntimeError, match="Personality not loaded"):
        personality.get_personality()


def test_list_personalities_returns_sorted_markdown_stems(tmp_path: Path) -> None:
    (tmp_path / "zeta.md").write_text("", encoding="utf-8")
    (tmp_path / "alpha.md").write_text("", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("", encoding="utf-8")

    assert personality.list_personalities(str(tmp_path)) == ["alpha", "zeta"]


def test_resolve_personality_uses_environment_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "voice.md"
    path.write_text("", encoding="utf-8")
    monkeypatch.setenv("PERSONALITY", "voice")

    assert personality.resolve_personality(None, str(tmp_path)) == str(path)


def test_resolve_personality_accepts_direct_paths(tmp_path: Path) -> None:
    path = tmp_path / "custom.md"

    assert personality.resolve_personality(str(path), str(tmp_path)) == str(path)


def test_resolve_personality_reports_available_names(tmp_path: Path) -> None:
    (tmp_path / "default.md").write_text("", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        personality.resolve_personality("missing", str(tmp_path))

    assert 'Personality "missing" not found' in str(exc.value)
    assert "Available: default" in str(exc.value)
