from typing import Any, Sequence

from requests_tracker.sql.sql_tracker import ExecuteParameters, SQLTracker


def install_sql_hook() -> None:
    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.backends.utils import CursorWrapper

    real_execute = CursorWrapper.execute
    real_executemany = CursorWrapper.executemany
    real_call_proc = CursorWrapper.callproc
    real_connect = BaseDatabaseWrapper.connect

    def execute(self: CursorWrapper, sql: str, params: ExecuteParameters = None) -> Any:
        sql_tracker = SQLTracker.current
        sql_tracker.set_database_cursor(self)
        sql_tracker.record(real_execute, self, sql, params)

    def executemany(
        self: CursorWrapper,
        sql: str,
        param_list: Sequence[ExecuteParameters],
    ) -> Any:
        sql_tracker = SQLTracker.current
        sql_tracker.set_database_cursor(self)
        sql_tracker.record(real_executemany, self, sql, param_list)

    def callproc(
        self: CursorWrapper,
        procname: str,
        params: ExecuteParameters = None,
    ) -> Any:
        sql_tracker = SQLTracker.current
        sql_tracker.set_database_cursor(self)
        sql_tracker.record(real_call_proc, self, procname, params)

    def connect(self: BaseDatabaseWrapper) -> Any:
        real_connect(self)
        sql_tracker = SQLTracker.current
        sql_tracker.set_database_wrapper(self)

    CursorWrapper.execute = execute  # type: ignore
    CursorWrapper.executemany = executemany  # type: ignore
    CursorWrapper.callproc = callproc  # type: ignore
    BaseDatabaseWrapper.connect = connect  # type: ignore
