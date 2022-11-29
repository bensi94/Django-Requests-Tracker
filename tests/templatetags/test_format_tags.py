import pytest

from tests.templatetags.conftest import TemplateRenderer


@pytest.mark.parametrize(
    "split_string, splitter, expected_result",
    [
        ("hello world", " ", "world"),
        ("hello.world", ".", "world"),
        ("hello,world", ",", "world"),
        ("hello.big.and.strange.world", ".", "world"),
    ],
)
def test_split_and_last(
    split_string: str,
    splitter: str,
    expected_result: str,
    template_renderer: TemplateRenderer,
) -> None:
    template = f"""
    {{% load format_tags %}}
    <div>{{{{ split_string|split_and_last:"{splitter}" }}}}</div>
    """
    context = {"split_string": split_string}

    result = template_renderer(template, context=context, strip=True)

    assert result == f"<div>{expected_result}</div>"


def test_split_and_last_default(template_renderer: TemplateRenderer) -> None:
    template = """
     {% load format_tags %}
     <div>{{ split_string|split_and_last }}</div>
     """
    context = {"split_string": "hello.big.and.strange.world"}

    result = template_renderer(template, context=context, strip=True)

    assert result == "<div>world</div>"


@pytest.mark.parametrize(
    "input_dict, key, expected_index",
    [
        ({"test_0": "value_0", "test_1": "value_1"}, "test_0", 0),
        ({"test_0": "value_0", "test_1": "value_1"}, "test_1", 1),
        ({"test_0": "value_0", "test_1": "value_1"}, "does_not_exist", None),
    ],
)
def test_dict_key_index(
    input_dict: dict[str, str],
    key: str,
    expected_index: int,
    template_renderer: TemplateRenderer,
) -> None:
    template = f"""
    {{% load format_tags %}}
    <div>{{{{ input_dict|dict_key_index:"{key}" }}}}</div>
    """
    context = {"input_dict": input_dict}

    result = template_renderer(template, context=context, strip=True)

    assert result == f"<div>{expected_index}</div>"


def test_simplify_sql(template_renderer: TemplateRenderer) -> None:
    template = """
    {% load format_tags %}
    <div>{% simplify_sql sql|safe %}</div>
    """
    sql = (
        'SELECT "auth_user.id", "auth_user.name" FROM "auth_user" '
        'WHERE "customers_client"."schema_name" = %s LIMIT 21'
    )

    context = {"sql": sql}

    result = template_renderer(template, context=context, strip=True)

    expected_formatted_sql = (
        "&lt;strong&gt;SELECT&lt;/strong&gt; &amp;#8226;&amp;#8226;&amp;#8226; "
        "&lt;strong&gt;FROM&lt;/strong&gt; "
        "&amp;quot;auth_user&amp;quot; &lt;strong&gt;WHERE&lt;/strong&gt; "
        "&amp;quot;customers_client&amp;quot;.&amp;quot;schema_name&amp;quot; = %s "
        "&lt;strong&gt;LIMIT&lt;/strong&gt; 21"
    )
    assert result == f"<div>{expected_formatted_sql}</div>"


def test_format_sql(template_renderer: TemplateRenderer) -> None:
    template = """
    {% load format_tags %}
    <div>{% format_sql sql|safe %}</div>
    """
    sql = (
        'SELECT "auth_user.id", "auth_user.name" FROM "auth_user" '
        'WHERE "customers_client"."schema_name" = %s LIMIT 21'
    )

    context = {"sql": sql}

    result = template_renderer(template, context=context, strip=True)

    expected_formatted_sql = (
        "&lt;strong&gt;SELECT&lt;/strong&gt; &amp;quot;auth_user.id&amp;quot;, "
        "&lt;br/&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;"
        "&amp;nbsp;&amp;quot;auth_user.name&amp;quot; "
        "&lt;strong&gt;&lt;br/&gt;&amp;nbsp;&amp;nbsp;FROM&lt;/strong&gt; "
        "&amp;quot;auth_user&amp;quot; "
        "&lt;strong&gt;&lt;br/&gt;&amp;nbsp;WHERE&lt;/strong&gt; "
        "&amp;quot;customers_client&amp;quot;.&amp;quot;schema_name&amp;quot; = %s "
        "&lt;strong&gt;&lt;br/&gt;&amp;nbsp;LIMIT&lt;/strong&gt; 21"
    )
    assert result == f"<div>{expected_formatted_sql}</div>"
