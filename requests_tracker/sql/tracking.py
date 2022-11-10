import contextlib
import datetime
import json
from decimal import Decimal
from time import time
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable, Iterator, Mapping, ParamSpec, Sequence
from uuid import UUID

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.utils import CursorWrapper
from django.utils.encoding import force_str

from requests_tracker import settings as dr_settings
from requests_tracker.sql.dataclasses import SQLQueryInfo
from requests_tracker.stack_trace import get_stack_trace

try:
    from psycopg2._json import Json as PostgresJson
    from psycopg2.extensions import STATUS_IN_TRANSACTION
except ImportError:
    PostgresJson = None  # type: ignore
    STATUS_IN_TRANSACTION = None  # type: ignore

if TYPE_CHECKING:
    from requests_tracker.sql.sql_collector import SQLCollector

    DecodeReturn = list["DecodeReturn" | str] | dict[str, "DecodeReturn" | str] | str

P = ParamSpec("P")
QuoteParamsReturn = dict[str, str] | list[str] | None
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


class SQLQueryTriggered(Exception):
    """Thrown when template panel triggers a query"""


class CustomDataBaseWrapper(BaseDatabaseWrapper):
    """Correctly type hinted database connection wrapper"""

    original_cursor: Callable[[], CursorWrapper]
    original_chunked_cursor: Callable[[], CursorWrapper]


