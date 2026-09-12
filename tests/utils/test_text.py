from utils.text import normalize_impact_meme


def test_normalize_text_with_single_dot():
    result = normalize_impact_meme(text="Hello world.")

    assert result == "Hello world"


def test_normalize_text_with_ellipsis():
    result = normalize_impact_meme(text="Hello world...")

    assert result == "Hello world..."


def test_normalize_text_with_dot_and_comma():
    result = normalize_impact_meme(text="Hello world,.")

    assert result == "Hello world"
