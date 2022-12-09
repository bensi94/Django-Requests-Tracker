import os
import re
from pprint import pformat
from typing import Any

from django import template
from django.utils.safestring import mark_safe

from requests_tracker.sql.sql_parser import parse_sql

register = template.Library()


@register.filter
def split_and_last(value: str, splitter: str = ".") -> str:
    """
    Takes in a string and splits it and returns the last item in the split.
    """
    return value.split(splitter)[-1]


@register.filter
def dict_key_index(input_dict: dict[str, Any], key: str) -> int | None:
    """
    Takes in a string key and returns the list index of the key.
    Returns None if key is not found.
    """
    return next(
        (i for i, dict_key in enumerate(input_dict.keys()) if dict_key == key),
        None,
    )


@register.filter
def pprint_datastructure_values(value: Any) -> str:
    return mark_safe(
        f"<pre>{pformat(value)}</pre>"
        if isinstance(value, (dict, list, tuple))
        else str(value)
    )


@register.simple_tag
def simplify_sql(sql: str) -> str:
    """
    Takes in sql string and reformats it for a collapsed view.
    """
    parsed_sql = parse_sql(sql, align_indent=False)
    simplify_re = re.compile(r"SELECT</strong> (...........*?) <strong>FROM")
    return simplify_re.sub(
        r"SELECT</strong> &#8226;&#8226;&#8226; <strong>FROM", parsed_sql
    )


@register.simple_tag
def format_sql(sql: str) -> str:
    """
    Reformats SQL with align indents and bolded keywords
    """
    return parse_sql(sql, align_indent=True)


@register.filter
def simplify_path(path: str) -> str:
    """
    Takes in python full path and returns it relative to the current running
    django project or site_packages.

    e.g.
    "/Users/my_user/Documents/django-project/venv/lib/python3.10/
    site-packages/django/contrib/staticfiles/handlers.py"
    =>
    ".../site-packages/django/contrib/staticfiles/handlers.py"
    """

    if "/site-packages" in path:
        return f"...{ path[path.index('/site-packages'): ] }"
    elif path.startswith(os.getcwd()):
        # This should be the directory of the django project
        return f"...{path[len(os.getcwd()): ] }"

    return path
