import contextlib
import datetime
import json
import re
import types
from contextvars import ContextVar
from decimal import Decimal
from time import time
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence
from uuid import UUID

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.utils import CursorWrapper
from django.utils.encoding import force_str

from requests_tracker import settings as dr_settings
from requests_tracker.sql.dataclasses import SQLQueryInfo
from requests_tracker.sql.sql_collector import SQLCollector
from requests_tracker.stack_trace import get_stack_trace

try:
    from psycopg2._json import Json as PostgresJson
    from psycopg2.extensions import STATUS_IN_TRANSACTION
except ImportError:
    PostgresJson = None  # type: ignore
    STATUS_IN_TRANSACTION = None  # type: ignore

if TYPE_CHECKING:

    DecodeReturn = list["DecodeReturn" | str] | dict[str, "DecodeReturn" | str] | str

SQLType = (
    None
    | bool
    | int
    | float
    | Decimal
    | str
    | bytes
    | datetime.date
    | datetime.datetime
    | UUID
    | tuple[Any, ...]
    | list[Any]
)

ExecuteParameters = Sequence[SQLType] | Mapping[str, SQLType] | None
ExecuteParametersOrSequence = ExecuteParameters | Sequence[ExecuteParameters]

QuoteParamsReturn = dict[str, str] | list[str] | None

_local: ContextVar["SQLTracker"] = ContextVar("current_sql_tracker")


class SQLTrackerMeta(type):
    @property
    def current(cls) -> "SQLTracker":
        """Returns the current instance of the sql tracker"""
        current_sql_tracker = _local.get(None)

        if current_sql_tracker is None:
            current_sql_tracker = SQLTracker()
            _local.set(current_sql_tracker)

        return current_sql_tracker


