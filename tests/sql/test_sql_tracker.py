from unittest.mock import Mock, PropertyMock
from uuid import UUID

import pytest
from psycopg2 import InternalError
from psycopg2._json import Json as PostgresJson
from psycopg2.extensions import (
    ISOLATION_LEVEL_AUTOCOMMIT,
    STATUS_BEGIN,
    STATUS_READY,
    TRANSACTION_STATUS_ACTIVE,
)

from requests_tracker.sql.sql_collector import SQLCollector
from requests_tracker.sql.sql_tracker import GLOBAL_SQL_TRACKER, SQLTracker, _local


def test_sql_trackers_nested() -> None:
    assert _local.get() == GLOBAL_SQL_TRACKER

    with SQLTracker() as sql_tracker1:
        assert _local.get() == sql_tracker1
        assert sql_tracker1._old_sql_trackers == [GLOBAL_SQL_TRACKER]

        with SQLTracker() as sql_tracker2:
            assert _local.get() == sql_tracker2
            assert sql_tracker2._old_sql_trackers == [sql_tracker1]

        assert _local.get() == sql_tracker1
        assert sql_tracker2._old_sql_trackers == []

    assert _local.get() == GLOBAL_SQL_TRACKER
    assert sql_tracker1._old_sql_trackers == []


def test_record__no_sql_collector() -> None:
    fake_method = Mock()
    database_cursor_mock = Mock()
    sql = "SELECT 1"
    params = ("fake_param",)

    with SQLTracker() as sql_tracker:
        sql_tracker.record(fake_method, database_cursor_mock, sql, params)

        assert sql_tracker._sql_collector is None
        fake_method.assert_called_once_with(database_cursor_mock, sql, params)


def test_record_no_database_wrapper() -> None:
    sql_collector = SQLCollector()

    with pytest.raises(RuntimeError) as runtime_error:
        with SQLTracker(sql_collector) as sql_tracker:
            sql_tracker.record(Mock(), Mock(), "SELECT 1", ("fake_param",))

    assert str(runtime_error.value) == "SQLTracker not correctly initialized"


def test_record__mock_sqlite_database_wrapper() -> None:
    sql_collector = SQLCollector()
    sql = "SELECT 1"
    params = ("fake_param",)
    alias = "default"
    vendor = "sqlite"
    fake_method = Mock()
    sqlite_wrapper_mock = Mock()
    sqlite_wrapper_mock.ops.last_executed_query.return_value = sql
    sqlite_wrapper_mock.alias = alias
    sqlite_wrapper_mock.vendor = vendor

    database_cursor_mock = Mock()

    with SQLTracker(sql_collector) as sql_tracker:
        sql_tracker.set_database_wrapper(sqlite_wrapper_mock)

        sql_tracker.record(fake_method, database_cursor_mock, sql, params)

        assert sql_tracker._sql_collector == sql_collector
        fake_method.assert_called_once_with(database_cursor_mock, sql, params)

    assert sql_collector.num_queries == 1
    assert sql_collector.queries[0].alias == alias
    assert sql_collector.queries[0].vendor == vendor
    assert sql_collector.queries[0].sql == sql
    assert sql_collector.queries[0].raw_sql == sql
    assert sql_collector.queries[0].params == '["fake_param"]'
    assert sql_collector.queries[0].raw_params == params
    assert sql_collector.queries[0].trans_id is None
    assert sql_collector.queries[0].trans_status is None
    assert sql_collector.queries[0].iso_level is None
    assert sql_collector.queries[0].is_select is True
    assert sql_collector.queries[0].is_slow is False
    assert sql_collector.queries[0].duplicate_count == 0
    assert sql_collector.queries[0].similar_count == 0


def test_record__mock_postgres_database_wrapper_connection_ready() -> None:
    sql_collector = SQLCollector()
    sql = "SELECT 1"
    params = (b"\x80", PostgresJson(adapted={"fake": "param"}))
    alias = "default"
    vendor = "postgresql"

    fake_method = Mock()
    connection = Mock()
    postgres_wrapper_mock = Mock()
    postgres_wrapper_mock.ops.last_executed_query.return_value = sql
    postgres_wrapper_mock.alias = alias
    postgres_wrapper_mock.vendor = vendor
    postgres_wrapper_mock.connection = connection
    connection.status = STATUS_READY
    connection.isolation_level = ISOLATION_LEVEL_AUTOCOMMIT
    connection.get_transaction_status.return_value = TRANSACTION_STATUS_ACTIVE

    database_cursor_mock = Mock()

    with SQLTracker(sql_collector) as sql_tracker:
        sql_tracker.set_database_wrapper(postgres_wrapper_mock)

        sql_tracker.record(
            fake_method,
            database_cursor_mock,
            sql,
            params,  # type: ignore
        )

        assert sql_tracker._sql_collector == sql_collector
        fake_method.assert_called_once_with(database_cursor_mock, sql, params)

    assert sql_collector.num_queries == 1
    assert sql_collector.queries[0].alias == alias
    assert sql_collector.queries[0].vendor == vendor
    assert sql_collector.queries[0].sql == sql
    assert sql_collector.queries[0].raw_sql == sql
    assert (
        sql_collector.queries[0].params
        == '["(encoded string)", "{\\"fake\\": \\"param\\"}"]'
    )
    assert sql_collector.queries[0].raw_params == params
    assert sql_collector.queries[0].trans_id is None
    assert sql_collector.queries[0].trans_status == TRANSACTION_STATUS_ACTIVE
    assert sql_collector.queries[0].iso_level == ISOLATION_LEVEL_AUTOCOMMIT
    assert sql_collector.queries[0].is_select is True
    assert sql_collector.queries[0].is_slow is False
    assert sql_collector.queries[0].duplicate_count == 0
    assert sql_collector.queries[0].similar_count == 0


