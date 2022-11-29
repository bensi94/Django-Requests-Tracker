import pytest

from requests_tracker.sql.dataclasses import SQLQueryInfo
from tests.constants import STANDARD_SQL_QUERY_INFO
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


@pytest.mark.parametrize(
    "color_number, expected_color",
    [
        (0, "#3e6cb2"),
        (1, "#b23ea6"),
        (2, "#b2843e"),
        (3, "#3eb24a"),
        (4, "#553eb2"),
        (5, "#b23e61"),
        (6, "#9bb23e"),
        (7, "#3eb28f"),
        (8, "#9b3eb2"),
        (9, "#b2613e"),
        (10, "#55b23e"),
    ],
)
def test_contrast_color_from_number(
    color_number: int,
    expected_color: str,
    template_renderer: TemplateRenderer,
) -> None:
    template = f"""
    {{% load style_tags %}}
    {{% contrast_color_from_number {color_number}%}}
    """

    assert template_renderer(template, strip=True) == expected_color


SQL_QUERIES = [
    SQLQueryInfo(**{**STANDARD_SQL_QUERY_INFO, "duration": 80}),  # type: ignore
    SQLQueryInfo(**{**STANDARD_SQL_QUERY_INFO, "duration": 40}),  # type: ignore
    SQLQueryInfo(**{**STANDARD_SQL_QUERY_INFO, "duration": 70}),  # type: ignore
    SQLQueryInfo(**{**STANDARD_SQL_QUERY_INFO, "duration": 10}),  # type: ignore
]


@pytest.mark.parametrize(
    "queries, current_index, expected_styles",
    [
        (
            SQL_QUERIES,
            0,
            "width: 40.000%; margin-left: 0.000%; background-color: #b2843e;",
        ),
        (
            SQL_QUERIES,
            1,
            "width: 20.000%; margin-left: 40.000%; background-color: #3eb24a;",
        ),
        (
            SQL_QUERIES,
            2,
            "width: 35.000%; margin-left: 60.000%; background-color: #3e6cb2;",
        ),
        (
            SQL_QUERIES,
            3,
            "width: 5.000%; margin-left: 95.000%; background-color: #b23ea6;",
        ),
    ],
)
def test_timeline_bar_styles(
    queries: list[SQLQueryInfo],
    current_index: int,
    expected_styles: str,
    template_renderer: TemplateRenderer,
) -> None:
    template = """
    {% load style_tags %}
    {% timeline_bar_styles queries total_time index %}
    """
    total_time = sum(query.duration for query in queries)

    context = {
        "queries": queries,
        "total_time": total_time,
        "index": current_index,
    }

    assert template_renderer(template, context=context, strip=True) == expected_styles
