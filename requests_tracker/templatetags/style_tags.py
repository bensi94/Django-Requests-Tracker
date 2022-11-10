from django import template
from django.template.defaultfilters import stringfilter

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