def test_record__mock_postgres_database_wrapper_connection_begin() -> None:
    sql_collector = SQLCollector()
    sql = "SELECT 1"
    params = None
    alias = "default"
    vendor = "postgresql"

    fake_method = Mock()
    connection = Mock()
    postgres_wrapper_mock = Mock()
    postgres_wrapper_mock.ops.last_executed_query.return_value = sql
    postgres_wrapper_mock.alias = alias
    postgres_wrapper_mock.vendor = vendor
    postgres_wrapper_mock.connection = connection
    connection.status = STATUS_BEGIN
    connection.isolation_level = ISOLATION_LEVEL_AUTOCOMMIT
    connection.get_transaction_status.return_value = TRANSACTION_STATUS_ACTIVE

    database_cursor_mock = Mock()

    with SQLTracker(sql_collector) as sql_tracker:
        sql_tracker.set_database_wrapper(postgres_wrapper_mock)

        sql_tracker.record(fake_method, database_cursor_mock, sql, params)

        assert sql_tracker._sql_collector == sql_collector
        fake_method.assert_called_once_with(database_cursor_mock, sql, params)

    assert sql_collector.num_queries == 1
    assert sql_collector.queries[0].alias == alias
    assert sql_collector.queries[0].vendor == vendor
    assert sql_collector.queries[0].sql == sql
    assert sql_collector.queries[0].raw_sql == sql
    assert sql_collector.queries[0].params == "null"
    assert sql_collector.queries[0].raw_params == params
    assert isinstance(UUID(sql_collector.queries[0].trans_id), UUID)
    assert sql_collector.queries[0].trans_status == TRANSACTION_STATUS_ACTIVE
    assert sql_collector.queries[0].iso_level == ISOLATION_LEVEL_AUTOCOMMIT
    assert sql_collector.queries[0].is_select is True
    assert sql_collector.queries[0].is_slow is False
    assert sql_collector.queries[0].duplicate_count == 0
    assert sql_collector.queries[0].similar_count == 0


def test_record_mock_postgres_database_wrapper_connection_ready_and_begin() -> None:
    sql_collector = SQLCollector()
    sql = "SELECT 1"
    params = {"fake_param": "fake_value"}
    alias = "default"
    vendor = "postgresql"

    fake_method = Mock()
    connection = Mock()
    postgres_wrapper_mock = Mock()
    postgres_wrapper_mock.ops.last_executed_query.return_value = sql
    postgres_wrapper_mock.alias = alias
    postgres_wrapper_mock.vendor = vendor
    postgres_wrapper_mock.connection = connection
    type(connection).status = PropertyMock(side_effect=[STATUS_READY, STATUS_BEGIN])
    connection.InternalError = InternalError
    type(connection).isolation_level = PropertyMock(
        side_effect=[connection.InternalError]
    )
    connection.get_transaction_status.return_value = TRANSACTION_STATUS_ACTIVE

    database_cursor_mock = Mock()

    with SQLTracker(sql_collector) as sql_tracker:
        sql_tracker.set_database_wrapper(postgres_wrapper_mock)

        sql_tracker.record(fake_method, database_cursor_mock, sql, params)

        assert sql_tracker._sql_collector == sql_collector
        fake_method.assert_called_once_with(database_cursor_mock, sql, params)

    assert sql_collector.num_queries == 1
    assert sql_collector.queries[0].alias == alias
    assert sql_collector.queries[0].vendor == vendor
    assert sql_collector.queries[0].sql == sql
    assert sql_collector.queries[0].raw_sql == sql
    assert sql_collector.queries[0].params == '{"fake_param": "fake_value"}'
    assert sql_collector.queries[0].raw_params == params
    assert isinstance(UUID(sql_collector.queries[0].trans_id), UUID)
    assert sql_collector.queries[0].trans_status == TRANSACTION_STATUS_ACTIVE
    assert sql_collector.queries[0].iso_level == "unknown"
    assert sql_collector.queries[0].iso_level == "unknown"
    assert sql_collector.queries[0].is_select is True
    assert sql_collector.queries[0].is_slow is False
    assert sql_collector.queries[0].duplicate_count == 0
    assert sql_collector.queries[0].similar_count == 0
