import colorsys

from django import template
from django.template.defaultfilters import stringfilter

from requests_tracker.sql.dataclasses import SQLQueryInfo

register = template.Library()


@register.filter("method_class")
@stringfilter
def method_bulma_color_class(method: str) -> str:
    """Takes in HTTP method and returns a bulma class for colorization"""
    match method:  # noqa: E999 (ruff does not recognise pattern matching)
        case "GET":
            return "is-info"
        case "POST":
            return "is-success"
        case "PUT":
            return "is-warning"
        case "PATCH":
            return "is-warning is-light"
        case "DELETE":
            return "is-danger"
        case _:
            return ""


@register.filter("status_code_class")
@stringfilter
def status_code_bulma_color_class(status_code_str: str) -> str:
    """Takes in HTTP status code and returns a bulma class for colorization"""

    try:
        status_code = int(status_code_str)
    except ValueError:
        status_code = 0

    if 200 > status_code >= 100:
        return "is-info"
    elif 300 > status_code >= 200:
        return "is-success"
    elif 400 > status_code >= 300:
        return "is-link"
    elif 500 > status_code >= 400:
        return "is-warning"
    elif status_code >= 500:
        return "is-danger"

    return "is-dark"


@register.simple_tag
def contrast_color_from_number(color_number: int) -> str:
    starting_color = 0.6  # Blue ish color
    shift = 0.1 * (color_number // 4)  # Shift by 10% for every 4 numbers
    color_addition = 0.25 * color_number  # Cycle the color scheme 25% at a time

    hue = (starting_color + color_addition + shift) % 1  # Only want decimal part
    saturation = 0.65
    value = 0.7

    hsv_tuple = (hue, saturation, value)

    return "#" + "".join(
        f"{int(color * 255):02x}" for color in colorsys.hsv_to_rgb(*hsv_tuple)
    )


@register.simple_tag
def timeline_bar_styles(
    queries: list[SQLQueryInfo],
    total_sql_time: float,
    current_index: int,
) -> str:
    current_query = queries[current_index]
    percentage = (current_query.duration / total_sql_time) * 100
    offset_percentage = (
        sum(query.duration for query in queries[:current_index]) / total_sql_time * 100
    )

    color = contrast_color_from_number(current_index + 100)
    return (
        f"width: {percentage:.3f}%; "
        f"margin-left: {offset_percentage:.3f}%; "
        f"background-color: {color};"
    )