class CustomCursorWrapper:
    """
    Wraps a cursor and logs queries.
    """

    def __init__(
        self,
        cursor: CursorWrapper,
        db: CustomDataBaseWrapper,
        logger: "SQLCollector",
    ) -> None:
        self.cursor = cursor
        # Instance of a BaseDatabaseWrapper subclass
        self.db = db
        # logger must implement a ``record`` method
        self.logger = logger

    def _quote_expr(self, element: Any) -> str:
        if isinstance(element, str):
            return "'%s'" % element.replace("'", "''")
        else:
            return repr(element)

    def _quote_params(self, params: ExecuteParametersOrSequence) -> QuoteParamsReturn:
        if params is None:
            return params
        if isinstance(params, dict):
            return {key: self._quote_expr(value) for key, value in params.items()}
        return [self._quote_expr(p) for p in params]

    def _decode(self, param: ExecuteParametersOrSequence) -> "DecodeReturn":
        if PostgresJson and isinstance(param, PostgresJson):
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

    def _record(
        self,
        method: Callable[[str, Any], Any],
        sql: str,
        params: ExecuteParametersOrSequence,
    ) -> Any:  # sourcery skip: remove-unnecessary-cast
        alias = self.db.alias
        vendor = self.db.vendor

        if vendor == "postgresql":
            # The underlying DB connection (as opposed to Django's wrapper)
            conn = self.db.connection
            initial_conn_status = conn.status

        start_time = time()
        try:
            return method(sql, params)
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
                raw_sql=self.db.ops.last_executed_query(
                    self.cursor, sql, self._quote_params(params)
                ),
                params=_params,
                raw_params=params,
                stacktrace=get_stack_trace(skip=2),
                start_time=start_time,
                stop_time=stop_time,
                is_slow=duration > dr_settings.get_config()["SQL_WARNING_THRESHOLD"],
                is_select=sql.lower().strip().startswith("select"),
            )

            if vendor == "postgresql":
                # If an erroneous query was ran on the connection, it might
                # be in a state where checking isolation_level raises an
                # exception.
                try:
                    iso_level = conn.isolation_level
                except conn.InternalError:
                    iso_level = "unknown"
                # PostgreSQL does not expose any sort of transaction ID, so it is
                # necessary to generate synthetic transaction IDs here.  If the
                # connection was not in a transaction when the query started, and was
                # after the query finished, a new transaction definitely started, so get
                # a new transaction ID from logger.new_transaction_id().  If the query
                # was in a transaction both before and after executing, make the
                # assumption that it is the same transaction and get the current
                # transaction ID from logger.current_transaction_id().  There is an edge
                # case where Django can start a transaction before the first query
                # executes, so in that case logger.current_transaction_id() will
                # generate a new transaction ID since one does not already exist.
                final_conn_status = conn.status
                if final_conn_status == STATUS_IN_TRANSACTION:
                    if initial_conn_status == STATUS_IN_TRANSACTION:
                        trans_id = self.logger.current_transaction_id(alias)
                    else:
                        trans_id = self.logger.new_transaction_id(alias)
                else:
                    trans_id = None

                sql_query_info.trans_id = trans_id
                sql_query_info.trans_status = conn.get_transaction_status()
                sql_query_info.iso_level = iso_level

            self.logger.record(sql_query_info)

    def callproc(self, procname: str, params: ExecuteParameters = None) -> Any:
        return self._record(self.cursor.callproc, procname, params)

    def execute(self, sql: str, params: ExecuteParameters = None) -> Any:
        return self._record(self.cursor.execute, sql, params)

    def executemany(self, sql: str, param_list: Sequence[ExecuteParameters]) -> Any:
        return self._record(self.cursor.executemany, sql, param_list)

    def __getattr__(self, attr: Any) -> Any:
        return getattr(self.cursor, attr)

    def __iter__(self) -> Iterator[tuple[Any, ...]]:
        return iter(self.cursor)

    def __enter__(self) -> "CustomCursorWrapper":
        return self

    def __exit__(
        self,
        exc_type: BaseException | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def wrap_cursor(
    connection: CustomDataBaseWrapper,
    statistics_collector: "SQLCollector",
) -> Callable[P, CustomCursorWrapper] | None:
    if hasattr(connection, "original_cursor"):
        return None
    connection.original_cursor = connection.cursor
    connection.original_chunked_cursor = connection.chunked_cursor

    def cursor(*args: P.args, **kwargs: P.kwargs) -> CustomCursorWrapper:
        # Per the DB API cursor() does not accept any arguments. There's
        # some code in the wild which does not follow that convention,
        # so we pass on the arguments even though it's not clean.
        # See:
        # https://github.com/jazzband/django-debug-toolbar/pull/615
        # https://github.com/jazzband/django-debug-toolbar/pull/896
        return CustomCursorWrapper(
            connection.original_cursor(*args, **kwargs),
            connection,
            statistics_collector,
        )

    def chunked_cursor(
        *args: P.args, **kwargs: P.kwargs
    ) -> CursorWrapper | CustomCursorWrapper:
        # prevent double wrapping
        # solves https://github.com/jazzband/django-debug-toolbar/issues/1239
        cursor = connection.original_chunked_cursor(*args, **kwargs)
        return (
            cursor
            if isinstance(cursor, CursorWrapper)
            else CustomCursorWrapper(cursor, connection, statistics_collector)
        )

    setattr(connection, "cursor", cursor)
    setattr(connection, "chunked_cursor", chunked_cursor)
    return cursor


def unwrap_cursor(connection: CustomDataBaseWrapper) -> None:
    if hasattr(connection, "original_cursor"):
        # Sometimes the cursor()/chunked_cursor() methods of the DatabaseWrapper
        # instance are already monkey patched before wrap_cursor() is called.  (In
        # particular, Django's SimpleTestCase monkey patches those methods for any
        # disallowed databases to raise an exception if they are accessed.)  Thus only
        # delete our monkey patch if the method we saved is the same as the class
        # method.  Otherwise, restore the prior monkey patch from our saved method.
        if connection.original_cursor == connection.__class__.cursor:  # type: ignore
            del connection.cursor
        else:
            setattr(connection, "cursor", connection.original_cursor)
        del connection.original_cursor

        if (
            connection.original_chunked_cursor  # type: ignore
            == connection.__class__.chunked_cursor
        ):
            del connection.chunked_cursor
        else:
            setattr(connection, "chunked_cursor", connection.original_chunked_cursor)
        del connection.original_chunked_cursor
