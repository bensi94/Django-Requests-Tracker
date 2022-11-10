from typing import Any, Callable

import pytest
from django.template import Context, Template
from mypy_extensions import DefaultArg

TemplateRenderer = Callable[
    [
        str,
        DefaultArg(dict | None, "context"),  # noqa F821
        DefaultArg(bool, "strip"),  # noqa F821
    ],
    str,
]


@pytest.fixture
def template_renderer() -> TemplateRenderer:
    def inner_renderer(
        template_str: str,
        context: dict[str, Any] | None = None,
        strip: bool = False,
    ) -> str:
        result = Template(template_str).render(Context(context))

        return result.replace("\n", "").strip() if strip else result

    return inner_renderer
