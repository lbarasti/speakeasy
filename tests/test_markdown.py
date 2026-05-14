import pytest

from speakeasy.markdown import strip_markdown


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("Hello **there**", "Hello there"),
        ("Use `uv run speakeasy` now", "Use uv run speakeasy now"),
        ("Read [the docs](https://example.com)", "Read the docs"),
        ("- first\n- second", "first\nsecond"),
        ("```python\nprint('hi')\n```", "print('hi')"),
        ("  \n\n", ""),
    ],
)
def test_strip_markdown_returns_spoken_text(source: str, expected: str) -> None:
    assert strip_markdown(source) == expected
