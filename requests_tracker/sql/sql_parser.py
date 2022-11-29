from functools import lru_cache
from typing import Generator

import sqlparse  # type: ignore
from django.utils.html import escape

SQLParseFilterGenerator = Generator[tuple[sqlparse.tokens.Token, str], None, None]


class BoldKeywordFilter:
    """sqlparse filter to bold SQ = L keywords"""

    @staticmethod
    def process(stream: SQLParseFilterGenerator) -> SQLParseFilterGenerator:
        """Process the token stream"""
        for token_type, value in stream:
            is_keyword = token_type in sqlparse.tokens.Keyword
            if is_keyword:
                yield sqlparse.tokens.Text, "<strong>"
            yield token_type, escape(value)
            if is_keyword:
                yield sqlparse.tokens.Text, "</strong>"


@lru_cache(maxsize=128)
def parse_sql(sql: str, align_indent: bool) -> str:
    stack = get_filter_stack(aligned_indent=align_indent)
    return "".join(stack.run(sql))


@lru_cache(maxsize=None)
def get_filter_stack(
    aligned_indent: bool,
) -> sqlparse.engine.FilterStack:
    stack = sqlparse.engine.FilterStack()
    stack.enable_grouping()
    if aligned_indent:
        stack.stmtprocess.append(
            sqlparse.filters.AlignedIndentFilter(char="&nbsp;", n="<br/>")
        )
    stack.preprocess.append(BoldKeywordFilter())  # add our custom filter
    stack.postprocess.append(sqlparse.filters.SerializerUnicode())  # tokens -> strings
    return stack