class SQLTracker(metaclass=SQLTrackerMeta):
    _old_sql_trackers: list["SQLTracker"]
    _sql_collector: SQLCollector | None
    database_wrapper: BaseDatabaseWrapper | None

    def __init__(self, sql_collector: SQLCollector | None = None) -> None:
        self._old_sql_trackers = []
        self._sql_collector = sql_collector
        self.database_wrapper = None

    def __enter__(self) -> "SQLTracker":
        self._old_sql_trackers.append(SQLTracker.current)
        _local.set(self)
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_value: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        old = self._old_sql_trackers.pop()
        _local.set(old)

    def set_database_wrapper(self, database_wrapper: BaseDatabaseWrapper) -> None:
        self.database_wrapper = database_wrapper

    @staticmethod
    def _quote_expr(element: Any) -> str:
        if isinstance(element, str):
            return f"""'{element.replace("'", "''")}'"""
        else:
            return repr(element)

    def _quote_params(self, params: ExecuteParametersOrSequence) -> QuoteParamsReturn:
        if params is None:
            return params
        if isinstance(params, dict):
            return {key: self._quote_expr(value) for key, value in params.items()}
        return [self._quote_expr(p) for p in params]

    def _get_raw_sql(
        self,
        cursor_self: CursorWrapper,
        sql: str,
        params: ExecuteParametersOrSequence,
        many: bool,
        vendor: str,
    ) -> str:

        # This is a hacky way to get the parameters correct for sqlite in executemany
        if (
            vendor == "sqlite"
            and many
            and isinstance(params, (tuple, list))
            and isinstance(params[0], (tuple, list))
        ):
            final_params: list[str] = []
            part_to_replace = re.search(r"(\(\s*%s.*\))", sql)[1]  # type: ignore
            sql = sql.replace(
                part_to_replace, ", ".join(part_to_replace for _ in params)
            )
            for current_params in zip(*params):  # noqa: B905
                final_params.extend(current_params)

            return self.database_wrapper.ops.last_executed_query(  # type: ignore
                cursor_self,
                sql,
                self._quote_params(final_params),
            )

        return self.database_wrapper.ops.last_executed_query(  # type: ignore
            cursor_self,
            sql,
            self._quote_params(params),
        )

    def _decode(self, param: ExecuteParametersOrSequence) -> "DecodeReturn":
        if PostgresJson is not None and isinstance(param, PostgresJson):
            return param.dumps(param.adapted)

        # If a sequence type, decode each element separately
        if isinstance(param, (tuple, list)):
            return [self._decode(element) for element in param]

        # If a dictionary type, decode each value separately
        if isinstance(param, dict):
            return {key: self._decode(value) for key, value in param.items()}

        # make sure datetime, date and time are converted to string by force_str
        CONVERT_TYPES = (datetime.datetime, datetime.date, datetime.time)
        try:
            return force_str(param, strings_only=not isinstance(param, CONVERT_TYPES))
        except UnicodeDecodeError:
            return "(encoded string)"

    @staticmethod
    def _get_postgres_isolation_level(conn: Any) -> Any:
        """
        If an erroneous query was ran on the connection, it might
        be in a state where checking isolation_level raises an exception.
        """
        try:
            return conn.isolation_level
        except conn.InternalError:
            return "unknown"

    def _get_postgres_transaction_id(
        self,
        conn: Any,
        initial_conn_status: int,
        alias: str,
    ) -> str | None:
        """
        PostgreSQL does not expose any sort of transaction ID, so it is necessary to
        generate synthetic transaction IDs here. If the connection was not in a
        transaction when the query started, and was after the query finished, a new
        transaction definitely started, so get a new transaction ID from
        logger.new_transaction_id(). If the query was in a transaction both before and
        after executing, make the assumption that it is the same transaction and get the
        current transaction ID from logger.current_transaction_id().
        There is an edge case where Django can start a transaction before the first
        query executes, so in that case logger.current_transaction_id() will generate
        a new transaction ID since one does not already exist.
        """
        final_conn_status = conn.status
        if (
            final_conn_status == STATUS_IN_TRANSACTION
            and self._sql_collector is not None
        ):
            if initial_conn_status == STATUS_IN_TRANSACTION:
                return self._sql_collector.current_transaction_id(alias)
            else:
                return self._sql_collector.new_transaction_id(alias)
        return None

    def record(
        self,
        method: Callable[[CursorWrapper, str, Any], Any],
        cursor_self: CursorWrapper,
        sql: str,
        params: ExecuteParametersOrSequence,
        many: bool = False,
    ) -> Any:  # sourcery skip: remove-unnecessary-cast

        # If we're not tracking SQL, just call the original method
        if self._sql_collector is None:
            return method(cursor_self, sql, params)

        if self.database_wrapper is None:
            raise RuntimeError("SQLTracker not correctly initialized")

        alias = self.database_wrapper.alias
        vendor = self.database_wrapper.vendor

        if vendor == "postgresql":
            # The underlying DB connection (as opposed to Django's wrapper)
            conn = self.database_wrapper.connection
            initial_conn_status = conn.status

        start_time = time()
        try:
            return method(cursor_self, sql, params)
        finally:
            stop_time = time()
            duration = (stop_time - start_time) * 1000
            _params = ""
            with contextlib.suppress(TypeError):
                _params = json.dumps(self._decode(params))
            # Sql might be an object (such as psycopg Composed).
            # For logging purposes, make sure it's str.
            sql = str(sql)

            sql_query_info = SQLQueryInfo(
                vendor=vendor,
                alias=alias,
                sql=sql,
                duration=duration,
                raw_sql=self._get_raw_sql(cursor_self, sql, params, many, vendor),
                params=_params,
                raw_params=params,
                stacktrace=get_stack_trace(skip=2),
                start_time=start_time,
                stop_time=stop_time,
                is_slow=duration > dr_settings.get_config()["SQL_WARNING_THRESHOLD"],
                is_select=sql.lower().strip().startswith("select"),
            )

            if vendor == "postgresql":
                sql_query_info.trans_id = self._get_postgres_transaction_id(
                    conn=conn,
                    initial_conn_status=initial_conn_status,
                    alias=alias,
                )
                sql_query_info.trans_status = conn.get_transaction_status()
                sql_query_info.iso_level = self._get_postgres_isolation_level(conn)

            self._sql_collector.record(sql_query_info)


GLOBAL_SQL_TRACKER = SQLTracker()
_local.set(GLOBAL_SQL_TRACKER)
