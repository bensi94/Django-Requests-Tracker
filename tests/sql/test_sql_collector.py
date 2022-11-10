from typing import Generator

import pytest
from django.contrib.auth.models import User
from django.db import connections

from requests_tracker.sql.sql_collector import SQLCollector
from requests_tracker.sql.tracking import CustomCursorWrapper


@pytest.fixture
def sql_collector() -> Generator[SQLCollector, None, None]:
    sql_collector = SQLCollector()
    yield sql_collector
    sql_collector.unwrap()


@pytest.mark.django_db
def test_record__single_query(sql_collector: SQLCollector) -> None:
    """Tests that SQLCollector wraps and collects a single query correctly"""
    result = User.objects.filter(username="test").exists()

    assert result is False
    assert type(connections.all()[0].cursor()) is CustomCursorWrapper  # type: ignore
    assert len(sql_collector.queries) == sql_collector.num_queries == 1
    query = sql_collector.queries[0]
    assert (
        query.sql
        == 'SELECT %s AS "a" FROM "auth_user" WHERE "auth_user"."username" = %s LIMIT 1'
    )
    assert query.params == '[1, "test"]'
    assert query.raw_sql == (
        'SELECT \'1\' AS "a" FROM "auth_user" WHERE "auth_user"."username" = '
        "'''test''' LIMIT 1"
    )
    assert query.vendor == "sqlite"
    assert query.alias == "default"
    assert query.is_select is True
    assert query.is_slow is False
    assert query.similar_count == 0
    assert query.duplicate_count == 0
    assert query.duration > 0


@pytest.mark.django_db
def test_generate_statistics__duplicate_queries(sql_collector: SQLCollector) -> None:
    """Tests that generate_statistics counts duplicate queries correctly"""
    query_result_1 = User.objects.filter(username="test").exists()
    query_result_2 = User.objects.filter(username="test").exists()
    sql_collector.generate_statistics()

    assert query_result_1 == query_result_2
    assert sql_collector.num_queries == 2
    assert sql_collector.total_duplicate_queries == 2
    assert sql_collector.total_similar_queries == 2
    query_1, query_2 = sql_collector.queries
    assert query_1.sql == query_2.sql
    assert query_1.raw_sql == query_2.raw_sql
    assert query_1.params == query_2.params == '[1, "test"]'
    assert query_1.duplicate_count == query_2.duplicate_count == 2
    assert query_1.similar_count == query_2.similar_count == 2


@pytest.mark.django_db
def test_generate_statistics__similar_queries_not_duplicates(
    sql_collector: SQLCollector,
) -> None:
    """Tests that generate_statistics counts non-duplicate, similar queries correctly"""
    query_result_1 = User.objects.filter(username="test").exists()
    query_result_2 = User.objects.filter(username="another_username").exists()
    sql_collector.generate_statistics()

    assert query_result_1 == query_result_2
    assert sql_collector.num_queries == 2
    assert sql_collector.total_duplicate_queries == 0
    assert sql_collector.total_similar_queries == 2
    query_1, query_2 = sql_collector.queries
    assert query_1.sql == query_2.sql
    assert query_1.raw_sql != query_2.raw_sql
    assert query_1.params != query_2.params
    assert query_1.duplicate_count == query_2.duplicate_count == 0
    assert query_1.similar_count == query_2.similar_count == 2
