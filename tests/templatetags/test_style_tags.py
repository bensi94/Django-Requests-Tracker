import pytest

from tests.templatetags.conftest import TemplateRenderer


@pytest.mark.parametrize(
    "method_type, expected_classes",
    [
        ("GET", "is-info"),
        ("POST", "is-success"),
        ("PUT", "is-warning"),
        ("PATCH", "is-warning is-light"),
        ("DELETE", "is-danger"),
        ("INVALID", ""),
    ],
)
def test_method_bulma_color_class(
    method_type: str,
    expected_classes: str,
    template_renderer: TemplateRenderer,
) -> None:
    template = """
    {% load style_tags %}
    <span class="{{ test|method_class }}"></span>
    """

    assert (
        template_renderer(template, {"test": method_type}, strip=True)
        == f'<span class="{expected_classes}"></span>'
    )
