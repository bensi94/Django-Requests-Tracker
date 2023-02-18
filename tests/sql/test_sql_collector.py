from typing import Generator, Tuple

import pytest
from django.conf import LazySettings
from django.contrib.auth.models import User
from django.db import connections

from requests_tracker.settings import get_config
from requests_tracker.sql.sql_collector import SQLCollector
from requests_tracker.sql.sql_hook import install_sql_hook
from requests_tracker.sql.sql_tracker import SQLTracker


@pytest.fixture
def sql_collector() -> Generator[SQLCollector, None, None]:
    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.backends.utils import CursorWrapper

    real_execute = CursorWrapper.execute
    real_executemany = CursorWrapper.executemany
    real_call_proc = CursorWrapper.callproc
    real_connect = BaseDatabaseWrapper.connect

    install_sql_hook()
    sql_collector = SQLCollector()
    with SQLTracker(sql_collector) as sql_tracker:
        sql_tracker.set_database_wrapper(connections["default"])

        yield sql_collector

    # Reset to default before pytest-django teardown begins
    CursorWrapper.execute = real_execute  # type: ignore
    CursorWrapper.executemany = real_executemany  # type: ignore
    CursorWrapper.callproc = real_call_proc  # type: ignore
    BaseDatabaseWrapper.connect = real_connect  # type: ignore


@pytest.mark.django_db
def test_record__single_query(sql_collector: SQLCollector) -> None:
    """Tests that SQLCollector wraps and collects a single query correctly"""
    result = User.objects.filter(username="test").exists()

    assert result is False
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
def test_record__executemany(sql_collector: SQLCollector) -> None:
    sql = "INSERT INTO django_content_type (app_label, model) VALUES (%s, %s)"
    with connections["default"].cursor() as cursor:
        cursor.executemany(sql, [("auth", "test1"), ("auth", "test2")])

    assert len(sql_collector.queries) == sql_collector.num_queries == 1
    query = sql_collector.queries[0]
    assert query.sql == sql
    assert query.params == '[["auth", "test1"], ["auth", "test2"]]'
    assert query.raw_sql == (
        "INSERT INTO django_content_type (app_label, model) "
        "VALUES ('''auth''', '''auth'''), ('''test1''', '''test2''')"
    )
    assert query.vendor == "sqlite"
    assert query.alias == "default"
    assert query.is_select is False
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


@pytest.mark.parametrize(
    "ignore_patterns, expected_number_of_queries",
    [
        ((), 2),
        ((r".*username.*test",), 1),
        ((r".*username.*another_username.*",), 1),
        ((r".*username.*",), 0),
        (
            (
                r".*username.*another_username.*",
                r".*username.*test.*",
            ),
            0,
        ),
    ],
)
@pytest.mark.django_db
def test_filtered_queries(
    sql_collector: SQLCollector,
    settings: LazySettings,
    ignore_patterns: Tuple[str],
    expected_number_of_queries: int,
) -> None:
    # Clear config cache to ensure settings are reloaded
    get_config.cache_clear()
    settings.REQUESTS_TRACKER_CONFIG[  # type: ignore
        "IGNORE_SQL_PATTERNS"
    ] = ignore_patterns
    User.objects.filter(username="test").exists()
    User.objects.filter(username="another_username").exists()

    assert sql_collector.num_queries == expected_number_of_queries
