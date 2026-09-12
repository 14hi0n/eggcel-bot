import pytest

from services.prompt_template_renderer import PromptTemplateRenderer


def test_render_replaces_placeholder():
    renderer = PromptTemplateRenderer()

    result = renderer.render(
        row_text="Hello my username is {{username}}",
        values={"username": "@pupupue"},
    )

    assert result == "Hello my username is @pupupue"


def test_render_replaces_multiple_placeholders():
    renderer = PromptTemplateRenderer()

    result = renderer.render(
        row_text="{{greating}} 私の名前は{{ name }}です。天気が{{ weather }}ですね。",
        values={
            "greating": "おはよう〜",
            "name": "重音テト",
            "weather": "明るい",
        },
    )

    assert result == "おはよう〜 私の名前は重音テトです。天気が明るいですね。"


def test_render_replaces_repeated_placeholder():
    renderer = PromptTemplateRenderer()

    result = renderer.render(
        row_text="{{ egg }}が大好きなので、毎日{{ egg }}を食べています。",
        values={"egg": "卵"},
    )

    assert result == "卵が大好きなので、毎日卵を食べています。"


def test_render_placeholder_is_case_insensitive():
    renderer = PromptTemplateRenderer()

    result = renderer.render(
        row_text="{{ name }} {{ NAME }} {{ Name }}",
        values={"name": "eggcel"},
    )

    assert result == "eggcel eggcel eggcel"


def test_render_returns_none_when_value_is_none():
    renderer = PromptTemplateRenderer()

    result = renderer.render(
        row_text="Hello, {{ name }}!",
        values={"name": None},
    )

    assert result is None


def test_render_unknown_placeholder():
    renderer = PromptTemplateRenderer()

    with pytest.raises(ValueError):
        renderer.render(
            row_text="Hello, {{ username }} {{ datetime }}",
            values={
                "username": "@mouse",
                "time": "13:55",
            },
        )
